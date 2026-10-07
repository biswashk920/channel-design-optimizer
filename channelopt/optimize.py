"""Design routines: best hydraulic sections, constrained optimisation, comparison."""
import math

import numpy as np
from scipy.optimize import brentq

from .checks import make_design
from .inputs import Inputs, NoSolution
from .sections import G, R_QMAX, R_VMAX, Circ, Trap, flow, normal_depth

Z_BEST = 1.0 / math.sqrt(3.0)          # half-hexagon side slope
OBJ_NAME = {"area": "gross section area", "flow_area": "water flow area", "perimeter": "wetted perimeter",
            "cost": "cost proxy (relative units)"}


def golden(f, a, b, tol=1e-10, maxit=200):
    """Golden-section search for the minimum of f on [a, b]."""
    gr = (math.sqrt(5.0) - 1.0) / 2.0
    c, d = b - gr * (b - a), a + gr * (b - a)
    fc, fd = f(c), f(d)
    for _ in range(maxit):
        if abs(b - a) < tol * (1.0 + abs(a) + abs(b)):
            break
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - gr * (b - a)
            fc = f(c)
        else:
            a, c, fc = c, d, fd
            d = a + gr * (b - a)
            fd = f(d)
    return (a + b) / 2.0


def _make(sec, inp, label, option):
    return make_design(sec, inp, normal_depth(sec, inp.Q, inp.S, inp.n), label, option)


# ---------------------------------------------------------------- best hydraulic
def best_for_z(inp, z, label, option):
    """Best hydraulic trapezoid for a given z: b/y = 2(sqrt(1+z^2) - z). z=0 gives b = 2y."""
    m = 2.0 * (math.sqrt(1.0 + z * z) - z)
    g = lambda y: flow(Trap(m * y, z), y, inp.S, inp.n) - inp.Q
    hi = 1.0
    while g(hi) < 0:
        hi *= 2.0
        if hi > 1e5:
            raise NoSolution("No solution for the best hydraulic section.")
    y = brentq(g, 1e-9, hi, xtol=1e-13, rtol=1e-12, maxiter=300)
    return make_design(Trap(m * y, z), inp, y, label, option)


# ---------------------------------------------------------------- 1-variable scan
def _scan_b(inp, z, label, option, N=400):
    """Search the bottom width b for a fixed side slope z."""
    b0 = best_for_z(inp, z, label, option)["b"]
    bs = sorted(set(np.geomspace(0.05 * b0, 20 * b0, N).tolist() + [b0]))
    rows = []
    for b in bs:
        try:
            rows.append(_make(Trap(b, z), inp, label, option))
        except NoSolution:
            continue
    curve = [{"b": d["b"], "A": d["A"], "P": d["P"], "y": d["y"], "obj": d["obj"], "ok": d["ok"]}
             for d in rows]
    feas = [d for d in rows if d["ok"]]
    if not feas:
        return min(rows, key=lambda d: d["viol"]), curve, False
    best = min(feas, key=lambda d: d["obj"])
    i = rows.index(best)
    lo, hi = rows[max(i - 1, 0)]["b"], rows[min(i + 1, len(rows) - 1)]["b"]
    big = best["obj"] * 100.0

    def pen(b):
        d = _make(Trap(b, z), inp, label, option)
        return d["obj"] if d["ok"] else big * (1.0 + d["viol"])

    if hi > lo:
        cand = _make(Trap(golden(pen, lo, hi), z), inp, label, option)
        if cand["ok"] and cand["obj"] < best["obj"]:
            best = cand
    return best, curve, True


def optimize_rect(inp):
    d, curve, feas = _scan_b(inp, 0.0, "Rectangular", "optimised width")
    d["curve"], d["feasible"] = curve, feas
    return d


def optimize_trap(inp):
    mode = inp.trap_mode
    if mode == "best_overall":
        d = best_for_z(inp, Z_BEST, "Trapezoidal", "best hydraulic section, z = 1/sqrt(3)")
        _, curve, _ = _scan_b(inp, Z_BEST, "", "", N=200)
        d["curve"], d["feasible"] = curve, d["ok"]
        return d
    if mode == "best_for_z":
        d = best_for_z(inp, inp.z, "Trapezoidal", f"best hydraulic section for z = {inp.z:g}")
        _, curve, _ = _scan_b(inp, inp.z, "", "", N=200)
        d["curve"], d["feasible"] = curve, d["ok"]
        return d
    if mode == "given_z":
        d, curve, feas = _scan_b(inp, inp.z, "Trapezoidal", f"optimised width, z = {inp.z:g}")
        d["curve"], d["feasible"] = curve, feas
        return d
    # scan_z: also search the side slope
    best, bestcurve, anyfeas = None, None, False
    for z in sorted(set(np.round(np.arange(0.0, 4.01, 0.1), 10).tolist() + [Z_BEST])):
        d, curve, feas = _scan_b(inp, z, "Trapezoidal", "optimised width and side slope", N=200)
        better = (best is None
                  or (feas and (not anyfeas or d["obj"] < best["obj"]))
                  or (not feas and not anyfeas and d["viol"] < best["viol"]))
        anyfeas = anyfeas or feas
        if better:
            best, bestcurve = d, curve
    best["curve"], best["feasible"] = bestcurve, anyfeas
    return best


# ---------------------------------------------------------------- circular
def partial_flow_curve(npts=101):
    """Ratios against full flow for y/D from 0 to 1 (independent of D, n, S)."""
    u = Circ(1.0)
    full_A, full_R = u.area(1.0), u.area(1.0) / u.perim(1.0)
    rows = []
    for r in np.linspace(0.0, 1.0, npts):
        if r == 0:
            rows.append({"yD": 0.0, "A": 0.0, "R": 0.0, "V": 0.0, "Q": 0.0})
            continue
        A = u.area(r)
        R = A / u.perim(r)
        V = (R / full_R) ** (2 / 3)
        rows.append({"yD": float(r), "A": A / full_A, "R": R / full_R, "V": V,
                     "Q": V * A / full_A})
    return rows


def optimize_circ(inp):
    tested = []
    if inp.free_diameter:
        g = lambda D: flow(Circ(D), inp.max_fill * D, inp.S, inp.n) - inp.Q
        hi = 1.0
        while g(hi) < 0:
            hi *= 2.0
            if hi > 1e4:
                raise NoSolution("No pipe diameter found.")
        D = brentq(g, 1e-3, hi, xtol=1e-13, rtol=1e-12, maxiter=300)
        cands = [D]
        option = f"exact diameter at y/D = {inp.max_fill:g}"
    else:
        cands = sorted(inp.diameters)
        option = "smallest listed diameter that passes"
    designs = []
    for D in cands:
        try:
            d = _make(Circ(D), inp, "Circular", option)
        except NoSolution:
            tested.append({"D": D, "y_over_D": None, "V": None, "ok": False,
                           "why": "too small to carry Q"})
            continue
        designs.append(d)
        tested.append({"D": D, "y_over_D": d["y"] / D, "V": d["V"], "ok": d["ok"],
                       "why": "; ".join(d["failures"]) or "passes"})
    if not designs:
        raise NoSolution("Even the largest pipe in the list cannot carry the design "
                         "discharge. Add larger diameters or use 'free diameter'.")
    feas = [d for d in designs if d["ok"]]
    best = min(feas, key=lambda d: d["obj"]) if feas else min(designs, key=lambda d: d["viol"])
    best["feasible"] = bool(feas)
    best["tested"] = tested
    best["partial_curve"] = partial_flow_curve()
    best["r_vmax"], best["r_qmax"] = R_VMAX, R_QMAX
    return best


# ---------------------------------------------------------------- top level
def design_section(inp, kind):
    inp.validate()
    return {"rectangular": optimize_rect, "trapezoidal": optimize_trap,
            "circular": optimize_circ}[kind](inp)


def compare(inp, sections=("rectangular", "trapezoidal", "circular")):
    """Design each requested section, add best-hydraulic references, recommend one."""
    inp.validate()
    res = {"designs": {}, "references": [], "errors": {}, "objective": inp.objective}
    for k in sections:
        try:
            res["designs"][k] = design_section(inp, k)
        except NoSolution as e:
            res["errors"][k] = str(e)
    for k, d in list(res["designs"].items()):
        if k == "circular":
            continue
        z = 0.0 if k == "rectangular" else inp.z
        lab = "Rectangular" if k == "rectangular" else "Trapezoidal"
        opt = "reference: best hydraulic section (b = 2y)" if k == "rectangular" else \
            f"reference: best hydraulic section for z = {z:g}"
        ref = best_for_z(inp, z, lab, opt)
        if abs(ref["b"] - d["b"]) > 0.01 * ref["b"] or abs(ref["z"] - d["z"]) > 1e-6:
            res["references"].append(ref)
    res["recommended"], res["reasons"] = recommend(inp, res)
    return res


def recommend(inp, res):
    ds = list(res["designs"].values())
    good = [d for d in ds if d["ok"]]
    name = OBJ_NAME[inp.objective]
    if not good:
        if not ds:
            return None, ["No section could be designed: " + "; ".join(res["errors"].values())]
        near = min(ds, key=lambda d: d["viol"])
        why = [f"No section passes every check. Closest: {near['label']}."]
        why += [f"{near['label']} fails: {t}" for t in near["failures"]]
        why.append("Relax a limit (velocity, width, depth) or change the lining.")
        return None, why
    best = min(good, key=lambda d: d["obj"])
    why = [f"{best['label']} has the lowest {name} ({best['obj']:.4g}) among the sections "
           f"that pass every check."]
    why += [c["text"] + " (OK)" for c in best["checks"] if c["ok"] and not c["warn"]]
    why += [f"Warning: {w}" for w in best["warnings"]]
    for d in ds:
        if d is best:
            continue
        if d["ok"]:
            why.append(f"{d['label']} also passes but its {name} is higher ({d['obj']:.4g}).")
        else:
            why.append(f"{d['label']} fails: " + "; ".join(d["failures"]) + ".")
    for k, msg in res["errors"].items():
        why.append(f"{k.capitalize()} not possible: {msg}")
    return best["label"].lower(), why

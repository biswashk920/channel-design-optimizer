"""Hydraulic checks and the 'design' record for one section."""
import math

from scipy.optimize import brentq

from .inputs import NoSolution
from .sections import G, Circ, Trap

TOL = 1e-9   # relative tolerance when comparing against limits


def freeboard(inp, y):
    return y * inp.fb / 100.0 if inp.fb_mode == "percent" else inp.fb


def froude(V, A, T):
    return V / math.sqrt(G * A / T)


def regime(Fr):
    if abs(Fr - 1.0) < 1e-3:
        return "critical"
    return "subcritical" if Fr < 1 else "supercritical"


def critical_depth(sec, Q):
    """Depth where Fr = 1, i.e. Q^2 T / (g A^3) = 1."""
    f = lambda y: Q * Q * sec.top(y) / (G * sec.area(y) ** 3) - 1.0
    if isinstance(sec, Circ):
        lo, hi = 1e-6 * sec.D, sec.D * (1 - 1e-9)
    else:
        lo, hi = 1e-9, 1.0
        while f(hi) > 0:
            hi *= 2.0
            if hi > 1e5:
                raise NoSolution("No critical depth found.")
    return brentq(f, lo, hi, xtol=1e-13, rtol=1e-12, maxiter=300)


def _check(name, ok, value, limit, text, viol=0.0, warn=False):
    return {"name": name, "ok": ok, "warn": warn, "value": value, "limit": limit,
            "text": text, "viol": 0.0 if ok else viol}


def make_design(sec, inp, y, label, option):
    """Evaluate section `sec` flowing at normal depth y; run all checks."""
    A, P, T = sec.area(y), sec.perim(y), sec.top(y)
    R, V = A / P, inp.Q / A
    Fr = froude(V, A, T)
    circ = isinstance(sec, Circ)
    if circ:
        fb, H, bank = sec.D - y, sec.D, sec.D
        a_exc = math.pi * sec.D ** 2 / 4
    else:
        fb = freeboard(inp, y)
        H = y + fb
        bank = sec.top(H)
        a_exc = (sec.b + sec.z * H) * H
    obj = {"area": a_exc, "flow_area": A, "perimeter": P,
           "cost": inp.c_exc * a_exc + inp.c_lin * P}[inp.objective]

    ch = []
    if inp.vmin is not None:
        ok = V >= inp.vmin * (1 - TOL)
        ch.append(_check("Minimum velocity", ok, V, inp.vmin,
                         f"V = {V:.2f} m/s vs minimum {inp.vmin:g} m/s (silting)",
                         (inp.vmin - V) / inp.vmin))
    if inp.vmax is not None:
        ok = V <= inp.vmax * (1 + TOL)
        ch.append(_check("Maximum velocity", ok, V, inp.vmax,
                         f"V = {V:.2f} m/s vs maximum {inp.vmax:g} m/s (erosion)",
                         (V - inp.vmax) / inp.vmax))
    warn = inp.fr_lo <= Fr <= inp.fr_hi
    ch.append(_check("Froude", True, Fr, None,
                     f"Fr = {Fr:.2f}, {regime(Fr)}" +
                     (" (close to critical: unstable surface, avoid)" if warn else ""),
                     warn=warn))
    if inp.max_width is not None:
        ok = bank <= inp.max_width * (1 + TOL)
        ch.append(_check("Width limit", ok, bank, inp.max_width,
                         f"Width at top = {bank:.2f} m vs limit {inp.max_width:g} m",
                         (bank - inp.max_width) / inp.max_width))
    if inp.max_depth is not None:
        ok = H <= inp.max_depth * (1 + TOL)
        ch.append(_check("Depth limit", ok, H, inp.max_depth,
                         f"Total depth = {H:.2f} m vs limit {inp.max_depth:g} m",
                         (H - inp.max_depth) / inp.max_depth))
    if circ:
        fill = y / sec.D
        ok = fill <= inp.max_fill * (1 + TOL)
        ch.append(_check("Filling ratio", ok, fill, inp.max_fill,
                         f"y/D = {fill:.2f} vs maximum {inp.max_fill:g} (air space)",
                         (fill - inp.max_fill) / inp.max_fill))

    return {
        "section": sec.kind, "label": label, "option": option, "sec": sec,
        "b": None if circ else sec.b, "z": None if circ else sec.z,
        "D": sec.D if circ else None,
        "y": y, "fb": fb, "H": H, "A": A, "A_gross": a_exc, "P": P, "R": R, "T": T, "bank": bank,
        "V": V, "Fr": Fr, "regime": regime(Fr), "yc": critical_depth(sec, inp.Q),
        "obj": obj, "checks": ch,
        "ok": all(c["ok"] for c in ch),
        "viol": sum(c["viol"] for c in ch),
        "failures": [c["text"] for c in ch if not c["ok"]],
        "warnings": [c["text"] for c in ch if c["warn"]],
    }

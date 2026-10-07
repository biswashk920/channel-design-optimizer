"""Turn results into a table (pandas), CSV and text."""
import pandas as pd

from .optimize import OBJ_NAME
from .plots import all_designs

CHECKS = ["Minimum velocity", "Maximum velocity", "Froude", "Width limit",
          "Depth limit", "Filling ratio"]


def to_row(d, objective):
    row = {
        "Section": d["label"] + (" (reference)" if d["option"].startswith("reference") else ""),
        "Option": d["option"],
        "Bottom width b (m)": d["b"],
        "Side slope z (H:1V)": d["z"],
        "Pipe diameter D (m)": d["D"],
        "Normal depth y (m)": d["y"],
        "Freeboard (m)": d["fb"],
        "Total depth (m)": d["H"],
        "Width at top of bank (m)": d["bank"],
        "Flow area A (m2)": d["A"],
        "Gross section area (m2)": d["A_gross"],
        "Wetted perimeter P (m)": d["P"],
        "Hydraulic radius R (m)": d["R"],
        "Water surface width T (m)": d["T"],
        "Velocity V (m/s)": d["V"],
        "Froude number": d["Fr"],
        "Flow regime": d["regime"],
        "Critical depth yc (m)": d["yc"],
        f"Objective: {OBJ_NAME[objective]}": d["obj"],
    }
    have = {c["name"]: c for c in d["checks"]}
    for name in CHECKS:
        c = have.get(name)
        if c is None:
            row["Check: " + name] = "n/a"
        elif c["warn"]:
            row["Check: " + name] = "WARNING"
        else:
            row["Check: " + name] = "PASS" if c["ok"] else "FAIL"
    row["All checks"] = "PASS" if d["ok"] else "FAIL"
    return row


def results_table(res, objective):
    return pd.DataFrame([to_row(d, objective) for d in all_designs(res)])


def write_csv(res, objective, path):
    results_table(res, objective).to_csv(path, index=False, float_format="%.4f")


def format_text(res, inp):
    df = results_table(res, objective=inp.objective)
    df = df.dropna(axis=1, how="all")
    lines = [df.set_index("Section").T.to_string(float_format=lambda v: f"{v:.3f}"), ""]
    rec = res["recommended"]
    lines.append("RECOMMENDED: " + (rec.upper() if rec else "none (no section passes all checks)"))
    lines += ["  - " + r for r in res["reasons"]]
    c = res["designs"].get("circular")
    if c and c.get("tested"):
        lines += ["", "Pipe diameters tested (y/D = filling ratio):"]
        for t in c["tested"]:
            yd = "-" if t["y_over_D"] is None else f"{t['y_over_D']:.2f}"
            v = "-" if t["V"] is None else f"{t['V']:.2f}"
            lines.append(f"  D = {t['D']:.3g} m  y/D = {yd}  V = {v} m/s  "
                         f"{'ok' if t['ok'] else 'no'}: {t['why']}")
    lines += ["", "Note: uniform flow only. Lining values and velocity limits are unverified "
              "typical figures: check them against a textbook."]
    return "\n".join(lines)

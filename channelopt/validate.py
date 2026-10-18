"""Compare textbook answers with this program's answers.

Fill examples/textbook_template.csv from your textbook, then run:
    python -m channelopt.validate examples/textbook_template.csv
"""
import csv
import sys

from .sections import Circ, Trap, normal_depth


def run(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not (r.get("Q") or "").strip():
                continue
            Q, S, n = float(r["Q"]), float(r["S"]), float(r["n"])
            kind = r["section"].strip().lower()
            if kind == "circular":
                sec = Circ(float(r["D"]))
            else:
                sec = Trap(float(r["b"]), float(r["z"] or 0) if kind == "trapezoidal" else 0.0)
            y = normal_depth(sec, Q, S, n)
            V = Q / sec.area(y)
            tol = float(r.get("tolerance_percent") or 1.0)
            row = {"name": r["name"], "source": r.get("source", ""), "y_calc": y, "V_calc": V,
                   "y_book": r.get("book_depth", "").strip(), "V_book": r.get("book_velocity", "").strip()}
            diffs = []
            for key, calc in (("y", y), ("V", V)):
                if row[key + "_book"]:
                    d = 100 * (calc / float(row[key + "_book"]) - 1)
                    row[key + "_diff_%"] = d
                    diffs.append(abs(d))
            row["pass"] = all(d <= tol for d in diffs) if diffs else None
            rows.append(row)
    return rows


def main(argv=None):
    path = (argv or sys.argv[1:] or ["examples/textbook_template.csv"])[0]
    rows = run(path)
    if not rows:
        print("No filled rows found. Add your textbook examples to", path)
        return 0
    print(f"{'example':28s}{'y calc':>9s}{'y book':>9s}{'diff %':>9s}{'V calc':>9s}{'V book':>9s}{'diff %':>9s}  result")
    for r in rows:
        f = lambda k: f"{r[k]:9.2f}" if k in r else f"{'-':>9s}"
        res = {True: "PASS", False: "FAIL", None: "no book values"}[r["pass"]]
        print(f"{r['name'][:27]:28s}{r['y_calc']:9.3f}{r['y_book']:>9s}{f('y_diff_%')}{r['V_calc']:9.3f}{r['V_book']:>9s}{f('V_diff_%')}  {res}")
    return 1 if any(r["pass"] is False for r in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())

import csv
import tempfile
import unittest
from pathlib import Path

from channelopt.cli import main
from channelopt.inputs import load_linings
from channelopt.sections import Circ, Trap, flow, normal_depth

ROOT = Path(__file__).resolve().parent.parent


class Cli(unittest.TestCase):
    def test_runs_and_writes_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            code = main(["--Q", "5", "--S", "0.001", "--lining", "concrete_trowel",
                         "--out", tmp, "--no-plots"])
            self.assertEqual(code, 0)
            with open(Path(tmp) / "results.csv", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertGreaterEqual(len(rows), 3)
            self.assertIn("Velocity V (m/s)", rows[0])

    def test_plots_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(main(["--Q", "2", "--S", "0.002", "--n", "0.015", "--out", tmp]), 0)
            for f in ("cross_sections.png", "optimisation_curves.png", "comparison.png"):
                self.assertTrue((Path(tmp) / f).stat().st_size > 1000)

    def test_friendly_errors_exit_code_2(self):
        self.assertEqual(main(["--Q", "-5", "--S", "0.001", "--n", "0.013"]), 2)
        self.assertEqual(main(["--Q", "5", "--S", "0", "--n", "0.013"]), 2)
        self.assertEqual(main(["--Q", "5", "--S", "0.001"]), 2)            # no n, no lining
        self.assertEqual(main(["--Q", "5", "--S", "0.001", "--lining", "nope"]), 2)

    def test_single_section(self):
        self.assertEqual(main(["--Q", "5", "--S", "0.001", "--n", "0.013",
                               "--section", "circular", "--free-diameter"]), 0)


class Linings(unittest.TestCase):
    def test_table_sane(self):
        for x in load_linings():
            self.assertLessEqual(x["n_min"], x["n"])
            self.assertLessEqual(x["n"], x["n_max"])
            self.assertGreater(x["vmax"], x["vmin"])


class TextbookTemplate(unittest.TestCase):
    """Reads examples/textbook_template.csv. Rows you fill in are checked automatically."""

    def test_filled_rows(self):
        path = ROOT / "examples" / "textbook_template.csv"
        with open(path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        n_checked = 0
        for r in rows:
            if not (r.get("Q") or "").strip():
                continue
            Q, S, n = float(r["Q"]), float(r["S"]), float(r["n"])
            kind = r["section"].strip().lower()
            sec = Circ(float(r["D"])) if kind == "circular" else \
                Trap(float(r["b"]), float(r["z"] or 0) if kind == "trapezoidal" else 0.0)
            y = normal_depth(sec, Q, S, n)
            tol = float(r.get("tolerance_percent") or 1.0) / 100
            if r.get("book_depth", "").strip():
                self.assertAlmostEqual(y / float(r["book_depth"]), 1.0, delta=tol, msg=r["name"])
            if r.get("book_velocity", "").strip():
                self.assertAlmostEqual(Q / sec.area(y) / float(r["book_velocity"]), 1.0,
                                       delta=tol, msg=r["name"])
            n_checked += 1
        print(f"\n[textbook template] {n_checked} filled row(s) checked", end=" ")


if __name__ == "__main__":
    unittest.main()

import csv, tempfile, unittest
from pathlib import Path

from channelopt import Inputs, compare
from channelopt.cli import main
from channelopt.validate import run


class Envelope(unittest.TestCase):
    def test_rough_deeper_smooth_faster(self):
        r = compare(Inputs(Q=5, S=0.001, n=0.013, n_min=0.011, n_max=0.015, vmax=6))
        for d in r["designs"].values():
            e = d["envelope"]
            self.assertLess(e["smooth"]["y"], d["y"])
            self.assertGreater(e["rough"]["y"], d["y"])
            self.assertGreater(e["smooth"]["V"], e["rough"]["V"])

    def test_detects_overtopping_and_bad_range(self):
        r = compare(Inputs(Q=5, S=0.001, n=0.013, n_min=0.013, n_max=0.06, fb=1.0, vmax=6))
        self.assertFalse(r["designs"]["rectangular"]["envelope"]["ok"])
        from channelopt import InputError
        with self.assertRaises(InputError):
            Inputs(Q=5, S=0.001, n=0.013, n_min=0.02, n_max=0.03).validate()

    def test_cli_uses_lining_range(self):
        self.assertEqual(main(["--Q", "5", "--S", "0.001", "--lining", "concrete_trowel"]), 0)


class ValidateReport(unittest.TestCase):
    def test_hand_example(self):
        # My own hand calculation (b=2, y=1, n=0.015, S=0.001 gives Q=2.656), not a textbook value
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "v.csv"
            p.write_text("name,source,Q,S,n,section,b,z,D,book_depth,book_velocity,tolerance_percent\n"
                         "hand,me,2.656,0.001,0.015,rectangular,2,,,1.0,1.328,0.5\n"
                         "blank,,,,,,,,,,,\n", encoding="utf-8")
            rows = run(p)
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["pass"])


if __name__ == "__main__":
    unittest.main()

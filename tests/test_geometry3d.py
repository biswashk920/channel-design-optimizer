import json, shutil, subprocess, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@unittest.skipUnless(shutil.which("node"), "Node.js not installed")
class Geometry(unittest.TestCase):
    def test_water_polygon_area_equals_flow_area(self):
        out = json.loads(subprocess.run(["node", str(ROOT / "tests" / "geom.js")], capture_output=True,
                                        text=True, check=True).stdout)
        self.assertEqual(set(out), {"rectangular", "trapezoidal", "circular"})
        for k, v in out.items():
            self.assertAlmostEqual(v["poly"] / v["area"], 1.0, delta=2e-3, msg=k)   # polygon approximates the arc
            top = v["D"] if v["D"] else v["H"]
            self.assertAlmostEqual(v["wallTop"], top, delta=0.01 * top, msg=k)
            self.assertGreater(v["qEnd"], 5.0, msg=k)     # rating curve reaches beyond design Q


if __name__ == "__main__":
    unittest.main()

"""Browser logic (run with Node) must match Python on the same inputs."""
import json, math, shutil, subprocess, tempfile, unittest
from pathlib import Path

from channelopt import Inputs, compare, load_linings

ROOT = Path(__file__).resolve().parent.parent
CASES = [dict(Q=5, S=0.001, n=0.013, vmax=6), dict(Q=0.8, S=0.004, n=0.015, vmin=0.6, vmax=3, z=2),
         dict(Q=30, S=0.0004, n=0.025, vmax=2, objective="perimeter", max_width=12),
         dict(Q=12, S=0.002, n=0.017, trap_mode="best_for_z", z=1.0, vmax=5),
         dict(Q=3, S=0.003, n=0.013, trap_mode="best_overall", objective="cost", fb_mode="fixed", fb=0.3, vmax=5),
         dict(Q=2, S=0.002, n=0.010, free_diameter=True, vmax=5)]


def js_inputs(c):
    d = Inputs(**c)
    return dict(Q=d.Q, S=d.S, n=d.n, z=d.z, mode=d.trap_mode, fbm=d.fb_mode, fb=d.fb, obj=d.objective,
                ce=d.c_exc, cl=d.c_lin, vmin=d.vmin, vmax=d.vmax, mw=d.max_width, md=d.max_depth,
                free=d.free_diameter, mf=d.max_fill, diams=list(d.diameters))


@unittest.skipUnless(shutil.which("node"), "Node.js not installed")
class Parity(unittest.TestCase):
    def test_matches_python(self):
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / "c.json"
            f.write_text(json.dumps([js_inputs(c) for c in CASES]))
            js = json.loads(subprocess.run(["node", str(ROOT / "tests" / "parity.js"), str(f)],
                                           capture_output=True, text=True, check=True).stdout)
        for c, j in zip(CASES, js):
            py = compare(Inputs(**c))
            self.assertEqual(py["recommended"], (j["rec"] or "").lower() or None, c)
            for k, d in py["designs"].items():
                for key, pk in (("y", "y"), ("A", "A"), ("V", "V"), ("Fr", "Fr"), ("yc", "yc")):
                    self.assertAlmostEqual(j[k][key] / d[pk], 1.0, delta=1e-6, msg=f"{k} {key} {c}")
                for key in ("b", "D", "obj"):
                    if d[key if key != "obj" else "obj"] is not None:
                        self.assertAlmostEqual(j[k][key] / d[key], 1.0, delta=1e-3, msg=f"{k} {key} {c}")
                self.assertEqual(j[k]["ok"], d["ok"])


class LiningCopy(unittest.TestCase):
    def test_html_table_matches_json(self):
        import re
        html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        copy = json.loads(re.search(r"/\*LININGS\*/(.*?)/\*END\*/", html, re.S).group(1))
        self.assertEqual(copy, load_linings())


if __name__ == "__main__":
    unittest.main()

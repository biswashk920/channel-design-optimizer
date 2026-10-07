import unittest

from channelopt import InputError, Inputs, NoSolution, compare, design_section
from channelopt.optimize import Z_BEST, best_for_z


def inp(**kw):
    base = dict(Q=5.0, S=0.001, n=0.013, vmax=6.0)
    base.update(kw)
    return Inputs(**base)


class Optimiser(unittest.TestCase):
    def test_unconstrained_rect_is_best_section(self):
        d = design_section(inp(objective="flow_area", vmin=None, vmax=None), "rectangular")
        self.assertAlmostEqual(d["b"] / d["y"], 2.0, places=3)

    def test_rect_perimeter_objective_is_best_section(self):
        d = design_section(inp(objective="perimeter", vmin=None, vmax=None), "rectangular")
        self.assertAlmostEqual(d["b"] / d["y"], 2.0, places=3)

    def test_trap_flow_area_matches_best_ratio(self):
        d = design_section(inp(objective="flow_area", vmin=None, vmax=None, z=1.5), "trapezoidal")
        ref = best_for_z(inp(), 1.5, "t", "x")
        self.assertAlmostEqual(d["A"] / ref["A"], 1.0, places=4)

    def test_scan_z_finds_half_hexagon_for_flow_area(self):
        d = design_section(inp(objective="flow_area", vmin=None, vmax=None, trap_mode="scan_z"),
                           "trapezoidal")
        ref = best_for_z(inp(), Z_BEST, "t", "x")
        self.assertAlmostEqual(d["A"] / ref["A"], 1.0, delta=2e-3)

    def test_cost_with_zero_excavation_cost_equals_perimeter(self):
        a = design_section(inp(objective="cost", c_exc=0.0, c_lin=1.0), "rectangular")
        b = design_section(inp(objective="perimeter"), "rectangular")
        self.assertAlmostEqual(a["b"], b["b"], delta=1e-3)

    def test_constraint_changes_answer_and_is_respected(self):
        free = design_section(inp(objective="flow_area", vmin=None, vmax=None), "rectangular")
        lim = design_section(inp(objective="flow_area", vmin=None, vmax=None, max_width=1.5),
                             "rectangular")
        self.assertLessEqual(lim["bank"], 1.5 * (1 + 1e-6))
        self.assertGreater(lim["A"], free["A"])
        self.assertTrue(lim["ok"])

    def test_velocity_limit_respected(self):
        d = design_section(inp(vmin=1.0, vmax=1.5), "rectangular")
        self.assertTrue(d["ok"])
        self.assertTrue(1.0 - 1e-8 <= d["V"] <= 1.5 + 1e-8)

    def test_impossible_constraints_report_not_crash(self):
        d = design_section(inp(max_width=0.5, max_depth=0.5), "rectangular")
        self.assertFalse(d["ok"])
        self.assertTrue(d["failures"])
        r = compare(inp(max_width=0.5, max_depth=0.5))
        self.assertIsNone(r["recommended"])
        self.assertIn("No section passes", r["reasons"][0])

    def test_circular_picks_smallest_passing_diameter(self):
        d = design_section(inp(), "circular")
        self.assertTrue(d["ok"])
        smaller = [t for t in d["tested"] if t["D"] < d["D"]]
        self.assertTrue(all(not t["ok"] for t in smaller))
        self.assertLessEqual(d["y"] / d["D"], 0.8 + 1e-9)

    def test_free_diameter_hits_fill_limit(self):
        d = design_section(inp(free_diameter=True, max_fill=0.8, vmax=None), "circular")
        self.assertAlmostEqual(d["y"] / d["D"], 0.8, places=6)

    def test_pipe_list_too_small(self):
        with self.assertRaises(NoSolution):
            design_section(inp(diameters=(0.3, 0.4)), "circular")

    def test_compare_returns_three_and_recommendation(self):
        r = compare(inp())
        self.assertEqual(set(r["designs"]), {"rectangular", "trapezoidal", "circular"})
        self.assertIsNotNone(r["recommended"])
        best = min((d for d in r["designs"].values() if d["ok"]), key=lambda d: d["obj"])
        self.assertEqual(r["recommended"], best["label"].lower())

    def test_best_overall_mode(self):
        d = design_section(inp(trap_mode="best_overall"), "trapezoidal")
        self.assertAlmostEqual(d["z"], Z_BEST, places=12)
        self.assertAlmostEqual(d["R"], d["y"] / 2, places=9)


class Validation(unittest.TestCase):
    def bad(self, text, **kw):
        with self.assertRaises(InputError) as cm:
            inp(**kw).validate()
        self.assertIn(text, str(cm.exception))

    def test_messages(self):
        self.bad("Design discharge", Q=-1.0)
        self.bad("Design discharge", Q=0.0)
        self.bad("Bed slope", S=0.0)
        self.bad("Bed slope", S=-0.001)
        self.bad("Bed slope", S=1.5)
        self.bad("Manning", n=0.0)
        self.bad("Manning", n=0.5)
        self.bad("Side slope", z=-1.0)
        self.bad("smaller than", vmin=3.0, vmax=2.0)
        self.bad("Maximum width", max_width=-2.0)
        self.bad("diameter list is empty", diameters=())
        self.bad("filling ratio", max_fill=1.5)
        self.bad("must be a number", Q=float("nan"))
        self.bad("must be a number", Q="five")

    def test_good_inputs_pass(self):
        inp().validate()


if __name__ == "__main__":
    unittest.main()

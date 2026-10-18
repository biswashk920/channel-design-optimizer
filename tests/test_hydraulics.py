"""Analytic checks (no textbook data). See README: these are NOT textbook examples."""
import math
import unittest

from channelopt.checks import critical_depth, froude, make_design
from channelopt.inputs import Inputs, NoSolution
from channelopt.optimize import Z_BEST, best_for_z, partial_flow_curve
from channelopt.sections import G, R_QMAX, R_VMAX, Circ, Trap, flow, normal_depth


class ManningRoundTrip(unittest.TestCase):
    CASES = [(5.0, 0.001, 0.013), (0.2, 0.01, 0.025), (50.0, 0.0002, 0.030), (1.0, 0.05, 0.015)]

    def test_trapezoid_and_rectangle(self):
        for Q, S, n in self.CASES:
            for b, z in [(2.0, 0.0), (3.0, 1.5), (0.5, 2.0), (10.0, 1.0)]:
                sec = Trap(b, z)
                y = normal_depth(sec, Q, S, n)
                self.assertAlmostEqual(flow(sec, y, S, n) / Q, 1.0, places=9)

    def test_circle(self):
        for Q, S, n in self.CASES:
            D = 6.0
            sec = Circ(D)
            try:
                y = normal_depth(sec, Q, S, n)
            except NoSolution:
                continue
            self.assertLessEqual(y, R_QMAX * D + 1e-9)
            self.assertAlmostEqual(flow(sec, y, S, n) / Q, 1.0, places=9)

    def test_rectangle_solved_by_hand(self):
        # My own hand calculation (not from a textbook): b = 2 m, y = 1 m, n = 0.015, S = 0.001
        # A = 2, P = 4, R = 0.5, R^(2/3) = 0.62996, S^0.5 = 0.031623
        # Q = 2 * 0.62996 * 0.031623 / 0.015 = 2.656 m3/s
        y = normal_depth(Trap(2.0, 0.0), 2.656, 0.001, 0.015)
        self.assertAlmostEqual(y, 1.0, places=3)


class BestSection(unittest.TestCase):
    inp = Inputs(Q=5.0, S=0.001, n=0.013)

    def test_rectangle_b_equals_2y(self):
        d = best_for_z(self.inp, 0.0, "r", "x")
        self.assertAlmostEqual(d["b"] / d["y"], 2.0, places=9)
        self.assertAlmostEqual(d["R"], d["y"] / 2, places=9)

    def test_trapezoid_ratio_formula(self):
        for z in (0.5, 1.0, 1.5, 2.0, 3.0):
            d = best_for_z(self.inp, z, "t", "x")
            self.assertAlmostEqual(d["b"] / d["y"], 2 * (math.sqrt(1 + z * z) - z), places=9)
            self.assertAlmostEqual(d["R"], d["y"] / 2, places=9)  # R = y/2 for every best section

    def test_closed_form_depth(self):
        # For a best section: Q n / sqrt(S) = (m+z) 2^(-2/3) y^(8/3)
        z = 1.5
        m = 2 * (math.sqrt(1 + z * z) - z)
        d = best_for_z(self.inp, z, "t", "x")
        y = (self.inp.Q * self.inp.n / math.sqrt(self.inp.S) / ((m + z) * 2 ** (-2 / 3))) ** (3 / 8)
        self.assertAlmostEqual(d["y"], y, places=8)

    def test_half_hexagon(self):
        d = best_for_z(self.inp, Z_BEST, "t", "x")
        side = d["y"] * math.sqrt(1 + Z_BEST ** 2)
        self.assertAlmostEqual(d["b"], side, places=9)      # all three sides equal
        self.assertAlmostEqual(math.degrees(math.atan(1 / Z_BEST)), 60.0, places=9)

    def test_z_optimum_has_smallest_perimeter(self):
        # For equal flow area the smallest perimeter is at z = 1/sqrt(3) (and best b/y)
        def perim_for_area(A, z):
            m = 2 * (math.sqrt(1 + z * z) - z)
            y = math.sqrt(A / (m + z))
            return m * y + 2 * y * math.sqrt(1 + z * z)
        pbest = perim_for_area(10.0, Z_BEST)
        for z in (0.0, 0.3, 0.5, 0.8, 1.0, 1.5, 2.0):
            self.assertGreaterEqual(perim_for_area(10.0, z), pbest - 1e-12)

    def test_best_section_beats_neighbours(self):
        d = best_for_z(self.inp, 1.5, "t", "x")
        for k in (0.7, 0.9, 1.1, 1.4):
            sec = Trap(d["b"] * k, 1.5)
            y = normal_depth(sec, self.inp.Q, self.inp.S, self.inp.n)
            self.assertGreater(sec.area(y), d["A"])


class CircularLimits(unittest.TestCase):
    def test_half_full_identities(self):
        c = {r["yD"]: r for r in partial_flow_curve(101)}
        self.assertAlmostEqual(c[0.5]["V"], 1.0, places=12)    # V(half) = V(full)
        self.assertAlmostEqual(c[0.5]["Q"], 0.5, places=12)    # Q(half) = Q(full)/2
        self.assertAlmostEqual(c[0.5]["A"], 0.5, places=12)
        self.assertAlmostEqual(c[1.0]["Q"], 1.0, places=12)

    def test_full_pipe_geometry(self):
        s = Circ(2.0)
        self.assertAlmostEqual(s.area(2.0), math.pi, places=12)
        self.assertAlmostEqual(s.perim(2.0), 2 * math.pi, places=12)
        self.assertAlmostEqual(s.area(2.0) / s.perim(2.0), 0.5, places=12)   # R = D/4

    def test_peaks_near_textbook_values(self):
        self.assertAlmostEqual(R_VMAX, 0.81, delta=0.005)
        self.assertAlmostEqual(R_QMAX, 0.94, delta=0.005)
        c = partial_flow_curve(1001)
        self.assertGreater(max(r["V"] for r in c), 1.0)   # V exceeds full-flow V
        self.assertGreater(max(r["Q"] for r in c), 1.0)   # Q exceeds full-flow Q

    def test_capacity_error(self):
        with self.assertRaises(NoSolution):
            normal_depth(Circ(0.3), 5.0, 0.001, 0.013)


class CriticalFlow(unittest.TestCase):
    def test_rectangular_closed_form(self):
        for b, Q in ((2.0, 5.0), (6.0, 30.0)):
            yc = critical_depth(Trap(b, 0.0), Q)
            self.assertAlmostEqual(yc, (Q ** 2 / (G * b * b)) ** (1 / 3), places=9)

    def test_froude_is_one_at_critical(self):
        sec = Trap(3.0, 1.5)
        yc = critical_depth(sec, 12.0)
        self.assertAlmostEqual(froude(12.0 / sec.area(yc), sec.area(yc), sec.top(yc)), 1.0, places=9)
        c = Circ(2.0)
        yc = critical_depth(c, 3.0)
        self.assertAlmostEqual(froude(3.0 / c.area(yc), c.area(yc), c.top(yc)), 1.0, places=7)

    def test_regimes(self):
        inp = Inputs(Q=5.0, S=0.0005, n=0.013)
        self.assertEqual(make_design(Trap(3, 0), inp, 1.5, "r", "x")["regime"], "subcritical")
        steep = Inputs(Q=5.0, S=0.05, n=0.013)
        y = normal_depth(Trap(3, 0), 5.0, 0.05, 0.013)
        d = make_design(Trap(3, 0), steep, y, "r", "x")
        self.assertEqual(d["regime"], "supercritical")


if __name__ == "__main__":
    unittest.main()

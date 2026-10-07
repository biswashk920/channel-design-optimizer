"""Cross-section geometry and Manning flow. Rectangle = trapezoid with z = 0."""
import math

from scipy.optimize import brentq, minimize_scalar

from .inputs import NoSolution

G = 9.81


class Trap:
    kind = "trapezoidal"
    ymax = None

    def __init__(self, b, z=0.0):
        self.b, self.z = b, z

    def area(self, y):
        return (self.b + self.z * y) * y

    def perim(self, y):
        return self.b + 2.0 * y * math.sqrt(1.0 + self.z ** 2)

    def top(self, y):
        return self.b + 2.0 * self.z * y


class Circ:
    kind = "circular"

    def __init__(self, D):
        self.D = D
        self.ymax = D

    def _theta(self, y):
        y = min(max(y, 0.0), self.D)
        return 2.0 * math.acos(1.0 - 2.0 * y / self.D)

    def area(self, y):
        th = self._theta(y)
        return self.D ** 2 / 8.0 * (th - math.sin(th))

    def perim(self, y):
        return self.D * self._theta(y) / 2.0

    def top(self, y):
        return self.D * math.sin(self._theta(y) / 2.0)


def flow(sec, y, S, n):
    """Manning discharge Q = (1/n) A R^(2/3) S^(1/2) at depth y."""
    A = sec.area(y)
    if A <= 0:
        return 0.0
    R = A / sec.perim(y)
    return A * R ** (2.0 / 3.0) * math.sqrt(S) / n


def _circ_ratio_peak(which):
    """y/D where velocity (which='v') or discharge ('q') is largest in a circle."""
    unit = Circ(1.0)

    def val(r):
        A, P = unit.area(r), unit.perim(r)
        R = A / P
        return -(R ** (2 / 3)) if which == "v" else -(A * R ** (2 / 3))

    return minimize_scalar(val, bounds=(0.5, 0.999), method="bounded",
                           options={"xatol": 1e-12}).x


R_VMAX = _circ_ratio_peak("v")   # about 0.81
R_QMAX = _circ_ratio_peak("q")   # about 0.94


def normal_depth(sec, Q, S, n):
    """Depth where Manning discharge equals Q (bracketed root-finding, brentq)."""
    f = lambda y: flow(sec, y, S, n) - Q
    if isinstance(sec, Circ):
        hi = R_QMAX * sec.D           # a circle carries most at y/D ~ 0.94
        if f(hi) < 0:
            raise NoSolution(
                f"A pipe of diameter {sec.D:g} m cannot carry {Q:g} m3/s at this slope "
                f"and roughness, even at its maximum open-flow capacity "
                f"({flow(sec, hi, S, n):.4g} m3/s). Use a larger pipe.")
        lo = 1e-9 * sec.D
    else:
        lo, hi = 1e-9, 1.0
        while f(hi) < 0:
            hi *= 2.0
            if hi > 1e5:
                raise NoSolution("No normal depth found (the depth would exceed 100 km). "
                                 "Check Q, slope and n.")
    return brentq(f, lo, hi, xtol=1e-13, rtol=1e-12, maxiter=300)

"""Inputs, validation and friendly error messages."""
from __future__ import annotations

import json
import math
import numbers
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple


class InputError(ValueError):
    """Something is wrong with the inputs (message is meant for the user)."""


class NoSolution(RuntimeError):
    """The equations have no solution for these numbers."""


DEFAULT_DIAMETERS = (0.3, 0.4, 0.5, 0.6, 0.75, 0.9, 1.0, 1.2, 1.5, 1.8, 2.0, 2.4)
TRAP_MODES = ("given_z", "best_for_z", "best_overall", "scan_z")
OBJECTIVES = ("area", "flow_area", "perimeter", "cost")


def load_linings():
    path = Path(__file__).parent / "data" / "linings.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)["linings"]


def _real(v):
    return isinstance(v, numbers.Real) and not isinstance(v, bool) and math.isfinite(v)


@dataclass
class Inputs:
    Q: float                      # design discharge, m3/s
    S: float                      # bed slope, m/m
    n: float                      # Manning roughness
    z: float = 1.5                # side slope (horizontal : 1 vertical)
    trap_mode: str = "given_z"
    fb_mode: str = "percent"      # "percent" of depth or "fixed" metres
    fb: float = 20.0
    vmin: Optional[float] = 0.6   # m/s, None = no limit
    vmax: Optional[float] = None
    max_width: Optional[float] = None
    max_depth: Optional[float] = None   # total depth incl. freeboard
    diameters: Tuple[float, ...] = DEFAULT_DIAMETERS
    free_diameter: bool = False
    max_fill: float = 0.80        # max y/D in a pipe
    objective: str = "area"
    c_exc: float = 1.0            # cost per m2 of excavation (relative)
    c_lin: float = 1.0            # cost per m of lined perimeter (relative)
    fr_lo: float = 0.8
    fr_hi: float = 1.2

    def validate(self):
        def pos(v, label, zero_ok=False):
            if not _real(v):
                raise InputError(f"{label} must be a number (got {v!r}).")
            if v < 0 or (v == 0 and not zero_ok):
                word = "zero or positive" if zero_ok else "greater than zero"
                raise InputError(f"{label} must be {word} (got {v}).")

        pos(self.Q, "Design discharge Q")
        if not _real(self.S) or self.S <= 0:
            raise InputError(
                "Bed slope S must be greater than zero. On a flat or adverse bed "
                "there is no uniform flow, because gravity is not driving the water.")
        if self.S >= 1:
            raise InputError("Bed slope S is in m/m, so 0.001 means 1 m drop per 1000 m. "
                             "A value of 1 or more looks like a typing mistake.")
        pos(self.n, "Manning's n")
        if self.n > 0.2:
            raise InputError("Manning's n above 0.2 is unrealistic for a designed channel. "
                             "Typical values are 0.010 to 0.040.")
        pos(self.z, "Side slope z", zero_ok=True)
        if self.trap_mode not in TRAP_MODES:
            raise InputError(f"Trapezoid mode must be one of {TRAP_MODES}.")
        if self.fb_mode not in ("percent", "fixed"):
            raise InputError("Freeboard mode must be 'percent' or 'fixed'.")
        pos(self.fb, "Freeboard", zero_ok=True)
        if self.fb_mode == "percent" and self.fb > 100:
            raise InputError("Freeboard above 100 % of the depth looks like a mistake.")
        for name, label in (("vmin", "Minimum velocity"), ("vmax", "Maximum velocity"),
                            ("max_width", "Maximum width"), ("max_depth", "Maximum depth")):
            v = getattr(self, name)
            if v is not None:
                pos(v, label, zero_ok=(name == "vmin"))
        if self.vmin is not None and self.vmax is not None and self.vmin >= self.vmax:
            raise InputError(f"Minimum velocity ({self.vmin}) must be smaller than "
                             f"maximum velocity ({self.vmax}).")
        if not self.free_diameter:
            if not self.diameters:
                raise InputError("The pipe diameter list is empty. Add diameters or "
                                 "switch on 'free diameter'.")
            for d in self.diameters:
                pos(d, "Each pipe diameter")
        if not _real(self.max_fill) or not (0 < self.max_fill <= 1):
            raise InputError("Maximum filling ratio y/D must be between 0 and 1 "
                             "(for example 0.8).")
        if self.objective not in OBJECTIVES:
            raise InputError(f"Objective must be one of {OBJECTIVES}.")
        pos(self.c_exc, "Excavation cost", zero_ok=True)
        pos(self.c_lin, "Lining cost", zero_ok=True)
        if self.objective == "cost" and self.c_exc == 0 and self.c_lin == 0:
            raise InputError("Both unit costs are zero, so the cost objective is meaningless.")
        return self

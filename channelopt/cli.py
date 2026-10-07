"""Command line interface:  python -m channelopt --Q 5 --S 0.001 --lining concrete_trowel"""
import argparse
import json
import sys
from pathlib import Path

from .inputs import InputError, Inputs, NoSolution, load_linings
from .optimize import compare
from .plots import save_all
from .report import format_text, write_csv

SECTIONS = {"rectangular": ("rectangular",), "trapezoidal": ("trapezoidal",),
            "circular": ("circular",),
            "all": ("rectangular", "trapezoidal", "circular")}


def build_parser():
    p = argparse.ArgumentParser(
        prog="python -m channelopt",
        description="Design open channels with Manning's equation (uniform flow).")
    a = p.add_argument
    a("--Q", type=float, help="design discharge, m3/s")
    a("--S", type=float, help="bed slope, m/m (0.001 = 1 m per km)")
    a("--n", type=float, help="Manning's n (or use --lining)")
    a("--lining", help="lining id, fills n and velocity limits (see --list-linings)")
    a("--section", choices=SECTIONS, default=None, help="default: all")
    a("--z", type=float, help="side slope for the trapezoid (H:1V)")
    a("--trap-mode", choices=["given_z", "best_for_z", "best_overall", "scan_z"])
    a("--fb-percent", type=float, help="freeboard as percent of depth (default 20)")
    a("--fb-fixed", type=float, help="freeboard in metres")
    a("--vmin", type=float, help="minimum velocity m/s (0 = off)")
    a("--vmax", type=float, help="maximum velocity m/s")
    a("--max-width", type=float)
    a("--max-depth", type=float, help="maximum total depth including freeboard, m")
    a("--diameters", help="comma list of pipe diameters in m, e.g. 0.6,0.9,1.2")
    a("--free-diameter", action="store_true", default=None)
    a("--max-fill", type=float, help="maximum y/D for pipes (default 0.8)")
    a("--objective", choices=["area", "flow_area", "perimeter", "cost"])
    a("--c-exc", type=float, help="cost per m2 of excavation (relative)")
    a("--c-lin", type=float, help="cost per m of lined perimeter (relative)")
    a("--config", help="JSON file with any of these settings")
    a("--out", help="folder for results.csv and PNG figures")
    a("--no-plots", action="store_true")
    a("--list-linings", action="store_true")
    return p


def settings_from(args):
    v = {}
    if args.config:
        with open(args.config, encoding="utf-8") as f:
            v.update(json.load(f))
    cli = {"Q": args.Q, "S": args.S, "n": args.n, "lining": args.lining,
           "section": args.section, "z": args.z, "trap_mode": args.trap_mode,
           "vmax": args.vmax, "max_width": args.max_width, "max_depth": args.max_depth,
           "free_diameter": args.free_diameter, "max_fill": args.max_fill,
           "objective": args.objective, "c_exc": args.c_exc, "c_lin": args.c_lin}
    v.update({k: x for k, x in cli.items() if x is not None})
    if args.vmin is not None:
        v["vmin"] = None if args.vmin == 0 else args.vmin
    if args.fb_fixed is not None:
        v["fb_mode"], v["fb"] = "fixed", args.fb_fixed
    elif args.fb_percent is not None:
        v["fb_mode"], v["fb"] = "percent", args.fb_percent
    if args.diameters:
        try:
            v["diameters"] = [float(x) for x in args.diameters.split(",")]
        except ValueError:
            raise InputError("--diameters must be numbers separated by commas, e.g. 0.6,0.9,1.2")
    return v


def to_inputs(v):
    v = dict(v)
    section = v.pop("section", "all")
    lin = v.pop("lining", None)
    if lin:
        table = {x["id"]: x for x in load_linings()}
        if lin not in table:
            raise InputError(f"Unknown lining '{lin}'. Use --list-linings to see the options.")
        v.setdefault("n", table[lin]["n"])
        if "vmax" not in v:
            v["vmax"] = table[lin]["vmax"]
        v.setdefault("vmin", table[lin]["vmin"])
    for need in ("Q", "S", "n"):
        if need not in v:
            raise InputError(f"Missing {need}. Give --{need} (n can come from --lining).")
    if "diameters" in v:
        v["diameters"] = tuple(v["diameters"])
    if section not in SECTIONS:
        raise InputError(f"Section must be one of {list(SECTIONS)}.")
    try:
        inp = Inputs(**v)
    except TypeError as e:
        raise InputError(f"Unknown setting: {e}")
    return inp.validate(), section


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.list_linings:
        print("UNVERIFIED typical values. Check against a textbook (e.g. Chow).\n")
        print(f"{'id':18s}{'n':>7s}{'n range':>14s}{'Vmax m/s':>10s}  description")
        for x in load_linings():
            print(f"{x['id']:18s}{x['n']:7.3f}{x['n_min']:7.3f}-{x['n_max']:.3f}"
                  f"{x['vmax']:10.1f}  {x['label']}")
        return 0
    try:
        inp, section = to_inputs(settings_from(args))
        res = compare(inp, SECTIONS[section or "all"] if section else SECTIONS["all"])
    except (InputError, NoSolution) as e:
        print(f"Input problem: {e}", file=sys.stderr)
        return 2
    except FileNotFoundError as e:
        print(f"File not found: {e.filename}", file=sys.stderr)
        return 2
    print(format_text(res, inp))
    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        write_csv(res, inp.objective, out / "results.csv")
        print(f"\nSaved {out / 'results.csv'}")
        if not args.no_plots:
            for f in save_all(res, out):
                print(f"Saved {f}")
    return 0

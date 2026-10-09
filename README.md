# Channel Design Optimizer

**Live app: https://biswashk920.github.io/channel-design-optimizer/**

Finds an efficient open-channel section (rectangular, trapezoidal, circular pipe) for a design flow, bed slope and roughness, using Manning's equation for steady uniform flow. It includes best hydraulic sections and checks velocity, Froude number, freeboard and size limits.

> **Learning tool, not for final design.** The roughness (n) and velocity tables are typical values written from memory and are **unverified**. Check them against a textbook such as Chow.

## Run locally (Anaconda Prompt)
```
pip install -r requirements.txt
python -m channelopt --Q 5 --S 0.001 --lining concrete_trowel --out examples/results
python -m channelopt --list-linings
python -m unittest discover -s tests -v
```
Other useful options: `--section circular --free-diameter`, `--trap-mode best_overall`, `--vmax 3`, `--max-width 8`, `--objective perimeter`, `--config examples/example_config.json`.

## Objectives
`area` (default) = gross section: channel excavation up to the top of the bank, or the whole pipe barrel. This makes the three types comparable. `flow_area` = water area only, `perimeter` = wetted perimeter, `cost` = excavation x c_exc + perimeter x c_lin (relative units). With gross area, vertical walls often win because bank stability is not modelled. Without limits, minimum *flow* area equals the best hydraulic section.

## Limitations
Uniform flow only (no backwater curves); no sediment transport; permissible velocities depend on the source; prismatic sections only; pipes treated as open-channel (not pressurised); the web page has no side-slope scan (`scan_z`) and no charts of the optimisation curve (Python makes both).

MIT licence.

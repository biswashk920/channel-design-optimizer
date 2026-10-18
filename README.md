<h1 align="center">Channel Design Optimizer</h1>

<p align="center"><a href="https://biswashk920.github.io/channel-design-optimizer/"><b>&#9654;&nbsp; OPEN THE WEB APP &nbsp;&#9654;</b></a></p>
<p align="center"><a href="https://biswashk920.github.io/channel-design-optimizer/">https://biswashk920.github.io/channel-design-optimizer/</a></p>

Enter a design discharge, a bed slope and a lining material. The tool sizes a rectangular channel, a trapezoidal channel and a circular pipe for steady uniform flow (Manning's equation), checks each one against your limits, and recommends the most efficient.

It comes in two forms:

- **Web app.** Runs in the browser with nothing to install. It gives a comparison table, cross-section drawings, a 3D view you can rotate, a rating curve, a specific-energy diagram and a CSV download.
- **Python package.** The same calculations, plus a side-slope search, a roughness-range check, saved figures and a validation report for your own textbook examples.

> **Check the lining table.** The roughness (n) values and velocity limits are typical figures and are **unverified**. Compare them with a textbook such as Chow before relying on any result.

---

## How to use the web app

Open the link above. The page has three input groups, a **Calculate** button and a **Download CSV** button.

### 1. Flow and ground

| Field | What to enter |
|---|---|
| Design flow Q | The discharge the channel must carry, in m³/s. |
| Bed slope S | Drop per unit length, in m/m. 0.001 means 1 m of drop per 1000 m. |
| Lining material | Pick a material to fill in n and the velocity limits, or choose "Custom" and type your own n. |
| Manning's roughness n | Higher n means a rougher surface and slower flow. Typical designed channels are 0.010 to 0.040. |

### 2. Shape options

| Field | What it does |
|---|---|
| Side slope z | Horizontal run per 1 vertical, for the trapezoid. z = 1.5 means 1.5 m across for every 1 m of height. |
| Trapezoid mode | "Use my z, optimise width" keeps your z and searches for the best width. "Best hydraulic section for my z" uses the width-to-depth ratio that gives the least wetted perimeter. "Best z overall" uses the half-hexagon section (z = 0.577). |
| Freeboard | Extra wall height above the water. Choose a percent of the water depth or a fixed height in metres, then type the value. |
| Goal | What to minimise: gross area (digging, or the whole pipe barrel), water flow area, wetted perimeter (lining), or a cost proxy. |
| Cost per m² dug / per m lined | Only used by the cost goal. Any consistent relative units work. |

### 3. Limits (leave a box empty for no limit)

| Field | What it does |
|---|---|
| Min velocity | Water slower than this may deposit silt. The default is 0.6 m/s. |
| Max velocity | Water faster than this may erode the lining. Filled in from the lining choice. |
| Max top width, max total depth | Site limits. Total depth includes freeboard. |
| Pipe diameters | The commercial sizes the circular case may choose from, separated by commas. |
| Compute exact pipe size | Set to "Yes" to solve for the exact diameter instead of using the list. |
| Max pipe filling y/D | The largest share of the pipe height the water may fill. The default 0.8 leaves air space. |

### Reading the results

1. **Table.** One column per section, showing dimensions, depth, area, wetted perimeter, velocity, Froude number, flow regime, critical depth and an overall PASS or FAIL. A warning mark next to the Froude number means the flow is close to critical (Froude between 0.8 and 1.2). The water surface is unstable there, so avoid it.
2. **Recommended section.** The section with the lowest goal value among those that pass every check. Sections that fail are listed with the reason.
3. **Cross-sections.** Each section drawn at its normal depth, with the freeboard line.
4. **3D view.** Drag to rotate. The slider sets the channel length. The dropdown switches section. The cross-section is enlarged so it stays visible next to a long channel.
5. **Rating curve.** Discharge against depth for the selected section. The marked point is your design flow.
6. **Specific-energy diagram.** Energy against depth. The marked points show the normal depth and the critical depth.
7. **Download CSV.** Saves the table as a file you can open in Excel.

### If you see an error message

The page checks inputs and explains the problem: a zero or negative flow, a zero slope (flat beds have no uniform flow), a minimum velocity above the maximum, or a pipe list with no valid sizes. If no section passes every check, the page says which check failed. Loosen a limit, change the lining, or add larger pipe sizes.

---

## What it calculates

- Normal depth from Manning's equation, found by bracketed root-finding rather than an explicit formula.
- Best hydraulic sections: rectangular `b = 2y`; trapezoidal `b/y = 2(sqrt(1+z^2) - z)`; the half hexagon `z = 1/sqrt(3)`; and circular pipe behaviour, with maximum velocity near y/D = 0.81 and maximum discharge near 0.94.
- Constrained optimisation of width for one of four goals: gross area, flow area, wetted perimeter or a cost proxy. The Python version can also search the side slope (`--trap-mode scan_z`).
- Checks: minimum and maximum velocity, Froude number and flow regime, critical depth, freeboard, width and depth limits, and pipe filling ratio.
- Roughness range (Python): the same section re-solved at the smoothest and roughest likely n. The smooth case tests erosion. The rough case tests overtopping and silting.

**About the default goal.** "Gross area" is the dug section up to the top of the bank, or the whole pipe barrel. Using water flow area alone would favour pipes unfairly, because the pipe wall is not counted. Gross area does not model bank stability, so vertical walls often win. If your soil needs sloped banks, set z and the trapezoid mode yourself.

---

## Python quick start

```
pip install -r requirements.txt
python -m channelopt --Q 5 --S 0.001 --lining concrete_trowel --out examples/results
python -m channelopt --list-linings
python -m channelopt.validate examples/textbook_template.csv
python -m unittest discover -s tests -v
```

More options: `--section circular --free-diameter`, `--trap-mode best_overall`, `--vmax 3`, `--max-width 8`, `--objective perimeter`, `--n-range 0.011,0.015`, `--config examples/example_config.json`.

To install it as a command, run `pip install .` and then `channelopt --Q 5 --S 0.001 --n 0.013`.

Example output is in [`examples/results`](examples/results).

---

## Validation

- 44 automated tests run on every push through GitHub Actions. They cover the Manning round trip, best-section formulas, circular limits, critical depth, input validation, the roughness check, and the browser code against Python on six test cases (using Node.js).
- The 3D geometry is tested by comparing the area of the drawn water shape with the hydraulic flow area.
- **No textbook worked examples are included.** The tests use analytic checks and one hand calculation. To validate against your course book, enter solved problems in `examples/textbook_template.csv` and run `python -m channelopt.validate`. For each row it prints the book answer, the computed answer and the percentage difference.
- The page layout, 3D drawing and CSV button have not been tested in an automated browser test.

---

## Limitations

- Steady uniform flow only. No backwater curves or hydraulic jumps.
- Prismatic sections with constant slope and roughness. No bends, transitions or compound sections.
- No sediment transport and no tractive-force check. Permissible velocities depend on the source you use.
- Pipes are treated as open-channel flow, not as pressurised pipes.
- The web page has no side-slope search and no roughness-range check. Those are Python only.

---

## Author

Biswash Kaphle

## Licence

MIT. See [LICENSE](LICENSE). Remember to put your name in the LICENSE file as well.
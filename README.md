# TI-84 Embedded Systems Toolkit — Python CLI Port

![Tests](https://github.com/Jacksole/ti84toolkit/actions/workflows/test.yml/badge.svg)

A Python/terminal port of the original TI-BASIC toolkit built for the TI-84 Plus.
Same modular philosophy — efficiency, clarity, extensibility — now running as a
real CLI instead of a calculator program, with no memory ceiling and no data
loss on reset.

## Status

**V1 complete** (Electronics, Logic, Math, Physics) **+ V2 complete**
(Statistics, Unit Conversion, History/Persistence, JSON output, Batch mode,
Config file, Gamification, Shell completion) **+ V3 complete** (CI, Plotting,
Circuit Diagrams, Show-Your-Work, Resistor BOM Finder) **+ V4 complete**
(Orbital Mechanics: Kepler's laws, Kepler's equation, Hohmann transfer)
**+ V5 complete** (Calculus, Geometry, Linear Algebra, Sequences & Series,
Probability Distributions, Finance/TVM).

Between V1 (calculator port) and V5, the toolkit now covers a full
high-school-through-early-college math/science curriculum: algebra,
geometry, trigonometry, calculus, linear algebra, sequences & series,
statistics, probability, physics, orbital mechanics, digital logic, and
electronics/finance math.

## Install

```bash
git clone <your-repo-url>
cd ti84toolkit
pip install -e .
```

This registers a `toolkit` command on your PATH. Alternatively, run directly
without installing:

```bash
pip install -r requirements.txt
python cli.py
```

## Usage

**Interactive menu** (matches the original TI-84 navigation flow):

```bash
toolkit
```

**Direct subcommands** (scriptable, for power users):

```bash
# Ohm's Law — provide exactly 2 of voltage/current/resistance
toolkit electronics ohms-law --current 2 --resistance 100

# Resistor color code (4-band or 5-band)
toolkit electronics resistor orange orange red gold

# 555 timer astable mode
toolkit electronics timer555 --r1 1000 --r2 1000 --c 0.000001

# Logic -- evaluate a single gate
toolkit logic gate NAND true true

# Logic -- truth table by gate name
toolkit logic truth-table XOR --inputs 2

# Logic -- truth table by boolean expression
toolkit logic truth-table "A AND (B OR NOT C)"

# Math -- quadratic solver (use --flag=-value for negative coefficients)
toolkit math quadratic --a 1 --b=-5 --c 6

# Math -- trigonometry
toolkit math trig sin 90

# Math -- general equation solving (linear, quadratic, and beyond)
toolkit math solve "2*x + 3 = 7"
toolkit math solve "x**2 - 4 = 0"

# Physics -- kinematics (exactly 3 of v0, v, a, t, d)
toolkit physics kinematics --v0 0 --a 2 --t 5

# Physics -- energy (kinetic, potential, or work)
toolkit physics energy kinetic --mass 2 --velocity 3
toolkit physics energy potential --mass 1 --height 10
toolkit physics energy work --force 10 --distance 5

# Physics -- power (from work+time OR force+velocity)
toolkit physics power --work 100 --time 4
toolkit physics power --force 10 --velocity 5

# Statistics -- descriptive stats (use -- before negative values)
toolkit stats describe 2 4 4 5 7 9

# Statistics -- five-number summary / quartiles
toolkit stats quartiles 1 2 3 4 5 6 7

# Statistics -- combinatorics
toolkit stats factorial 5
toolkit stats npr 5 2
toolkit stats ncr 5 2

# Units -- convert between units in a category
toolkit units convert length 1 km m
toolkit units convert temperature 100 c f
toolkit units convert resistance 2.2 kohm ohm
toolkit units list-units length

# History -- view or clear your local calculation log
toolkit history show
toolkit history show --limit 5 --module electronics
toolkit history clear --yes

# JSON output -- add --json before the subcommand, for any command
toolkit --json math solve "2*x + 3 = 7"
toolkit --json units convert length 1 mi km

# Batch mode -- run a sequence of commands from a file
toolkit batch my_commands.txt

# Show your work -- print the step-by-step derivation
toolkit electronics ohms-law --current 2 --resistance 100 --steps
toolkit physics kinematics --v0 0 --a 2 --t 5 --steps

# Plotting -- save a chart (headless-safe, works over SSH/WSL)
toolkit physics kinematics --v0 0 --a 2 --t 5 --plot
toolkit electronics timer555 --r1 1000 --r2 1000 --c 0.000001 --plot

# Circuit diagrams -- save a schematic/color-band image
toolkit electronics resistor orange orange red gold --diagram
toolkit electronics timer555 --r1 1000 --r2 1000 --c 0.000001 --diagram

# Resistor combo finder -- closest standard single/series/parallel match
toolkit electronics bom 4700
toolkit electronics bom 4700 --series E12

# Orbital mechanics -- period, velocity, Kepler's equation, Hohmann transfer
toolkit orbital period --a 6779000 --body earth
toolkit orbital velocity --r 6779000 --kind circular --body earth
toolkit orbital velocity --r 6779000 --kind escape --body earth
toolkit orbital kepler-equation 1.0 0.5 --steps
toolkit orbital hohmann --r1 6671000 --r2 42164000 --body earth --steps --plot

# Calculus -- derivatives, integrals, limits, Taylor series
toolkit calculus derivative "x**3 + 2*x"
toolkit calculus integral "x**2" --lower 0 --upper 3
toolkit calculus limit "sin(x)/x" 0
toolkit calculus taylor-series "exp(x)" --order 4

# Geometry -- shapes, Pythagorean theorem, distance
toolkit geometry circle 3
toolkit geometry triangle-sides 3 4 5
toolkit geometry pythagorean-hypotenuse 3 4
toolkit geometry sphere 3

# Linear algebra -- vectors and matrices (comma/semicolon-delimited)
toolkit linalg vector-dot "1,2,3" "4,5,6"
toolkit linalg matrix-det "1,2;3,4"
toolkit linalg matrix-inverse "4,7;2,6"

# Sequences and series
toolkit sequences arithmetic-sum --a1 1 --d 1 --n 10
toolkit sequences geometric-sum-infinite --a1 1 --r 0.5

# Probability distributions
toolkit probability normal-cdf 1.96
toolkit probability binomial-pmf --n 10 --k 5 --p 0.5

# Finance -- TVM solver (any 4 of n/rate/pv/pmt/fv) and compound interest
toolkit finance tvm --n 360 --rate 6 --pv 300000 --fv 0 --steps
toolkit finance compound-interest --principal 1000 --rate 5 --years 10
```

Run `toolkit electronics --help`, `toolkit logic --help`, `toolkit math --help`,
`toolkit physics --help`, `toolkit stats --help`, `toolkit units --help`,
`toolkit history --help`, `toolkit orbital --help`, `toolkit calculus --help`,
`toolkit geometry --help`, `toolkit linalg --help`, `toolkit sequences --help`,
`toolkit probability --help`, or `toolkit finance --help` to see all options
for any command.

### Shell completion

Built into `typer` at no extra cost:

```bash
toolkit --install-completion
```

### Config file

Optional, at `~/.config/ti84toolkit/config.toml`:

```ini
[physics]
gravity = 9.81

[display]
precision = 6
```

Currently `physics.gravity` sets the default for `toolkit physics energy potential`
(override per-call with `--gravity`). `display.precision` is reserved for a
future formatting pass.

### Calculation history

Every successful calculation is logged locally to `~/.ti84toolkit/history.db`
(SQLite). Nothing leaves your machine. View it anytime with `toolkit history show`,
or wipe it with `toolkit history clear`.

### Batch file format

One command's arguments per line (omit the leading `toolkit`), `#` for comments:

```
# my_commands.txt
electronics ohms-law --current 2 --resistance 100
math quadratic --a 1 --b -5 --c 6
stats factorial 5
```

### Gamification

Milestone badges (1 / 10 / 50 / 100 / 500 logged calculations) print
automatically the moment you cross a threshold — a small callback to the
original doc's V2 "badge system" idea.

### Continuous integration

`.github/workflows/test.yml` runs the full pytest suite on every push/PR to
`main`, across Python 3.9–3.12.

### Plotting

`--plot` (kinematics, 555 timer) saves a PNG chart instead of/in addition to
the text result:
- Kinematics: position(t) and velocity(t) curves
- 555 timer: the astable output square wave, duty cycle visible in the
  high/low segment widths

Uses matplotlib's Agg backend, so it works headlessly over SSH/WSL without
an X server or WSLg.

### Circuit diagrams

`--diagram` (resistor, 555 timer) saves a schematic image:
- Resistor: the physical resistor body with its actual decoded color bands
- 555 timer: the classic astable wiring (VCC → R1 → DIS, DIS → R2 → THR,
  THR tied to TRIG, capacitor to GND, OUT broken out) — a real schematic via
  `schemdraw`, not just a picture

### Show your work

`--steps` (Ohm's Law, kinematics) prints the derivation instead of just the
final numbers — which values were known, which equation applies, the
substitution, and the result. Useful as a teaching aid, not just an answer key.

### Resistor combo finder (BOM)

`toolkit electronics bom <target>` searches standard E12/E24 resistor values
and returns the closest single resistor, series pair, and parallel pair —
answers "I need 4.7kΩ, what do I actually have on hand?" instead of just
decoding a resistor you already hold.

### Orbital mechanics

Two-body Kepler mechanics and Hohmann transfer orbits — `toolkit orbital
period`, `velocity`, `kepler-equation`, `hohmann`. Deliberately scoped to
math that could plausibly have run on the original calculator: closed-form
equations (Kepler's Third Law, vis-viva, circular/escape velocity) plus one
Newton-Raphson iteration for Kepler's equation (transcendental, but iterative
root-finding is exactly what TI-BASIC's loops handle). `--body earth` (also
moon/mars/sun/jupiter) supplies the right gravitational parameter without
looking it up by hand. `--steps` shows the derivation, `--plot` on `hohmann`
saves a diagram of both orbits and the connecting transfer ellipse.

N-body simulation (3+ mutually gravitating bodies) is explicitly out of
scope: unlike everything else in this toolkit, it has no closed-form
solution and requires numerical integration over many timesteps — genuinely
new capability rather than something the original hardware could plausibly
have done, if given unlimited memory.

### Calculus

`toolkit calculus derivative/integral/limit/taylor-series` — symbolic
differentiation, indefinite/definite integration, two-sided/one-sided
limits (including at infinity), and Taylor series expansion, all sympy-backed.
Distinct from orbital mechanics: orbital mechanics only implements
pre-solved formulas that were originally *derived* with calculus; this
module lets you actually perform the calculus operations yourself.

### Geometry

`toolkit geometry circle/rectangle/triangle-bh/triangle-sides/
pythagorean-hypotenuse/pythagorean-leg/distance/sphere/cylinder/cone/box` —
area/perimeter/volume/surface-area for common 2D and 3D shapes, the
Pythagorean theorem in either direction, and the 2D/3D distance formula.

### Linear Algebra

`toolkit linalg vector-dot/vector-cross/vector-magnitude/vector-normalize/
vector-angle/matrix-add/matrix-multiply/matrix-transpose/matrix-det/
matrix-inverse` — vectors and matrices are passed as delimited strings
(`"1,2,3"` for vectors, `"1,2;3,4"` for matrices) to keep CLI usage simple.
Notable inclusion: the TI-84's `[MATRX]` button and matrix editor are one of
its signature features — a toolkit port that skipped matrices would be
missing something the original calculator was genuinely known for.

### Sequences and Series

`toolkit sequences arithmetic-term/arithmetic-sum/geometric-term/
geometric-sum/geometric-sum-infinite` — TI-84 has a dedicated SEQ graphing
mode for exactly this material.

### Probability Distributions

`toolkit probability binomial-pmf/binomial-cdf/binomial-stats/normal-pdf/
normal-cdf/normal-cdf-range/inverse-normal-cdf/z-score` — distinct from the
statistics module (descriptive stats + combinatorics): distributions are a
different, commonly-taught piece. TI-84's `normalcdf`/`invNorm`/`binompdf`
are AP Statistics staples that combinatorics alone doesn't cover.

### Finance

`toolkit finance tvm/compound-interest` — a full Time Value of Money solver
matching the TI-84's built-in Finance app (`APPS → Finance → TVM Solver`).
Given any 4 of `{n, rate, pv, pmt, fv}`, solves for the 5th; n/pv/pmt/fv are
closed-form, and the interest rate (no closed form) is solved via bisection
— the same iterative-root-finding spirit as Kepler's equation. Sanity-checked
against a real-world $300k/30yr/6% mortgage payment (~$1,798/month).

## Project Structure

```
ti84toolkit/
├── cli.py                  # Entrypoint: typer app, menu/subcommands/JSON/history/batch
├── .github/workflows/
│   └── test.yml             # CI: pytest across Python 3.9-3.12 on every push/PR
├── core/
│   ├── menu.py              # Interactive menu system (rich-based)
│   ├── validation.py        # Shared input validation
│   ├── history.py           # SQLite-backed calculation history
│   ├── config.py            # ~/.config/ti84toolkit/config.toml parser
│   └── badges.py            # Milestone-based gamification
├── modules/
│   ├── electronics.py       # Ohm's Law, resistor color code, 555 timer
│   ├── logic.py              # Gate evaluation, truth tables, boolean expression parsing
│   ├── math_tools.py         # Quadratic solver, trigonometry, sympy-backed equation solving
│   ├── physics.py            # Kinematics solver (sympy-backed), energy, power
│   ├── statistics_tools.py   # Descriptive stats, quartiles, combinatorics (nPr/nCr)
│   ├── units.py              # Length, mass, time, temperature, electrical unit conversion
│   ├── plotting.py           # Kinematics/555 timer/Hohmann transfer chart generation (matplotlib)
│   ├── circuits.py           # Resistor color-band + 555 astable schematic diagrams
│   ├── resistor_bom.py       # Standard-value resistor combination finder
│   └── orbital.py            # Kepler's laws, Kepler's equation, Hohmann transfer
│   ├── calculus.py           # Symbolic derivatives, integrals, limits, Taylor series
│   ├── geometry.py           # 2D/3D shapes, Pythagorean theorem, distance formula
│   ├── linear_algebra.py     # Vector and matrix operations (numpy-backed)
│   ├── sequences.py          # Arithmetic and geometric sequences/series
│   ├── probability.py        # Binomial and normal distributions
│   └── finance.py            # TVM solver, compound interest
├── tests/                    # 271 tests total (pytest), one file per module
├── requirements.txt
└── setup.py
```

## Testing

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

## Roadmap

All V1-V5 features are complete. Remaining ideas, if this keeps growing:

- **Broader config coverage** — `display.precision` is parsed but not yet
  applied to output formatting
- **Export** — `toolkit history show --format csv` for pulling a session's
  work into a worksheet or report
- **More unit categories** — area, volume, energy, pressure
- **Richer batch mode** — variables/templating across lines, not just a
  literal command list
- **More circuit diagrams** — voltage divider, RC filter, op-amp configs
- **BOM for other components** — capacitor/inductor standard-value finder,
  alongside the existing resistor combo finder
- **N-body simulation** — explicitly deferred (see Orbital Mechanics above);
  would need numerical integration, not just more equations
- **Differential equations** — a natural calculus follow-on (sympy already
  supports `dsolve`)
- **Complex numbers as a first-class tool** — currently only surface
  implicitly (quadratic solver's complex roots); TI-84 supports complex
  arithmetic as its own mode

Already brought forward from earlier wishlists: truth table generator and
boolean expression evaluator (Logic), a fully general sympy-backed
kinematics solver (Physics) rather than a SUVAT lookup table, and the
persistent calculation history that was explicitly impossible on the
original TI-84 hardware.

## Design Notes

The original TI-84 constraints (monochrome, ~24KB RAM, no persistent storage)
shaped the original architecture around strict modularity and input
validation before execution. This port keeps that discipline — every compute
function is pure and separately testable, and the CLI layer (menu or
subcommand) never touches calculation logic directly — while dropping the
constraints that no longer apply.

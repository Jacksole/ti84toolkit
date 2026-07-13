# TI-84 Embedded Systems Toolkit — Python CLI Port

A Python/terminal port of the original TI-BASIC toolkit built for the TI-84 Plus.
Same modular philosophy — efficiency, clarity, extensibility — now running as a
real CLI instead of a calculator program, with no memory ceiling and no data
loss on reset.

## Status

**V1 complete** (Electronics, Logic, Math, Physics) **+ V2 complete**
(Statistics, Unit Conversion, History/Persistence, JSON output, Batch mode,
Config file, Gamification, Shell completion).

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
```

Run `toolkit electronics --help`, `toolkit logic --help`, `toolkit math --help`,
`toolkit physics --help`, `toolkit stats --help`, `toolkit units --help`, or
`toolkit history --help` to see all options for any command.

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

## Project Structure

```
ti84toolkit/
├── cli.py                  # Entrypoint: typer app, menu/subcommands/JSON/history/batch
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
│   └── units.py              # Length, mass, time, temperature, electrical unit conversion
├── tests/                    # 131 tests total (pytest), one file per module
├── requirements.txt
└── setup.py
```

## Testing

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

## Roadmap

All V1 modules and all planned V2 additions are complete. Remaining ideas,
if this keeps growing:

- **Broader config coverage** — `display.precision` is parsed but not yet
  applied to output formatting
- **Export** — `toolkit history show --format csv` for pulling a session's
  work into a worksheet or report
- **More unit categories** — area, volume, energy, pressure
- **Richer batch mode** — variables/templating across lines, not just a
  literal command list

Already brought forward from the original V2 wishlist: truth table generator
and boolean expression evaluator (Logic), a fully general sympy-backed
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

# TI-84 Embedded Systems Toolkit — Python CLI Port

A Python/terminal port of the original TI-BASIC toolkit built for the TI-84 Plus.
Same modular philosophy — efficiency, clarity, extensibility — now running as a
real CLI instead of a calculator program, with no memory ceiling and no data
loss on reset.

## Status

**All four V1 modules complete (Electronics, Logic, Math, Physics), plus
Statistics** — originally deferred in the V1 handoff doc's Known Limitations
("No statistics module (deferred)"), now built out as a V2 addition.

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
```

Run `toolkit electronics --help`, `toolkit logic --help`, `toolkit math --help`,
`toolkit physics --help`, or `toolkit stats --help` to see all options for any command.

## Project Structure

```
ti84toolkit/
├── cli.py                  # Entrypoint: typer app, routes to menu or subcommands
├── core/
│   ├── menu.py              # Interactive menu system (rich-based)
│   └── validation.py        # Shared input validation
├── modules/
│   ├── electronics.py       # Ohm's Law, resistor color code, 555 timer
│   ├── logic.py              # Gate evaluation, truth tables, boolean expression parsing
│   ├── math_tools.py         # Quadratic solver, trigonometry, sympy-backed equation solving
│   ├── physics.py            # Kinematics solver (sympy-backed), energy, power
│   └── statistics_tools.py   # Descriptive stats, quartiles, combinatorics (nPr/nCr)
├── tests/
│   ├── test_electronics.py
│   ├── test_logic.py
│   ├── test_math_tools.py
│   ├── test_physics.py
│   └── test_statistics_tools.py  # 92 tests total (pytest)
├── requirements.txt
└── setup.py
```

## Testing

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

## Roadmap

All V1 modules (Electronics, Logic, Math, Physics) plus the V2 Statistics
addition are complete. Remaining ideas, in rough priority order:

- **Unit conversion module** — metric/imperial, engineering units (resistance,
  voltage, force) — pairs naturally with the electronics module
- **History/persistence** — SQLite-backed calculation log, viewable via
  `toolkit history`; impossible on the original hardware due to RAM reset,
  trivial here
- **JSON output flag** (`--json`) across all commands, for scripting/piping
- **Shell completion** — `typer` supports this out of the box
- **Batch/scripting mode** — run a sequence of commands from a `.txt` file,
  output a report
- **Config file** — `~/.config/ti84toolkit/config.toml` for default gravity
  constant, decimal precision, color theme
- **Gamification** — badge system / easter eggs, per the original doc's V2 plan

Already brought forward from the original V2 wishlist: the truth table
generator and boolean expression evaluator (Logic module), and a fully
general sympy-backed kinematics solver (Physics module) rather than a lookup
table of the classic SUVAT equations.

## Design Notes

The original TI-84 constraints (monochrome, ~24KB RAM, no persistent storage)
shaped the original architecture around strict modularity and input
validation before execution. This port keeps that discipline — every compute
function is pure and separately testable, and the CLI layer (menu or
subcommand) never touches calculation logic directly — while dropping the
constraints that no longer apply.

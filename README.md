# TI-84 Embedded Systems Toolkit — Python CLI Port

A Python/terminal port of the original TI-BASIC toolkit built for the TI-84 Plus.
Same modular philosophy — efficiency, clarity, extensibility — now running as a
real CLI instead of a calculator program, with no memory ceiling and no data
loss on reset.

## Status

**All four V1 modules complete: Electronics, Logic, Math, and Physics.**
See Roadmap below for what's next.

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
```

Run `toolkit electronics --help`, `toolkit logic --help`, `toolkit math --help`,
or `toolkit physics --help` to see all options for any command.

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
│   └── physics.py            # Kinematics solver (sympy-backed), energy, power
├── tests/
│   ├── test_electronics.py
│   ├── test_logic.py
│   ├── test_math_tools.py
│   └── test_physics.py       # 74 tests total (pytest)
├── requirements.txt
└── setup.py
```

## Testing

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

## Roadmap (V2)

All four V1 modules (Electronics, Logic, Math, Physics) are complete. What's
left from the original handoff doc's V2 wishlist, now unconstrained by
calculator memory limits:

- **Statistics module** — deferred in V1, now feasible
- **History/persistence** — optional SQLite-backed calculation log (impossible
  on the original hardware due to RAM reset; trivial here)
- **Theming** — `rich` theme support as a nod to the original "theme/visual
  modes" plan
- **Gamification** — badge system / easter eggs, per the original doc's V2 plan

Already brought forward from the original V2 roadmap: the truth table
generator and boolean expression evaluator (originally deferred as "advanced
logic tools") are implemented in the Logic module. The kinematics solver also
goes beyond the original scope by solving all 10 possible combinations of
3-known-of-5 variables generally via sympy, rather than a lookup table of the
classic SUVAT equations.

## Design Notes

The original TI-84 constraints (monochrome, ~24KB RAM, no persistent storage)
shaped the original architecture around strict modularity and input
validation before execution. This port keeps that discipline — every compute
function is pure and separately testable, and the CLI layer (menu or
subcommand) never touches calculation logic directly — while dropping the
constraints that no longer apply.

# TI-84 Embedded Systems Toolkit — Python CLI Port

A Python/terminal port of the original TI-BASIC toolkit built for the TI-84 Plus.
Same modular philosophy — efficiency, clarity, extensibility — now running as a
real CLI instead of a calculator program, with no memory ceiling and no data
loss on reset.

## Status

**Electronics module: complete.** Math, Physics, and Logic are stubbed in the
menu and ready to be built out next (see Roadmap below).

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
```

Run `toolkit electronics --help` to see all options for any command.

## Project Structure

```
ti84toolkit/
├── cli.py                  # Entrypoint: typer app, routes to menu or subcommands
├── core/
│   ├── menu.py              # Interactive menu system (rich-based)
│   └── validation.py        # Shared input validation
├── modules/
│   └── electronics.py       # Ohm's Law, resistor color code, 555 timer
├── tests/
│   └── test_electronics.py  # Unit tests (pytest)
├── requirements.txt
└── setup.py
```

## Testing

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

## Roadmap (V2)

Carried over from the original handoff doc, now unconstrained by calculator
memory limits:

- **Math module** — algebra, trig, equation solving (likely backed by `sympy`)
- **Physics module** — kinematics, energy/power calculations
- **Logic module** — gate simulation + rendered truth tables
- **Statistics module** — deferred in V1, now feasible
- **History/persistence** — optional SQLite-backed calculation log (impossible
  on the original hardware due to RAM reset; trivial here)
- **Theming** — `rich` theme support as a nod to the original "theme/visual
  modes" plan

## Design Notes

The original TI-84 constraints (monochrome, ~24KB RAM, no persistent storage)
shaped the original architecture around strict modularity and input
validation before execution. This port keeps that discipline — every compute
function is pure and separately testable, and the CLI layer (menu or
subcommand) never touches calculation logic directly — while dropping the
constraints that no longer apply.

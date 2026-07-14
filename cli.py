"""
TI-84 Embedded Systems Toolkit -- CLI entrypoint.

Run with no arguments for the interactive menu (matches the original TI-84 flow).
Run with a subcommand for direct, scriptable access:

    toolkit electronics ohms-law --voltage 5 --resistance 100
    toolkit electronics resistor red red brown gold
    toolkit electronics timer555 --r1 1000 --r2 1000 --c 0.000001

Add --json anywhere before the subcommand for machine-readable output:

    toolkit --json math solve "2*x + 3 = 7"

Every successful calculation is logged to a local SQLite history
(~/.ti84toolkit/history.db) -- see `toolkit history --help`.
"""
from __future__ import annotations

import json
import shlex
from pathlib import Path
from typing import Callable, Optional

import typer
from rich.console import Console
from rich.table import Table

from core import badges, config, history
from core.menu import main_menu
from core.validation import ValidationError
from modules import calculus, circuits, electronics, finance, geometry, linear_algebra, logic, math_tools, orbital, physics, plotting, probability, resistor_bom, sequences, statistics_tools, units

console = Console()

app = typer.Typer(
    name="toolkit",
    help="TI-84 Embedded Systems Toolkit -- electronics, math, physics, logic, statistics, and unit conversion.",
    no_args_is_help=False,
)

electronics_app = typer.Typer(help="Electronics utilities: Ohm's Law, resistor codes, 555 timer.")
app.add_typer(electronics_app, name="electronics")

logic_app = typer.Typer(help="Digital logic: gate evaluation and truth table generation.")
app.add_typer(logic_app, name="logic")

math_app = typer.Typer(help="Math tools: quadratic solver, trigonometry, general equation solving.")
app.add_typer(math_app, name="math")

physics_app = typer.Typer(help="Physics: kinematics solver, energy and power calculations.")
app.add_typer(physics_app, name="physics")

stats_app = typer.Typer(help="Statistics: descriptive stats, quartiles, combinatorics (nPr/nCr).")
app.add_typer(stats_app, name="stats")

units_app = typer.Typer(help="Unit conversion: length, mass, time, temperature, and electrical units.")
app.add_typer(units_app, name="units")

history_app = typer.Typer(help="View or clear locally saved calculation history.")
app.add_typer(history_app, name="history")

orbital_app = typer.Typer(help="Orbital mechanics: Kepler's laws, vis-viva, Kepler's equation, Hohmann transfers.")
app.add_typer(orbital_app, name="orbital")

calculus_app = typer.Typer(help="Calculus: derivatives, integrals, limits, Taylor series.")
app.add_typer(calculus_app, name="calculus")

geometry_app = typer.Typer(help="Geometry: 2D/3D shapes, Pythagorean theorem, distance formula.")
app.add_typer(geometry_app, name="geometry")

linalg_app = typer.Typer(help="Linear algebra: vector and matrix operations.")
app.add_typer(linalg_app, name="linalg")

sequences_app = typer.Typer(help="Sequences and series: arithmetic and geometric.")
app.add_typer(sequences_app, name="sequences")

probability_app = typer.Typer(help="Probability distributions: binomial and normal.")
app.add_typer(probability_app, name="probability")

finance_app = typer.Typer(help="Finance: TVM solver, compound interest.")
app.add_typer(finance_app, name="finance")


# ---------------------------------------------------------------------------
# Global state (JSON mode) + shared helpers
# ---------------------------------------------------------------------------

_json_mode = False


@app.callback(invoke_without_command=True)
def root(
    ctx: typer.Context,
    json_output: bool = typer.Option(
        False, "--json", help="Output machine-readable JSON instead of formatted text."
    ),
) -> None:
    """No subcommand given -> launch the interactive menu."""
    global _json_mode
    _json_mode = json_output
    if ctx.invoked_subcommand is None:
        main_menu()


def emit(data: dict, render: Callable[[], None]) -> None:
    """Print `data` as JSON if --json was passed, otherwise call `render()` for human output."""
    if _json_mode:
        console.print(json.dumps(data, indent=2, default=str))
    else:
        render()


def log_calculation(module: str, operation: str, inputs: dict, result_str: str) -> None:
    """Log a calculation to history and announce a badge if a milestone was just crossed."""
    history.log_entry(module, operation, inputs, result_str)
    if not _json_mode:
        badge = badges.badge_for_count(history.count_entries())
        if badge:
            name, description = badge
            console.print(f"\n[bold yellow]{name}[/bold yellow] -- {description}")


def _fail(e: ValidationError) -> None:
    if _json_mode:
        console.print(json.dumps({"error": str(e)}, indent=2))
    else:
        console.print(f"[red]Error:[/red] {e}")
    raise typer.Exit(code=1)


def _default_output_path(prefix: str) -> str:
    import time
    return f"{prefix}_{int(time.time())}.png"


# ---------------------------------------------------------------------------
# electronics ohms-law
# ---------------------------------------------------------------------------


@electronics_app.command("ohms-law")
def ohms_law_cmd(
    voltage: Optional[float] = typer.Option(None, "--voltage", "-v", help="Voltage in volts"),
    current: Optional[float] = typer.Option(None, "--current", "-i", help="Current in amps"),
    resistance: Optional[float] = typer.Option(None, "--resistance", "-r", help="Resistance in ohms"),
    steps: bool = typer.Option(False, "--steps", help="Show the step-by-step derivation"),
) -> None:
    """Solve Ohm's Law given exactly two of voltage, current, resistance."""
    try:
        result = electronics.ohms_law(voltage, current, resistance)
    except ValidationError as e:
        _fail(e)

    data = {
        "solved_for": result.solved_for, "voltage": result.voltage,
        "current": result.current, "resistance": result.resistance, "power": result.power,
    }
    if steps:
        data["steps"] = result.steps

    def render():
        console.print(f"[green]Solved for {result.solved_for}[/green]")
        console.print(f"  V = {result.voltage:g} V")
        console.print(f"  I = {result.current:g} A")
        console.print(f"  R = {result.resistance:g} \u03a9")
        console.print(f"  P = {result.power:g} W")
        if steps:
            console.print("\n[bold]Steps:[/bold]")
            for line in result.steps:
                console.print(f"  {line}")

    emit(data, render)
    log_calculation("electronics", "ohms-law", {"voltage": voltage, "current": current, "resistance": resistance}, f"V={result.voltage:g},I={result.current:g},R={result.resistance:g}")


# ---------------------------------------------------------------------------
# electronics resistor
# ---------------------------------------------------------------------------


@electronics_app.command("resistor")
def resistor_cmd(
    bands: list[str] = typer.Argument(..., help="Color bands, e.g. orange orange red gold"),
    diagram: bool = typer.Option(False, "--diagram", help="Save a color-band diagram image"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Path for the diagram image (with --diagram)"),
) -> None:
    """Decode a 4-band or 5-band resistor color code."""
    try:
        result = electronics.resistor_color_code(bands)
    except ValidationError as e:
        _fail(e)

    data = {"ohms": result.ohms, "tolerance": result.tolerance, "display": result.display}

    diagram_path = None
    if diagram:
        try:
            diagram_path = circuits.draw_resistor_diagram(
                bands, result.display, result.tolerance, output or _default_output_path("resistor_diagram")
            )
            data["diagram_path"] = diagram_path
        except ValidationError as e:
            _fail(e)

    def render():
        console.print(f"[green]Resistance:[/green] {result.display}")
        console.print(f"[green]Tolerance:[/green] {result.tolerance}")
        if diagram_path:
            console.print(f"[dim]Diagram saved to {diagram_path}[/dim]")

    emit(data, render)
    log_calculation("electronics", "resistor", {"bands": bands}, f"{result.display} {result.tolerance}")


# ---------------------------------------------------------------------------
# electronics timer555
# ---------------------------------------------------------------------------


@electronics_app.command("timer555")
def timer555_cmd(
    r1: float = typer.Option(..., "--r1", help="R1 in ohms"),
    r2: float = typer.Option(..., "--r2", help="R2 in ohms"),
    c: float = typer.Option(..., "--c", help="Capacitance in farads (e.g. 0.000001 for 1uF)"),
    plot: bool = typer.Option(False, "--plot", help="Save a waveform plot of the output square wave"),
    diagram: bool = typer.Option(False, "--diagram", help="Save a schematic of the astable circuit"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Path for the image (only valid with a single --plot/--diagram)"),
) -> None:
    """Compute frequency and duty cycle for a 555 timer in astable mode."""
    try:
        result = electronics.timer_555_astable(r1, r2, c)
    except ValidationError as e:
        _fail(e)

    data = {
        "frequency_hz": result.frequency_hz, "period_s": result.period_s,
        "duty_cycle_pct": result.duty_cycle_pct, "time_high_s": result.time_high_s, "time_low_s": result.time_low_s,
    }

    plot_path = diagram_path = None
    try:
        if plot:
            single = output if (output and not diagram) else _default_output_path("timer555_waveform")
            plot_path = plotting.plot_555_waveform(result.frequency_hz, result.duty_cycle_pct, single)
            data["plot_path"] = plot_path
        if diagram:
            single = output if (output and not plot) else _default_output_path("timer555_circuit")
            diagram_path = circuits.draw_555_astable_circuit(r1, r2, c, single)
            data["diagram_path"] = diagram_path
    except ValidationError as e:
        _fail(e)

    def render():
        console.print(f"[green]Frequency:[/green] {result.frequency_hz:.2f} Hz")
        console.print(f"[green]Period:[/green] {result.period_s * 1000:.4f} ms")
        console.print(f"[green]Duty Cycle:[/green] {result.duty_cycle_pct:.2f}%")
        console.print(f"[green]Time High:[/green] {result.time_high_s * 1000:.4f} ms")
        console.print(f"[green]Time Low:[/green] {result.time_low_s * 1000:.4f} ms")
        if plot_path:
            console.print(f"[dim]Waveform plot saved to {plot_path}[/dim]")
        if diagram_path:
            console.print(f"[dim]Circuit diagram saved to {diagram_path}[/dim]")

    emit(data, render)
    log_calculation("electronics", "timer555", {"r1": r1, "r2": r2, "c": c}, f"{result.frequency_hz:.2f} Hz")


# ---------------------------------------------------------------------------
# electronics bom (resistor combination finder)
# ---------------------------------------------------------------------------


@electronics_app.command("bom")
def bom_cmd(
    target: float = typer.Argument(..., help="Target resistance in ohms"),
    series: str = typer.Option("E24", "--series", help="Standard series: E12 or E24"),
    top: int = typer.Option(3, "--top", help="Number of options to show"),
) -> None:
    """Find the closest standard single resistor, series pair, and parallel pair to a target value."""
    try:
        options = resistor_bom.find_resistor_combo(target, series, top)
    except ValidationError as e:
        _fail(e)

    data = {
        "target_ohms": target, "series": series,
        "options": [
            {"kind": o.kind, "values": o.values, "achieved_ohms": o.achieved_ohms, "error_pct": o.error_pct}
            for o in options
        ],
    }

    def render():
        console.print(f"[green]Target:[/green] {target:g} \u03a9  ([dim]{series} series[/dim])")
        for o in options:
            console.print(f"  {resistor_bom.format_option(o)}")

    emit(data, render)
    log_calculation("electronics", "bom", {"target": target, "series": series}, resistor_bom.format_option(options[0]) if options else "no options")


def _render_truth_table(result, title: str) -> None:
    table = Table(title=title)
    for var in result.variables:
        table.add_column(var, justify="center")
    table.add_column("Output", justify="center", style="bold")

    for combo, output in result.rows:
        row = ["T" if v else "F" for v in combo]
        row.append("[green]T[/green]" if output else "[red]F[/red]")
        table.add_row(*row)

    console.print(table)


# ---------------------------------------------------------------------------
# logic gate
# ---------------------------------------------------------------------------


@logic_app.command("gate")
def gate_cmd(
    gate: str = typer.Argument(..., help=f"Gate name: {', '.join(logic.GATE_NAMES)}"),
    inputs: list[str] = typer.Argument(..., help="Boolean inputs, e.g. true false 1 0"),
) -> None:
    """Evaluate a single gate against given boolean inputs."""
    try:
        bool_inputs = [_parse_bool(i) for i in inputs]
        result = logic.evaluate_gate(gate, bool_inputs)
    except ValidationError as e:
        _fail(e)

    data = {"gate": gate.upper(), "inputs": inputs, "result": result}
    emit(data, lambda: console.print(f"[green]{gate.upper()}({', '.join(inputs)}) = {result}[/green]"))
    log_calculation("logic", "gate", {"gate": gate, "inputs": inputs}, str(result))


def _parse_bool(value: str) -> bool:
    v = value.strip().lower()
    if v in ("true", "t", "1"):
        return True
    if v in ("false", "f", "0"):
        return False
    raise ValidationError(f"'{value}' is not a valid boolean (use true/false, 1/0, t/f).")


# ---------------------------------------------------------------------------
# logic truth-table
# ---------------------------------------------------------------------------


@logic_app.command("truth-table")
def truth_table_cmd(
    expression: str = typer.Argument(
        ..., help='Gate name (e.g. "AND") or boolean expression (e.g. "A AND (B OR NOT C)")'
    ),
    inputs: int = typer.Option(
        2, "--inputs", "-n", help="Number of inputs (only used when EXPRESSION is a plain gate name)"
    ),
) -> None:
    """Generate a truth table for a gate name or a boolean expression."""
    try:
        if expression.strip().upper() in logic.GATE_NAMES:
            result = logic.gate_truth_table(expression, inputs)
        else:
            result = logic.expression_truth_table(expression)
    except ValidationError as e:
        _fail(e)

    if _json_mode:
        console.print(json.dumps({
            "variables": result.variables,
            "rows": [{"inputs": combo, "output": out} for combo, out in result.rows],
        }, indent=2))
    else:
        _render_truth_table(result, expression.upper())
    log_calculation("logic", "truth-table", {"expression": expression, "inputs": inputs}, f"{len(result.rows)} rows")


# ---------------------------------------------------------------------------
# math quadratic
# ---------------------------------------------------------------------------


@math_app.command("quadratic")
def quadratic_cmd(
    a: float = typer.Option(..., "--a", help="Coefficient a in ax^2 + bx + c = 0"),
    b: float = typer.Option(..., "--b", help="Coefficient b"),
    c: float = typer.Option(..., "--c", help="Coefficient c"),
) -> None:
    """Solve a quadratic equation ax^2 + bx + c = 0."""
    try:
        result = math_tools.quadratic_solve(a, b, c)
    except ValidationError as e:
        _fail(e)

    roots_str = [str(complex(r.real + 0.0, r.imag)) for r in result.roots]
    data = {"discriminant": result.discriminant, "nature": result.nature, "roots": roots_str}

    def render():
        console.print(f"[green]Discriminant:[/green] {result.discriminant:g} ({result.nature})")
        for i, root in enumerate(result.roots, 1):
            real = root.real + 0.0
            if root.imag == 0:
                console.print(f"  x{i} = {real:g}")
            else:
                console.print(f"  x{i} = {real:g} {'+' if root.imag >= 0 else '-'} {abs(root.imag):g}i")

    emit(data, render)
    log_calculation("math", "quadratic", {"a": a, "b": b, "c": c}, result.nature)


# ---------------------------------------------------------------------------
# math trig
# ---------------------------------------------------------------------------


@math_app.command("trig")
def trig_cmd(
    function: str = typer.Argument(..., help="sin, cos, tan, asin, acos, or atan"),
    value: float = typer.Argument(..., help="Input value"),
    unit: str = typer.Option("deg", "--unit", "-u", help="'deg' or 'rad'"),
) -> None:
    """Evaluate a trig function."""
    try:
        result = math_tools.trig_evaluate(function, value, unit)
    except ValidationError as e:
        _fail(e)

    is_inverse = function.strip().lower().startswith("a")
    data = {"function": function, "value": value, "unit": unit, "result": result}

    def render():
        console.print(f"[green]{function}({value}) = {result:g}{' ' + unit if is_inverse else ''}[/green]")

    emit(data, render)
    log_calculation("math", "trig", {"function": function, "value": value, "unit": unit}, f"{result:g}")


# ---------------------------------------------------------------------------
# math solve
# ---------------------------------------------------------------------------


@math_app.command("solve")
def solve_cmd(
    equation: str = typer.Argument(..., help='Equation, e.g. "2*x + 3 = 7" or "x**2 - 4 = 0"'),
    variable: str = typer.Option("x", "--var", help="Variable to solve for"),
) -> None:
    """Solve an equation for the given variable (linear, quadratic, or beyond)."""
    try:
        result = math_tools.solve_equation(equation, variable)
    except ValidationError as e:
        _fail(e)

    data = {"variable": result.variable, "solutions": result.solutions}
    emit(data, lambda: console.print(f"[green]{result.variable} = {', '.join(result.solutions)}[/green]"))
    log_calculation("math", "solve", {"equation": equation, "variable": variable}, ", ".join(result.solutions))


# ---------------------------------------------------------------------------
# physics kinematics
# ---------------------------------------------------------------------------


@physics_app.command("kinematics")
def kinematics_cmd(
    v0: Optional[float] = typer.Option(None, "--v0", help="Initial velocity (m/s)"),
    v: Optional[float] = typer.Option(None, "--v", help="Final velocity (m/s)"),
    a: Optional[float] = typer.Option(None, "--a", help="Acceleration (m/s^2)"),
    t: Optional[float] = typer.Option(None, "--t", help="Time (s)"),
    d: Optional[float] = typer.Option(None, "--d", help="Displacement (m)"),
    steps: bool = typer.Option(False, "--steps", help="Show the step-by-step derivation"),
    plot: bool = typer.Option(False, "--plot", help="Save a position/velocity vs. time chart"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Path for the plot image (with --plot)"),
) -> None:
    """Solve constant-acceleration kinematics given exactly 3 of v0, v, a, t, d."""
    try:
        result = physics.kinematics_solve(v0, v, a, t, d)
    except ValidationError as e:
        _fail(e)

    data = {"solved_for": result.solved_for, **result.values}
    if steps:
        data["steps"] = result.steps

    plot_path = None
    if plot:
        try:
            plot_path = plotting.plot_kinematics(
                result.values["v0"], result.values["a"], result.values["t"],
                output or _default_output_path("kinematics_plot"),
            )
            data["plot_path"] = plot_path
        except ValidationError as e:
            _fail(e)

    def render():
        console.print(f"[green]Solved for {' and '.join(result.solved_for)}:[/green]")
        console.print(f"  v0 = {result.values['v0']:g} m/s")
        console.print(f"  v  = {result.values['v']:g} m/s")
        console.print(f"  a  = {result.values['a']:g} m/s\u00b2")
        console.print(f"  t  = {result.values['t']:g} s")
        console.print(f"  d  = {result.values['d']:g} m")
        if steps:
            console.print("\n[bold]Steps:[/bold]")
            for line in result.steps:
                console.print(f"  {line}")
        if plot_path:
            console.print(f"[dim]Plot saved to {plot_path}[/dim]")

    emit(data, render)
    log_calculation("physics", "kinematics", {"v0": v0, "v": v, "a": a, "t": t, "d": d}, f"solved {result.solved_for}")


# ---------------------------------------------------------------------------
# physics energy
# ---------------------------------------------------------------------------


@physics_app.command("energy")
def energy_cmd(
    kind: str = typer.Argument(..., help="kinetic, potential, or work"),
    mass: Optional[float] = typer.Option(None, "--mass", help="Mass in kg (kinetic/potential)"),
    velocity: Optional[float] = typer.Option(None, "--velocity", help="Velocity in m/s (kinetic)"),
    height: Optional[float] = typer.Option(None, "--height", help="Height in m (potential)"),
    gravity: Optional[float] = typer.Option(
        None, "--gravity", help="Gravity in m/s^2 (potential; defaults to config or Earth's 9.81)"
    ),
    force: Optional[float] = typer.Option(None, "--force", help="Force in N (work)"),
    distance: Optional[float] = typer.Option(None, "--distance", help="Distance in m (work)"),
) -> None:
    """Compute kinetic energy, gravitational potential energy, or work done."""
    kind = kind.strip().lower()
    g = gravity if gravity is not None else config.get_gravity()
    try:
        if kind == "kinetic":
            if mass is None or velocity is None:
                raise ValidationError("kinetic energy requires --mass and --velocity.")
            result = physics.kinetic_energy(mass, velocity)
        elif kind == "potential":
            if mass is None or height is None:
                raise ValidationError("potential energy requires --mass and --height.")
            result = physics.potential_energy(mass, height, g)
        elif kind == "work":
            if force is None or distance is None:
                raise ValidationError("work requires --force and --distance.")
            result = physics.work_done(force, distance)
        else:
            raise ValidationError("kind must be one of: kinetic, potential, work.")
    except ValidationError as e:
        _fail(e)

    data = {"kind": kind, "label": result.label, "joules": result.joules}
    emit(data, lambda: console.print(f"[green]{result.label}:[/green] {result.joules:g} J"))
    log_calculation("physics", "energy", {"kind": kind, "mass": mass, "velocity": velocity, "height": height, "force": force, "distance": distance}, f"{result.joules:g} J")


# ---------------------------------------------------------------------------
# physics power
# ---------------------------------------------------------------------------


@physics_app.command("power")
def power_cmd(
    work: Optional[float] = typer.Option(None, "--work", help="Work in J (used with --time)"),
    time: Optional[float] = typer.Option(None, "--time", help="Time in s (used with --work)"),
    force: Optional[float] = typer.Option(None, "--force", help="Force in N (used with --velocity)"),
    velocity: Optional[float] = typer.Option(None, "--velocity", help="Velocity in m/s (used with --force)"),
) -> None:
    """Compute power from either (work, time) or (force, velocity)."""
    try:
        if work is not None and time is not None:
            result = physics.power_from_work(work, time)
        elif force is not None and velocity is not None:
            result = physics.power_from_force_velocity(force, velocity)
        else:
            raise ValidationError("Provide either (--work and --time) or (--force and --velocity).")
    except ValidationError as e:
        _fail(e)

    data = {"watts": result.watts}
    emit(data, lambda: console.print(f"[green]Power:[/green] {result.watts:g} W"))
    log_calculation("physics", "power", {"work": work, "time": time, "force": force, "velocity": velocity}, f"{result.watts:g} W")


# ---------------------------------------------------------------------------
# stats describe
# ---------------------------------------------------------------------------


@stats_app.command("describe")
def describe_cmd(
    data_points: list[float] = typer.Argument(..., help="Data points, e.g. 2 4 4 5 7 9 (use -- before negative values)"),
) -> None:
    """Compute descriptive statistics (mean, median, mode, variance, std dev, range)."""
    try:
        result = statistics_tools.describe(data_points)
    except ValidationError as e:
        _fail(e)

    payload = {
        "count": result.count, "sum": result.sum, "mean": result.mean, "median": result.median,
        "mode": result.mode, "variance_sample": result.variance_sample, "stdev_sample": result.stdev_sample,
        "variance_population": result.variance_population, "stdev_population": result.stdev_population,
        "min": result.minimum, "max": result.maximum, "range": result.data_range,
    }

    def render():
        console.print(f"[green]n:[/green] {result.count}    [green]Sum:[/green] {result.sum:g}")
        console.print(f"[green]Mean:[/green] {result.mean:g}    [green]Median:[/green] {result.median:g}")
        mode_str = ", ".join(f"{m:g}" for m in result.mode) if result.mode else "none"
        console.print(f"[green]Mode:[/green] {mode_str}")
        console.print(f"[green]Range:[/green] {result.data_range:g}  (min {result.minimum:g}, max {result.maximum:g})")
        console.print(f"[green]Population variance / stdev:[/green] {result.variance_population:g} / {result.stdev_population:g}")
        if result.variance_sample is not None:
            console.print(f"[green]Sample variance / stdev:[/green] {result.variance_sample:g} / {result.stdev_sample:g}")

    emit(payload, render)
    log_calculation("stats", "describe", {"n": len(data_points)}, f"mean={result.mean:g}")


# ---------------------------------------------------------------------------
# stats quartiles
# ---------------------------------------------------------------------------


@stats_app.command("quartiles")
def quartiles_cmd(
    data_points: list[float] = typer.Argument(..., help="Data points (use -- before negative values)"),
) -> None:
    """Compute the five-number summary (min, Q1, median, Q3, max) and IQR."""
    try:
        result = statistics_tools.five_number_summary(data_points)
    except ValidationError as e:
        _fail(e)

    payload = {"min": result.minimum, "q1": result.q1, "median": result.median, "q3": result.q3, "max": result.maximum, "iqr": result.iqr}

    def render():
        console.print(f"[green]Min:[/green] {result.minimum:g}   [green]Q1:[/green] {result.q1:g}")
        console.print(f"[green]Median:[/green] {result.median:g}   [green]Q3:[/green] {result.q3:g}")
        console.print(f"[green]Max:[/green] {result.maximum:g}   [green]IQR:[/green] {result.iqr:g}")

    emit(payload, render)
    log_calculation("stats", "quartiles", {"n": len(data_points)}, f"median={result.median:g}")


# ---------------------------------------------------------------------------
# stats combinatorics
# ---------------------------------------------------------------------------


@stats_app.command("factorial")
def factorial_cmd(n: int = typer.Argument(..., help="n!")) -> None:
    """Compute n factorial."""
    try:
        result = statistics_tools.factorial(n)
    except ValidationError as e:
        _fail(e)
    emit({"n": n, "result": result}, lambda: console.print(f"[green]{n}! = {result}[/green]"))
    log_calculation("stats", "factorial", {"n": n}, str(result))


@stats_app.command("npr")
def npr_cmd(
    n: int = typer.Argument(..., help="Total items"),
    r: int = typer.Argument(..., help="Items chosen (order matters)"),
) -> None:
    """Compute nPr (permutations)."""
    try:
        result = statistics_tools.permutations(n, r)
    except ValidationError as e:
        _fail(e)
    emit({"n": n, "r": r, "result": result}, lambda: console.print(f"[green]{n}P{r} = {result}[/green]"))
    log_calculation("stats", "npr", {"n": n, "r": r}, str(result))


@stats_app.command("ncr")
def ncr_cmd(
    n: int = typer.Argument(..., help="Total items"),
    r: int = typer.Argument(..., help="Items chosen (order doesn't matter)"),
) -> None:
    """Compute nCr (combinations)."""
    try:
        result = statistics_tools.combinations(n, r)
    except ValidationError as e:
        _fail(e)
    emit({"n": n, "r": r, "result": result}, lambda: console.print(f"[green]{n}C{r} = {result}[/green]"))
    log_calculation("stats", "ncr", {"n": n, "r": r}, str(result))


# ---------------------------------------------------------------------------
# units convert / list-units
# ---------------------------------------------------------------------------


@units_app.command("convert")
def units_convert_cmd(
    category: str = typer.Argument(..., help=f"Category: {', '.join(units.CATEGORY_NAMES)}"),
    value: float = typer.Argument(..., help="Value to convert (use -- before negative values)"),
    from_unit: str = typer.Argument(..., help="Source unit"),
    to_unit: str = typer.Argument(..., help="Target unit"),
) -> None:
    """Convert a value between units within a category."""
    try:
        result = units.convert(category, value, from_unit, to_unit)
    except ValidationError as e:
        _fail(e)

    data = {"category": result.category, "value": result.value, "from": result.from_unit, "to": result.to_unit, "result": result.result}

    def render():
        console.print(f"[green]{result.value:g} {result.from_unit} = {result.result:g} {result.to_unit}[/green]")

    emit(data, render)
    log_calculation("units", "convert", {"category": category, "value": value, "from": from_unit, "to": to_unit}, f"{result.result:g} {to_unit}")


@units_app.command("list-units")
def units_list_cmd(category: str = typer.Argument(..., help=f"Category: {', '.join(units.CATEGORY_NAMES)}")) -> None:
    """List valid unit names for a category."""
    try:
        unit_list = units.units_for_category(category)
    except ValidationError as e:
        _fail(e)
    emit({"category": category, "units": unit_list}, lambda: console.print(f"[green]{category}:[/green] {', '.join(unit_list)}"))


# ---------------------------------------------------------------------------
# history show / clear
# ---------------------------------------------------------------------------


@history_app.command("show")
def history_show_cmd(
    limit: int = typer.Option(20, "--limit", "-n", help="Max number of entries to show"),
    module: Optional[str] = typer.Option(None, "--module", "-m", help="Filter by module (e.g. electronics)"),
) -> None:
    """Show recent calculation history."""
    entries = history.get_history(limit=limit, module=module)

    if _json_mode:
        console.print(json.dumps([
            {"id": e.id, "timestamp": e.timestamp, "module": e.module, "operation": e.operation, "inputs": e.inputs, "result": e.result}
            for e in entries
        ], indent=2))
        return

    if not entries:
        console.print("[yellow]No calculation history yet.[/yellow]")
        return

    table = Table(title="Calculation History")
    table.add_column("ID", justify="right")
    table.add_column("Time")
    table.add_column("Module")
    table.add_column("Operation")
    table.add_column("Result")
    for e in entries:
        table.add_row(str(e.id), e.timestamp, e.module, e.operation, e.result)
    console.print(table)


@history_app.command("clear")
def history_clear_cmd(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip the confirmation prompt"),
) -> None:
    """Delete all saved calculation history."""
    if not yes and not _json_mode:
        confirmed = typer.confirm("Delete all calculation history? This cannot be undone.")
        if not confirmed:
            console.print("Cancelled.")
            raise typer.Exit()

    removed = history.clear_history()
    emit({"deleted": removed}, lambda: console.print(f"[green]Deleted {removed} history entries.[/green]"))


# ---------------------------------------------------------------------------
# orbital period / velocity / kepler-equation / hohmann
# ---------------------------------------------------------------------------


def _resolve_mu(mu: Optional[float], body: Optional[str]) -> float:
    if mu is not None:
        return mu
    if body:
        return orbital.body_mu(body)
    raise ValidationError("Provide either --mu directly or --body (e.g. earth, moon, mars, sun, jupiter).")


@orbital_app.command("period")
def orbital_period_cmd(
    semi_major_axis: float = typer.Option(..., "--a", help="Semi-major axis in meters"),
    mu: Optional[float] = typer.Option(None, "--mu", help="Gravitational parameter (m^3/s^2)"),
    body: Optional[str] = typer.Option(None, "--body", help=f"Central body: {', '.join(orbital.BODIES)}"),
) -> None:
    """Orbital period via Kepler's Third Law."""
    try:
        mu_val = _resolve_mu(mu, body)
        period = orbital.orbital_period(semi_major_axis, mu_val)
    except ValidationError as e:
        _fail(e)

    data = {"semi_major_axis_m": semi_major_axis, "mu": mu_val, "period_s": period}

    def render():
        console.print(f"[green]Period:[/green] {period:g} s  ({period / 60:.2f} min, {period / 3600:.2f} hr, {period / 86400:.3f} days)")

    emit(data, render)
    log_calculation("orbital", "period", {"a": semi_major_axis, "body": body}, f"{period:g} s")


@orbital_app.command("velocity")
def orbital_velocity_cmd(
    r: float = typer.Option(..., "--r", help="Radius at which to evaluate velocity (m)"),
    kind: str = typer.Option("circular", "--kind", help="circular, escape, or vis-viva"),
    a: Optional[float] = typer.Option(None, "--a", help="Orbit semi-major axis in meters (required for vis-viva)"),
    mu: Optional[float] = typer.Option(None, "--mu", help="Gravitational parameter (m^3/s^2)"),
    body: Optional[str] = typer.Option(None, "--body", help=f"Central body: {', '.join(orbital.BODIES)}"),
) -> None:
    """Compute circular, escape, or vis-viva orbital velocity."""
    kind = kind.strip().lower()
    try:
        mu_val = _resolve_mu(mu, body)
        if kind == "circular":
            v = orbital.circular_velocity(r, mu_val)
        elif kind == "escape":
            v = orbital.escape_velocity(r, mu_val)
        elif kind == "vis-viva":
            if a is None:
                raise ValidationError("vis-viva requires --a (the orbit's semi-major axis).")
            v = orbital.vis_viva_velocity(r, a, mu_val)
        else:
            raise ValidationError("kind must be one of: circular, escape, vis-viva.")
    except ValidationError as e:
        _fail(e)

    data = {"kind": kind, "r_m": r, "velocity_mps": v}
    emit(data, lambda: console.print(f"[green]{kind.capitalize()} velocity:[/green] {v:g} m/s ({v / 1000:.3f} km/s)"))
    log_calculation("orbital", "velocity", {"kind": kind, "r": r, "body": body}, f"{v:g} m/s")


@orbital_app.command("kepler-equation")
def kepler_equation_cmd(
    mean_anomaly: float = typer.Argument(..., help="Mean anomaly in radians"),
    eccentricity: float = typer.Argument(..., help="Orbital eccentricity (0 <= e < 1)"),
    steps: bool = typer.Option(False, "--steps", help="Show the Newton-Raphson iteration steps"),
) -> None:
    """Solve Kepler's equation (M = E - e*sin(E)) via Newton-Raphson."""
    try:
        result = orbital.solve_kepler_equation(mean_anomaly, eccentricity)
    except ValidationError as e:
        _fail(e)

    data = {
        "mean_anomaly_rad": result.mean_anomaly_rad, "eccentricity": result.eccentricity,
        "eccentric_anomaly_rad": result.eccentric_anomaly_rad, "true_anomaly_rad": result.true_anomaly_rad,
        "iterations": result.iterations,
    }
    if steps:
        data["steps"] = result.steps

    def render():
        console.print(f"[green]Eccentric anomaly (E):[/green] {result.eccentric_anomaly_rad:g} rad")
        console.print(f"[green]True anomaly (\u03bd):[/green] {result.true_anomaly_rad:g} rad")
        console.print(f"[dim]Converged in {result.iterations} iterations[/dim]")
        if steps:
            console.print("\n[bold]Steps:[/bold]")
            for line in result.steps:
                console.print(f"  {line}")

    emit(data, render)
    log_calculation("orbital", "kepler-equation", {"M": mean_anomaly, "e": eccentricity}, f"E={result.eccentric_anomaly_rad:g}")


@orbital_app.command("hohmann")
def hohmann_cmd(
    r1: float = typer.Option(..., "--r1", help="Departure orbit radius (m)"),
    r2: float = typer.Option(..., "--r2", help="Arrival orbit radius (m)"),
    mu: Optional[float] = typer.Option(None, "--mu", help="Gravitational parameter (m^3/s^2)"),
    body: Optional[str] = typer.Option(None, "--body", help=f"Central body: {', '.join(orbital.BODIES)}"),
    steps: bool = typer.Option(False, "--steps", help="Show the step-by-step derivation"),
    plot: bool = typer.Option(False, "--plot", help="Save a diagram of the transfer orbit"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Path for the plot image (with --plot)"),
) -> None:
    """Compute the two burns, total delta-v, and transfer time for a Hohmann transfer."""
    try:
        mu_val = _resolve_mu(mu, body)
        result = orbital.hohmann_transfer(r1, r2, mu_val)
    except ValidationError as e:
        _fail(e)

    data = {
        "r1_m": result.r1_m, "r2_m": result.r2_m, "delta_v1_mps": result.delta_v1_mps,
        "delta_v2_mps": result.delta_v2_mps, "total_delta_v_mps": result.total_delta_v_mps,
        "transfer_time_s": result.transfer_time_s,
    }
    if steps:
        data["steps"] = result.steps

    plot_path = None
    if plot:
        try:
            plot_path = plotting.plot_hohmann_transfer(r1, r2, output or _default_output_path("hohmann_transfer"))
            data["plot_path"] = plot_path
        except ValidationError as e:
            _fail(e)

    def render():
        console.print(f"[green]Burn 1 (departure):[/green] {result.delta_v1_mps:g} m/s")
        console.print(f"[green]Burn 2 (arrival):[/green] {result.delta_v2_mps:g} m/s")
        console.print(f"[green]Total delta-v:[/green] {result.total_delta_v_mps:g} m/s")
        console.print(f"[green]Transfer time:[/green] {result.transfer_time_s:g} s ({result.transfer_time_s / 3600:.2f} hr)")
        if steps:
            console.print("\n[bold]Steps:[/bold]")
            for line in result.steps:
                console.print(f"  {line}")
        if plot_path:
            console.print(f"[dim]Transfer orbit diagram saved to {plot_path}[/dim]")

    emit(data, render)
    log_calculation("orbital", "hohmann", {"r1": r1, "r2": r2, "body": body}, f"dv={result.total_delta_v_mps:g} m/s")


# ---------------------------------------------------------------------------
# calculus
# ---------------------------------------------------------------------------


@calculus_app.command("derivative")
def derivative_cmd(
    expression: str = typer.Argument(..., help='Expression, e.g. "x**3 + 2*x"'),
    var: str = typer.Option("x", "--var", help="Variable to differentiate with respect to"),
    order: int = typer.Option(1, "--order", help="Derivative order"),
) -> None:
    """Compute the nth derivative of an expression."""
    try:
        result = calculus.derivative(expression, var, order)
    except ValidationError as e:
        _fail(e)
    data = {"expression": expression, "var": var, "order": order, "result": result.result}
    emit(data, lambda: console.print(f"[green]d^{order}/d{var}^{order} ({expression}) = {result.result}[/green]"))
    log_calculation("calculus", "derivative", {"expression": expression, "var": var, "order": order}, result.result)


@calculus_app.command("integral")
def integral_cmd(
    expression: str = typer.Argument(..., help='Expression, e.g. "x**2"'),
    var: str = typer.Option("x", "--var", help="Variable to integrate with respect to"),
    lower: Optional[float] = typer.Option(None, "--lower", help="Lower bound (definite integral)"),
    upper: Optional[float] = typer.Option(None, "--upper", help="Upper bound (definite integral)"),
) -> None:
    """Compute an indefinite or definite integral."""
    try:
        result = calculus.integral(expression, var, lower, upper)
    except ValidationError as e:
        _fail(e)
    data = {"expression": expression, "var": var, "lower": lower, "upper": upper, "result": result.result}
    emit(data, lambda: console.print(f"[green]\u222b {expression} d{var} = {result.result}[/green]"))
    log_calculation("calculus", "integral", {"expression": expression, "var": var, "lower": lower, "upper": upper}, result.result)


@calculus_app.command("limit")
def limit_cmd(
    expression: str = typer.Argument(..., help='Expression, e.g. "sin(x)/x"'),
    point: str = typer.Argument(..., help="Point the variable approaches (number, or 'oo'/'-oo' for infinity)"),
    var: str = typer.Option("x", "--var", help="Variable"),
    direction: str = typer.Option("both", "--direction", help="'both', 'left', or 'right'"),
) -> None:
    """Compute a limit."""
    try:
        result = calculus.limit(expression, var, point, direction)
    except ValidationError as e:
        _fail(e)
    data = {"expression": expression, "var": var, "point": point, "direction": direction, "result": result.result}
    emit(data, lambda: console.print(f"[green]lim ({var}->{point}) ({expression}) = {result.result}[/green]"))
    log_calculation("calculus", "limit", {"expression": expression, "point": point, "direction": direction}, result.result)


@calculus_app.command("taylor-series")
def taylor_series_cmd(
    expression: str = typer.Argument(..., help='Expression, e.g. "exp(x)"'),
    var: str = typer.Option("x", "--var", help="Variable"),
    point: float = typer.Option(0, "--point", help="Expansion point"),
    order: int = typer.Option(5, "--order", help="Expansion order"),
) -> None:
    """Compute the Taylor series expansion of an expression about a point."""
    try:
        result = calculus.taylor_series(expression, var, point, order)
    except ValidationError as e:
        _fail(e)
    data = {"expression": expression, "var": var, "point": point, "order": order, "result": result.result}
    emit(data, lambda: console.print(f"[green]{expression} \u2248 {result.result}[/green]  [dim](about {var}={point}, order {order})[/dim]"))
    log_calculation("calculus", "taylor-series", {"expression": expression, "point": point, "order": order}, result.result)


# ---------------------------------------------------------------------------
# geometry
# ---------------------------------------------------------------------------


def _render_shape(result) -> None:
    console.print(f"[green]{result.shape.capitalize()}:[/green]")
    for key, val in result.measurements.items():
        console.print(f"  {key.replace('_', ' ')}: {val:g}")


@geometry_app.command("circle")
def geometry_circle_cmd(radius: float = typer.Argument(..., help="Radius")) -> None:
    """Area and circumference of a circle."""
    try:
        result = geometry.circle(radius)
    except ValidationError as e:
        _fail(e)
    emit({"shape": "circle", **result.measurements}, lambda: _render_shape(result))
    log_calculation("geometry", "circle", {"radius": radius}, f"area={result.measurements['area']:g}")


@geometry_app.command("rectangle")
def geometry_rectangle_cmd(length: float = typer.Argument(...), width: float = typer.Argument(...)) -> None:
    """Area and perimeter of a rectangle."""
    try:
        result = geometry.rectangle(length, width)
    except ValidationError as e:
        _fail(e)
    emit({"shape": "rectangle", **result.measurements}, lambda: _render_shape(result))
    log_calculation("geometry", "rectangle", {"length": length, "width": width}, f"area={result.measurements['area']:g}")


@geometry_app.command("triangle-bh")
def geometry_triangle_bh_cmd(base: float = typer.Argument(...), height: float = typer.Argument(...)) -> None:
    """Area of a triangle from base and height."""
    try:
        result = geometry.triangle_base_height(base, height)
    except ValidationError as e:
        _fail(e)
    emit({"shape": "triangle", **result.measurements}, lambda: _render_shape(result))
    log_calculation("geometry", "triangle-bh", {"base": base, "height": height}, f"area={result.measurements['area']:g}")


@geometry_app.command("triangle-sides")
def geometry_triangle_sides_cmd(
    a: float = typer.Argument(...), b: float = typer.Argument(...), c: float = typer.Argument(...)
) -> None:
    """Area (Heron's formula) and perimeter of a triangle given all three sides."""
    try:
        result = geometry.triangle_sides(a, b, c)
    except ValidationError as e:
        _fail(e)
    emit({"shape": "triangle", **result.measurements}, lambda: _render_shape(result))
    log_calculation("geometry", "triangle-sides", {"a": a, "b": b, "c": c}, f"area={result.measurements['area']:g}")


@geometry_app.command("pythagorean-hypotenuse")
def geometry_pyth_hyp_cmd(leg_a: float = typer.Argument(...), leg_b: float = typer.Argument(...)) -> None:
    """Hypotenuse given two legs."""
    try:
        result = geometry.pythagorean_hypotenuse(leg_a, leg_b)
    except ValidationError as e:
        _fail(e)
    emit({"hypotenuse": result}, lambda: console.print(f"[green]Hypotenuse:[/green] {result:g}"))
    log_calculation("geometry", "pythagorean-hypotenuse", {"leg_a": leg_a, "leg_b": leg_b}, f"{result:g}")


@geometry_app.command("pythagorean-leg")
def geometry_pyth_leg_cmd(hypotenuse: float = typer.Argument(...), other_leg: float = typer.Argument(...)) -> None:
    """Missing leg given the hypotenuse and the other leg."""
    try:
        result = geometry.pythagorean_leg(hypotenuse, other_leg)
    except ValidationError as e:
        _fail(e)
    emit({"leg": result}, lambda: console.print(f"[green]Leg:[/green] {result:g}"))
    log_calculation("geometry", "pythagorean-leg", {"hypotenuse": hypotenuse, "other_leg": other_leg}, f"{result:g}")


@geometry_app.command("distance")
def geometry_distance_cmd(
    x1: float = typer.Option(..., "--x1"), y1: float = typer.Option(..., "--y1"),
    x2: float = typer.Option(..., "--x2"), y2: float = typer.Option(..., "--y2"),
    z1: Optional[float] = typer.Option(None, "--z1", help="Provide z1 and z2 for 3D distance"),
    z2: Optional[float] = typer.Option(None, "--z2"),
) -> None:
    """Distance between two points (2D, or 3D if z1/z2 are given)."""
    if (z1 is None) != (z2 is None):
        _fail(ValidationError("Provide both z1 and z2 for 3D, or neither for 2D."))
    if z1 is not None:
        result = geometry.distance_3d(x1, y1, z1, x2, y2, z2)
    else:
        result = geometry.distance_2d(x1, y1, x2, y2)
    emit({"distance": result}, lambda: console.print(f"[green]Distance:[/green] {result:g}"))
    log_calculation("geometry", "distance", {"x1": x1, "y1": y1, "x2": x2, "y2": y2}, f"{result:g}")


@geometry_app.command("sphere")
def geometry_sphere_cmd(radius: float = typer.Argument(...)) -> None:
    """Volume and surface area of a sphere."""
    try:
        result = geometry.sphere(radius)
    except ValidationError as e:
        _fail(e)
    emit({"shape": "sphere", **result.measurements}, lambda: _render_shape(result))
    log_calculation("geometry", "sphere", {"radius": radius}, f"volume={result.measurements['volume']:g}")


@geometry_app.command("cylinder")
def geometry_cylinder_cmd(radius: float = typer.Argument(...), height: float = typer.Argument(...)) -> None:
    """Volume and surface area of a cylinder."""
    try:
        result = geometry.cylinder(radius, height)
    except ValidationError as e:
        _fail(e)
    emit({"shape": "cylinder", **result.measurements}, lambda: _render_shape(result))
    log_calculation("geometry", "cylinder", {"radius": radius, "height": height}, f"volume={result.measurements['volume']:g}")


@geometry_app.command("cone")
def geometry_cone_cmd(radius: float = typer.Argument(...), height: float = typer.Argument(...)) -> None:
    """Volume and surface area of a cone."""
    try:
        result = geometry.cone(radius, height)
    except ValidationError as e:
        _fail(e)
    emit({"shape": "cone", **result.measurements}, lambda: _render_shape(result))
    log_calculation("geometry", "cone", {"radius": radius, "height": height}, f"volume={result.measurements['volume']:g}")


@geometry_app.command("box")
def geometry_box_cmd(
    length: float = typer.Argument(...), width: float = typer.Argument(...), height: float = typer.Argument(...)
) -> None:
    """Volume and surface area of a rectangular box."""
    try:
        result = geometry.box(length, width, height)
    except ValidationError as e:
        _fail(e)
    emit({"shape": "box", **result.measurements}, lambda: _render_shape(result))
    log_calculation("geometry", "box", {"length": length, "width": width, "height": height}, f"volume={result.measurements['volume']:g}")


# ---------------------------------------------------------------------------
# linalg
# ---------------------------------------------------------------------------


def _parse_vector_arg(s: str) -> list[float]:
    try:
        return [float(x) for x in s.split(",")]
    except ValueError:
        raise ValidationError(f"Could not parse vector '{s}' -- expected comma-separated numbers, e.g. 1,2,3")


def _parse_matrix_arg(s: str) -> list[list[float]]:
    rows = s.split(";")
    try:
        return [[float(x) for x in row.split(",")] for row in rows]
    except ValueError:
        raise ValidationError(f"Could not parse matrix '{s}' -- expected semicolon-separated rows, e.g. 1,2;3,4")


@linalg_app.command("vector-dot")
def vector_dot_cmd(v1: str = typer.Argument(..., help="e.g. 1,2,3"), v2: str = typer.Argument(...)) -> None:
    """Dot product of two vectors."""
    try:
        result = linear_algebra.vector_dot(_parse_vector_arg(v1), _parse_vector_arg(v2))
    except ValidationError as e:
        _fail(e)
    emit({"result": result}, lambda: console.print(f"[green]Dot product:[/green] {result:g}"))
    log_calculation("linalg", "vector-dot", {"v1": v1, "v2": v2}, f"{result:g}")


@linalg_app.command("vector-cross")
def vector_cross_cmd(v1: str = typer.Argument(..., help="e.g. 1,0,0"), v2: str = typer.Argument(...)) -> None:
    """Cross product of two 3D vectors."""
    try:
        result = linear_algebra.vector_cross(_parse_vector_arg(v1), _parse_vector_arg(v2))
    except ValidationError as e:
        _fail(e)
    emit({"result": result}, lambda: console.print(f"[green]Cross product:[/green] ({', '.join(f'{x:g}' for x in result)})"))
    log_calculation("linalg", "vector-cross", {"v1": v1, "v2": v2}, str(result))


@linalg_app.command("vector-magnitude")
def vector_magnitude_cmd(v: str = typer.Argument(..., help="e.g. 3,4")) -> None:
    """Magnitude (length) of a vector."""
    try:
        result = linear_algebra.vector_magnitude(_parse_vector_arg(v))
    except ValidationError as e:
        _fail(e)
    emit({"result": result}, lambda: console.print(f"[green]Magnitude:[/green] {result:g}"))
    log_calculation("linalg", "vector-magnitude", {"v": v}, f"{result:g}")


@linalg_app.command("vector-normalize")
def vector_normalize_cmd(v: str = typer.Argument(..., help="e.g. 3,4")) -> None:
    """Unit vector in the same direction."""
    try:
        result = linear_algebra.vector_normalize(_parse_vector_arg(v))
    except ValidationError as e:
        _fail(e)
    emit({"result": result}, lambda: console.print(f"[green]Unit vector:[/green] ({', '.join(f'{x:g}' for x in result)})"))
    log_calculation("linalg", "vector-normalize", {"v": v}, str(result))


@linalg_app.command("vector-angle")
def vector_angle_cmd(v1: str = typer.Argument(...), v2: str = typer.Argument(...)) -> None:
    """Angle between two vectors, in degrees."""
    try:
        result_rad = linear_algebra.vector_angle_between(_parse_vector_arg(v1), _parse_vector_arg(v2))
    except ValidationError as e:
        _fail(e)
    result_deg = result_rad * 180 / 3.141592653589793
    emit({"radians": result_rad, "degrees": result_deg}, lambda: console.print(f"[green]Angle:[/green] {result_deg:g}\u00b0 ({result_rad:g} rad)"))
    log_calculation("linalg", "vector-angle", {"v1": v1, "v2": v2}, f"{result_deg:g} deg")


def _render_matrix(rows: list[list[float]]) -> None:
    table = Table(show_header=False)
    for _ in rows[0]:
        table.add_column(justify="right")
    for row in rows:
        table.add_row(*[f"{x:g}" for x in row])
    console.print(table)


@linalg_app.command("matrix-add")
def matrix_add_cmd(m1: str = typer.Argument(..., help="e.g. 1,2;3,4"), m2: str = typer.Argument(...)) -> None:
    """Add two matrices."""
    try:
        result = linear_algebra.matrix_add(_parse_matrix_arg(m1), _parse_matrix_arg(m2))
    except ValidationError as e:
        _fail(e)
    emit({"result": result.rows}, lambda: _render_matrix(result.rows))
    log_calculation("linalg", "matrix-add", {"m1": m1, "m2": m2}, str(result.rows))


@linalg_app.command("matrix-multiply")
def matrix_multiply_cmd(m1: str = typer.Argument(...), m2: str = typer.Argument(...)) -> None:
    """Multiply two matrices."""
    try:
        result = linear_algebra.matrix_multiply(_parse_matrix_arg(m1), _parse_matrix_arg(m2))
    except ValidationError as e:
        _fail(e)
    emit({"result": result.rows}, lambda: _render_matrix(result.rows))
    log_calculation("linalg", "matrix-multiply", {"m1": m1, "m2": m2}, str(result.rows))


@linalg_app.command("matrix-transpose")
def matrix_transpose_cmd(m: str = typer.Argument(...)) -> None:
    """Transpose a matrix."""
    try:
        result = linear_algebra.matrix_transpose(_parse_matrix_arg(m))
    except ValidationError as e:
        _fail(e)
    emit({"result": result.rows}, lambda: _render_matrix(result.rows))
    log_calculation("linalg", "matrix-transpose", {"m": m}, str(result.rows))


@linalg_app.command("matrix-det")
def matrix_det_cmd(m: str = typer.Argument(...)) -> None:
    """Determinant of a square matrix."""
    try:
        result = linear_algebra.matrix_determinant(_parse_matrix_arg(m))
    except ValidationError as e:
        _fail(e)
    emit({"determinant": result}, lambda: console.print(f"[green]Determinant:[/green] {result:g}"))
    log_calculation("linalg", "matrix-det", {"m": m}, f"{result:g}")


@linalg_app.command("matrix-inverse")
def matrix_inverse_cmd(m: str = typer.Argument(...)) -> None:
    """Inverse of a square matrix."""
    try:
        result = linear_algebra.matrix_inverse(_parse_matrix_arg(m))
    except ValidationError as e:
        _fail(e)
    emit({"result": result.rows}, lambda: _render_matrix(result.rows))
    log_calculation("linalg", "matrix-inverse", {"m": m}, str(result.rows))


# ---------------------------------------------------------------------------
# sequences
# ---------------------------------------------------------------------------


@sequences_app.command("arithmetic-term")
def arithmetic_term_cmd(
    a1: float = typer.Option(..., "--a1"), d: float = typer.Option(..., "--d"), n: int = typer.Option(..., "--n")
) -> None:
    """nth term of an arithmetic sequence."""
    try:
        result = sequences.arithmetic_nth_term(a1, d, n)
    except ValidationError as e:
        _fail(e)
    emit({"result": result}, lambda: console.print(f"[green]a_{n} =[/green] {result:g}"))
    log_calculation("sequences", "arithmetic-term", {"a1": a1, "d": d, "n": n}, f"{result:g}")


@sequences_app.command("arithmetic-sum")
def arithmetic_sum_cmd(
    a1: float = typer.Option(..., "--a1"), d: float = typer.Option(..., "--d"), n: int = typer.Option(..., "--n")
) -> None:
    """Sum of the first n terms of an arithmetic sequence."""
    try:
        result = sequences.arithmetic_sum(a1, d, n)
    except ValidationError as e:
        _fail(e)
    emit({"result": result}, lambda: console.print(f"[green]S_{n} =[/green] {result:g}"))
    log_calculation("sequences", "arithmetic-sum", {"a1": a1, "d": d, "n": n}, f"{result:g}")


@sequences_app.command("geometric-term")
def geometric_term_cmd(
    a1: float = typer.Option(..., "--a1"), r: float = typer.Option(..., "--r"), n: int = typer.Option(..., "--n")
) -> None:
    """nth term of a geometric sequence."""
    try:
        result = sequences.geometric_nth_term(a1, r, n)
    except ValidationError as e:
        _fail(e)
    emit({"result": result}, lambda: console.print(f"[green]a_{n} =[/green] {result:g}"))
    log_calculation("sequences", "geometric-term", {"a1": a1, "r": r, "n": n}, f"{result:g}")


@sequences_app.command("geometric-sum")
def geometric_sum_cmd(
    a1: float = typer.Option(..., "--a1"), r: float = typer.Option(..., "--r"), n: int = typer.Option(..., "--n")
) -> None:
    """Sum of the first n terms of a geometric sequence."""
    try:
        result = sequences.geometric_sum(a1, r, n)
    except ValidationError as e:
        _fail(e)
    emit({"result": result}, lambda: console.print(f"[green]S_{n} =[/green] {result:g}"))
    log_calculation("sequences", "geometric-sum", {"a1": a1, "r": r, "n": n}, f"{result:g}")


@sequences_app.command("geometric-sum-infinite")
def geometric_sum_infinite_cmd(a1: float = typer.Option(..., "--a1"), r: float = typer.Option(..., "--r")) -> None:
    """Sum of an infinite geometric series (requires |r| < 1)."""
    try:
        result = sequences.geometric_sum_infinite(a1, r)
    except ValidationError as e:
        _fail(e)
    emit({"sum": result.sum}, lambda: console.print(f"[green]S_\u221e =[/green] {result.sum:g}"))
    log_calculation("sequences", "geometric-sum-infinite", {"a1": a1, "r": r}, f"{result.sum:g}")


# ---------------------------------------------------------------------------
# probability
# ---------------------------------------------------------------------------


@probability_app.command("binomial-pmf")
def binomial_pmf_cmd(n: int = typer.Option(..., "--n"), k: int = typer.Option(..., "--k"), p: float = typer.Option(..., "--p")) -> None:
    """P(X = k) for X ~ Binomial(n, p)."""
    try:
        result = probability.binomial_pmf(n, k, p)
    except ValidationError as e:
        _fail(e)
    emit({"result": result}, lambda: console.print(f"[green]P(X = {k}):[/green] {result:g}"))
    log_calculation("probability", "binomial-pmf", {"n": n, "k": k, "p": p}, f"{result:g}")


@probability_app.command("binomial-cdf")
def binomial_cdf_cmd(n: int = typer.Option(..., "--n"), k: int = typer.Option(..., "--k"), p: float = typer.Option(..., "--p")) -> None:
    """P(X <= k) for X ~ Binomial(n, p)."""
    try:
        result = probability.binomial_cdf(n, k, p)
    except ValidationError as e:
        _fail(e)
    emit({"result": result}, lambda: console.print(f"[green]P(X \u2264 {k}):[/green] {result:g}"))
    log_calculation("probability", "binomial-cdf", {"n": n, "k": k, "p": p}, f"{result:g}")


@probability_app.command("binomial-stats")
def binomial_stats_cmd(n: int = typer.Option(..., "--n"), p: float = typer.Option(..., "--p")) -> None:
    """Mean, variance, and stdev of X ~ Binomial(n, p)."""
    try:
        result = probability.binomial_stats(n, p)
    except ValidationError as e:
        _fail(e)
    data = {"mean": result.mean, "variance": result.variance, "stdev": result.stdev}
    emit(data, lambda: console.print(f"[green]Mean:[/green] {result.mean:g}  [green]Variance:[/green] {result.variance:g}  [green]Stdev:[/green] {result.stdev:g}"))
    log_calculation("probability", "binomial-stats", {"n": n, "p": p}, f"mean={result.mean:g}")


@probability_app.command("normal-pdf")
def normal_pdf_cmd(x: float = typer.Argument(...), mean: float = typer.Option(0, "--mean"), stdev: float = typer.Option(1, "--stdev")) -> None:
    """Normal distribution PDF at x."""
    try:
        result = probability.normal_pdf(x, mean, stdev)
    except ValidationError as e:
        _fail(e)
    emit({"result": result}, lambda: console.print(f"[green]f({x}):[/green] {result:g}"))
    log_calculation("probability", "normal-pdf", {"x": x, "mean": mean, "stdev": stdev}, f"{result:g}")


@probability_app.command("normal-cdf")
def normal_cdf_cmd(x: float = typer.Argument(...), mean: float = typer.Option(0, "--mean"), stdev: float = typer.Option(1, "--stdev")) -> None:
    """P(X <= x) for X ~ Normal(mean, stdev)."""
    try:
        result = probability.normal_cdf(x, mean, stdev)
    except ValidationError as e:
        _fail(e)
    emit({"result": result}, lambda: console.print(f"[green]P(X \u2264 {x}):[/green] {result:g}"))
    log_calculation("probability", "normal-cdf", {"x": x, "mean": mean, "stdev": stdev}, f"{result:g}")


@probability_app.command("normal-cdf-range")
def normal_cdf_range_cmd(
    low: float = typer.Argument(...), high: float = typer.Argument(...),
    mean: float = typer.Option(0, "--mean"), stdev: float = typer.Option(1, "--stdev"),
) -> None:
    """P(low <= X <= high) for X ~ Normal(mean, stdev)."""
    try:
        result = probability.normal_cdf_range(low, high, mean, stdev)
    except ValidationError as e:
        _fail(e)
    emit({"result": result}, lambda: console.print(f"[green]P({low} \u2264 X \u2264 {high}):[/green] {result:g}"))
    log_calculation("probability", "normal-cdf-range", {"low": low, "high": high, "mean": mean, "stdev": stdev}, f"{result:g}")


@probability_app.command("inverse-normal-cdf")
def inverse_normal_cdf_cmd(p: float = typer.Argument(...), mean: float = typer.Option(0, "--mean"), stdev: float = typer.Option(1, "--stdev")) -> None:
    """The x such that P(X <= x) = p (TI-84's invNorm)."""
    try:
        result = probability.inverse_normal_cdf(p, mean, stdev)
    except ValidationError as e:
        _fail(e)
    emit({"result": result}, lambda: console.print(f"[green]x:[/green] {result:g}"))
    log_calculation("probability", "inverse-normal-cdf", {"p": p, "mean": mean, "stdev": stdev}, f"{result:g}")


@probability_app.command("z-score")
def z_score_cmd(x: float = typer.Argument(...), mean: float = typer.Option(..., "--mean"), stdev: float = typer.Option(..., "--stdev")) -> None:
    """Z-score of x given a mean and standard deviation."""
    try:
        result = probability.z_score(x, mean, stdev)
    except ValidationError as e:
        _fail(e)
    emit({"result": result}, lambda: console.print(f"[green]z:[/green] {result:g}"))
    log_calculation("probability", "z-score", {"x": x, "mean": mean, "stdev": stdev}, f"{result:g}")


# ---------------------------------------------------------------------------
# finance
# ---------------------------------------------------------------------------


@finance_app.command("tvm")
def tvm_cmd(
    n: Optional[float] = typer.Option(None, "--n", help="Number of payment periods"),
    rate: Optional[float] = typer.Option(None, "--rate", help="Annual interest rate, percent"),
    pv: Optional[float] = typer.Option(None, "--pv", help="Present value (negative if paid out)"),
    pmt: Optional[float] = typer.Option(None, "--pmt", help="Payment per period (negative if paid out)"),
    fv: Optional[float] = typer.Option(None, "--fv", help="Future value (negative if paid out)"),
    payments_per_year: int = typer.Option(12, "--payments-per-year", help="Compounding/payment frequency"),
    begin: bool = typer.Option(False, "--begin", help="Payments at beginning of period (annuity due)"),
    steps: bool = typer.Option(False, "--steps", help="Show the derivation"),
) -> None:
    """TVM solver: given any 4 of {n, rate, pv, pmt, fv}, solve for the 5th."""
    try:
        result = finance.solve_tvm(n, rate, pv, pmt, fv, payments_per_year, begin)
    except ValidationError as e:
        _fail(e)

    data = {"n": result.n, "rate_percent": result.rate_percent, "pv": result.pv, "pmt": result.pmt, "fv": result.fv, "solved_for": result.solved_for}
    if steps:
        data["steps"] = result.steps

    def render():
        console.print(f"[green]Solved for {result.solved_for}:[/green]")
        console.print(f"  n = {result.n:g}")
        console.print(f"  rate = {result.rate_percent:g}%")
        console.print(f"  pv = {result.pv:g}")
        console.print(f"  pmt = {result.pmt:g}")
        console.print(f"  fv = {result.fv:g}")
        if steps:
            console.print("\n[bold]Steps:[/bold]")
            for line in result.steps:
                console.print(f"  {line}")

    emit(data, render)
    log_calculation("finance", "tvm", {"n": n, "rate": rate, "pv": pv, "pmt": pmt, "fv": fv}, f"solved {result.solved_for}")


@finance_app.command("compound-interest")
def compound_interest_cmd(
    principal: float = typer.Option(..., "--principal"),
    rate: float = typer.Option(..., "--rate", help="Annual rate, percent"),
    compounds_per_year: int = typer.Option(12, "--compounds-per-year"),
    years: float = typer.Option(..., "--years"),
) -> None:
    """Future value of a lump sum under compound interest (no recurring payments)."""
    try:
        result = finance.compound_interest(principal, rate, compounds_per_year, years)
    except ValidationError as e:
        _fail(e)
    data = {"future_value": result.future_value, "interest_earned": result.interest_earned}
    emit(data, lambda: console.print(f"[green]Future value:[/green] {result.future_value:g}  [green]Interest earned:[/green] {result.interest_earned:g}"))
    log_calculation("finance", "compound-interest", {"principal": principal, "rate": rate, "years": years}, f"fv={result.future_value:g}")


# ---------------------------------------------------------------------------
# batch mode
# ---------------------------------------------------------------------------


@app.command("batch")
def batch_cmd(
    file: Path = typer.Argument(..., help="Path to a text file of toolkit commands, one per line"),
) -> None:
    """Run a sequence of toolkit commands from a file (one command's arguments per line, '#' for comments)."""
    from typer.testing import CliRunner

    if not file.exists():
        console.print(f"[red]Error:[/red] file not found: {file}")
        raise typer.Exit(code=1)

    lines = [ln.strip() for ln in file.read_text().splitlines() if ln.strip() and not ln.strip().startswith("#")]
    if not lines:
        console.print("[yellow]No commands found in batch file.[/yellow]")
        return

    runner = CliRunner()
    for line in lines:
        console.print(f"[bold cyan]$ toolkit {line}[/bold cyan]")
        result = runner.invoke(app, shlex.split(line))
        console.print(result.output.rstrip() or "[dim](no output)[/dim]")
        console.print()


if __name__ == "__main__":
    app()

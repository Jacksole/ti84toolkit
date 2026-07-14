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
from modules import circuits, electronics, logic, math_tools, physics, plotting, resistor_bom, statistics_tools, units

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

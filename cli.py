"""
TI-84 Embedded Systems Toolkit -- CLI entrypoint.

Run with no arguments for the interactive menu (matches the original TI-84 flow).
Run with a subcommand for direct, scriptable access:

    toolkit electronics ohms-law --voltage 5 --resistance 100
    toolkit electronics resistor red red brown gold
    toolkit electronics timer555 --r1 1000 --r2 1000 --c 0.000001
"""
from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console

from core.menu import main_menu
from core.validation import ValidationError
from modules import electronics, logic, math_tools, physics

console = Console()

app = typer.Typer(
    name="toolkit",
    help="TI-84 Embedded Systems Toolkit -- electronics, math, physics, and logic utilities.",
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


@app.callback(invoke_without_command=True)
def root(ctx: typer.Context) -> None:
    """No subcommand given -> launch the interactive menu."""
    if ctx.invoked_subcommand is None:
        main_menu()


# ---------------------------------------------------------------------------
# electronics ohms-law
# ---------------------------------------------------------------------------


@electronics_app.command("ohms-law")
def ohms_law_cmd(
    voltage: Optional[float] = typer.Option(None, "--voltage", "-v", help="Voltage in volts"),
    current: Optional[float] = typer.Option(None, "--current", "-i", help="Current in amps"),
    resistance: Optional[float] = typer.Option(None, "--resistance", "-r", help="Resistance in ohms"),
) -> None:
    """Solve Ohm's Law given exactly two of voltage, current, resistance."""
    try:
        result = electronics.ohms_law(voltage, current, resistance)
    except ValidationError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

    console.print(f"[green]Solved for {result.solved_for}[/green]")
    console.print(f"  V = {result.voltage:g} V")
    console.print(f"  I = {result.current:g} A")
    console.print(f"  R = {result.resistance:g} Ω")
    console.print(f"  P = {result.power:g} W")


# ---------------------------------------------------------------------------
# electronics resistor
# ---------------------------------------------------------------------------


@electronics_app.command("resistor")
def resistor_cmd(
    bands: list[str] = typer.Argument(..., help="Color bands, e.g. orange orange red gold"),
) -> None:
    """Decode a 4-band or 5-band resistor color code."""
    try:
        result = electronics.resistor_color_code(bands)
    except ValidationError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

    console.print(f"[green]Resistance:[/green] {result.display}")
    console.print(f"[green]Tolerance:[/green] {result.tolerance}")


# ---------------------------------------------------------------------------
# electronics timer555
# ---------------------------------------------------------------------------


@electronics_app.command("timer555")
def timer555_cmd(
    r1: float = typer.Option(..., "--r1", help="R1 in ohms"),
    r2: float = typer.Option(..., "--r2", help="R2 in ohms"),
    c: float = typer.Option(..., "--c", help="Capacitance in farads (e.g. 0.000001 for 1uF)"),
) -> None:
    """Compute frequency and duty cycle for a 555 timer in astable mode."""
    try:
        result = electronics.timer_555_astable(r1, r2, c)
    except ValidationError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

    console.print(f"[green]Frequency:[/green] {result.frequency_hz:.2f} Hz")
    console.print(f"[green]Period:[/green] {result.period_s * 1000:.4f} ms")
    console.print(f"[green]Duty Cycle:[/green] {result.duty_cycle_pct:.2f}%")
    console.print(f"[green]Time High:[/green] {result.time_high_s * 1000:.4f} ms")
    console.print(f"[green]Time Low:[/green] {result.time_low_s * 1000:.4f} ms")


def _render_truth_table(result, title: str) -> None:
    from rich.table import Table

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
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

    console.print(f"[green]{gate.upper()}({', '.join(inputs)}) = {result}[/green]")


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
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

    _render_truth_table(result, expression.upper())


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
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

    console.print(f"[green]Discriminant:[/green] {result.discriminant:g} ({result.nature})")
    for i, root in enumerate(result.roots, 1):
        real = root.real + 0.0  # normalize -0.0 to 0.0
        if root.imag == 0:
            console.print(f"  x{i} = {real:g}")
        else:
            console.print(f"  x{i} = {real:g} {'+' if root.imag >= 0 else '-'} {abs(root.imag):g}i")


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
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

    is_inverse = function.strip().lower().startswith("a")
    out_unit = unit if is_inverse else ""
    console.print(f"[green]{function}({value}) = {result:g}{' ' + unit if is_inverse else ''}[/green]")


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
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

    console.print(f"[green]{result.variable} = {', '.join(result.solutions)}[/green]")


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
) -> None:
    """Solve constant-acceleration kinematics given exactly 3 of v0, v, a, t, d."""
    try:
        result = physics.kinematics_solve(v0, v, a, t, d)
    except ValidationError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

    console.print(f"[green]Solved for {' and '.join(result.solved_for)}:[/green]")
    console.print(f"  v0 = {result.values['v0']:g} m/s")
    console.print(f"  v  = {result.values['v']:g} m/s")
    console.print(f"  a  = {result.values['a']:g} m/s²")
    console.print(f"  t  = {result.values['t']:g} s")
    console.print(f"  d  = {result.values['d']:g} m")


# ---------------------------------------------------------------------------
# physics energy
# ---------------------------------------------------------------------------


@physics_app.command("energy")
def energy_cmd(
    kind: str = typer.Argument(..., help="kinetic, potential, or work"),
    mass: Optional[float] = typer.Option(None, "--mass", help="Mass in kg (kinetic/potential)"),
    velocity: Optional[float] = typer.Option(None, "--velocity", help="Velocity in m/s (kinetic)"),
    height: Optional[float] = typer.Option(None, "--height", help="Height in m (potential)"),
    gravity: float = typer.Option(9.81, "--gravity", help="Gravity in m/s^2 (potential, default Earth)"),
    force: Optional[float] = typer.Option(None, "--force", help="Force in N (work)"),
    distance: Optional[float] = typer.Option(None, "--distance", help="Distance in m (work)"),
) -> None:
    """Compute kinetic energy, gravitational potential energy, or work done."""
    kind = kind.strip().lower()
    try:
        if kind == "kinetic":
            if mass is None or velocity is None:
                raise ValidationError("kinetic energy requires --mass and --velocity.")
            result = physics.kinetic_energy(mass, velocity)
        elif kind == "potential":
            if mass is None or height is None:
                raise ValidationError("potential energy requires --mass and --height.")
            result = physics.potential_energy(mass, height, gravity)
        elif kind == "work":
            if force is None or distance is None:
                raise ValidationError("work requires --force and --distance.")
            result = physics.work_done(force, distance)
        else:
            raise ValidationError("kind must be one of: kinetic, potential, work.")
    except ValidationError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

    console.print(f"[green]{result.label}:[/green] {result.joules:g} J")


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
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

    console.print(f"[green]Power:[/green] {result.watts:g} W")


if __name__ == "__main__":
    app()

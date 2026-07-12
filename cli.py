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
from modules import electronics, logic, math_tools

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


if __name__ == "__main__":
    app()

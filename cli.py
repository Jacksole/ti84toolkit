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
from modules import electronics

console = Console()

app = typer.Typer(
    name="toolkit",
    help="TI-84 Embedded Systems Toolkit -- electronics, math, physics, and logic utilities.",
    no_args_is_help=False,
)

electronics_app = typer.Typer(help="Electronics utilities: Ohm's Law, resistor codes, 555 timer.")
app.add_typer(electronics_app, name="electronics")


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


if __name__ == "__main__":
    app()

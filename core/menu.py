"""
Interactive menu system -- mirrors the original TOOLKIT -> Module -> Input ->
Compute -> Output -> Return flow from the TI-84 version, but rendered with
`rich` instead of ASCII headers.
"""
from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from core.validation import ValidationError, prompt_float
from modules import electronics

console = Console()


def _pause() -> None:
    Prompt.ask("\n[dim]Press Enter to return[/dim]", default="", show_default=False)


def _header(title: str) -> None:
    console.clear()
    console.print(Panel.fit(f"[bold cyan]{title}[/bold cyan]", border_style="cyan"))


# ---------------------------------------------------------------------------
# Electronics submenu
# ---------------------------------------------------------------------------


def _menu_ohms_law() -> None:
    _header("Ohm's Law Solver")
    console.print("Enter exactly TWO of the three values below. Leave the unknown one blank.\n")

    voltage = prompt_float("Voltage (V)", allow_blank=True)
    current = prompt_float("Current (A)", allow_blank=True)
    resistance = prompt_float("Resistance (Ω)", allow_blank=True)

    try:
        result = electronics.ohms_law(voltage, current, resistance)
        console.print(
            f"\n[green]Solved for {result.solved_for}:[/green]\n"
            f"  V = {result.voltage:g} V\n"
            f"  I = {result.current:g} A\n"
            f"  R = {result.resistance:g} Ω\n"
            f"  P = {result.power:g} W"
        )
    except ValidationError as e:
        console.print(f"[red]{e}[/red]")
    _pause()


def _menu_resistor() -> None:
    _header("Resistor Color Code Decoder")
    console.print("Enter band colors separated by spaces (4 or 5 bands).")
    console.print("[dim]Example: orange orange red gold[/dim]\n")

    raw = Prompt.ask("Bands")
    try:
        result = electronics.resistor_color_code(raw.split())
        console.print(
            f"\n[green]Resistance:[/green] {result.display}  "
            f"[green]Tolerance:[/green] {result.tolerance}"
        )
    except ValidationError as e:
        console.print(f"[red]{e}[/red]")
    _pause()


def _menu_timer555() -> None:
    _header("555 Timer (Astable Mode)")

    r1 = prompt_float("R1 (Ω)")
    r2 = prompt_float("R2 (Ω)")
    c = prompt_float("C (Farads, e.g. 0.000001 for 1µF)")

    try:
        result = electronics.timer_555_astable(r1, r2, c)
        console.print(
            f"\n[green]Frequency:[/green] {result.frequency_hz:.2f} Hz\n"
            f"[green]Period:[/green] {result.period_s * 1000:.4f} ms\n"
            f"[green]Duty Cycle:[/green] {result.duty_cycle_pct:.2f}%\n"
            f"[green]Time High:[/green] {result.time_high_s * 1000:.4f} ms\n"
            f"[green]Time Low:[/green] {result.time_low_s * 1000:.4f} ms"
        )
    except ValidationError as e:
        console.print(f"[red]{e}[/red]")
    _pause()


def _electronics_menu() -> None:
    while True:
        _header("Electronics")
        console.print("1. Ohm's Law Solver")
        console.print("2. Resistor Color Code Decoder")
        console.print("3. 555 Timer (Astable)")
        console.print("0. Back\n")

        choice = Prompt.ask("Select", choices=["0", "1", "2", "3"], show_choices=False)
        if choice == "0":
            return
        elif choice == "1":
            _menu_ohms_law()
        elif choice == "2":
            _menu_resistor()
        elif choice == "3":
            _menu_timer555()


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------


def main_menu() -> None:
    while True:
        _header("TI-84 Embedded Systems Toolkit")
        console.print("1. Electronics")
        console.print("2. Math  [dim](coming soon)[/dim]")
        console.print("3. Physics  [dim](coming soon)[/dim]")
        console.print("4. Logic  [dim](coming soon)[/dim]")
        console.print("0. Exit\n")

        choice = Prompt.ask("Select", choices=["0", "1", "2", "3", "4"], show_choices=False)
        if choice == "0":
            console.print("\n[cyan]Goodbye.[/cyan]")
            return
        elif choice == "1":
            _electronics_menu()
        else:
            console.print("\n[yellow]This module isn't built yet.[/yellow]")
            _pause()

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
from modules import electronics, logic, math_tools

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
# Logic submenu
# ---------------------------------------------------------------------------


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


def _menu_gate_eval() -> None:
    _header("Gate Evaluator")
    console.print(f"Available gates: {', '.join(logic.GATE_NAMES)}\n")

    gate = Prompt.ask("Gate").strip().upper()
    raw_inputs = Prompt.ask("Inputs (space-separated, e.g. true false)")

    try:
        bool_inputs = []
        for tok in raw_inputs.split():
            v = tok.strip().lower()
            if v in ("true", "t", "1"):
                bool_inputs.append(True)
            elif v in ("false", "f", "0"):
                bool_inputs.append(False)
            else:
                raise ValidationError(f"'{tok}' is not a valid boolean.")
        result = logic.evaluate_gate(gate, bool_inputs)
        console.print(f"\n[green]{gate}({raw_inputs}) = {result}[/green]")
    except ValidationError as e:
        console.print(f"[red]{e}[/red]")
    _pause()


def _menu_truth_table() -> None:
    _header("Truth Table Generator")
    console.print("Enter a gate name (e.g. AND) or a boolean expression (e.g. A AND (B OR NOT C))\n")

    expr = Prompt.ask("Gate or expression")

    try:
        if expr.strip().upper() in logic.GATE_NAMES:
            n = prompt_float("Number of inputs")
            result = logic.gate_truth_table(expr, int(n))
        else:
            result = logic.expression_truth_table(expr)
        console.print()
        _render_truth_table(result, expr.upper())
    except ValidationError as e:
        console.print(f"[red]{e}[/red]")
    _pause()


def _logic_menu() -> None:
    while True:
        _header("Logic")
        console.print("1. Evaluate a Gate")
        console.print("2. Generate Truth Table")
        console.print("0. Back\n")

        choice = Prompt.ask("Select", choices=["0", "1", "2"], show_choices=False)
        if choice == "0":
            return
        elif choice == "1":
            _menu_gate_eval()
        elif choice == "2":
            _menu_truth_table()


# ---------------------------------------------------------------------------
# Math submenu
# ---------------------------------------------------------------------------


def _menu_quadratic() -> None:
    _header("Quadratic Solver")
    console.print("Solve ax² + bx + c = 0\n")

    a = prompt_float("a")
    b = prompt_float("b")
    c = prompt_float("c")

    try:
        result = math_tools.quadratic_solve(a, b, c)
        console.print(f"\n[green]Discriminant:[/green] {result.discriminant:g} ({result.nature})")
        for i, root in enumerate(result.roots, 1):
            real = root.real + 0.0
            if root.imag == 0:
                console.print(f"  x{i} = {real:g}")
            else:
                sign = "+" if root.imag >= 0 else "-"
                console.print(f"  x{i} = {real:g} {sign} {abs(root.imag):g}i")
    except ValidationError as e:
        console.print(f"[red]{e}[/red]")
    _pause()


def _menu_trig() -> None:
    _header("Trigonometry")
    console.print("Functions: sin, cos, tan, asin, acos, atan\n")

    function = Prompt.ask("Function").strip().lower()
    value = prompt_float("Value")
    unit = Prompt.ask("Unit", choices=["deg", "rad"], default="deg")

    try:
        result = math_tools.trig_evaluate(function, value, unit)
        is_inverse = function.startswith("a")
        suffix = f" {unit}" if is_inverse else ""
        console.print(f"\n[green]{function}({value}) = {result:g}{suffix}[/green]")
    except ValidationError as e:
        console.print(f"[red]{e}[/red]")
    _pause()


def _menu_solve_equation() -> None:
    _header("Equation Solver")
    console.print('Enter an equation, e.g. "2*x + 3 = 7" or "x**2 - 4 = 0"\n')

    equation = Prompt.ask("Equation")
    variable = Prompt.ask("Variable", default="x")

    try:
        result = math_tools.solve_equation(equation, variable)
        console.print(f"\n[green]{result.variable} = {', '.join(result.solutions)}[/green]")
    except ValidationError as e:
        console.print(f"[red]{e}[/red]")
    _pause()


def _math_menu() -> None:
    while True:
        _header("Math")
        console.print("1. Quadratic Solver")
        console.print("2. Trigonometry")
        console.print("3. Equation Solver")
        console.print("0. Back\n")

        choice = Prompt.ask("Select", choices=["0", "1", "2", "3"], show_choices=False)
        if choice == "0":
            return
        elif choice == "1":
            _menu_quadratic()
        elif choice == "2":
            _menu_trig()
        elif choice == "3":
            _menu_solve_equation()


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
        elif choice == "2":
            _math_menu()
        elif choice == "4":
            _logic_menu()
        else:
            console.print("\n[yellow]This module isn't built yet.[/yellow]")
            _pause()

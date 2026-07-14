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
from modules import calculus, circuits, electronics, finance, geometry, linear_algebra, logic, math_tools, orbital, physics, plotting, probability, resistor_bom, sequences, statistics_tools, units

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
        if Prompt.ask("\nShow step-by-step derivation?", choices=["y", "n"], default="n") == "y":
            console.print()
            for line in result.steps:
                console.print(f"  {line}")
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
        if Prompt.ask("Save a color-band diagram image?", choices=["y", "n"], default="n") == "y":
            path = Prompt.ask("Save as", default="resistor_diagram.png")
            saved = circuits.draw_resistor_diagram(raw.split(), result.display, result.tolerance, path)
            console.print(f"[dim]Saved to {saved}[/dim]")
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
        if Prompt.ask("Save a waveform plot?", choices=["y", "n"], default="n") == "y":
            path = Prompt.ask("Save as", default="timer555_waveform.png")
            saved = plotting.plot_555_waveform(result.frequency_hz, result.duty_cycle_pct, path)
            console.print(f"[dim]Saved to {saved}[/dim]")
        if Prompt.ask("Save a circuit schematic?", choices=["y", "n"], default="n") == "y":
            path = Prompt.ask("Save as", default="timer555_circuit.png")
            saved = circuits.draw_555_astable_circuit(r1, r2, c, path)
            console.print(f"[dim]Saved to {saved}[/dim]")
    except ValidationError as e:
        console.print(f"[red]{e}[/red]")
    _pause()


def _menu_resistor_bom() -> None:
    _header("Resistor Combo Finder")
    console.print("Find the closest standard resistor(s) to a target value.\n")

    target = prompt_float("Target resistance (Ω)")
    series = Prompt.ask("Series", choices=["E12", "E24"], default="E24")

    try:
        options = resistor_bom.find_resistor_combo(target, series)
        console.print(f"\n[green]Target:[/green] {target:g} \u03a9  [dim]({series} series)[/dim]")
        for o in options:
            console.print(f"  {resistor_bom.format_option(o)}")
    except ValidationError as e:
        console.print(f"[red]{e}[/red]")
    _pause()


def _electronics_menu() -> None:
    while True:
        _header("Electronics")
        console.print("1. Ohm's Law Solver")
        console.print("2. Resistor Color Code Decoder")
        console.print("3. 555 Timer (Astable)")
        console.print("4. Resistor Combo Finder (BOM)")
        console.print("0. Back\n")

        choice = Prompt.ask("Select", choices=["0", "1", "2", "3", "4"], show_choices=False)
        if choice == "0":
            return
        elif choice == "1":
            _menu_ohms_law()
        elif choice == "2":
            _menu_resistor()
        elif choice == "3":
            _menu_timer555()
        elif choice == "4":
            _menu_resistor_bom()


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
# Physics submenu
# ---------------------------------------------------------------------------


def _menu_kinematics() -> None:
    _header("Kinematics Solver")
    console.print("Enter exactly THREE of the five values below. Leave the other two blank.\n")

    v0 = prompt_float("Initial velocity v0 (m/s)", allow_blank=True)
    v = prompt_float("Final velocity v (m/s)", allow_blank=True)
    a = prompt_float("Acceleration a (m/s²)", allow_blank=True)
    t = prompt_float("Time t (s)", allow_blank=True)
    d = prompt_float("Displacement d (m)", allow_blank=True)

    try:
        result = physics.kinematics_solve(v0, v, a, t, d)
        console.print(f"\n[green]Solved for {' and '.join(result.solved_for)}:[/green]")
        console.print(f"  v0 = {result.values['v0']:g} m/s")
        console.print(f"  v  = {result.values['v']:g} m/s")
        console.print(f"  a  = {result.values['a']:g} m/s²")
        console.print(f"  t  = {result.values['t']:g} s")
        console.print(f"  d  = {result.values['d']:g} m")
        if Prompt.ask("\nShow step-by-step derivation?", choices=["y", "n"], default="n") == "y":
            console.print()
            for line in result.steps:
                console.print(f"  {line}")
        if Prompt.ask("Save a position/velocity vs. time plot?", choices=["y", "n"], default="n") == "y":
            path = Prompt.ask("Save as", default="kinematics_plot.png")
            saved = plotting.plot_kinematics(result.values["v0"], result.values["a"], result.values["t"], path)
            console.print(f"[dim]Saved to {saved}[/dim]")
    except ValidationError as e:
        console.print(f"[red]{e}[/red]")
    _pause()


def _menu_energy() -> None:
    _header("Energy Calculator")
    console.print("1. Kinetic Energy\n2. Gravitational Potential Energy\n3. Work Done\n")

    choice = Prompt.ask("Select", choices=["1", "2", "3"], show_choices=False)

    try:
        if choice == "1":
            mass = prompt_float("Mass (kg)")
            velocity = prompt_float("Velocity (m/s)")
            result = physics.kinetic_energy(mass, velocity)
        elif choice == "2":
            mass = prompt_float("Mass (kg)")
            height = prompt_float("Height (m)")
            g = prompt_float("Gravity (m/s², blank for Earth 9.81)", allow_blank=True)
            result = physics.potential_energy(mass, height, g if g is not None else 9.81)
        else:
            force = prompt_float("Force (N)")
            distance = prompt_float("Distance (m)")
            result = physics.work_done(force, distance)

        console.print(f"\n[green]{result.label}:[/green] {result.joules:g} J")
    except ValidationError as e:
        console.print(f"[red]{e}[/red]")
    _pause()


def _menu_power() -> None:
    _header("Power Calculator")
    console.print("1. From Work + Time\n2. From Force + Velocity\n")

    choice = Prompt.ask("Select", choices=["1", "2"], show_choices=False)

    try:
        if choice == "1":
            work = prompt_float("Work (J)")
            time = prompt_float("Time (s)")
            result = physics.power_from_work(work, time)
        else:
            force = prompt_float("Force (N)")
            velocity = prompt_float("Velocity (m/s)")
            result = physics.power_from_force_velocity(force, velocity)

        console.print(f"\n[green]Power:[/green] {result.watts:g} W")
    except ValidationError as e:
        console.print(f"[red]{e}[/red]")
    _pause()


def _physics_menu() -> None:
    while True:
        _header("Physics")
        console.print("1. Kinematics Solver")
        console.print("2. Energy Calculator")
        console.print("3. Power Calculator")
        console.print("0. Back\n")

        choice = Prompt.ask("Select", choices=["0", "1", "2", "3"], show_choices=False)
        if choice == "0":
            return
        elif choice == "1":
            _menu_kinematics()
        elif choice == "2":
            _menu_energy()
        elif choice == "3":
            _menu_power()


# ---------------------------------------------------------------------------
# Statistics submenu
# ---------------------------------------------------------------------------


def _prompt_data_list() -> list[float]:
    from core.validation import ValidationError as VE, parse_float

    raw = Prompt.ask("Data points (space-separated, e.g. 2 4 4 5 7 9)")
    values = []
    for tok in raw.split():
        values.append(parse_float(tok, "data point"))
    return values


def _menu_describe() -> None:
    _header("Descriptive Statistics")

    try:
        data = _prompt_data_list()
        result = statistics_tools.describe(data)
        console.print(f"\n[green]n:[/green] {result.count}    [green]Sum:[/green] {result.sum:g}")
        console.print(f"[green]Mean:[/green] {result.mean:g}    [green]Median:[/green] {result.median:g}")
        mode_str = ", ".join(f"{m:g}" for m in result.mode) if result.mode else "none"
        console.print(f"[green]Mode:[/green] {mode_str}")
        console.print(f"[green]Range:[/green] {result.data_range:g}  (min {result.minimum:g}, max {result.maximum:g})")
        console.print(f"[green]Population variance / stdev:[/green] {result.variance_population:g} / {result.stdev_population:g}")
        if result.variance_sample is not None:
            console.print(f"[green]Sample variance / stdev:[/green] {result.variance_sample:g} / {result.stdev_sample:g}")
    except ValidationError as e:
        console.print(f"[red]{e}[/red]")
    _pause()


def _menu_quartiles() -> None:
    _header("Five-Number Summary")

    try:
        data = _prompt_data_list()
        result = statistics_tools.five_number_summary(data)
        console.print(f"\n[green]Min:[/green] {result.minimum:g}   [green]Q1:[/green] {result.q1:g}")
        console.print(f"[green]Median:[/green] {result.median:g}   [green]Q3:[/green] {result.q3:g}")
        console.print(f"[green]Max:[/green] {result.maximum:g}   [green]IQR:[/green] {result.iqr:g}")
    except ValidationError as e:
        console.print(f"[red]{e}[/red]")
    _pause()


def _menu_combinatorics() -> None:
    _header("Combinatorics")
    console.print("1. Factorial (n!)\n2. Permutations (nPr)\n3. Combinations (nCr)\n")

    choice = Prompt.ask("Select", choices=["1", "2", "3"], show_choices=False)

    try:
        if choice == "1":
            n = int(prompt_float("n"))
            result = statistics_tools.factorial(n)
            console.print(f"\n[green]{n}! = {result}[/green]")
        elif choice == "2":
            n = int(prompt_float("n"))
            r = int(prompt_float("r"))
            result = statistics_tools.permutations(n, r)
            console.print(f"\n[green]{n}P{r} = {result}[/green]")
        else:
            n = int(prompt_float("n"))
            r = int(prompt_float("r"))
            result = statistics_tools.combinations(n, r)
            console.print(f"\n[green]{n}C{r} = {result}[/green]")
    except ValidationError as e:
        console.print(f"[red]{e}[/red]")
    _pause()


def _statistics_menu() -> None:
    while True:
        _header("Statistics")
        console.print("1. Descriptive Statistics")
        console.print("2. Five-Number Summary (Quartiles)")
        console.print("3. Combinatorics (n!, nPr, nCr)")
        console.print("0. Back\n")

        choice = Prompt.ask("Select", choices=["0", "1", "2", "3"], show_choices=False)
        if choice == "0":
            return
        elif choice == "1":
            _menu_describe()
        elif choice == "2":
            _menu_quartiles()
        elif choice == "3":
            _menu_combinatorics()


# ---------------------------------------------------------------------------
# Units submenu
# ---------------------------------------------------------------------------


def _menu_units() -> None:
    _header("Unit Conversion")
    console.print(f"Categories: {', '.join(units.CATEGORY_NAMES)}\n")

    category = Prompt.ask("Category").strip().lower()

    try:
        valid_units = units.units_for_category(category)
        console.print(f"[dim]Units: {', '.join(valid_units)}[/dim]\n")
        value = prompt_float("Value")
        from_unit = Prompt.ask("From unit")
        to_unit = Prompt.ask("To unit")
        result = units.convert(category, value, from_unit, to_unit)
        console.print(f"\n[green]{result.value:g} {result.from_unit} = {result.result:g} {result.to_unit}[/green]")
    except ValidationError as e:
        console.print(f"[red]{e}[/red]")
    _pause()


# ---------------------------------------------------------------------------
# Orbital Mechanics submenu
# ---------------------------------------------------------------------------


def _resolve_mu_menu() -> float:
    console.print(f"[dim]Known bodies: {', '.join(orbital.BODIES)}[/dim]")
    choice = Prompt.ask("Use a known body, or enter mu manually?", choices=["body", "mu"], default="body")
    if choice == "body":
        return orbital.body_mu(Prompt.ask("Body"))
    return prompt_float("Gravitational parameter mu (m^3/s^2)")


def _menu_orbital_period() -> None:
    _header("Orbital Period (Kepler's Third Law)")
    a = prompt_float("Semi-major axis (m)")
    try:
        mu = _resolve_mu_menu()
        period = orbital.orbital_period(a, mu)
        console.print(f"\n[green]Period:[/green] {period:g} s  ({period / 60:.2f} min, {period / 3600:.2f} hr, {period / 86400:.3f} days)")
    except ValidationError as e:
        console.print(f"[red]{e}[/red]")
    _pause()


def _menu_orbital_velocity() -> None:
    _header("Orbital Velocity")
    console.print("1. Circular\n2. Escape\n3. Vis-viva (at radius r, in orbit of semi-major axis a)\n")
    choice = Prompt.ask("Select", choices=["1", "2", "3"], show_choices=False)

    try:
        r = prompt_float("Radius r (m)")
        mu = _resolve_mu_menu()
        if choice == "1":
            v = orbital.circular_velocity(r, mu)
            label = "Circular"
        elif choice == "2":
            v = orbital.escape_velocity(r, mu)
            label = "Escape"
        else:
            a = prompt_float("Semi-major axis a (m)")
            v = orbital.vis_viva_velocity(r, a, mu)
            label = "Vis-viva"
        console.print(f"\n[green]{label} velocity:[/green] {v:g} m/s ({v / 1000:.3f} km/s)")
    except ValidationError as e:
        console.print(f"[red]{e}[/red]")
    _pause()


def _menu_kepler_equation() -> None:
    _header("Kepler's Equation Solver")
    console.print("Solve M = E - e*sin(E) for the eccentric anomaly, via Newton-Raphson.\n")

    m = prompt_float("Mean anomaly M (radians)")
    e = prompt_float("Eccentricity e (0 to <1)")

    try:
        result = orbital.solve_kepler_equation(m, e)
        console.print(f"\n[green]Eccentric anomaly (E):[/green] {result.eccentric_anomaly_rad:g} rad")
        console.print(f"[green]True anomaly (\u03bd):[/green] {result.true_anomaly_rad:g} rad")
        console.print(f"[dim]Converged in {result.iterations} iterations[/dim]")
        if Prompt.ask("\nShow step-by-step derivation?", choices=["y", "n"], default="n") == "y":
            console.print()
            for line in result.steps:
                console.print(f"  {line}")
    except ValidationError as e:
        console.print(f"[red]{e}[/red]")
    _pause()


def _menu_hohmann() -> None:
    _header("Hohmann Transfer")

    r1 = prompt_float("Departure orbit radius r1 (m)")
    r2 = prompt_float("Arrival orbit radius r2 (m)")

    try:
        mu = _resolve_mu_menu()
        result = orbital.hohmann_transfer(r1, r2, mu)
        console.print(f"\n[green]Burn 1 (departure):[/green] {result.delta_v1_mps:g} m/s")
        console.print(f"[green]Burn 2 (arrival):[/green] {result.delta_v2_mps:g} m/s")
        console.print(f"[green]Total delta-v:[/green] {result.total_delta_v_mps:g} m/s")
        console.print(f"[green]Transfer time:[/green] {result.transfer_time_s:g} s ({result.transfer_time_s / 3600:.2f} hr)")
        if Prompt.ask("\nShow step-by-step derivation?", choices=["y", "n"], default="n") == "y":
            console.print()
            for line in result.steps:
                console.print(f"  {line}")
        if Prompt.ask("Save a transfer orbit diagram?", choices=["y", "n"], default="n") == "y":
            path = Prompt.ask("Save as", default="hohmann_transfer.png")
            saved = plotting.plot_hohmann_transfer(r1, r2, path)
            console.print(f"[dim]Saved to {saved}[/dim]")
    except ValidationError as e:
        console.print(f"[red]{e}[/red]")
    _pause()


def _orbital_menu() -> None:
    while True:
        _header("Orbital Mechanics")
        console.print("1. Orbital Period (Kepler's Third Law)")
        console.print("2. Orbital Velocity (circular / escape / vis-viva)")
        console.print("3. Kepler's Equation Solver")
        console.print("4. Hohmann Transfer")
        console.print("0. Back\n")

        choice = Prompt.ask("Select", choices=["0", "1", "2", "3", "4"], show_choices=False)
        if choice == "0":
            return
        elif choice == "1":
            _menu_orbital_period()
        elif choice == "2":
            _menu_orbital_velocity()
        elif choice == "3":
            _menu_kepler_equation()
        elif choice == "4":
            _menu_hohmann()


# ---------------------------------------------------------------------------
# Calculus submenu
# ---------------------------------------------------------------------------


def _menu_calculus() -> None:
    while True:
        _header("Calculus")
        console.print("1. Derivative")
        console.print("2. Integral")
        console.print("3. Limit")
        console.print("4. Taylor Series")
        console.print("0. Back\n")

        choice = Prompt.ask("Select", choices=["0", "1", "2", "3", "4"], show_choices=False)
        if choice == "0":
            return

        expr = Prompt.ask('Expression (e.g. "x**3 + 2*x")')
        var = Prompt.ask("Variable", default="x")

        try:
            if choice == "1":
                order = int(prompt_float("Order (blank for 1)", allow_blank=True) or 1)
                result = calculus.derivative(expr, var, order)
                console.print(f"\n[green]Result:[/green] {result.result}")
            elif choice == "2":
                definite = Prompt.ask("Definite integral?", choices=["y", "n"], default="n") == "y"
                lower = prompt_float("Lower bound") if definite else None
                upper = prompt_float("Upper bound") if definite else None
                result = calculus.integral(expr, var, lower, upper)
                console.print(f"\n[green]Result:[/green] {result.result}")
            elif choice == "3":
                point = Prompt.ask("Point (number, or 'oo'/'-oo' for infinity)")
                direction = Prompt.ask("Direction", choices=["both", "left", "right"], default="both")
                result = calculus.limit(expr, var, point, direction)
                console.print(f"\n[green]Result:[/green] {result.result}")
            else:
                point = prompt_float("Expansion point (blank for 0)", allow_blank=True) or 0
                order = int(prompt_float("Order (blank for 5)", allow_blank=True) or 5)
                result = calculus.taylor_series(expr, var, point, order)
                console.print(f"\n[green]Result:[/green] {result.result}")
        except ValidationError as e:
            console.print(f"[red]{e}[/red]")
        _pause()


# ---------------------------------------------------------------------------
# Geometry submenu
# ---------------------------------------------------------------------------


def _render_shape_menu(result) -> None:
    console.print(f"\n[green]{result.shape.capitalize()}:[/green]")
    for key, val in result.measurements.items():
        console.print(f"  {key.replace('_', ' ')}: {val:g}")


def _menu_geometry() -> None:
    while True:
        _header("Geometry")
        console.print("1. Circle")
        console.print("2. Rectangle")
        console.print("3. Triangle (base & height)")
        console.print("4. Triangle (3 sides, Heron's formula)")
        console.print("5. Pythagorean theorem")
        console.print("6. Distance between two points")
        console.print("7. Sphere")
        console.print("8. Cylinder")
        console.print("9. Cone")
        console.print("10. Box")
        console.print("0. Back\n")

        choice = Prompt.ask("Select", choices=[str(i) for i in range(11)], show_choices=False)
        if choice == "0":
            return

        try:
            if choice == "1":
                _render_shape_menu(geometry.circle(prompt_float("Radius")))
            elif choice == "2":
                _render_shape_menu(geometry.rectangle(prompt_float("Length"), prompt_float("Width")))
            elif choice == "3":
                _render_shape_menu(geometry.triangle_base_height(prompt_float("Base"), prompt_float("Height")))
            elif choice == "4":
                _render_shape_menu(geometry.triangle_sides(prompt_float("Side a"), prompt_float("Side b"), prompt_float("Side c")))
            elif choice == "5":
                if Prompt.ask("Solve for", choices=["hypotenuse", "leg"], default="hypotenuse") == "hypotenuse":
                    result = geometry.pythagorean_hypotenuse(prompt_float("Leg a"), prompt_float("Leg b"))
                    console.print(f"\n[green]Hypotenuse:[/green] {result:g}")
                else:
                    result = geometry.pythagorean_leg(prompt_float("Hypotenuse"), prompt_float("Other leg"))
                    console.print(f"\n[green]Leg:[/green] {result:g}")
            elif choice == "6":
                is_3d = Prompt.ask("3D?", choices=["y", "n"], default="n") == "y"
                x1, y1 = prompt_float("x1"), prompt_float("y1")
                x2, y2 = prompt_float("x2"), prompt_float("y2")
                if is_3d:
                    z1, z2 = prompt_float("z1"), prompt_float("z2")
                    result = geometry.distance_3d(x1, y1, z1, x2, y2, z2)
                else:
                    result = geometry.distance_2d(x1, y1, x2, y2)
                console.print(f"\n[green]Distance:[/green] {result:g}")
            elif choice == "7":
                _render_shape_menu(geometry.sphere(prompt_float("Radius")))
            elif choice == "8":
                _render_shape_menu(geometry.cylinder(prompt_float("Radius"), prompt_float("Height")))
            elif choice == "9":
                _render_shape_menu(geometry.cone(prompt_float("Radius"), prompt_float("Height")))
            else:
                _render_shape_menu(geometry.box(prompt_float("Length"), prompt_float("Width"), prompt_float("Height")))
        except ValidationError as e:
            console.print(f"[red]{e}[/red]")
        _pause()


# ---------------------------------------------------------------------------
# Linear Algebra submenu
# ---------------------------------------------------------------------------


def _prompt_vector(label: str) -> list[float]:
    raw = Prompt.ask(f"{label} (comma-separated, e.g. 1,2,3)")
    return [float(x) for x in raw.split(",")]


def _prompt_matrix(label: str) -> list[list[float]]:
    raw = Prompt.ask(f"{label} (rows separated by ';', e.g. 1,2;3,4)")
    return [[float(x) for x in row.split(",")] for row in raw.split(";")]


def _render_vector(v) -> None:
    console.print(f"[green]Result:[/green] ({', '.join(f'{x:g}' for x in v)})")


def _render_matrix_menu(rows: list[list[float]]) -> None:
    for row in rows:
        console.print("  " + "  ".join(f"{x:g}" for x in row))


def _menu_linalg() -> None:
    while True:
        _header("Linear Algebra")
        console.print("1. Vector Dot Product")
        console.print("2. Vector Cross Product")
        console.print("3. Vector Magnitude")
        console.print("4. Vector Normalize")
        console.print("5. Vector Angle Between")
        console.print("6. Matrix Add")
        console.print("7. Matrix Multiply")
        console.print("8. Matrix Transpose")
        console.print("9. Matrix Determinant")
        console.print("10. Matrix Inverse")
        console.print("0. Back\n")

        choice = Prompt.ask("Select", choices=[str(i) for i in range(11)], show_choices=False)
        if choice == "0":
            return

        try:
            if choice == "1":
                console.print(f"\n[green]Result:[/green] {linear_algebra.vector_dot(_prompt_vector('v1'), _prompt_vector('v2')):g}")
            elif choice == "2":
                console.print()
                _render_vector(linear_algebra.vector_cross(_prompt_vector("v1"), _prompt_vector("v2")))
            elif choice == "3":
                console.print(f"\n[green]Result:[/green] {linear_algebra.vector_magnitude(_prompt_vector('v')):g}")
            elif choice == "4":
                console.print()
                _render_vector(linear_algebra.vector_normalize(_prompt_vector("v")))
            elif choice == "5":
                angle = linear_algebra.vector_angle_between(_prompt_vector("v1"), _prompt_vector("v2"))
                console.print(f"\n[green]Angle:[/green] {angle * 180 / 3.141592653589793:g}\u00b0 ({angle:g} rad)")
            elif choice == "6":
                console.print()
                _render_matrix_menu(linear_algebra.matrix_add(_prompt_matrix("M1"), _prompt_matrix("M2")).rows)
            elif choice == "7":
                console.print()
                _render_matrix_menu(linear_algebra.matrix_multiply(_prompt_matrix("M1"), _prompt_matrix("M2")).rows)
            elif choice == "8":
                console.print()
                _render_matrix_menu(linear_algebra.matrix_transpose(_prompt_matrix("M")).rows)
            elif choice == "9":
                console.print(f"\n[green]Determinant:[/green] {linear_algebra.matrix_determinant(_prompt_matrix('M')):g}")
            else:
                console.print()
                _render_matrix_menu(linear_algebra.matrix_inverse(_prompt_matrix("M")).rows)
        except ValidationError as e:
            console.print(f"[red]{e}[/red]")
        _pause()


# ---------------------------------------------------------------------------
# Sequences submenu
# ---------------------------------------------------------------------------


def _menu_sequences() -> None:
    while True:
        _header("Sequences and Series")
        console.print("1. Arithmetic nth Term")
        console.print("2. Arithmetic Sum")
        console.print("3. Geometric nth Term")
        console.print("4. Geometric Sum")
        console.print("5. Geometric Sum (infinite)")
        console.print("0. Back\n")

        choice = Prompt.ask("Select", choices=["0", "1", "2", "3", "4", "5"], show_choices=False)
        if choice == "0":
            return

        try:
            if choice in ("1", "2"):
                a1 = prompt_float("First term (a1)")
                d = prompt_float("Common difference (d)")
                n = int(prompt_float("n"))
                if choice == "1":
                    console.print(f"\n[green]a_{n} =[/green] {sequences.arithmetic_nth_term(a1, d, n):g}")
                else:
                    console.print(f"\n[green]S_{n} =[/green] {sequences.arithmetic_sum(a1, d, n):g}")
            elif choice in ("3", "4"):
                a1 = prompt_float("First term (a1)")
                r = prompt_float("Common ratio (r)")
                n = int(prompt_float("n"))
                if choice == "3":
                    console.print(f"\n[green]a_{n} =[/green] {sequences.geometric_nth_term(a1, r, n):g}")
                else:
                    console.print(f"\n[green]S_{n} =[/green] {sequences.geometric_sum(a1, r, n):g}")
            else:
                a1 = prompt_float("First term (a1)")
                r = prompt_float("Common ratio (r, must satisfy |r| < 1)")
                result = sequences.geometric_sum_infinite(a1, r)
                console.print(f"\n[green]S_\u221e =[/green] {result.sum:g}")
        except ValidationError as e:
            console.print(f"[red]{e}[/red]")
        _pause()


# ---------------------------------------------------------------------------
# Probability submenu
# ---------------------------------------------------------------------------


def _menu_probability() -> None:
    while True:
        _header("Probability Distributions")
        console.print("1. Binomial PMF")
        console.print("2. Binomial CDF")
        console.print("3. Binomial Stats (mean/variance/stdev)")
        console.print("4. Normal PDF")
        console.print("5. Normal CDF")
        console.print("6. Normal CDF Range")
        console.print("7. Inverse Normal CDF")
        console.print("8. Z-Score")
        console.print("0. Back\n")

        choice = Prompt.ask("Select", choices=[str(i) for i in range(9)], show_choices=False)
        if choice == "0":
            return

        try:
            if choice in ("1", "2", "3"):
                n = int(prompt_float("n"))
                if choice == "3":
                    p = prompt_float("p")
                    result = probability.binomial_stats(n, p)
                    console.print(f"\n[green]Mean:[/green] {result.mean:g}  [green]Variance:[/green] {result.variance:g}  [green]Stdev:[/green] {result.stdev:g}")
                else:
                    k = int(prompt_float("k"))
                    p = prompt_float("p")
                    if choice == "1":
                        console.print(f"\n[green]P(X = {k}):[/green] {probability.binomial_pmf(n, k, p):g}")
                    else:
                        console.print(f"\n[green]P(X \u2264 {k}):[/green] {probability.binomial_cdf(n, k, p):g}")
            else:
                mean = prompt_float("Mean", allow_blank=True) or 0
                stdev = prompt_float("Standard deviation", allow_blank=True) or 1
                if choice == "4":
                    x = prompt_float("x")
                    console.print(f"\n[green]f(x):[/green] {probability.normal_pdf(x, mean, stdev):g}")
                elif choice == "5":
                    x = prompt_float("x")
                    console.print(f"\n[green]P(X \u2264 x):[/green] {probability.normal_cdf(x, mean, stdev):g}")
                elif choice == "6":
                    low = prompt_float("Low")
                    high = prompt_float("High")
                    console.print(f"\n[green]P(low \u2264 X \u2264 high):[/green] {probability.normal_cdf_range(low, high, mean, stdev):g}")
                elif choice == "7":
                    p = prompt_float("p (0 to 1)")
                    console.print(f"\n[green]x:[/green] {probability.inverse_normal_cdf(p, mean, stdev):g}")
                else:
                    x = prompt_float("x")
                    console.print(f"\n[green]z:[/green] {probability.z_score(x, mean, stdev):g}")
        except ValidationError as e:
            console.print(f"[red]{e}[/red]")
        _pause()


# ---------------------------------------------------------------------------
# Finance submenu
# ---------------------------------------------------------------------------


def _menu_finance() -> None:
    while True:
        _header("Finance")
        console.print("1. TVM Solver (loans, mortgages, annuities)")
        console.print("2. Compound Interest (lump sum, no payments)")
        console.print("0. Back\n")

        choice = Prompt.ask("Select", choices=["0", "1", "2"], show_choices=False)
        if choice == "0":
            return

        try:
            if choice == "1":
                console.print("Enter exactly 4 of the 5 values below. Leave the unknown one blank.\n")
                n = prompt_float("n (number of periods)", allow_blank=True)
                rate = prompt_float("Annual rate, percent", allow_blank=True)
                pv = prompt_float("Present value (negative if paid out)", allow_blank=True)
                pmt = prompt_float("Payment per period (negative if paid out)", allow_blank=True)
                fv = prompt_float("Future value (negative if paid out)", allow_blank=True)
                ppy = int(prompt_float("Payments per year", allow_blank=True) or 12)
                result = finance.solve_tvm(n, rate, pv, pmt, fv, ppy)
                console.print(f"\n[green]Solved for {result.solved_for}:[/green]")
                console.print(f"  n = {result.n:g}")
                console.print(f"  rate = {result.rate_percent:g}%")
                console.print(f"  pv = {result.pv:g}")
                console.print(f"  pmt = {result.pmt:g}")
                console.print(f"  fv = {result.fv:g}")
                if Prompt.ask("\nShow step-by-step derivation?", choices=["y", "n"], default="n") == "y":
                    console.print()
                    for line in result.steps:
                        console.print(f"  {line}")
            else:
                principal = prompt_float("Principal")
                rate = prompt_float("Annual rate, percent")
                compounds = int(prompt_float("Compounds per year", allow_blank=True) or 12)
                years = prompt_float("Years")
                result = finance.compound_interest(principal, rate, compounds, years)
                console.print(f"\n[green]Future value:[/green] {result.future_value:g}")
                console.print(f"[green]Interest earned:[/green] {result.interest_earned:g}")
        except ValidationError as e:
            console.print(f"[red]{e}[/red]")
        _pause()


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------


def main_menu() -> None:
    while True:
        _header("TI-84 Embedded Systems Toolkit")
        console.print("1. Electronics")
        console.print("2. Math")
        console.print("3. Physics")
        console.print("4. Logic")
        console.print("5. Statistics")
        console.print("6. Unit Conversion")
        console.print("7. Orbital Mechanics")
        console.print("8. Calculus")
        console.print("9. Geometry")
        console.print("10. Linear Algebra")
        console.print("11. Sequences and Series")
        console.print("12. Probability Distributions")
        console.print("13. Finance")
        console.print("0. Exit\n")

        choice = Prompt.ask("Select", choices=[str(i) for i in range(14)], show_choices=False)
        if choice == "0":
            console.print("\n[cyan]Goodbye.[/cyan]")
            return
        elif choice == "1":
            _electronics_menu()
        elif choice == "2":
            _math_menu()
        elif choice == "3":
            _physics_menu()
        elif choice == "4":
            _logic_menu()
        elif choice == "5":
            _statistics_menu()
        elif choice == "6":
            _menu_units()
        elif choice == "7":
            _orbital_menu()
        elif choice == "8":
            _menu_calculus()
        elif choice == "9":
            _menu_geometry()
        elif choice == "10":
            _menu_linalg()
        elif choice == "11":
            _menu_sequences()
        elif choice == "12":
            _menu_probability()
        elif choice == "13":
            _menu_finance()

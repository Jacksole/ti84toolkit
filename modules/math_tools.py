"""
Math module -- algebra tools, trigonometry, and equation solving.

V1 scope, per the original handoff doc: "Algebra tools / Trigonometry /
Equation solving." Equation solving is backed by sympy here, which gives
this port real symbolic-math capability the TI-84 BASIC version never had
(non-linear equations, exact fractions/radicals instead of decimal
approximations, etc.).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import sympy
from sympy.core.sympify import SympifyError

from core.validation import ValidationError

# ---------------------------------------------------------------------------
# Algebra: quadratic solver
# ---------------------------------------------------------------------------


@dataclass
class QuadraticResult:
    roots: tuple[complex, complex]
    discriminant: float
    nature: str  # "two real roots", "one repeated real root", "two complex roots"


def quadratic_solve(a: float, b: float, c: float) -> QuadraticResult:
    """Solve ax^2 + bx + c = 0 using the quadratic formula."""
    if a == 0:
        raise ValidationError("Coefficient 'a' cannot be zero (this would not be quadratic -- use linear solving).")

    discriminant = b**2 - 4 * a * c

    if discriminant > 0:
        sqrt_d = math.sqrt(discriminant)
        r1 = (-b + sqrt_d) / (2 * a)
        r2 = (-b - sqrt_d) / (2 * a)
        nature = "two real roots"
        roots = (complex(r1), complex(r2))
    elif discriminant == 0:
        r = -b / (2 * a)
        nature = "one repeated real root"
        roots = (complex(r), complex(r))
    else:
        sqrt_d = math.sqrt(-discriminant)
        real = -b / (2 * a)
        imag = sqrt_d / (2 * a)
        nature = "two complex roots"
        roots = (complex(real, imag), complex(real, -imag))

    return QuadraticResult(roots, discriminant, nature)


# ---------------------------------------------------------------------------
# Trigonometry
# ---------------------------------------------------------------------------

_TRIG_FUNCS = {
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
}


def trig_evaluate(function: str, value: float, unit: str = "deg") -> float:
    """Evaluate a trig function. `unit` applies to the input for sin/cos/tan,
    and to the output for asin/acos/atan (inverse functions)."""
    fn_name = function.strip().lower()
    unit = unit.strip().lower()

    if fn_name not in _TRIG_FUNCS:
        raise ValidationError(f"Unknown function '{function}'. Valid: {', '.join(_TRIG_FUNCS)}.")
    if unit not in ("deg", "rad"):
        raise ValidationError(f"Unit must be 'deg' or 'rad' (got '{unit}').")

    fn = _TRIG_FUNCS[fn_name]
    is_inverse = fn_name.startswith("a")

    try:
        if is_inverse:
            result = fn(value)
            return math.degrees(result) if unit == "deg" else result
        else:
            angle = math.radians(value) if unit == "deg" else value
            return fn(angle)
    except ValueError as e:
        raise ValidationError(f"Domain error evaluating {function}({value}): {e}")


# ---------------------------------------------------------------------------
# General equation solving (sympy-backed)
# ---------------------------------------------------------------------------


@dataclass
class EquationResult:
    variable: str
    solutions: list[str]  # stringified sympy solutions (keeps exact form, e.g. "sqrt(2)")


def solve_equation(equation: str, variable: str = "x") -> EquationResult:
    """Solve an equation string like '2*x + 3 = 7' or 'x**2 - 4 = 0' for the given variable.

    Accepts a single '=' to split LHS/RHS; if no '=' is present, assumes '... = 0'.
    """
    equation = equation.strip()
    if not equation:
        raise ValidationError("Equation cannot be empty.")

    if equation.count("=") > 1:
        raise ValidationError("Equation must contain at most one '=' sign.")

    try:
        var = sympy.symbols(variable)
    except Exception:
        raise ValidationError(f"'{variable}' is not a valid variable name.")

    try:
        if "=" in equation:
            lhs_str, rhs_str = equation.split("=")
            lhs = sympy.sympify(lhs_str.strip())
            rhs = sympy.sympify(rhs_str.strip())
            expr = sympy.Eq(lhs, rhs)
        else:
            expr = sympy.Eq(sympy.sympify(equation), 0)
    except (SympifyError, SyntaxError, TypeError) as e:
        raise ValidationError(f"Could not parse equation '{equation}': {e}")

    try:
        solutions = sympy.solve(expr, var)
    except NotImplementedError as e:
        raise ValidationError(f"sympy could not solve this equation: {e}")

    if not solutions:
        raise ValidationError(f"No solutions found for '{equation}' (or the variable '{variable}' doesn't appear).")

    return EquationResult(variable, [str(s) for s in solutions])

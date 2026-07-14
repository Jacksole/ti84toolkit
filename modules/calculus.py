"""
Calculus module -- symbolic differentiation, integration, limits, and Taylor
series, backed by sympy.

Distinct from the orbital mechanics module: orbital mechanics uses results
that were originally *derived* with calculus (vis-viva, Kepler's laws) but
only implements the pre-solved closed-form equations. This module lets the
user actually perform the calculus operations themselves.
"""
from __future__ import annotations

from dataclasses import dataclass

import sympy
from sympy.core.sympify import SympifyError

from core.validation import ValidationError


def _parse_expr(expr_str: str, variable: str):
    try:
        var = sympy.symbols(variable)
    except Exception:
        raise ValidationError(f"'{variable}' is not a valid variable name.")
    try:
        expr = sympy.sympify(expr_str)
    except (SympifyError, SyntaxError, TypeError) as e:
        raise ValidationError(f"Could not parse expression '{expr_str}': {e}")
    return expr, var


@dataclass
class DerivativeResult:
    expression: str
    variable: str
    order: int
    result: str


def derivative(expr_str: str, variable: str = "x", order: int = 1) -> DerivativeResult:
    """Compute the order-th derivative of expr_str with respect to variable."""
    if order < 1:
        raise ValidationError("Order must be at least 1.")
    expr, var = _parse_expr(expr_str, variable)
    try:
        result = sympy.diff(expr, var, order)
    except Exception as e:
        raise ValidationError(f"Could not differentiate '{expr_str}': {e}")
    return DerivativeResult(expr_str, variable, order, str(result))


@dataclass
class IntegralResult:
    expression: str
    variable: str
    lower: str | None
    upper: str | None
    result: str


def integral(
    expr_str: str, variable: str = "x", lower: float | None = None, upper: float | None = None
) -> IntegralResult:
    """Compute the indefinite integral, or the definite integral if both
    lower and upper bounds are given."""
    if (lower is None) != (upper is None):
        raise ValidationError("Provide both lower and upper bounds for a definite integral, or neither for indefinite.")

    expr, var = _parse_expr(expr_str, variable)
    try:
        if lower is None:
            result = sympy.integrate(expr, var)
            result_str = f"{result} + C"
        else:
            result = sympy.integrate(expr, (var, lower, upper))
            result_str = str(result)
    except Exception as e:
        raise ValidationError(f"Could not integrate '{expr_str}': {e}")

    return IntegralResult(expr_str, variable, str(lower) if lower is not None else None, str(upper) if upper is not None else None, result_str)


@dataclass
class LimitResult:
    expression: str
    variable: str
    point: str
    direction: str
    result: str


def limit(expr_str: str, variable: str = "x", point: float | str = 0, direction: str = "both") -> LimitResult:
    """Compute the limit of expr_str as variable approaches point.

    direction: 'both', 'left' (from below, '-'), or 'right' (from above, '+').
    point may be a number or 'oo'/'-oo' for infinity.
    """
    direction = direction.strip().lower()
    if direction not in ("both", "left", "right"):
        raise ValidationError("direction must be 'both', 'left', or 'right'.")

    expr, var = _parse_expr(expr_str, variable)
    try:
        point_val = sympy.sympify(point) if isinstance(point, str) else point
    except (SympifyError, SyntaxError, TypeError):
        raise ValidationError(f"Could not parse limit point '{point}'.")

    try:
        if direction == "both":
            result = sympy.limit(expr, var, point_val)
        elif direction == "left":
            result = sympy.limit(expr, var, point_val, dir="-")
        else:
            result = sympy.limit(expr, var, point_val, dir="+")
    except Exception as e:
        raise ValidationError(f"Could not compute limit of '{expr_str}': {e}")

    return LimitResult(expr_str, variable, str(point), direction, str(result))


@dataclass
class TaylorSeriesResult:
    expression: str
    variable: str
    point: float
    order: int
    result: str


def taylor_series(expr_str: str, variable: str = "x", point: float = 0, order: int = 5) -> TaylorSeriesResult:
    """Compute the Taylor series expansion of expr_str about `point`, up to `order`."""
    if order < 1:
        raise ValidationError("Order must be at least 1.")

    expr, var = _parse_expr(expr_str, variable)
    try:
        series = sympy.series(expr, var, point, order + 1).removeO()
    except Exception as e:
        raise ValidationError(f"Could not expand '{expr_str}' as a Taylor series: {e}")

    return TaylorSeriesResult(expr_str, variable, point, order, str(sympy.nsimplify(series)))

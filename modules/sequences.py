"""
Sequences and series module -- arithmetic and geometric sequences, their
nth terms, and partial/infinite sums. TI-84 has a dedicated SEQ graphing
mode for exactly this.
"""
from __future__ import annotations

from dataclasses import dataclass

from core.validation import ValidationError


def _check_positive_int(n: int, label: str) -> None:
    if n < 1:
        raise ValidationError(f"{label} must be a positive integer.")


# ---------------------------------------------------------------------------
# Arithmetic sequences: a_n = a1 + (n-1)*d
# ---------------------------------------------------------------------------


def arithmetic_nth_term(a1: float, d: float, n: int) -> float:
    """The nth term of an arithmetic sequence with first term a1 and common difference d."""
    _check_positive_int(n, "n")
    return a1 + (n - 1) * d


def arithmetic_sum(a1: float, d: float, n: int) -> float:
    """Sum of the first n terms of an arithmetic sequence: S_n = n/2 * (2*a1 + (n-1)*d)."""
    _check_positive_int(n, "n")
    return n / 2 * (2 * a1 + (n - 1) * d)


# ---------------------------------------------------------------------------
# Geometric sequences: a_n = a1 * r^(n-1)
# ---------------------------------------------------------------------------


def geometric_nth_term(a1: float, r: float, n: int) -> float:
    """The nth term of a geometric sequence with first term a1 and common ratio r."""
    _check_positive_int(n, "n")
    return a1 * r ** (n - 1)


def geometric_sum(a1: float, r: float, n: int) -> float:
    """Sum of the first n terms of a geometric sequence.

    S_n = a1 * n                    if r == 1
    S_n = a1 * (1 - r^n) / (1 - r)  otherwise
    """
    _check_positive_int(n, "n")
    if r == 1:
        return a1 * n
    return a1 * (1 - r**n) / (1 - r)


@dataclass
class InfiniteSumResult:
    a1: float
    r: float
    sum: float


def geometric_sum_infinite(a1: float, r: float) -> InfiniteSumResult:
    """Sum of an infinite geometric series: S = a1 / (1 - r), only convergent for |r| < 1."""
    if abs(r) >= 1:
        raise ValidationError(f"An infinite geometric series only converges for |r| < 1 (got r = {r:g}).")
    return InfiniteSumResult(a1, r, a1 / (1 - r))

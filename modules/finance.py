"""
Finance module -- Time Value of Money (TVM) solver, matching the TI-84's
built-in Finance app (APPS -> Finance -> TVM Solver), plus a simpler
standalone compound interest calculator for the common no-payments case.

Sign convention (standard financial-calculator convention, matching the
TI-84): cash you pay out is negative, cash you receive is positive. A loan
you take out is a positive PV (you receive it) with negative PMT (you pay
it back); a savings account is a negative PV (you deposit it) with a
positive FV (you receive it back later).

TVM equation (ordinary annuity when begin=False, annuity due when begin=True):
    PV*(1+i)^N + PMT*(1+i*k)*((1+i)^N - 1)/i + FV = 0   (i != 0)
    PV + PMT*N + FV = 0                                  (i == 0)
where i is the periodic interest rate (decimal) and k = 1 if begin else 0.

Solving for N, PV, PMT, or FV is closed-form (algebra). Solving for the
interest rate has no closed form -- solved via bisection, in the same
iterative-root-finding spirit as Kepler's equation elsewhere in this toolkit.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from core.validation import ValidationError, require_exactly_n_known


def _tvm_balance(pv: float, pmt: float, fv: float, i: float, n: float, k: int) -> float:
    if abs(i) < 1e-12:
        return pv + pmt * n + fv
    factor = (1 + i) ** n
    return pv * factor + pmt * (1 + i * k) * (factor - 1) / i + fv


def _solve_rate_bisection(pv: float, pmt: float, fv: float, n: float, k: int) -> float:
    lo, hi = -0.999999, 10.0
    f_lo = _tvm_balance(pv, pmt, fv, lo, n, k)
    f_hi = _tvm_balance(pv, pmt, fv, hi, n, k)

    if f_lo == 0:
        return lo
    if f_hi == 0:
        return hi
    if (f_lo > 0) == (f_hi > 0):
        raise ValidationError(
            "Could not find an interest rate solution in a reasonable range "
            "(-99.9999% to 1000% per period) -- check your cash flow signs."
        )

    for _ in range(200):
        mid = (lo + hi) / 2
        f_mid = _tvm_balance(pv, pmt, fv, mid, n, k)
        if abs(f_mid) < 1e-12 or (hi - lo) < 1e-14:
            return mid
        if (f_mid > 0) == (f_lo > 0):
            lo, f_lo = mid, f_mid
        else:
            hi, f_hi = mid, f_mid
    return (lo + hi) / 2


@dataclass
class TVMResult:
    n: float
    rate_percent: float
    pv: float
    pmt: float
    fv: float
    solved_for: str
    steps: list[str]


def solve_tvm(
    n: float | None = None,
    rate_percent: float | None = None,
    pv: float | None = None,
    pmt: float | None = None,
    fv: float | None = None,
    payments_per_year: int = 12,
    begin: bool = False,
) -> TVMResult:
    """Solve for whichever ONE of n, rate_percent, pv, pmt, fv is left as None,
    given the other four."""
    known = {"n": n, "rate_percent": rate_percent, "pv": pv, "pmt": pmt, "fv": fv}
    require_exactly_n_known(known, 4, "TVM")

    if payments_per_year < 1:
        raise ValidationError("payments_per_year must be at least 1.")

    unknown = next(name for name, val in known.items() if val is None)
    k = 1 if begin else 0
    steps = [f"Solving for {unknown}, {payments_per_year} payments/year, {'annuity due' if begin else 'ordinary annuity'}"]

    if unknown == "rate_percent":
        i = _solve_rate_bisection(pv, pmt, fv, n, k)
        rate_percent = i * payments_per_year * 100
        steps.append(f"Periodic rate found via bisection: i = {i:g} -> annual rate = {rate_percent:g}%")
    else:
        i = (rate_percent / 100) / payments_per_year
        steps.append(f"Periodic rate: i = ({rate_percent:g}/100) / {payments_per_year} = {i:g}")

        if unknown == "n":
            if abs(i) < 1e-12:
                if pmt == 0:
                    raise ValidationError("Cannot solve for n when rate is 0 and pmt is 0 (n is undetermined).")
                n = -(pv + fv) / pmt
            else:
                annuity_factor = (1 + i * k) / i
                denom = pv + pmt * annuity_factor
                numer = pmt * annuity_factor - fv
                if denom == 0:
                    raise ValidationError("Cannot solve for n -- this combination of values has no solution.")
                factor = numer / denom
                if factor <= 0:
                    raise ValidationError("Cannot solve for n -- these values imply a negative or zero growth factor.")
                n = math.log(factor) / math.log(1 + i)
            steps.append(f"n = {n:g} periods")

        elif unknown == "pv":
            if abs(i) < 1e-12:
                pv = -(fv + pmt * n)
            else:
                factor = (1 + i) ** n
                pv = -(fv + pmt * (1 + i * k) * (factor - 1) / i) / factor
            steps.append(f"pv = {pv:g}")

        elif unknown == "fv":
            if abs(i) < 1e-12:
                fv = -(pv + pmt * n)
            else:
                factor = (1 + i) ** n
                fv = -(pv * factor + pmt * (1 + i * k) * (factor - 1) / i)
            steps.append(f"fv = {fv:g}")

        elif unknown == "pmt":
            if abs(i) < 1e-12:
                pmt = -(pv + fv) / n
            else:
                factor = (1 + i) ** n
                pmt = -(pv * factor + fv) / ((1 + i * k) * (factor - 1) / i)
            steps.append(f"pmt = {pmt:g}")

    return TVMResult(n, rate_percent, pv, pmt, fv, unknown, steps)


# ---------------------------------------------------------------------------
# Simple compound interest (no payments) -- a friendlier entry point for the
# common case, alongside the fully general TVM solver above.
# ---------------------------------------------------------------------------


@dataclass
class CompoundInterestResult:
    principal: float
    future_value: float
    interest_earned: float


def compound_interest(principal: float, annual_rate_percent: float, compounds_per_year: int, years: float) -> CompoundInterestResult:
    """Future value of a lump-sum deposit under compound interest (no recurring payments)."""
    if principal <= 0:
        raise ValidationError("Principal must be positive.")
    if compounds_per_year < 1:
        raise ValidationError("compounds_per_year must be at least 1.")
    if years <= 0:
        raise ValidationError("Years must be positive.")

    i = (annual_rate_percent / 100) / compounds_per_year
    n = compounds_per_year * years
    fv = principal * (1 + i) ** n
    return CompoundInterestResult(principal, fv, fv - principal)

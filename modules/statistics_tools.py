"""
Statistics module -- explicitly called out as "deferred" in the original
handoff doc's V1 Known Limitations ("No statistics module (deferred)").
Feasible now that memory isn't a constraint.

Covers:
  - Descriptive statistics (mean, median, mode, variance, std dev, range)
  - Five-number summary / quartiles (for box-plot style analysis)
  - Combinatorics (nPr, nCr, factorial) -- a callback to the TI-84's
    physical nPr/nCr buttons
"""
from __future__ import annotations

import math
import statistics as _stats
from dataclasses import dataclass

from core.validation import ValidationError

# ---------------------------------------------------------------------------
# Descriptive statistics
# ---------------------------------------------------------------------------


@dataclass
class DescriptiveStats:
    count: int
    sum: float
    mean: float
    median: float
    mode: list[float]  # can be multimodal
    variance_sample: float | None   # None when count < 2
    stdev_sample: float | None
    variance_population: float
    stdev_population: float
    minimum: float
    maximum: float
    data_range: float


def describe(data: list[float]) -> DescriptiveStats:
    """Compute standard descriptive statistics for a dataset."""
    if not data:
        raise ValidationError("Dataset cannot be empty.")

    n = len(data)
    mean = _stats.mean(data)
    median = _stats.median(data)

    try:
        modes = _stats.multimode(data)
        # If every value is unique, multimode returns all of them -- not meaningfully "the mode".
        if len(modes) == n:
            modes = []
    except _stats.StatisticsError:
        modes = []

    variance_sample = _stats.variance(data) if n >= 2 else None
    stdev_sample = _stats.stdev(data) if n >= 2 else None
    variance_population = _stats.pvariance(data)
    stdev_population = _stats.pstdev(data)

    return DescriptiveStats(
        count=n,
        sum=sum(data),
        mean=mean,
        median=median,
        mode=sorted(modes),
        variance_sample=variance_sample,
        stdev_sample=stdev_sample,
        variance_population=variance_population,
        stdev_population=stdev_population,
        minimum=min(data),
        maximum=max(data),
        data_range=max(data) - min(data),
    )


# ---------------------------------------------------------------------------
# Quartiles / five-number summary
# ---------------------------------------------------------------------------


@dataclass
class FiveNumberSummary:
    minimum: float
    q1: float
    median: float
    q3: float
    maximum: float
    iqr: float


def five_number_summary(data: list[float]) -> FiveNumberSummary:
    """Compute the five-number summary (min, Q1, median, Q3, max) using the
    exclusive median method (same convention as most stats textbooks and the
    TI-84's own 1-Var Stats)."""
    if len(data) < 2:
        raise ValidationError("Need at least 2 data points to compute quartiles.")

    sorted_data = sorted(data)
    n = len(sorted_data)
    median = _stats.median(sorted_data)

    mid = n // 2
    lower_half = sorted_data[:mid]
    upper_half = sorted_data[mid + (n % 2):]

    q1 = _stats.median(lower_half)
    q3 = _stats.median(upper_half)

    return FiveNumberSummary(
        minimum=sorted_data[0],
        q1=q1,
        median=median,
        q3=q3,
        maximum=sorted_data[-1],
        iqr=q3 - q1,
    )


# ---------------------------------------------------------------------------
# Combinatorics
# ---------------------------------------------------------------------------


def _validate_nr(n: int, r: int) -> None:
    if n < 0 or r < 0:
        raise ValidationError("n and r must both be non-negative.")
    if r > n:
        raise ValidationError(f"r ({r}) cannot be greater than n ({n}).")


def factorial(n: int) -> int:
    if n < 0:
        raise ValidationError("n must be non-negative.")
    return math.factorial(n)


def permutations(n: int, r: int) -> int:
    """nPr -- number of ordered arrangements of r items from n."""
    _validate_nr(n, r)
    return math.factorial(n) // math.factorial(n - r)


def combinations(n: int, r: int) -> int:
    """nCr -- number of unordered selections of r items from n."""
    _validate_nr(n, r)
    return math.comb(n, r)

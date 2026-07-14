"""
Probability distributions module -- binomial and normal distributions.

Distinct from the statistics module, which covers descriptive stats
(mean/median/mode/variance) and combinatorics (nPr/nCr). Distributions are a
different, commonly-taught piece: TI-84's normalcdf/invNorm/binompdf are
staples of any AP Statistics course, and combinatorics alone doesn't cover
that ground.

Uses Python's built-in statistics.NormalDist (3.8+) for the normal
distribution -- no extra dependency needed.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist

from core.validation import ValidationError

# ---------------------------------------------------------------------------
# Binomial distribution
# ---------------------------------------------------------------------------


def _check_binomial_params(n: int, k: int, p: float) -> None:
    if n < 0:
        raise ValidationError("n must be non-negative.")
    if k < 0 or k > n:
        raise ValidationError(f"k must be between 0 and n (got k={k}, n={n}).")
    if not (0 <= p <= 1):
        raise ValidationError("p (probability of success) must be between 0 and 1.")


def binomial_pmf(n: int, k: int, p: float) -> float:
    """P(X = k) for X ~ Binomial(n, p): C(n,k) * p^k * (1-p)^(n-k)."""
    _check_binomial_params(n, k, p)
    return math.comb(n, k) * p**k * (1 - p) ** (n - k)


def binomial_cdf(n: int, k: int, p: float) -> float:
    """P(X <= k) for X ~ Binomial(n, p): sum of the pmf from 0 to k."""
    _check_binomial_params(n, k, p)
    return sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k + 1))


@dataclass
class BinomialStats:
    n: int
    p: float
    mean: float
    variance: float
    stdev: float


def binomial_stats(n: int, p: float) -> BinomialStats:
    """Mean, variance, and standard deviation of X ~ Binomial(n, p)."""
    if n < 0:
        raise ValidationError("n must be non-negative.")
    if not (0 <= p <= 1):
        raise ValidationError("p must be between 0 and 1.")
    mean = n * p
    variance = n * p * (1 - p)
    return BinomialStats(n, p, mean, variance, math.sqrt(variance))


# ---------------------------------------------------------------------------
# Normal distribution
# ---------------------------------------------------------------------------


def _check_stdev(stdev: float) -> None:
    if stdev <= 0:
        raise ValidationError("Standard deviation must be positive.")


def normal_pdf(x: float, mean: float = 0, stdev: float = 1) -> float:
    _check_stdev(stdev)
    return NormalDist(mean, stdev).pdf(x)


def normal_cdf(x: float, mean: float = 0, stdev: float = 1) -> float:
    """P(X <= x) for X ~ Normal(mean, stdev)."""
    _check_stdev(stdev)
    return NormalDist(mean, stdev).cdf(x)


def normal_cdf_range(low: float, high: float, mean: float = 0, stdev: float = 1) -> float:
    """P(low <= X <= high) for X ~ Normal(mean, stdev)."""
    _check_stdev(stdev)
    if low > high:
        raise ValidationError("low must be <= high.")
    dist = NormalDist(mean, stdev)
    return dist.cdf(high) - dist.cdf(low)


def inverse_normal_cdf(p: float, mean: float = 0, stdev: float = 1) -> float:
    """The x such that P(X <= x) = p -- i.e. the inverse CDF (TI-84's invNorm)."""
    _check_stdev(stdev)
    if not (0 < p < 1):
        raise ValidationError("p must be strictly between 0 and 1.")
    return NormalDist(mean, stdev).inv_cdf(p)


def z_score(x: float, mean: float, stdev: float) -> float:
    _check_stdev(stdev)
    return (x - mean) / stdev

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.validation import ValidationError
from modules import probability


class TestBinomial:
    def test_pmf_fair_coin(self):
        # P(exactly 5 heads in 10 fair coin flips)
        result = probability.binomial_pmf(10, 5, 0.5)
        assert math.isclose(result, 0.24609375)

    def test_cdf_equals_sum_of_pmf(self):
        cdf = probability.binomial_cdf(10, 3, 0.5)
        manual = sum(probability.binomial_pmf(10, k, 0.5) for k in range(4))
        assert math.isclose(cdf, manual)

    def test_cdf_at_n_equals_1(self):
        assert math.isclose(probability.binomial_cdf(5, 5, 0.3), 1.0)

    def test_stats(self):
        # Binomial(20, 0.5): mean=10, variance=5
        result = probability.binomial_stats(20, 0.5)
        assert math.isclose(result.mean, 10)
        assert math.isclose(result.variance, 5)
        assert math.isclose(result.stdev, math.sqrt(5))

    def test_rejects_k_greater_than_n(self):
        with pytest.raises(ValidationError):
            probability.binomial_pmf(5, 10, 0.5)

    def test_rejects_invalid_probability(self):
        with pytest.raises(ValidationError):
            probability.binomial_pmf(5, 2, 1.5)
        with pytest.raises(ValidationError):
            probability.binomial_pmf(5, 2, -0.1)


class TestNormal:
    def test_standard_normal_cdf_at_mean(self):
        assert math.isclose(probability.normal_cdf(0, 0, 1), 0.5)

    def test_standard_normal_cdf_1_96(self):
        # classic 95% two-tailed z-value
        assert math.isclose(probability.normal_cdf(1.96, 0, 1), 0.975, abs_tol=1e-4)

    def test_cdf_range_68_percent_rule(self):
        # ~68% of a normal distribution falls within 1 stdev of the mean
        result = probability.normal_cdf_range(-1, 1, 0, 1)
        assert math.isclose(result, 0.6827, abs_tol=1e-3)

    def test_inverse_cdf_roundtrip(self):
        p = 0.975
        x = probability.inverse_normal_cdf(p, 0, 1)
        assert math.isclose(probability.normal_cdf(x, 0, 1), p, abs_tol=1e-9)

    def test_z_score(self):
        assert probability.z_score(85, 75, 5) == 2.0

    def test_rejects_nonpositive_stdev(self):
        with pytest.raises(ValidationError):
            probability.normal_cdf(0, 0, 0)
        with pytest.raises(ValidationError):
            probability.z_score(1, 0, -1)

    def test_inverse_cdf_rejects_out_of_range_p(self):
        with pytest.raises(ValidationError):
            probability.inverse_normal_cdf(1.5)
        with pytest.raises(ValidationError):
            probability.inverse_normal_cdf(0)

    def test_cdf_range_rejects_low_greater_than_high(self):
        with pytest.raises(ValidationError):
            probability.normal_cdf_range(5, 1)

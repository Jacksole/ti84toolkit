import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.validation import ValidationError
from modules import calculus


class TestDerivative:
    def test_power_rule(self):
        result = calculus.derivative("x**3", "x")
        assert result.result == "3*x**2"

    def test_second_order(self):
        result = calculus.derivative("x**3", "x", order=2)
        assert result.result == "6*x"

    def test_trig_derivative(self):
        result = calculus.derivative("sin(x)", "x")
        assert result.result == "cos(x)"

    def test_rejects_order_below_1(self):
        with pytest.raises(ValidationError):
            calculus.derivative("x**2", "x", order=0)

    def test_unparseable_expression_raises(self):
        with pytest.raises(ValidationError):
            calculus.derivative("x @@ 2 ##", "x")


class TestIntegral:
    def test_indefinite(self):
        result = calculus.integral("x**2", "x")
        assert result.result == "x**3/3 + C"

    def test_definite(self):
        result = calculus.integral("x**2", "x", lower=0, upper=3)
        assert result.result == "9"

    def test_definite_requires_both_bounds(self):
        with pytest.raises(ValidationError):
            calculus.integral("x**2", "x", lower=0, upper=None)

    def test_trig_integral(self):
        result = calculus.integral("cos(x)", "x")
        assert result.result == "sin(x) + C"


class TestLimit:
    def test_simple_limit(self):
        result = calculus.limit("x**2", "x", 3)
        assert result.result == "9"

    def test_classic_sinx_over_x_limit(self):
        result = calculus.limit("sin(x)/x", "x", 0)
        assert result.result == "1"

    def test_limit_at_infinity(self):
        result = calculus.limit("1/x", "x", "oo")
        assert result.result == "0"

    def test_invalid_direction_raises(self):
        with pytest.raises(ValidationError):
            calculus.limit("x**2", "x", 0, direction="sideways")

    def test_one_sided_limit(self):
        result = calculus.limit("1/x", "x", 0, direction="right")
        assert result.result == "oo"


class TestTaylorSeries:
    def test_exp_series_at_zero(self):
        result = calculus.taylor_series("exp(x)", "x", 0, order=4)
        # e^x = 1 + x + x^2/2 + x^3/6 + x^4/24 + ...
        assert "1" in result.result and "x" in result.result

    def test_rejects_order_below_1(self):
        with pytest.raises(ValidationError):
            calculus.taylor_series("sin(x)", "x", 0, order=0)

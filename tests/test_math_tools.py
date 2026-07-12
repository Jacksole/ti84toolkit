import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.validation import ValidationError
from modules import math_tools


class TestQuadraticSolve:
    def test_two_real_roots(self):
        # x^2 - 5x + 6 = 0 -> roots 2, 3
        result = math_tools.quadratic_solve(1, -5, 6)
        assert result.nature == "two real roots"
        roots_real = sorted(r.real for r in result.roots)
        assert math.isclose(roots_real[0], 2.0)
        assert math.isclose(roots_real[1], 3.0)

    def test_repeated_root(self):
        # x^2 - 4x + 4 = 0 -> repeated root 2
        result = math_tools.quadratic_solve(1, -4, 4)
        assert result.nature == "one repeated real root"
        assert math.isclose(result.roots[0].real, 2.0)
        assert math.isclose(result.roots[1].real, 2.0)

    def test_complex_roots(self):
        # x^2 + 1 = 0 -> roots +-i
        result = math_tools.quadratic_solve(1, 0, 1)
        assert result.nature == "two complex roots"
        assert math.isclose(result.roots[0].imag, 1.0)
        assert math.isclose(result.roots[1].imag, -1.0)

    def test_a_zero_raises(self):
        with pytest.raises(ValidationError):
            math_tools.quadratic_solve(0, 2, 3)


class TestTrigEvaluate:
    def test_sin_90_degrees(self):
        assert math.isclose(math_tools.trig_evaluate("sin", 90, "deg"), 1.0, abs_tol=1e-9)

    def test_cos_0_degrees(self):
        assert math.isclose(math_tools.trig_evaluate("cos", 0, "deg"), 1.0, abs_tol=1e-9)

    def test_sin_radians(self):
        assert math.isclose(math_tools.trig_evaluate("sin", math.pi / 2, "rad"), 1.0, abs_tol=1e-9)

    def test_asin_returns_degrees_by_default(self):
        assert math.isclose(math_tools.trig_evaluate("asin", 1, "deg"), 90.0, abs_tol=1e-9)

    def test_asin_returns_radians_when_requested(self):
        assert math.isclose(math_tools.trig_evaluate("asin", 1, "rad"), math.pi / 2, abs_tol=1e-9)

    def test_unknown_function_raises(self):
        with pytest.raises(ValidationError):
            math_tools.trig_evaluate("sec", 45, "deg")

    def test_invalid_unit_raises(self):
        with pytest.raises(ValidationError):
            math_tools.trig_evaluate("sin", 45, "gradians")

    def test_asin_domain_error(self):
        with pytest.raises(ValidationError):
            math_tools.trig_evaluate("asin", 2, "deg")  # outside [-1, 1]


class TestSolveEquation:
    def test_linear_equation(self):
        result = math_tools.solve_equation("2*x + 3 = 7", "x")
        assert result.solutions == ["2"]

    def test_quadratic_via_sympy(self):
        result = math_tools.solve_equation("x**2 - 4 = 0", "x")
        assert set(result.solutions) == {"-2", "2"}

    def test_implicit_zero_rhs(self):
        result = math_tools.solve_equation("x - 10", "x")
        assert result.solutions == ["10"]

    def test_empty_equation_raises(self):
        with pytest.raises(ValidationError):
            math_tools.solve_equation("", "x")

    def test_multiple_equals_raises(self):
        with pytest.raises(ValidationError):
            math_tools.solve_equation("x = 2 = 3", "x")

    def test_no_solution_variable_absent_raises(self):
        with pytest.raises(ValidationError):
            math_tools.solve_equation("5 = 5", "x")

    def test_unparseable_equation_raises(self):
        with pytest.raises(ValidationError):
            math_tools.solve_equation("2x +++ = ", "x")

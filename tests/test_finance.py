import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.validation import ValidationError
from modules import finance


class TestCompoundInterest:
    def test_basic_growth(self):
        result = finance.compound_interest(1000, 5, 1, 10)
        assert math.isclose(result.future_value, 1000 * 1.05**10)

    def test_interest_earned(self):
        result = finance.compound_interest(1000, 5, 1, 10)
        assert math.isclose(result.interest_earned, result.future_value - 1000)

    def test_rejects_nonpositive_principal(self):
        with pytest.raises(ValidationError):
            finance.compound_interest(0, 5, 1, 10)

    def test_rejects_nonpositive_years(self):
        with pytest.raises(ValidationError):
            finance.compound_interest(1000, 5, 1, 0)


class TestTVMSolver:
    def test_requires_exactly_four_known(self):
        with pytest.raises(ValidationError):
            finance.solve_tvm(n=10, rate_percent=5, pv=-1000)
        with pytest.raises(ValidationError):
            finance.solve_tvm(n=10, rate_percent=5, pv=-1000, pmt=0, fv=1000)

    def test_solve_fv_matches_compound_interest(self):
        result = finance.solve_tvm(n=60, rate_percent=6, pv=-1000, pmt=0, payments_per_year=12)
        expected = finance.compound_interest(1000, 6, 12, 5).future_value
        assert math.isclose(result.fv, expected, rel_tol=1e-9)

    def test_mortgage_payment_sanity_check(self):
        # $300,000 30-year mortgage at 6% annual (monthly payments) ->
        # real-world monthly payment is well-known to be ~$1,798-1,799
        result = finance.solve_tvm(n=360, rate_percent=6, pv=300_000, fv=0, payments_per_year=12)
        assert 1_790 < abs(result.pmt) < 1_810

    def test_solve_for_n_roundtrip(self):
        fv_result = finance.solve_tvm(n=24, rate_percent=5, pv=-1000, pmt=-50, payments_per_year=12)
        n_result = finance.solve_tvm(rate_percent=5, pv=-1000, pmt=-50, fv=fv_result.fv, payments_per_year=12)
        assert math.isclose(n_result.n, 24, rel_tol=1e-6)

    def test_solve_for_rate_roundtrip(self):
        fv_result = finance.solve_tvm(n=36, rate_percent=7, pv=-2000, pmt=-100, payments_per_year=12)
        rate_result = finance.solve_tvm(n=36, pv=-2000, pmt=-100, fv=fv_result.fv, payments_per_year=12)
        assert math.isclose(rate_result.rate_percent, 7, rel_tol=1e-4)

    def test_solve_for_pmt(self):
        result = finance.solve_tvm(n=360, rate_percent=6, pv=300_000, fv=0, payments_per_year=12)
        recheck = finance.solve_tvm(n=360, rate_percent=6, pv=300_000, pmt=result.pmt, payments_per_year=12)
        assert math.isclose(recheck.fv, 0, abs_tol=1e-4)

    def test_zero_rate_case(self):
        result = finance.solve_tvm(n=10, rate_percent=0, pv=-1000, pmt=-50, payments_per_year=12)
        assert math.isclose(result.fv, -(-1000 + -50 * 10))

    def test_steps_present(self):
        result = finance.solve_tvm(n=360, rate_percent=6, pv=300_000, fv=0, payments_per_year=12)
        assert len(result.steps) > 0

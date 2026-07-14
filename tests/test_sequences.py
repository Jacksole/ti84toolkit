import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.validation import ValidationError
from modules import sequences


class TestArithmetic:
    def test_nth_term(self):
        # 2, 5, 8, 11, ... a1=2, d=3 -> 5th term = 14
        assert sequences.arithmetic_nth_term(2, 3, 5) == 14

    def test_sum(self):
        # 1+2+3+...+10 = 55
        assert sequences.arithmetic_sum(1, 1, 10) == 55

    def test_rejects_nonpositive_n(self):
        with pytest.raises(ValidationError):
            sequences.arithmetic_nth_term(1, 1, 0)


class TestGeometric:
    def test_nth_term(self):
        # 3, 6, 12, 24, ... a1=3, r=2 -> 4th term = 24
        assert sequences.geometric_nth_term(3, 2, 4) == 24

    def test_sum(self):
        # 1+2+4+8+16 = 31
        assert sequences.geometric_sum(1, 2, 5) == 31

    def test_sum_ratio_1(self):
        # r=1 -> every term equals a1, sum = a1*n
        assert sequences.geometric_sum(5, 1, 4) == 20

    def test_infinite_sum(self):
        # 1 + 1/2 + 1/4 + ... = 2
        result = sequences.geometric_sum_infinite(1, 0.5)
        assert math.isclose(result.sum, 2.0)

    def test_infinite_sum_diverges_raises(self):
        with pytest.raises(ValidationError):
            sequences.geometric_sum_infinite(1, 1.5)
        with pytest.raises(ValidationError):
            sequences.geometric_sum_infinite(1, -1)

    def test_rejects_nonpositive_n(self):
        with pytest.raises(ValidationError):
            sequences.geometric_sum(1, 2, -1)

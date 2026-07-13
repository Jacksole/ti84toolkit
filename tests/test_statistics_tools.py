import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.validation import ValidationError
from modules import statistics_tools as stats


class TestDescribe:
    def test_basic_stats(self):
        result = stats.describe([2, 4, 4, 4, 5, 5, 7, 9])
        assert result.count == 8
        assert math.isclose(result.mean, 5.0)
        assert math.isclose(result.median, 4.5)
        assert result.mode == [4]
        assert result.minimum == 2
        assert result.maximum == 9
        assert result.data_range == 7

    def test_known_variance_stdev(self):
        # Simple dataset with well-known population variance = 2, stdev = sqrt(2)
        result = stats.describe([1, 2, 3, 4, 5])
        assert math.isclose(result.variance_population, 2.0)
        assert math.isclose(result.stdev_population, math.sqrt(2))
        assert math.isclose(result.mean, 3.0)

    def test_single_value_has_no_sample_variance(self):
        result = stats.describe([5])
        assert result.variance_sample is None
        assert result.stdev_sample is None
        assert result.variance_population == 0
        assert result.mean == 5

    def test_multimodal(self):
        result = stats.describe([1, 1, 2, 2, 3])
        assert result.mode == [1, 2]

    def test_no_meaningful_mode_when_all_unique(self):
        result = stats.describe([1, 2, 3, 4])
        assert result.mode == []

    def test_empty_data_raises(self):
        with pytest.raises(ValidationError):
            stats.describe([])


class TestFiveNumberSummary:
    def test_odd_length_dataset(self):
        # Classic textbook example
        result = stats.five_number_summary([1, 2, 3, 4, 5, 6, 7])
        assert result.minimum == 1
        assert result.median == 4
        assert result.maximum == 7
        assert result.q1 == 2
        assert result.q3 == 6
        assert result.iqr == 4

    def test_even_length_dataset(self):
        result = stats.five_number_summary([1, 2, 3, 4, 5, 6])
        assert result.median == 3.5
        assert result.q1 == 2
        assert result.q3 == 5

    def test_unsorted_input_is_handled(self):
        result = stats.five_number_summary([5, 1, 4, 2, 3])
        assert result.minimum == 1
        assert result.maximum == 5

    def test_requires_at_least_two_points(self):
        with pytest.raises(ValidationError):
            stats.five_number_summary([1])


class TestCombinatorics:
    def test_factorial(self):
        assert stats.factorial(5) == 120
        assert stats.factorial(0) == 1

    def test_factorial_negative_raises(self):
        with pytest.raises(ValidationError):
            stats.factorial(-1)

    def test_permutations(self):
        # 5P2 = 20
        assert stats.permutations(5, 2) == 20

    def test_combinations(self):
        # 5C2 = 10
        assert stats.combinations(5, 2) == 10

    def test_r_greater_than_n_raises(self):
        with pytest.raises(ValidationError):
            stats.permutations(3, 5)
        with pytest.raises(ValidationError):
            stats.combinations(3, 5)

    def test_negative_values_raise(self):
        with pytest.raises(ValidationError):
            stats.permutations(-1, 2)
        with pytest.raises(ValidationError):
            stats.combinations(5, -2)

    def test_r_equals_n(self):
        assert stats.permutations(4, 4) == 24
        assert stats.combinations(4, 4) == 1

    def test_r_equals_zero(self):
        assert stats.permutations(5, 0) == 1
        assert stats.combinations(5, 0) == 1

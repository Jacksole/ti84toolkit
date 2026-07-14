import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.validation import ValidationError
from modules import resistor_bom


class TestStandardValues:
    def test_e24_includes_known_values(self):
        values = resistor_bom.standard_values("E24", min_decade=2, max_decade=2)
        assert 100.0 in values
        assert 220.0 in values
        assert 470.0 in values

    def test_e12_is_subset_of_e24_pattern(self):
        e12 = resistor_bom.standard_values("E12", min_decade=2, max_decade=2)
        assert 100.0 in e12
        assert 220.0 in e12
        # E12 shouldn't have E24-only values like 240
        assert 240.0 not in e12

    def test_unknown_series_raises(self):
        with pytest.raises(ValidationError):
            resistor_bom.standard_values("E96")

    def test_values_sorted_ascending(self):
        values = resistor_bom.standard_values("E24", min_decade=0, max_decade=1)
        assert values == sorted(values)


class TestFindResistorCombo:
    def test_exact_standard_value_found_as_single(self):
        # 4.7k is a standard E24 value -- should be found with ~0% error
        options = resistor_bom.find_resistor_combo(4700, series="E24")
        single = next(o for o in options if o.kind == "single")
        assert math.isclose(single.achieved_ohms, 4700, rel_tol=1e-6)
        assert single.error_pct < 0.01

    def test_returns_single_series_and_parallel(self):
        options = resistor_bom.find_resistor_combo(3300)
        kinds = {o.kind for o in options}
        assert "single" in kinds
        assert "series" in kinds
        assert "parallel" in kinds

    def test_results_sorted_by_error(self):
        options = resistor_bom.find_resistor_combo(1234)
        errors = [o.error_pct for o in options]
        assert errors == sorted(errors)

    def test_series_pair_sums_correctly(self):
        options = resistor_bom.find_resistor_combo(3300)
        series_opt = next(o for o in options if o.kind == "series")
        assert math.isclose(sum(series_opt.values), series_opt.achieved_ohms, rel_tol=1e-6)

    def test_parallel_pair_computed_correctly(self):
        options = resistor_bom.find_resistor_combo(3300)
        par_opt = next(o for o in options if o.kind == "parallel")
        r1, r2 = par_opt.values
        expected = (r1 * r2) / (r1 + r2)
        assert math.isclose(expected, par_opt.achieved_ohms, rel_tol=1e-6)

    def test_nonpositive_target_raises(self):
        with pytest.raises(ValidationError):
            resistor_bom.find_resistor_combo(0)
        with pytest.raises(ValidationError):
            resistor_bom.find_resistor_combo(-100)

    def test_top_n_limits_results(self):
        options = resistor_bom.find_resistor_combo(1000, top_n=2)
        assert len(options) <= 2


class TestFormatOption:
    def test_single_format(self):
        option = resistor_bom.BomOption("single", [4700], 4700, 0.0)
        result = resistor_bom.format_option(option)
        assert "single" in result
        assert "4.7k" in result

    def test_series_format_uses_plus(self):
        option = resistor_bom.BomOption("series", [1000, 2200], 3200, 3.03)
        result = resistor_bom.format_option(option)
        assert "+" in result

    def test_parallel_format_uses_double_bar(self):
        option = resistor_bom.BomOption("parallel", [1000, 1000], 500, 0.0)
        result = resistor_bom.format_option(option)
        assert "||" in result

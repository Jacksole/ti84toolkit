import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.validation import ValidationError
from modules import units


class TestLinearConversions:
    def test_length_km_to_m(self):
        result = units.convert("length", 1, "km", "m")
        assert math.isclose(result.result, 1000)

    def test_length_in_to_cm(self):
        result = units.convert("length", 1, "in", "cm")
        assert math.isclose(result.result, 2.54)

    def test_mass_lb_to_kg(self):
        result = units.convert("mass", 1, "lb", "kg")
        assert math.isclose(result.result, 0.45359237)

    def test_time_hr_to_s(self):
        result = units.convert("time", 1, "hr", "s")
        assert math.isclose(result.result, 3600)

    def test_resistance_kohm_to_ohm(self):
        result = units.convert("resistance", 2.2, "kohm", "ohm")
        assert math.isclose(result.result, 2200)

    def test_voltage_millivolt_to_volt(self):
        result = units.convert("voltage", 500, "millivolt", "volt")
        assert math.isclose(result.result, 0.5)

    def test_current_amp_to_milliamp(self):
        result = units.convert("current", 1.5, "amp", "milliamp")
        assert math.isclose(result.result, 1500)

    def test_round_trip_identity(self):
        result = units.convert("length", 100, "m", "ft")
        back = units.convert("length", result.result, "ft", "m")
        assert math.isclose(back.result, 100, rel_tol=1e-9)

    def test_unknown_category_raises(self):
        with pytest.raises(ValidationError):
            units.convert("volume", 1, "l", "gal")

    def test_unknown_unit_raises(self):
        with pytest.raises(ValidationError):
            units.convert("length", 1, "smoot", "m")


class TestTemperatureConversion:
    def test_c_to_f_freezing(self):
        result = units.convert("temperature", 0, "c", "f")
        assert math.isclose(result.result, 32)

    def test_c_to_f_boiling(self):
        result = units.convert("temperature", 100, "c", "f")
        assert math.isclose(result.result, 212)

    def test_f_to_c(self):
        result = units.convert("temperature", 98.6, "f", "c")
        assert math.isclose(result.result, 37.0, abs_tol=0.01)

    def test_c_to_k(self):
        result = units.convert("temperature", 0, "c", "k")
        assert math.isclose(result.result, 273.15)

    def test_k_to_c(self):
        result = units.convert("temperature", 0, "k", "c")
        assert math.isclose(result.result, -273.15)

    def test_aliases_work(self):
        result = units.convert("temperature", 0, "celsius", "fahrenheit")
        assert math.isclose(result.result, 32)

    def test_below_absolute_zero_raises(self):
        with pytest.raises(ValidationError):
            units.convert("temperature", -300, "c", "f")

    def test_unknown_temp_unit_raises(self):
        with pytest.raises(ValidationError):
            units.convert("temperature", 0, "rankine", "c")


class TestUnitsForCategory:
    def test_length_units(self):
        result = units.units_for_category("length")
        assert "m" in result and "ft" in result

    def test_temperature_units(self):
        assert units.units_for_category("temperature") == ["c", "f", "k"]

    def test_unknown_category_raises(self):
        with pytest.raises(ValidationError):
            units.units_for_category("volume")

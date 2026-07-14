import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.validation import ValidationError
from modules import electronics


class TestOhmsLaw:
    def test_solve_voltage(self):
        result = electronics.ohms_law(current=2, resistance=100)
        assert result.voltage == 200
        assert result.solved_for == "voltage"
        assert result.power == 400

    def test_solve_current(self):
        result = electronics.ohms_law(voltage=10, resistance=5)
        assert result.current == 2
        assert result.solved_for == "current"

    def test_solve_resistance(self):
        result = electronics.ohms_law(voltage=12, current=3)
        assert result.resistance == 4
        assert result.solved_for == "resistance"

    def test_requires_exactly_two(self):
        with pytest.raises(ValidationError):
            electronics.ohms_law(voltage=5)
        with pytest.raises(ValidationError):
            electronics.ohms_law(voltage=5, current=1, resistance=5)

    def test_zero_current_when_solving_resistance_raises(self):
        with pytest.raises(ValidationError):
            electronics.ohms_law(voltage=5, current=0)

    def test_steps_are_populated(self):
        result = electronics.ohms_law(current=2, resistance=100)
        assert len(result.steps) >= 3
        assert any("Ohm's Law" in s for s in result.steps)
        assert any("200" in s for s in result.steps)


class TestResistorColorCode:
    def test_4_band_orange_orange_red_gold(self):
        # 33 * 100 = 3300 ohms, 5% tolerance
        result = electronics.resistor_color_code(["orange", "orange", "red", "gold"])
        assert result.ohms == 3300
        assert result.tolerance == "±5%"
        assert result.display == "3.3 kΩ"

    def test_5_band(self):
        # brown black black brown brown -> 100 * 10 = 1000 ohms, ±1%
        result = electronics.resistor_color_code(["brown", "black", "black", "brown", "brown"])
        assert result.ohms == 1000
        assert result.tolerance == "±1%"

    def test_invalid_band_count(self):
        with pytest.raises(ValidationError):
            electronics.resistor_color_code(["red", "red"])

    def test_invalid_color(self):
        with pytest.raises(ValidationError):
            electronics.resistor_color_code(["mauve", "red", "black", "gold"])

    def test_case_insensitive(self):
        result = electronics.resistor_color_code(["ORANGE", "Orange", "red", "GOLD"])
        assert result.ohms == 3300


class TestTimer555:
    def test_astable_basic(self):
        # R1=1k, R2=1k, C=1uF
        result = electronics.timer_555_astable(1000, 1000, 0.000001)
        expected_freq = 1 / (0.693 * (1000 + 2 * 1000) * 0.000001)
        assert math.isclose(result.frequency_hz, expected_freq, rel_tol=1e-9)
        assert result.duty_cycle_pct > 50  # R1+R2 high time always > R2 low time

    def test_rejects_zero_values(self):
        with pytest.raises(ValidationError):
            electronics.timer_555_astable(0, 1000, 0.000001)
        with pytest.raises(ValidationError):
            electronics.timer_555_astable(1000, 1000, 0)

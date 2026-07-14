import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.validation import ValidationError
from modules import circuits


class TestDrawResistorDiagram:
    def test_creates_png_file_4_band(self, tmp_path):
        output = tmp_path / "resistor.png"
        result = circuits.draw_resistor_diagram(
            ["orange", "orange", "red", "gold"], "3.3 kΩ", "±5%", str(output)
        )
        assert result == str(output)
        assert output.exists()
        assert output.stat().st_size > 0

    def test_creates_png_file_5_band(self, tmp_path):
        output = tmp_path / "resistor5.png"
        result = circuits.draw_resistor_diagram(
            ["brown", "black", "black", "brown", "brown"], "1 kΩ", "±1%", str(output)
        )
        assert output.exists()

    def test_unknown_color_raises(self, tmp_path):
        output = tmp_path / "resistor.png"
        with pytest.raises(ValidationError):
            circuits.draw_resistor_diagram(["mauve", "red", "black", "gold"], "2 kΩ", "±5%", str(output))

    def test_case_insensitive(self, tmp_path):
        output = tmp_path / "resistor.png"
        result = circuits.draw_resistor_diagram(["ORANGE", "Orange", "RED", "GOLD"], "3.3 kΩ", "±5%", str(output))
        assert Path(result).exists()


class TestDraw555Circuit:
    def test_creates_output_file(self, tmp_path):
        output = tmp_path / "circuit.png"
        result = circuits.draw_555_astable_circuit(1000, 1000, 0.000001, str(output))
        assert result == str(output)
        assert Path(result).exists()

    def test_rejects_nonpositive_values(self, tmp_path):
        output = tmp_path / "circuit.png"
        with pytest.raises(ValidationError):
            circuits.draw_555_astable_circuit(0, 1000, 0.000001, str(output))
        with pytest.raises(ValidationError):
            circuits.draw_555_astable_circuit(1000, 1000, 0, str(output))

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.validation import ValidationError
from modules import plotting


class TestPlotKinematics:
    def test_creates_png_file(self, tmp_path):
        output = tmp_path / "kinematics.png"
        result = plotting.plot_kinematics(v0=0, a=2, t=5, output_path=str(output))
        assert result == str(output)
        assert output.exists()
        assert output.stat().st_size > 0

    def test_rejects_nonpositive_time(self, tmp_path):
        output = tmp_path / "kinematics.png"
        with pytest.raises(ValidationError):
            plotting.plot_kinematics(v0=0, a=2, t=0, output_path=str(output))


class TestPlot555Waveform:
    def test_creates_png_file(self, tmp_path):
        output = tmp_path / "waveform.png"
        result = plotting.plot_555_waveform(frequency_hz=1000, duty_cycle_pct=60, output_path=str(output))
        assert result == str(output)
        assert output.exists()
        assert output.stat().st_size > 0

    def test_rejects_nonpositive_frequency(self, tmp_path):
        output = tmp_path / "waveform.png"
        with pytest.raises(ValidationError):
            plotting.plot_555_waveform(frequency_hz=0, duty_cycle_pct=50, output_path=str(output))

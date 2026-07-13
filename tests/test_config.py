import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def isolated_config(monkeypatch, tmp_path):
    config_file = tmp_path / "config.toml"
    monkeypatch.setenv("TI84TOOLKIT_CONFIG_PATH", str(config_file))
    yield config_file


from core import config  # noqa: E402


class TestConfig:
    def test_defaults_when_no_file(self):
        assert config.get_gravity() == 9.81
        assert config.get_precision() == 6

    def test_custom_gravity(self, isolated_config):
        isolated_config.write_text("[physics]\ngravity = 1.62\n")
        assert config.get_gravity() == 1.62

    def test_custom_precision(self, isolated_config):
        isolated_config.write_text("[display]\nprecision = 3\n")
        assert config.get_precision() == 3

    def test_multiple_sections(self, isolated_config):
        isolated_config.write_text("[physics]\ngravity = 3.71\n\n[display]\nprecision = 4\n")
        assert config.get_gravity() == 3.71
        assert config.get_precision() == 4

    def test_comments_and_blank_lines_ignored(self, isolated_config):
        isolated_config.write_text("# comment\n\n[physics]\n# another comment\ngravity = 24.79\n")
        assert config.get_gravity() == 24.79

    def test_malformed_file_falls_back_to_defaults(self, isolated_config):
        isolated_config.write_text("not a valid config &&&")
        assert config.get_gravity() == 9.81

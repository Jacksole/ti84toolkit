import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch, tmp_path):
    """Point every test at a throwaway DB file so tests never touch the real
    ~/.ti84toolkit/history.db, and never leak state between tests."""
    db_file = tmp_path / "test_history.db"
    monkeypatch.setenv("TI84TOOLKIT_DB_PATH", str(db_file))
    yield db_file


from core import history  # noqa: E402  (import after fixture setup pattern is intentional)


class TestLogging:
    def test_log_and_retrieve(self):
        history.log_entry("electronics", "ohms-law", {"current": 2, "resistance": 100}, "voltage=200")
        entries = history.get_history()
        assert len(entries) == 1
        assert entries[0].module == "electronics"
        assert entries[0].operation == "ohms-law"
        assert entries[0].inputs == {"current": 2, "resistance": 100}
        assert entries[0].result == "voltage=200"

    def test_most_recent_first(self):
        history.log_entry("math", "quadratic", {"a": 1}, "first")
        history.log_entry("math", "quadratic", {"a": 2}, "second")
        entries = history.get_history()
        assert entries[0].result == "second"
        assert entries[1].result == "first"

    def test_limit(self):
        for i in range(5):
            history.log_entry("logic", "gate", {"n": i}, f"result{i}")
        entries = history.get_history(limit=3)
        assert len(entries) == 3

    def test_filter_by_module(self):
        history.log_entry("electronics", "ohms-law", {}, "a")
        history.log_entry("math", "quadratic", {}, "b")
        history.log_entry("electronics", "resistor", {}, "c")
        entries = history.get_history(module="electronics")
        assert len(entries) == 2
        assert all(e.module == "electronics" for e in entries)

    def test_count_entries(self):
        assert history.count_entries() == 0
        history.log_entry("physics", "kinematics", {}, "x")
        assert history.count_entries() == 1

    def test_clear_history(self):
        history.log_entry("stats", "describe", {}, "x")
        history.log_entry("stats", "describe", {}, "y")
        removed = history.clear_history()
        assert removed == 2
        assert history.count_entries() == 0

    def test_empty_history_returns_empty_list(self):
        assert history.get_history() == []

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import badges


class TestBadges:
    def test_first_calculation_badge(self):
        result = badges.badge_for_count(1)
        assert result is not None
        assert "First Calculation" in result[0]

    def test_no_badge_between_milestones(self):
        assert badges.badge_for_count(5) is None
        assert badges.badge_for_count(11) is None

    def test_milestone_badge(self):
        result = badges.badge_for_count(10)
        assert result is not None
        assert "10" in result[1]

    def test_zero_has_no_badge(self):
        assert badges.badge_for_count(0) is None

    def test_all_badges_returns_list(self):
        result = badges.all_badges()
        assert len(result) == 5
        assert all(len(b) == 3 for b in result)

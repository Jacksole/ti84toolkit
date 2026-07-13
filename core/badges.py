"""
Lightweight gamification -- badges unlocked based on total logged
calculations. A nod to the original doc's V2 roadmap ("Badge system / Hidden
features / Easter eggs"), kept simple: milestone-based, no persistent
per-badge state needed since it's derived purely from the history count.
"""
from __future__ import annotations

_BADGES = [
    (1, "🔧 First Calculation", "Welcome to the toolkit."),
    (10, "📐 Getting the Hang of It", "10 calculations logged."),
    (50, "⚙️ Regular User", "50 calculations logged."),
    (100, "🏆 Toolkit Veteran", "100 calculations logged."),
    (500, "🚀 Systems Engineer", "500 calculations logged."),
]


def badge_for_count(count: int) -> tuple[str, str] | None:
    """Return (name, description) if `count` exactly matches a milestone threshold, else None.

    Checking for an exact match (not >=) means the badge announcement fires
    once, right when the milestone is crossed, rather than on every
    subsequent calculation.
    """
    for threshold, name, description in _BADGES:
        if count == threshold:
            return name, description
    return None


def all_badges() -> list[tuple[int, str, str]]:
    return list(_BADGES)

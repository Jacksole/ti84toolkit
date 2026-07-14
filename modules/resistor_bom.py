"""
Resistor combination finder -- "I need X ohms, what standard resistors get
me closest?" Searches standard E12/E24 series values for the closest single
resistor, series pair, and parallel pair to a target resistance.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations_with_replacement

from core.validation import ValidationError

# Base values within one decade (1x - 9.1x), per IEC 60063 preferred number series.
_E12_BASE = [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]
_E24_BASE = [
    1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
    3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1,
]

_SERIES = {"E12": _E12_BASE, "E24": _E24_BASE}


def standard_values(series: str = "E24", min_decade: int = -1, max_decade: int = 6) -> list[float]:
    """Generate standard resistor values across decades (default 0.1 ohm to 10 Mohm)."""
    series = series.strip().upper()
    if series not in _SERIES:
        raise ValidationError(f"Unknown series '{series}'. Valid: {', '.join(_SERIES)}.")

    base = _SERIES[series]
    values = set()
    for decade in range(min_decade, max_decade + 1):
        for b in base:
            values.add(round(b * (10**decade), 6))
    return sorted(values)


@dataclass
class BomOption:
    kind: str  # "single", "series", or "parallel"
    values: list[float]
    achieved_ohms: float
    error_pct: float


def _fmt_ohms(v: float) -> str:
    if v >= 1_000_000:
        return f"{v / 1_000_000:g}M\u03a9"
    if v >= 1_000:
        return f"{v / 1_000:g}k\u03a9"
    return f"{v:g}\u03a9"


def find_resistor_combo(target_ohms: float, series: str = "E24", top_n: int = 3) -> list[BomOption]:
    """Find the closest single resistor, series pair, and parallel pair from
    standard values to a target resistance. Returns up to `top_n` options,
    best (lowest error) first."""
    if target_ohms <= 0:
        raise ValidationError("Target resistance must be positive.")

    values = standard_values(series)
    options: list[BomOption] = []

    # Single closest value
    closest = min(values, key=lambda v: abs(v - target_ohms))
    options.append(BomOption("single", [closest], closest, abs(closest - target_ohms) / target_ohms * 100))

    # Restrict candidate pairs to values within a reasonable window of the target,
    # to keep the search fast and the results sensible (no point pairing a 1M
    # resistor toward a 100-ohm target).
    window = [v for v in values if target_ohms * 0.02 <= v <= target_ohms * 2]
    if not window:
        window = values

    best_series = None
    best_series_error = None
    best_parallel = None
    best_parallel_error = None

    for r1, r2 in combinations_with_replacement(window, 2):
        series_sum = r1 + r2
        series_error = abs(series_sum - target_ohms) / target_ohms
        if best_series_error is None or series_error < best_series_error:
            best_series_error = series_error
            best_series = (r1, r2, series_sum)

        parallel_val = (r1 * r2) / (r1 + r2)
        parallel_error = abs(parallel_val - target_ohms) / target_ohms
        if best_parallel_error is None or parallel_error < best_parallel_error:
            best_parallel_error = parallel_error
            best_parallel = (r1, r2, parallel_val)

    if best_series is not None:
        r1, r2, achieved = best_series
        options.append(BomOption("series", sorted([r1, r2]), achieved, best_series_error * 100))

    if best_parallel is not None:
        r1, r2, achieved = best_parallel
        options.append(BomOption("parallel", sorted([r1, r2]), achieved, best_parallel_error * 100))

    options.sort(key=lambda o: o.error_pct)
    return options[:top_n]


def format_option(option: BomOption) -> str:
    values_str = " + ".join(_fmt_ohms(v) for v in option.values) if option.kind == "series" else \
                 " || ".join(_fmt_ohms(v) for v in option.values) if option.kind == "parallel" else \
                 _fmt_ohms(option.values[0])
    return f"{option.kind}: {values_str} = {_fmt_ohms(option.achieved_ohms)} ({option.error_pct:.2f}% error)"

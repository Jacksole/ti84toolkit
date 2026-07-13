"""
Unit conversion module -- pairs naturally with the electronics module
(resistance/voltage/current prefixes) and rounds out the toolkit's general
engineering-math utility.

Categories are grouped by physical quantity. Most categories convert via a
simple linear factor to a base unit; temperature is handled separately since
Celsius/Fahrenheit/Kelvin require offsets, not just scaling.
"""
from __future__ import annotations

from dataclasses import dataclass

from core.validation import ValidationError

# ---------------------------------------------------------------------------
# Linear (factor-to-base) categories
# ---------------------------------------------------------------------------

# Each category maps unit name -> multiplier to convert TO the base unit.
_LENGTH_M = {
    "mm": 0.001, "cm": 0.01, "m": 1.0, "km": 1000.0,
    "in": 0.0254, "ft": 0.3048, "yd": 0.9144, "mi": 1609.344,
}

_MASS_KG = {
    "mg": 1e-6, "g": 0.001, "kg": 1.0,
    "oz": 0.028349523125, "lb": 0.45359237,
}

_TIME_S = {
    "ms": 0.001, "s": 1.0, "min": 60.0, "hr": 3600.0, "day": 86400.0,
}

_RESISTANCE_OHM = {
    "milliohm": 0.001, "ohm": 1.0, "kohm": 1_000.0, "mohm": 1_000_000.0,
}

_VOLTAGE_V = {
    "microvolt": 1e-6, "millivolt": 0.001, "volt": 1.0, "kilovolt": 1_000.0,
}

_CURRENT_A = {
    "microamp": 1e-6, "milliamp": 0.001, "amp": 1.0, "kiloamp": 1_000.0,
}

_CATEGORIES = {
    "length": _LENGTH_M,
    "mass": _MASS_KG,
    "time": _TIME_S,
    "resistance": _RESISTANCE_OHM,
    "voltage": _VOLTAGE_V,
    "current": _CURRENT_A,
}

CATEGORY_NAMES = sorted(_CATEGORIES.keys()) + ["temperature"]


@dataclass
class ConversionResult:
    category: str
    value: float
    from_unit: str
    to_unit: str
    result: float


def _convert_linear(category: str, table: dict[str, float], value: float, from_unit: str, to_unit: str) -> float:
    from_unit = from_unit.strip().lower()
    to_unit = to_unit.strip().lower()

    if from_unit not in table:
        raise ValidationError(f"Unknown {category} unit '{from_unit}'. Valid units: {', '.join(sorted(table))}.")
    if to_unit not in table:
        raise ValidationError(f"Unknown {category} unit '{to_unit}'. Valid units: {', '.join(sorted(table))}.")

    base_value = value * table[from_unit]
    return base_value / table[to_unit]


# ---------------------------------------------------------------------------
# Temperature (requires offsets, not just scaling)
# ---------------------------------------------------------------------------

_TEMP_UNITS = {"c", "f", "k", "celsius", "fahrenheit", "kelvin"}
_TEMP_ALIASES = {"celsius": "c", "fahrenheit": "f", "kelvin": "k"}


def _normalize_temp_unit(unit: str) -> str:
    u = unit.strip().lower()
    u = _TEMP_ALIASES.get(u, u)
    if u not in ("c", "f", "k"):
        raise ValidationError(f"Unknown temperature unit '{unit}'. Valid units: c, f, k (or celsius/fahrenheit/kelvin).")
    return u


def _temp_to_celsius(value: float, unit: str) -> float:
    if unit == "c":
        return value
    if unit == "f":
        return (value - 32) * 5 / 9
    if unit == "k":
        return value - 273.15
    raise AssertionError("unreachable")  # pragma: no cover


def _celsius_to(value_c: float, unit: str) -> float:
    if unit == "c":
        return value_c
    if unit == "f":
        return value_c * 9 / 5 + 32
    if unit == "k":
        return value_c + 273.15
    raise AssertionError("unreachable")  # pragma: no cover


def convert_temperature(value: float, from_unit: str, to_unit: str) -> ConversionResult:
    from_u = _normalize_temp_unit(from_unit)
    to_u = _normalize_temp_unit(to_unit)

    if to_u == "k" and value < 0 and from_u == "k":
        raise ValidationError("Kelvin cannot be negative.")

    celsius = _temp_to_celsius(value, from_u)
    if celsius < -273.15:
        raise ValidationError("Result is below absolute zero -- check your input.")

    result = _celsius_to(celsius, to_u)
    return ConversionResult("temperature", value, from_unit, to_unit, result)


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------


def convert(category: str, value: float, from_unit: str, to_unit: str) -> ConversionResult:
    """Convert `value` from `from_unit` to `to_unit` within the given category."""
    category = category.strip().lower()

    if category == "temperature":
        return convert_temperature(value, from_unit, to_unit)

    if category not in _CATEGORIES:
        raise ValidationError(f"Unknown category '{category}'. Valid categories: {', '.join(CATEGORY_NAMES)}.")

    table = _CATEGORIES[category]
    result = _convert_linear(category, table, value, from_unit, to_unit)
    return ConversionResult(category, value, from_unit, to_unit, result)


def units_for_category(category: str) -> list[str]:
    category = category.strip().lower()
    if category == "temperature":
        return ["c", "f", "k"]
    if category not in _CATEGORIES:
        raise ValidationError(f"Unknown category '{category}'. Valid categories: {', '.join(CATEGORY_NAMES)}.")
    return sorted(_CATEGORIES[category])

"""
Electronics module -- port of the TI-84 Embedded Systems Toolkit's electronics tools.

Covers:
  - Ohm's Law solver (V, I, R -- solve for the missing one)
  - Resistor color code decoder (4-band and 5-band)
  - 555 Timer astable mode calculator (frequency + duty cycle)
"""
from __future__ import annotations

from dataclasses import dataclass

from core.validation import ValidationError, require_exactly_n_known

# ---------------------------------------------------------------------------
# Ohm's Law
# ---------------------------------------------------------------------------


@dataclass
class OhmsLawResult:
    voltage: float
    current: float
    resistance: float
    power: float
    solved_for: str
    steps: list[str]


def ohms_law(voltage: float | None = None, current: float | None = None, resistance: float | None = None) -> OhmsLawResult:
    """Solve Ohm's Law given exactly two of (voltage, current, resistance)."""
    require_exactly_n_known(
        {"voltage": voltage, "current": current, "resistance": resistance}, 2, "Ohm's Law"
    )

    steps: list[str] = []

    if voltage is None:
        if current == 0:
            raise ValidationError("Current cannot be zero when solving for voltage.")
        steps.append("Known: I (current), R (resistance). Unknown: V (voltage).")
        steps.append("Ohm's Law: V = I x R")
        steps.append(f"V = {current:g} x {resistance:g}")
        voltage = current * resistance
        steps.append(f"V = {voltage:g} V")
        solved_for = "voltage"
    elif current is None:
        if resistance == 0:
            raise ValidationError("Resistance cannot be zero when solving for current.")
        steps.append("Known: V (voltage), R (resistance). Unknown: I (current).")
        steps.append("Ohm's Law: V = I x R  ->  I = V / R")
        steps.append(f"I = {voltage:g} / {resistance:g}")
        current = voltage / resistance
        steps.append(f"I = {current:g} A")
        solved_for = "current"
    else:
        if current == 0:
            raise ValidationError("Current cannot be zero when solving for resistance.")
        steps.append("Known: V (voltage), I (current). Unknown: R (resistance).")
        steps.append("Ohm's Law: V = I x R  ->  R = V / I")
        steps.append(f"R = {voltage:g} / {current:g}")
        resistance = voltage / current
        steps.append(f"R = {resistance:g} \u03a9")
        solved_for = "resistance"

    power = voltage * current
    steps.append(f"Power check: P = V x I = {voltage:g} x {current:g} = {power:g} W")

    return OhmsLawResult(voltage, current, resistance, power, solved_for, steps)


# ---------------------------------------------------------------------------
# Resistor color code
# ---------------------------------------------------------------------------

COLOR_DIGIT = {
    "black": 0, "brown": 1, "red": 2, "orange": 3, "yellow": 4,
    "green": 5, "blue": 6, "violet": 7, "gray": 8, "grey": 8, "white": 9,
}

COLOR_MULTIPLIER = {
    "black": 1, "brown": 10, "red": 100, "orange": 1_000, "yellow": 10_000,
    "green": 100_000, "blue": 1_000_000, "violet": 10_000_000,
    "gold": 0.1, "silver": 0.01,
}

COLOR_TOLERANCE = {
    "brown": "±1%", "red": "±2%", "green": "±0.5%", "blue": "±0.25%",
    "violet": "±0.1%", "gray": "±0.05%", "grey": "±0.05%",
    "gold": "±5%", "silver": "±10%", "none": "±20%",
}


@dataclass
class ResistorResult:
    ohms: float
    tolerance: str
    display: str


def resistor_color_code(bands: list[str]) -> ResistorResult:
    """Decode a 4-band or 5-band resistor color code into resistance + tolerance."""
    bands = [b.strip().lower() for b in bands]

    if len(bands) not in (4, 5):
        raise ValidationError(f"Expected 4 or 5 color bands, got {len(bands)}.")

    n_digits = 2 if len(bands) == 4 else 3
    digit_bands = bands[:n_digits]
    mult_band = bands[n_digits]
    tol_band = bands[n_digits + 1]

    for b in digit_bands:
        if b not in COLOR_DIGIT:
            raise ValidationError(f"'{b}' is not a valid digit color.")
    if mult_band not in COLOR_MULTIPLIER:
        raise ValidationError(f"'{mult_band}' is not a valid multiplier color.")
    if tol_band not in COLOR_TOLERANCE:
        raise ValidationError(f"'{tol_band}' is not a valid tolerance color.")

    digits = "".join(str(COLOR_DIGIT[b]) for b in digit_bands)
    base = int(digits)
    ohms = base * COLOR_MULTIPLIER[mult_band]
    tolerance = COLOR_TOLERANCE[tol_band]

    display = _format_ohms(ohms)
    return ResistorResult(ohms, tolerance, display)


def _format_ohms(ohms: float) -> str:
    if ohms >= 1_000_000:
        return f"{ohms / 1_000_000:g} MΩ"
    if ohms >= 1_000:
        return f"{ohms / 1_000:g} kΩ"
    return f"{ohms:g} Ω"


# ---------------------------------------------------------------------------
# 555 Timer -- astable mode
# ---------------------------------------------------------------------------


@dataclass
class Timer555Result:
    frequency_hz: float
    period_s: float
    duty_cycle_pct: float
    time_high_s: float
    time_low_s: float


def timer_555_astable(r1_ohms: float, r2_ohms: float, c_farads: float) -> Timer555Result:
    """Compute frequency and duty cycle for a 555 timer in astable mode.

    Standard formulas:
      t_high = 0.693 * (R1 + R2) * C
      t_low  = 0.693 * R2 * C
      f      = 1.44 / ((R1 + 2*R2) * C)
    """
    if r1_ohms <= 0 or r2_ohms <= 0 or c_farads <= 0:
        raise ValidationError("R1, R2, and C must all be positive, nonzero values.")

    t_high = 0.693 * (r1_ohms + r2_ohms) * c_farads
    t_low = 0.693 * r2_ohms * c_farads
    period = t_high + t_low
    frequency = 1.0 / period
    duty_cycle = (t_high / period) * 100

    return Timer555Result(frequency, period, duty_cycle, t_high, t_low)

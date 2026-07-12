"""
Shared input validation for the TI-84 Embedded Systems Toolkit.

Mirrors the original TI-BASIC design principle: validate before execution,
never let a bad input reach a compute function.
"""
from __future__ import annotations


class ValidationError(ValueError):
    """Raised when user input fails validation. Carries a human-readable message."""


def parse_float(value: str, field_name: str, *, allow_zero: bool = True, allow_negative: bool = True) -> float:
    """Parse a string into a float with toolkit-consistent error messages."""
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} must be a number (got {value!r}).")

    if not allow_negative and result < 0:
        raise ValidationError(f"{field_name} cannot be negative (got {result}).")
    if not allow_zero and result == 0:
        raise ValidationError(f"{field_name} cannot be zero.")
    return result


def require_exactly_n_known(known: dict[str, float | None], n: int, group_name: str) -> None:
    """Ensure exactly n of the given values are provided (not None) -- used for Ohm's Law style solvers."""
    provided = [k for k, v in known.items() if v is not None]
    if len(provided) != n:
        names = ", ".join(known.keys())
        raise ValidationError(
            f"{group_name}: provide exactly {n} of ({names}) and leave the rest unset. "
            f"You provided {len(provided)}: {', '.join(provided) if provided else 'none'}."
        )


def prompt_float(prompt_text: str, *, allow_blank: bool = False) -> float | None:
    """Interactive prompt helper -- used by the menu system. Returns None if blank and allowed."""
    from rich.prompt import Prompt

    while True:
        raw = Prompt.ask(prompt_text)
        if raw.strip() == "" and allow_blank:
            return None
        try:
            return parse_float(raw, prompt_text)
        except ValidationError as e:
            from rich import print as rprint
            rprint(f"[red]{e}[/red]")

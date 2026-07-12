"""
Physics module -- kinematics equations, energy, and power calculations.

V1 scope, per the original handoff doc: "Kinematics equations / Energy and
power calculations."

Kinematics is solved generally (not via a lookup table of the 4-5 classic
SUVAT equations) by handing the two independent equations of motion to
sympy and substituting whichever 3 of the 5 variables (v0, v, a, t, d) are
known -- this covers all C(5,3) = 10 input combinations correctly, including
the ones that require the quadratic (position) equation.
"""
from __future__ import annotations

from dataclasses import dataclass

import sympy

from core.validation import ValidationError, require_exactly_n_known

# ---------------------------------------------------------------------------
# Kinematics
# ---------------------------------------------------------------------------

_V0, _V, _A, _T, _D = sympy.symbols("v0 v a t d")

# The two independent equations of motion under constant acceleration.
# Every other SUVAT equation (e.g. v^2 = v0^2 + 2*a*d) is derivable from these two.
_EQ_VELOCITY = sympy.Eq(_V, _V0 + _A * _T)
_EQ_POSITION = sympy.Eq(_D, _V0 * _T + sympy.Rational(1, 2) * _A * _T**2)

_SYMBOLS = {"v0": _V0, "v": _V, "a": _A, "t": _T, "d": _D}


@dataclass
class KinematicsResult:
    values: dict[str, float]  # all five variables, resolved
    solved_for: list[str]     # which two were computed


def kinematics_solve(
    v0: float | None = None,
    v: float | None = None,
    a: float | None = None,
    t: float | None = None,
    d: float | None = None,
) -> KinematicsResult:
    """Solve for the two unknown kinematics variables given exactly three known ones."""
    known = {"v0": v0, "v": v, "a": a, "t": t, "d": d}
    require_exactly_n_known(known, 3, "Kinematics")

    unknown_names = [name for name, val in known.items() if val is None]

    eq1 = _EQ_VELOCITY.subs({_SYMBOLS[n]: val for n, val in known.items() if val is not None})
    eq2 = _EQ_POSITION.subs({_SYMBOLS[n]: val for n, val in known.items() if val is not None})
    unknown_symbols = [_SYMBOLS[n] for n in unknown_names]

    try:
        solutions = sympy.solve([eq1, eq2], unknown_symbols, dict=True)
    except NotImplementedError as e:
        raise ValidationError(f"Could not solve this combination of kinematics variables: {e}")

    if not solutions:
        raise ValidationError(
            "No consistent solution found for these values -- check that they describe physically possible motion."
        )

    # Time should be non-negative and real; prefer such a solution if multiple exist (quadratic case).
    def is_valid(sol: dict) -> bool:
        for sym, expr in sol.items():
            if not expr.is_real:
                return False
            if sym == _T and expr < 0:
                return False
        return True

    chosen = next((s for s in solutions if is_valid(s)), None)
    if chosen is None:
        raise ValidationError(
            "No physically valid solution found (results were complex or implied negative time)."
        )

    resolved = dict(known)
    for sym, expr in chosen.items():
        name = next(n for n, s in _SYMBOLS.items() if s == sym)
        resolved[name] = float(expr)

    return KinematicsResult(resolved, unknown_names)


# ---------------------------------------------------------------------------
# Energy and power
# ---------------------------------------------------------------------------

_G_DEFAULT = 9.81  # m/s^2, standard gravity


@dataclass
class EnergyResult:
    label: str
    joules: float


def kinetic_energy(mass_kg: float, velocity_mps: float) -> EnergyResult:
    if mass_kg <= 0:
        raise ValidationError("Mass must be positive.")
    return EnergyResult("Kinetic Energy", 0.5 * mass_kg * velocity_mps**2)


def potential_energy(mass_kg: float, height_m: float, gravity: float = _G_DEFAULT) -> EnergyResult:
    if mass_kg <= 0:
        raise ValidationError("Mass must be positive.")
    return EnergyResult("Gravitational Potential Energy", mass_kg * gravity * height_m)


def work_done(force_n: float, distance_m: float) -> EnergyResult:
    return EnergyResult("Work", force_n * distance_m)


@dataclass
class PowerResult:
    watts: float


def power_from_work(work_joules: float, time_s: float) -> PowerResult:
    if time_s <= 0:
        raise ValidationError("Time must be positive.")
    return PowerResult(work_joules / time_s)


def power_from_force_velocity(force_n: float, velocity_mps: float) -> PowerResult:
    return PowerResult(force_n * velocity_mps)

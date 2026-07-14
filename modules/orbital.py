"""
Orbital mechanics module -- two-body Kepler mechanics and Hohmann transfer
orbits.

Deliberately scoped to problems with closed-form or simple-iterative
solutions (the same tier of math a TI-84 could plausibly have run):
  - Kepler's Third Law (orbital period)
  - Vis-viva equation (orbital velocity at any point in an orbit)
  - Escape velocity / circular orbital velocity
  - Kepler's equation (mean anomaly -> eccentric anomaly), solved via
    Newton-Raphson -- transcendental, but iterative root-finding is exactly
    what TI-BASIC's For(/While( loops are built for
  - Hohmann transfer orbits (minimum-delta-v two-burn transfer between
    circular orbits)

N-body simulation (3+ mutually gravitating bodies) is out of scope: it has
no closed-form solution, requires numerical integration over many timesteps,
and is genuinely new capability rather than a restored one -- unlike
everything above, it could not plausibly have run on the original hardware.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from core.validation import ValidationError

# ---------------------------------------------------------------------------
# Standard gravitational parameters (mu = G*M, m^3/s^2) and mean radii (m)
# for common bodies, so callers can work in altitude rather than raw radius.
# ---------------------------------------------------------------------------

BODIES = {
    "earth": {"mu": 3.986004418e14, "radius": 6_371_000.0},
    "moon": {"mu": 4.9048695e12, "radius": 1_737_400.0},
    "mars": {"mu": 4.282837e13, "radius": 3_389_500.0},
    "sun": {"mu": 1.32712440018e20, "radius": 696_340_000.0},
    "jupiter": {"mu": 1.26686534e17, "radius": 69_911_000.0},
}


def body_mu(name: str) -> float:
    name = name.strip().lower()
    if name not in BODIES:
        raise ValidationError(f"Unknown body '{name}'. Known bodies: {', '.join(BODIES)}.")
    return BODIES[name]["mu"]


def body_radius(name: str) -> float:
    name = name.strip().lower()
    if name not in BODIES:
        raise ValidationError(f"Unknown body '{name}'. Known bodies: {', '.join(BODIES)}.")
    return BODIES[name]["radius"]


def _check_positive(value: float, label: str) -> None:
    if value <= 0:
        raise ValidationError(f"{label} must be positive.")


# ---------------------------------------------------------------------------
# Kepler's Third Law
# ---------------------------------------------------------------------------


def orbital_period(semi_major_axis_m: float, mu: float) -> float:
    """Orbital period (s) via Kepler's Third Law: T = 2*pi*sqrt(a^3 / mu)."""
    _check_positive(semi_major_axis_m, "Semi-major axis")
    _check_positive(mu, "Gravitational parameter (mu)")
    return 2 * math.pi * math.sqrt(semi_major_axis_m**3 / mu)


def semi_major_axis_from_period(period_s: float, mu: float) -> float:
    """Inverse of orbital_period: a = (mu * (T / (2*pi))^2)^(1/3)."""
    _check_positive(period_s, "Period")
    _check_positive(mu, "Gravitational parameter (mu)")
    return (mu * (period_s / (2 * math.pi)) ** 2) ** (1 / 3)


# ---------------------------------------------------------------------------
# Vis-viva, escape velocity, circular velocity
# ---------------------------------------------------------------------------


def vis_viva_velocity(r_m: float, a_m: float, mu: float) -> float:
    """Orbital speed (m/s) at radius r in an orbit of semi-major axis a: v = sqrt(mu*(2/r - 1/a))."""
    _check_positive(r_m, "Radius")
    _check_positive(a_m, "Semi-major axis")
    _check_positive(mu, "Gravitational parameter (mu)")
    value = mu * (2 / r_m - 1 / a_m)
    if value < 0:
        raise ValidationError("2/r - 1/a is negative -- this radius is not reachable on this orbit.")
    return math.sqrt(value)


def escape_velocity(r_m: float, mu: float) -> float:
    """Escape velocity (m/s) at radius r: v = sqrt(2*mu/r)."""
    _check_positive(r_m, "Radius")
    _check_positive(mu, "Gravitational parameter (mu)")
    return math.sqrt(2 * mu / r_m)


def circular_velocity(r_m: float, mu: float) -> float:
    """Circular orbital velocity (m/s) at radius r: v = sqrt(mu/r)."""
    _check_positive(r_m, "Radius")
    _check_positive(mu, "Gravitational parameter (mu)")
    return math.sqrt(mu / r_m)


# ---------------------------------------------------------------------------
# Kepler's equation: M = E - e*sin(E), solved via Newton-Raphson
# ---------------------------------------------------------------------------


@dataclass
class KeplerEquationResult:
    mean_anomaly_rad: float
    eccentricity: float
    eccentric_anomaly_rad: float
    true_anomaly_rad: float
    iterations: int
    steps: list[str]


def solve_kepler_equation(
    mean_anomaly_rad: float, eccentricity: float, tolerance: float = 1e-10, max_iterations: int = 100
) -> KeplerEquationResult:
    """Solve M = E - e*sin(E) for E (eccentric anomaly) via Newton-Raphson,
    then derive the true anomaly. Restricted to elliptical orbits (0 <= e < 1)."""
    if not (0 <= eccentricity < 1):
        raise ValidationError("Eccentricity must be in [0, 1) for this elliptical-orbit solver.")

    steps = [
        f"Kepler's equation: M = E - e*sin(E), with M = {mean_anomaly_rad:g} rad, e = {eccentricity:g}",
        "Newton-Raphson: E_(n+1) = E_n - (E_n - e*sin(E_n) - M) / (1 - e*cos(E_n))",
    ]

    e = eccentricity
    m = mean_anomaly_rad
    E = m if e < 0.8 else math.pi  # standard starting-guess heuristic for high eccentricity

    for i in range(1, max_iterations + 1):
        f = E - e * math.sin(E) - m
        f_prime = 1 - e * math.cos(E)
        if f_prime == 0:
            raise ValidationError("Newton-Raphson derivative hit zero -- could not converge.")
        delta = f / f_prime
        E -= delta
        if i <= 5 or abs(delta) < tolerance:
            steps.append(f"Iteration {i}: E = {E:g} (correction {delta:.2e})")
        if abs(delta) < tolerance:
            break
    else:
        raise ValidationError(f"Did not converge within {max_iterations} iterations.")

    true_anomaly = 2 * math.atan2(math.sqrt(1 + e) * math.sin(E / 2), math.sqrt(1 - e) * math.cos(E / 2))
    steps.append(f"True anomaly: nu = 2*atan2(sqrt(1+e)*sin(E/2), sqrt(1-e)*cos(E/2)) = {true_anomaly:g} rad")

    return KeplerEquationResult(mean_anomaly_rad, eccentricity, E, true_anomaly, i, steps)


# ---------------------------------------------------------------------------
# Hohmann transfer
# ---------------------------------------------------------------------------


@dataclass
class HohmannTransferResult:
    r1_m: float
    r2_m: float
    delta_v1_mps: float
    delta_v2_mps: float
    total_delta_v_mps: float
    transfer_time_s: float
    transfer_semi_major_axis_m: float
    steps: list[str]


def hohmann_transfer(r1_m: float, r2_m: float, mu: float) -> HohmannTransferResult:
    """Compute the two burns, total delta-v, and transfer time for a Hohmann
    transfer between two circular orbits of radii r1 and r2."""
    _check_positive(r1_m, "r1")
    _check_positive(r2_m, "r2")
    _check_positive(mu, "Gravitational parameter (mu)")
    if r1_m == r2_m:
        raise ValidationError("r1 and r2 must differ -- no transfer needed between identical circular orbits.")

    a_transfer = (r1_m + r2_m) / 2
    v1_circular = circular_velocity(r1_m, mu)
    v2_circular = circular_velocity(r2_m, mu)
    v1_transfer = vis_viva_velocity(r1_m, a_transfer, mu)
    v2_transfer = vis_viva_velocity(r2_m, a_transfer, mu)

    delta_v1 = abs(v1_transfer - v1_circular)
    delta_v2 = abs(v2_circular - v2_transfer)
    total_delta_v = delta_v1 + delta_v2
    transfer_time = math.pi * math.sqrt(a_transfer**3 / mu)  # half the transfer ellipse's period

    direction = "raising" if r2_m > r1_m else "lowering"
    steps = [
        f"Transfer orbit semi-major axis: a = (r1 + r2) / 2 = ({r1_m:g} + {r2_m:g}) / 2 = {a_transfer:g} m",
        f"Circular velocity at r1: v1_circ = sqrt(mu/r1) = {v1_circular:g} m/s",
        f"Circular velocity at r2: v2_circ = sqrt(mu/r2) = {v2_circular:g} m/s",
        f"Transfer-orbit velocity at r1 (vis-viva): v1_trans = {v1_transfer:g} m/s",
        f"Transfer-orbit velocity at r2 (vis-viva): v2_trans = {v2_transfer:g} m/s",
        f"Burn 1 (departure, {direction} orbit): dv1 = |v1_trans - v1_circ| = {delta_v1:g} m/s",
        f"Burn 2 (arrival, circularize): dv2 = |v2_circ - v2_trans| = {delta_v2:g} m/s",
        f"Total delta-v = dv1 + dv2 = {total_delta_v:g} m/s",
        f"Transfer time = half the transfer ellipse's period = pi*sqrt(a^3/mu) = {transfer_time:g} s",
    ]

    return HohmannTransferResult(
        r1_m, r2_m, delta_v1, delta_v2, total_delta_v, transfer_time, a_transfer, steps
    )

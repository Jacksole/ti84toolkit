"""
Plotting module -- renders charts to PNG files (matplotlib's Agg backend, so
it works headlessly over SSH/WSL without an X server or WSLg).

Covers:
  - Kinematics: position(t) and velocity(t) curves for constant-acceleration motion
  - 555 timer: the astable-mode output square wave
"""
from __future__ import annotations

import math

import matplotlib

matplotlib.use("Agg")  # must happen before pyplot import; avoids requiring a display

import matplotlib.pyplot as plt

from core.validation import ValidationError


def plot_kinematics(v0: float, a: float, t: float, output_path: str) -> str:
    """Plot position(t) and velocity(t) for constant-acceleration motion from 0 to t.

    Returns the output path on success.
    """
    if t <= 0:
        raise ValidationError("Time must be positive to plot a motion curve.")

    n_points = 200
    times = [t * i / (n_points - 1) for i in range(n_points)]
    positions = [v0 * ti + 0.5 * a * ti**2 for ti in times]
    velocities = [v0 + a * ti for ti in times]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 6), sharex=True)

    ax1.plot(times, positions, color="#2563eb", linewidth=2)
    ax1.set_ylabel("Position (m)")
    ax1.set_title("Kinematics: Position and Velocity vs. Time")
    ax1.grid(True, alpha=0.3)

    ax2.plot(times, velocities, color="#dc2626", linewidth=2)
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("Velocity (m/s)")
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def plot_555_waveform(frequency_hz: float, duty_cycle_pct: float, output_path: str, num_cycles: int = 4) -> str:
    """Plot the astable-mode 555 timer output as a square wave over `num_cycles` periods."""
    if frequency_hz <= 0:
        raise ValidationError("Frequency must be positive to plot a waveform.")

    period = 1.0 / frequency_hz
    high_time = period * (duty_cycle_pct / 100.0)
    low_time = period - high_time

    times = [0.0]
    values = [1]
    t = 0.0
    for _ in range(num_cycles):
        t += high_time
        times += [t, t]
        values += [1, 0]
        t += low_time
        times += [t, t]
        values += [0, 1]
    times.pop()
    values.pop()

    fig, ax = plt.subplots(figsize=(8, 3))
    ax.step(times, values, where="post", color="#16a34a", linewidth=2)
    ax.set_ylim(-0.2, 1.2)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["LOW", "HIGH"])
    ax.set_xlabel("Time (s)")
    ax.set_title(f"555 Timer Output (Astable) -- {frequency_hz:.2f} Hz, {duty_cycle_pct:.1f}% duty cycle")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def plot_hohmann_transfer(r1_m: float, r2_m: float, output_path: str) -> str:
    """Plot both circular orbits and the transfer ellipse connecting them,
    viewed from above with the primary body at the origin."""
    if r1_m <= 0 or r2_m <= 0:
        raise ValidationError("r1 and r2 must both be positive to plot a transfer.")
    if r1_m == r2_m:
        raise ValidationError("r1 and r2 must differ to plot a transfer.")

    n = 300
    thetas = [2 * math.pi * i / (n - 1) for i in range(n)]

    orbit1_x = [r1_m * math.cos(th) for th in thetas]
    orbit1_y = [r1_m * math.sin(th) for th in thetas]
    orbit2_x = [r2_m * math.cos(th) for th in thetas]
    orbit2_y = [r2_m * math.sin(th) for th in thetas]

    # Transfer ellipse: semi-major axis a, periapsis at r1, apoapsis at r2 (or vice versa),
    # traced only across the half (0 to pi) that represents the actual transfer arc.
    a = (r1_m + r2_m) / 2
    c = abs(r2_m - r1_m) / 2  # linear eccentricity
    b = math.sqrt(max(a**2 - c**2, 0))
    sign = 1 if r2_m > r1_m else -1
    center_x = -sign * c  # focus (primary body) is at the origin

    half_thetas = [math.pi * i / (n - 1) for i in range(n)]
    transfer_x = [center_x + a * math.cos(th) * sign for th in half_thetas]
    transfer_y = [b * math.sin(th) for th in half_thetas]

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(orbit1_x, orbit1_y, color="#2563eb", linewidth=1.5, label=f"Orbit 1 (r={r1_m:,.0f} m)")
    ax.plot(orbit2_x, orbit2_y, color="#16a34a", linewidth=1.5, label=f"Orbit 2 (r={r2_m:,.0f} m)")
    ax.plot(transfer_x, transfer_y, color="#dc2626", linewidth=2, linestyle="--", label="Transfer orbit")
    ax.scatter([0], [0], color="#444444", s=80, zorder=5, label="Primary body")

    ax.set_aspect("equal")
    ax.set_title("Hohmann Transfer Orbit")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path

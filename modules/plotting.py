"""
Plotting module -- renders charts to PNG files (matplotlib's Agg backend, so
it works headlessly over SSH/WSL without an X server or WSLg).

Covers:
  - Kinematics: position(t) and velocity(t) curves for constant-acceleration motion
  - 555 timer: the astable-mode output square wave
"""
from __future__ import annotations

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

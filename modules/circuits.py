"""
Circuit diagram module -- visual companions to the electronics module.

- draw_resistor_diagram: renders the physical resistor body with its actual
  color bands (matplotlib patches -- schemdraw doesn't model color-band
  styling, so this is hand-drawn).
- draw_555_astable_circuit: renders the classic 555 astable wiring
  (schemdraw, which is built for exactly this kind of schematic).

Both save to PNG and work headlessly (matplotlib's Agg backend).
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import schemdraw
import schemdraw.elements as elm

from core.validation import ValidationError

_COLOR_HEX = {
    "black": "#1a1a1a", "brown": "#7B3F00", "red": "#e60000", "orange": "#ff8c00",
    "yellow": "#ffd700", "green": "#0a8a0a", "blue": "#0044cc", "violet": "#8a2be2",
    "gray": "#808080", "grey": "#808080", "white": "#f5f5f5",
    "gold": "#d4af37", "silver": "#c0c0c0",
}


def draw_resistor_diagram(bands: list[str], display_value: str, tolerance: str, output_path: str) -> str:
    """Draw a resistor body with its actual color bands, labeled with the decoded value."""
    bands = [b.strip().lower() for b in bands]
    for b in bands:
        if b not in _COLOR_HEX:
            raise ValidationError(f"'{b}' has no defined color for diagram rendering.")

    fig, ax = plt.subplots(figsize=(6, 2.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3)
    ax.axis("off")

    # Leads
    ax.plot([0, 2.5], [1.5, 1.5], color="#444444", linewidth=3, zorder=1)
    ax.plot([7.5, 10], [1.5, 1.5], color="#444444", linewidth=3, zorder=1)

    # Resistor body
    body = patches.FancyBboxPatch(
        (2.5, 0.7), 5.0, 1.6, boxstyle="round,pad=0,rounding_size=0.3",
        linewidth=1.5, edgecolor="#8a6a3d", facecolor="#e8c99a", zorder=2,
    )
    ax.add_patch(body)

    # Color bands, evenly spaced along the body, last band (tolerance) set apart near the right lead
    n = len(bands)
    body_start, body_end = 2.9, 7.1
    if n == 4:
        positions = [body_start + 0.55 * i for i in range(3)] + [body_end - 0.4]
    else:  # 5-band
        positions = [body_start + 0.5 * i for i in range(4)] + [body_end - 0.4]

    for color, x in zip(bands, positions):
        band = patches.Rectangle((x, 0.7), 0.35, 1.6, facecolor=_COLOR_HEX[color], edgecolor="none", zorder=3)
        ax.add_patch(band)

    ax.text(5, 2.55, f"{display_value}  {tolerance}", ha="center", va="bottom", fontsize=13, fontweight="bold")
    ax.text(5, 0.3, "  ".join(b.upper() for b in bands), ha="center", va="top", fontsize=8, color="#555555")

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def draw_555_astable_circuit(r1_ohms: float, r2_ohms: float, c_farads: float, output_path: str) -> str:
    """Draw the classic 555 timer astable-mode circuit with labeled component values."""
    if r1_ohms <= 0 or r2_ohms <= 0 or c_farads <= 0:
        raise ValidationError("R1, R2, and C must all be positive to draw the circuit.")

    def fmt_ohms(v: float) -> str:
        if v >= 1_000_000:
            return f"{v / 1_000_000:g}M\u03a9"
        if v >= 1_000:
            return f"{v / 1_000:g}k\u03a9"
        return f"{v:g}\u03a9"

    def fmt_farads(v: float) -> str:
        if v < 1e-9:
            return f"{v * 1e12:g}pF"
        if v < 1e-6:
            return f"{v * 1e9:g}nF"
        if v < 1e-3:
            return f"{v * 1e6:g}\u00b5F"
        return f"{v:g}F"

    d = schemdraw.Drawing()

    ic = elm.Ic(
        pins=[
            elm.IcPin(name="GND", side="left", pin="1"),
            elm.IcPin(name="TRIG", side="left", pin="2"),
            elm.IcPin(name="OUT", side="right", pin="3"),
            elm.IcPin(name="CTRL", side="bottom", pin="5"),
            elm.IcPin(name="THR", side="left", pin="6"),
            elm.IcPin(name="DIS", side="left", pin="7"),
            elm.IcPin(name="VCC", side="top", pin="8"),
        ],
        edgepadW=0.9, edgepadH=0.9, pinspacing=1.2,
    ).label("555", loc="center").at((3, 0))
    d += ic

    d += elm.Resistor().at(ic.DIS).up().length(1.5).label(f"R1\n{fmt_ohms(r1_ohms)}")
    d += elm.Dot().label("VCC", loc="top")

    d += elm.Resistor().at(ic.DIS).to(ic.THR).label(f"R2\n{fmt_ohms(r2_ohms)}")
    d += elm.Line().endpoints(ic.THR, ic.TRIG)  # THR and TRIG tied together, standard astable wiring

    d += elm.Capacitor().at(ic.TRIG).down().length(1.5).label(f"C\n{fmt_farads(c_farads)}", loc="bottom")
    d += elm.Ground()

    d += elm.Line().at(ic.OUT).right().length(1).label("OUTPUT", loc="right")

    d.save(output_path)
    return output_path

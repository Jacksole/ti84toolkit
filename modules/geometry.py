"""
Geometry module -- area/perimeter/volume/surface-area for common shapes,
Pythagorean theorem, and the distance formula. A surprising gap for a
toolkit that otherwise claims high-school-through-college math coverage.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from core.validation import ValidationError


def _check_positive(value: float, label: str) -> None:
    if value <= 0:
        raise ValidationError(f"{label} must be positive.")


# ---------------------------------------------------------------------------
# 2D shapes
# ---------------------------------------------------------------------------


@dataclass
class ShapeResult:
    shape: str
    measurements: dict[str, float]


def circle(radius: float) -> ShapeResult:
    _check_positive(radius, "Radius")
    return ShapeResult("circle", {"area": math.pi * radius**2, "circumference": 2 * math.pi * radius})


def rectangle(length: float, width: float) -> ShapeResult:
    _check_positive(length, "Length")
    _check_positive(width, "Width")
    return ShapeResult("rectangle", {"area": length * width, "perimeter": 2 * (length + width)})


def triangle_base_height(base: float, height: float) -> ShapeResult:
    _check_positive(base, "Base")
    _check_positive(height, "Height")
    return ShapeResult("triangle", {"area": 0.5 * base * height})


def triangle_sides(a: float, b: float, c: float) -> ShapeResult:
    """Area (Heron's formula) and perimeter of a triangle given all three side lengths."""
    for label, v in (("a", a), ("b", b), ("c", c)):
        _check_positive(v, f"Side {label}")
    if a + b <= c or a + c <= b or b + c <= a:
        raise ValidationError("These three side lengths cannot form a triangle (triangle inequality violated).")

    s = (a + b + c) / 2
    area = math.sqrt(s * (s - a) * (s - b) * (s - c))
    return ShapeResult("triangle", {"area": area, "perimeter": a + b + c})


# ---------------------------------------------------------------------------
# Pythagorean theorem and distance formula
# ---------------------------------------------------------------------------


def pythagorean_hypotenuse(leg_a: float, leg_b: float) -> float:
    _check_positive(leg_a, "Leg a")
    _check_positive(leg_b, "Leg b")
    return math.sqrt(leg_a**2 + leg_b**2)


def pythagorean_leg(hypotenuse: float, other_leg: float) -> float:
    _check_positive(hypotenuse, "Hypotenuse")
    _check_positive(other_leg, "Other leg")
    if other_leg >= hypotenuse:
        raise ValidationError("The known leg must be shorter than the hypotenuse.")
    return math.sqrt(hypotenuse**2 - other_leg**2)


def distance_2d(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def distance_3d(x1: float, y1: float, z1: float, x2: float, y2: float, z2: float) -> float:
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)


# ---------------------------------------------------------------------------
# 3D solids
# ---------------------------------------------------------------------------


def sphere(radius: float) -> ShapeResult:
    _check_positive(radius, "Radius")
    return ShapeResult("sphere", {
        "volume": (4 / 3) * math.pi * radius**3,
        "surface_area": 4 * math.pi * radius**2,
    })


def cylinder(radius: float, height: float) -> ShapeResult:
    _check_positive(radius, "Radius")
    _check_positive(height, "Height")
    return ShapeResult("cylinder", {
        "volume": math.pi * radius**2 * height,
        "surface_area": 2 * math.pi * radius * (radius + height),
    })


def cone(radius: float, height: float) -> ShapeResult:
    _check_positive(radius, "Radius")
    _check_positive(height, "Height")
    slant_height = math.sqrt(radius**2 + height**2)
    return ShapeResult("cone", {
        "volume": (1 / 3) * math.pi * radius**2 * height,
        "surface_area": math.pi * radius * (radius + slant_height),
    })


def box(length: float, width: float, height: float) -> ShapeResult:
    _check_positive(length, "Length")
    _check_positive(width, "Width")
    _check_positive(height, "Height")
    return ShapeResult("box", {
        "volume": length * width * height,
        "surface_area": 2 * (length * width + length * height + width * height),
    })

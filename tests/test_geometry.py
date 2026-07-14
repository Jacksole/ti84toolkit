import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.validation import ValidationError
from modules import geometry


class TestCircle:
    def test_area_and_circumference(self):
        result = geometry.circle(3)
        assert math.isclose(result.measurements["area"], math.pi * 9)
        assert math.isclose(result.measurements["circumference"], 2 * math.pi * 3)

    def test_rejects_nonpositive(self):
        with pytest.raises(ValidationError):
            geometry.circle(0)
        with pytest.raises(ValidationError):
            geometry.circle(-1)


class TestRectangle:
    def test_area_and_perimeter(self):
        result = geometry.rectangle(4, 5)
        assert result.measurements["area"] == 20
        assert result.measurements["perimeter"] == 18


class TestTriangle:
    def test_base_height(self):
        result = geometry.triangle_base_height(6, 4)
        assert result.measurements["area"] == 12

    def test_herons_formula_3_4_5(self):
        # classic 3-4-5 right triangle -> area 6
        result = geometry.triangle_sides(3, 4, 5)
        assert math.isclose(result.measurements["area"], 6)
        assert result.measurements["perimeter"] == 12

    def test_triangle_inequality_violation_raises(self):
        with pytest.raises(ValidationError):
            geometry.triangle_sides(1, 1, 10)


class TestPythagorean:
    def test_hypotenuse_3_4(self):
        assert math.isclose(geometry.pythagorean_hypotenuse(3, 4), 5)

    def test_leg_from_hypotenuse(self):
        assert math.isclose(geometry.pythagorean_leg(5, 3), 4)

    def test_leg_must_be_shorter_than_hypotenuse(self):
        with pytest.raises(ValidationError):
            geometry.pythagorean_leg(5, 6)


class TestDistance:
    def test_distance_2d(self):
        assert math.isclose(geometry.distance_2d(0, 0, 3, 4), 5)

    def test_distance_3d(self):
        assert math.isclose(geometry.distance_3d(0, 0, 0, 1, 2, 2), 3)


class TestSolids:
    def test_sphere(self):
        result = geometry.sphere(3)
        assert math.isclose(result.measurements["volume"], (4 / 3) * math.pi * 27)
        assert math.isclose(result.measurements["surface_area"], 4 * math.pi * 9)

    def test_cylinder(self):
        result = geometry.cylinder(2, 5)
        assert math.isclose(result.measurements["volume"], math.pi * 4 * 5)

    def test_cone(self):
        result = geometry.cone(3, 4)
        # slant height = 5 (3-4-5 triangle)
        expected_sa = math.pi * 3 * (3 + 5)
        assert math.isclose(result.measurements["surface_area"], expected_sa)

    def test_box(self):
        result = geometry.box(2, 3, 4)
        assert result.measurements["volume"] == 24
        assert result.measurements["surface_area"] == 2 * (6 + 8 + 12)

    def test_rejects_nonpositive_dimensions(self):
        with pytest.raises(ValidationError):
            geometry.box(0, 3, 4)

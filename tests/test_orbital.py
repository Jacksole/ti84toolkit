import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.validation import ValidationError
from modules import orbital


class TestBodies:
    def test_earth_mu(self):
        assert orbital.body_mu("earth") == pytest.approx(3.986004418e14)

    def test_case_insensitive(self):
        assert orbital.body_mu("EARTH") == orbital.body_mu("earth")

    def test_unknown_body_raises(self):
        with pytest.raises(ValidationError):
            orbital.body_mu("pluto")

    def test_body_radius(self):
        assert orbital.body_radius("earth") == pytest.approx(6_371_000.0)


class TestOrbitalPeriod:
    def test_iss_period_roughly_92_minutes(self):
        r = orbital.body_radius("earth") + 408_000
        period = orbital.orbital_period(r, orbital.body_mu("earth"))
        assert 90 * 60 < period < 95 * 60

    def test_moon_period_roughly_27_days(self):
        period = orbital.orbital_period(384_400_000, orbital.body_mu("earth"))
        days = period / 86400
        assert 27.0 < days < 27.5

    def test_rejects_nonpositive_values(self):
        with pytest.raises(ValidationError):
            orbital.orbital_period(0, orbital.body_mu("earth"))
        with pytest.raises(ValidationError):
            orbital.orbital_period(1000, 0)

    def test_inverse_round_trip(self):
        a = 7_000_000.0
        mu = orbital.body_mu("earth")
        period = orbital.orbital_period(a, mu)
        back = orbital.semi_major_axis_from_period(period, mu)
        assert math.isclose(back, a, rel_tol=1e-9)


class TestVelocities:
    def test_circular_velocity_matches_vis_viva_for_circular_orbit(self):
        r = 7_000_000.0
        mu = orbital.body_mu("earth")
        assert math.isclose(orbital.vis_viva_velocity(r, r, mu), orbital.circular_velocity(r, mu), rel_tol=1e-9)

    def test_escape_velocity_is_sqrt2_times_circular(self):
        r = 7_000_000.0
        mu = orbital.body_mu("earth")
        assert math.isclose(orbital.escape_velocity(r, mu), orbital.circular_velocity(r, mu) * math.sqrt(2), rel_tol=1e-9)

    def test_leo_circular_velocity_roughly_7_8_kms(self):
        r = orbital.body_radius("earth") + 400_000
        v = orbital.circular_velocity(r, orbital.body_mu("earth"))
        assert 7_500 < v < 7_800

    def test_vis_viva_rejects_unreachable_radius(self):
        with pytest.raises(ValidationError):
            orbital.vis_viva_velocity(100_000_000, 1_000_000, orbital.body_mu("earth"))

    def test_rejects_nonpositive_inputs(self):
        with pytest.raises(ValidationError):
            orbital.circular_velocity(0, orbital.body_mu("earth"))
        with pytest.raises(ValidationError):
            orbital.escape_velocity(7_000_000, 0)


class TestKeplerEquation:
    def test_circular_orbit_trivial_case(self):
        result = orbital.solve_kepler_equation(1.0, 0.0)
        assert math.isclose(result.eccentric_anomaly_rad, 1.0, abs_tol=1e-8)
        assert math.isclose(result.true_anomaly_rad, 1.0, abs_tol=1e-8)

    def test_converges_for_moderate_eccentricity(self):
        result = orbital.solve_kepler_equation(1.0, 0.5)
        M_check = result.eccentric_anomaly_rad - 0.5 * math.sin(result.eccentric_anomaly_rad)
        assert math.isclose(M_check, 1.0, abs_tol=1e-8)

    def test_converges_for_high_eccentricity(self):
        result = orbital.solve_kepler_equation(0.1, 0.95)
        M_check = result.eccentric_anomaly_rad - 0.95 * math.sin(result.eccentric_anomaly_rad)
        assert math.isclose(M_check, 0.1, abs_tol=1e-8)

    def test_rejects_eccentricity_out_of_range(self):
        with pytest.raises(ValidationError):
            orbital.solve_kepler_equation(1.0, 1.0)
        with pytest.raises(ValidationError):
            orbital.solve_kepler_equation(1.0, -0.1)

    def test_steps_present(self):
        result = orbital.solve_kepler_equation(1.0, 0.3)
        assert len(result.steps) > 0


class TestHohmannTransfer:
    def test_leo_to_geo(self):
        mu = orbital.body_mu("earth")
        r1 = orbital.body_radius("earth") + 300_000
        r2 = 42_164_000
        result = orbital.hohmann_transfer(r1, r2, mu)
        assert result.delta_v1_mps > 0
        assert result.delta_v2_mps > 0
        assert result.total_delta_v_mps == pytest.approx(result.delta_v1_mps + result.delta_v2_mps)
        assert 3_500 < result.total_delta_v_mps < 4_500

    def test_lowering_orbit(self):
        mu = orbital.body_mu("earth")
        result = orbital.hohmann_transfer(42_164_000, 7_000_000, mu)
        assert result.total_delta_v_mps > 0

    def test_rejects_equal_radii(self):
        with pytest.raises(ValidationError):
            orbital.hohmann_transfer(7_000_000, 7_000_000, orbital.body_mu("earth"))

    def test_rejects_nonpositive_values(self):
        with pytest.raises(ValidationError):
            orbital.hohmann_transfer(0, 7_000_000, orbital.body_mu("earth"))

    def test_transfer_time_positive(self):
        result = orbital.hohmann_transfer(7_000_000, 10_000_000, orbital.body_mu("earth"))
        assert result.transfer_time_s > 0

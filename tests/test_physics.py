import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.validation import ValidationError
from modules import physics


class TestKinematicsSolve:
    def test_solve_for_v_and_d_given_v0_a_t(self):
        # v0=0, a=2, t=5 -> v = 10, d = 25
        result = physics.kinematics_solve(v0=0, a=2, t=5)
        assert set(result.solved_for) == {"v", "d"}
        assert math.isclose(result.values["v"], 10)
        assert math.isclose(result.values["d"], 25)

    def test_solve_for_t_and_d_given_v0_v_a(self):
        # v0=0, v=20, a=4 -> t=5, d=50
        result = physics.kinematics_solve(v0=0, v=20, a=4)
        assert math.isclose(result.values["t"], 5)
        assert math.isclose(result.values["d"], 50)

    def test_solve_for_a_and_d_given_v0_v_t(self):
        # v0=0, v=10, t=2 -> a=5, d=10
        result = physics.kinematics_solve(v0=0, v=10, t=2)
        assert math.isclose(result.values["a"], 5)
        assert math.isclose(result.values["d"], 10)

    def test_solve_for_v0_and_a_given_v_t_d(self):
        # constant velocity case: v=10, t=4, d=40 -> v0=10, a=0
        result = physics.kinematics_solve(v=10, t=4, d=40)
        assert math.isclose(result.values["v0"], 10)
        assert math.isclose(result.values["a"], 0)

    def test_requires_exactly_three_known(self):
        with pytest.raises(ValidationError):
            physics.kinematics_solve(v0=0, a=2)  # only 2 known
        with pytest.raises(ValidationError):
            physics.kinematics_solve(v0=0, v=1, a=2, t=3)  # 4 known

    def test_negative_time_solution_rejected(self):
        # v0=10, v=0, d=10 implies deceleration; should pick the physically valid (t>=0) root
        result = physics.kinematics_solve(v0=10, v=0, d=10)
        assert result.values["t"] >= 0


class TestEnergyAndPower:
    def test_kinetic_energy(self):
        # 0.5 * 2kg * (3 m/s)^2 = 9 J
        result = physics.kinetic_energy(2, 3)
        assert math.isclose(result.joules, 9)

    def test_kinetic_energy_rejects_nonpositive_mass(self):
        with pytest.raises(ValidationError):
            physics.kinetic_energy(0, 5)
        with pytest.raises(ValidationError):
            physics.kinetic_energy(-1, 5)

    def test_potential_energy_default_gravity(self):
        # 1kg * 9.81 * 10m
        result = physics.potential_energy(1, 10)
        assert math.isclose(result.joules, 98.1)

    def test_potential_energy_custom_gravity(self):
        result = physics.potential_energy(1, 10, gravity=1.62)  # moon gravity
        assert math.isclose(result.joules, 16.2)

    def test_work_done(self):
        result = physics.work_done(10, 5)
        assert math.isclose(result.joules, 50)

    def test_power_from_work(self):
        result = physics.power_from_work(100, 4)
        assert math.isclose(result.watts, 25)

    def test_power_from_work_rejects_nonpositive_time(self):
        with pytest.raises(ValidationError):
            physics.power_from_work(100, 0)

    def test_power_from_force_velocity(self):
        result = physics.power_from_force_velocity(10, 5)
        assert math.isclose(result.watts, 50)

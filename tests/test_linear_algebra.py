import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.validation import ValidationError
from modules import linear_algebra as la


class TestVectors:
    def test_dot_product(self):
        assert la.vector_dot([1, 2, 3], [4, 5, 6]) == 32

    def test_dot_product_mismatched_length_raises(self):
        with pytest.raises(ValidationError):
            la.vector_dot([1, 2], [1, 2, 3])

    def test_cross_product_standard_basis(self):
        # i x j = k
        result = la.vector_cross([1, 0, 0], [0, 1, 0])
        assert [round(x, 9) for x in result] == [0, 0, 1]

    def test_cross_product_requires_3d(self):
        with pytest.raises(ValidationError):
            la.vector_cross([1, 2], [3, 4])

    def test_magnitude_3_4_5(self):
        assert math.isclose(la.vector_magnitude([3, 4]), 5)

    def test_normalize_returns_unit_vector(self):
        result = la.vector_normalize([3, 4])
        assert math.isclose(la.vector_magnitude(result), 1.0)

    def test_normalize_zero_vector_raises(self):
        with pytest.raises(ValidationError):
            la.vector_normalize([0, 0, 0])

    def test_angle_between_perpendicular_vectors(self):
        angle = la.vector_angle_between([1, 0], [0, 1])
        assert math.isclose(angle, math.pi / 2)

    def test_angle_between_parallel_vectors(self):
        angle = la.vector_angle_between([1, 0], [2, 0])
        assert math.isclose(angle, 0, abs_tol=1e-9)

    def test_empty_vector_raises(self):
        with pytest.raises(ValidationError):
            la.vector_magnitude([])


class TestMatrices:
    def test_add(self):
        result = la.matrix_add([[1, 2], [3, 4]], [[5, 6], [7, 8]])
        assert result.rows == [[6.0, 8.0], [10.0, 12.0]]

    def test_add_mismatched_dims_raises(self):
        with pytest.raises(ValidationError):
            la.matrix_add([[1, 2]], [[1, 2], [3, 4]])

    def test_multiply(self):
        result = la.matrix_multiply([[1, 2], [3, 4]], [[5, 6], [7, 8]])
        assert result.rows == [[19.0, 22.0], [43.0, 50.0]]

    def test_multiply_incompatible_dims_raises(self):
        with pytest.raises(ValidationError):
            la.matrix_multiply([[1, 2, 3]], [[1, 2]])

    def test_transpose(self):
        result = la.matrix_transpose([[1, 2, 3], [4, 5, 6]])
        assert result.rows == [[1.0, 4.0], [2.0, 5.0], [3.0, 6.0]]

    def test_determinant_2x2(self):
        # det([[1,2],[3,4]]) = 1*4 - 2*3 = -2
        assert math.isclose(la.matrix_determinant([[1, 2], [3, 4]]), -2)

    def test_determinant_requires_square(self):
        with pytest.raises(ValidationError):
            la.matrix_determinant([[1, 2, 3], [4, 5, 6]])

    def test_inverse(self):
        result = la.matrix_inverse([[4, 7], [2, 6]])
        # verify A * A^-1 == identity
        import numpy as np
        product = np.array([[4, 7], [2, 6]]) @ np.array(result.rows)
        assert np.allclose(product, np.eye(2))

    def test_inverse_singular_matrix_raises(self):
        with pytest.raises(ValidationError):
            la.matrix_inverse([[1, 2], [2, 4]])  # rows are linearly dependent

    def test_ragged_rows_raise(self):
        with pytest.raises(ValidationError):
            la.matrix_determinant([[1, 2], [3]])

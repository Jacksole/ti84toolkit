"""
Linear algebra module -- vector and matrix operations, backed by numpy
(already a transitive dependency via matplotlib).

Notable inclusion: the TI-84's [MATRX] button and dedicated matrix editor
are one of its signature, most-used features -- a calculator toolkit port
that skipped matrices would be missing something the original hardware was
genuinely known for.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from core.validation import ValidationError

# ---------------------------------------------------------------------------
# Vectors
# ---------------------------------------------------------------------------


def _to_vector(values: list[float]) -> np.ndarray:
    if not values:
        raise ValidationError("Vector cannot be empty.")
    return np.array(values, dtype=float)


def vector_dot(v1: list[float], v2: list[float]) -> float:
    a, b = _to_vector(v1), _to_vector(v2)
    if a.shape != b.shape:
        raise ValidationError(f"Vectors must be the same length (got {len(v1)} and {len(v2)}).")
    return float(np.dot(a, b))


def vector_cross(v1: list[float], v2: list[float]) -> list[float]:
    if len(v1) != 3 or len(v2) != 3:
        raise ValidationError("Cross product requires two 3D vectors.")
    a, b = _to_vector(v1), _to_vector(v2)
    return list(np.cross(a, b))


def vector_magnitude(v: list[float]) -> float:
    a = _to_vector(v)
    return float(np.linalg.norm(a))


def vector_normalize(v: list[float]) -> list[float]:
    a = _to_vector(v)
    magnitude = np.linalg.norm(a)
    if magnitude == 0:
        raise ValidationError("Cannot normalize the zero vector.")
    return list(a / magnitude)


def vector_angle_between(v1: list[float], v2: list[float]) -> float:
    """Angle between two vectors, in radians."""
    a, b = _to_vector(v1), _to_vector(v2)
    if a.shape != b.shape:
        raise ValidationError(f"Vectors must be the same length (got {len(v1)} and {len(v2)}).")
    mag_a, mag_b = np.linalg.norm(a), np.linalg.norm(b)
    if mag_a == 0 or mag_b == 0:
        raise ValidationError("Cannot compute an angle with the zero vector.")
    cos_theta = np.clip(np.dot(a, b) / (mag_a * mag_b), -1.0, 1.0)
    return float(np.arccos(cos_theta))


# ---------------------------------------------------------------------------
# Matrices
# ---------------------------------------------------------------------------


def _to_matrix(rows: list[list[float]]) -> np.ndarray:
    if not rows or not rows[0]:
        raise ValidationError("Matrix cannot be empty.")
    row_len = len(rows[0])
    if any(len(r) != row_len for r in rows):
        raise ValidationError("All matrix rows must have the same length.")
    return np.array(rows, dtype=float)


def _check_square(m: np.ndarray) -> None:
    if m.shape[0] != m.shape[1]:
        raise ValidationError(f"Matrix must be square (got {m.shape[0]}x{m.shape[1]}).")


@dataclass
class MatrixResult:
    rows: list[list[float]]


def matrix_add(a: list[list[float]], b: list[list[float]]) -> MatrixResult:
    ma, mb = _to_matrix(a), _to_matrix(b)
    if ma.shape != mb.shape:
        raise ValidationError(f"Matrices must have the same dimensions (got {ma.shape} and {mb.shape}).")
    return MatrixResult((ma + mb).tolist())


def matrix_multiply(a: list[list[float]], b: list[list[float]]) -> MatrixResult:
    ma, mb = _to_matrix(a), _to_matrix(b)
    if ma.shape[1] != mb.shape[0]:
        raise ValidationError(
            f"Cannot multiply a {ma.shape[0]}x{ma.shape[1]} matrix by a {mb.shape[0]}x{mb.shape[1]} matrix "
            f"-- inner dimensions must match."
        )
    return MatrixResult((ma @ mb).tolist())


def matrix_transpose(a: list[list[float]]) -> MatrixResult:
    ma = _to_matrix(a)
    return MatrixResult(ma.T.tolist())


def matrix_determinant(a: list[list[float]]) -> float:
    ma = _to_matrix(a)
    _check_square(ma)
    return float(np.linalg.det(ma))


def matrix_inverse(a: list[list[float]]) -> MatrixResult:
    ma = _to_matrix(a)
    _check_square(ma)
    det = np.linalg.det(ma)
    if abs(det) < 1e-12:
        raise ValidationError("Matrix is singular (determinant is zero) -- it has no inverse.")
    return MatrixResult(np.linalg.inv(ma).tolist())

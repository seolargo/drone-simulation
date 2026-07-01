"""
Rotation matrix özellik doğrulaması.

Rastgele yönelimler için R = Rz(ψ)Ry(θ)Rx(φ) üretilir ve ortogonallik/birim
determinant özellikleri sayısal olarak sınanır:
    R Rᵀ = I    (=> ‖R Rᵀ - I‖ ≈ 0)
    det(R) = 1
"""

import numpy as np

from physics import rotation_matrix


def run(n=200, seed=31):
    rng = np.random.default_rng(seed)
    dets, orth = [], []
    eye = np.eye(3)
    for _ in range(n):
        R = rotation_matrix(*rng.uniform(-np.pi, np.pi, 3))
        dets.append(float(np.linalg.det(R)))
        orth.append(float(np.max(np.abs(R @ R.T - eye))))
    return dets, orth

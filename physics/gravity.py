"""
Yerçekimi modeli (3 boyutlu).

Aşağı yönde (-z) sabit bir ivme üretir.
"""

import numpy as np

from config import GRAVITY


class Gravity:
    def __init__(self, g=GRAVITY):
        self.g = g

    def acceleration(self):
        """Anlık ivme vektörü [ax, ay, az] döndürür."""
        return np.array([0.0, 0.0, -self.g], dtype=float)

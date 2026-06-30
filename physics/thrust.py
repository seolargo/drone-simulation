"""
İtki (thrust) modeli.

Kontrol girdisine göre bir ivme vektörü üretir. Dikey itki, yerçekimini
yenebilmek için ondan büyük seçilir; böylece drone tırmanabilir/asılı kalabilir.

control: 3 bileşenli vektör, her biri genelde {-1, 0, +1}
    control[0] -> x (sağ/sol)
    control[1] -> y (ileri/geri)
    control[2] -> z (yukarı/aşağı)
"""

import numpy as np

from config import THRUST_UP, THRUST_HORIZ


class Thrust:
    def __init__(self, up=THRUST_UP, horiz=THRUST_HORIZ):
        self.up = up
        self.horiz = horiz

    def acceleration(self, control):
        cx, cy, cz = control
        return np.array([cx * self.horiz,
                         cy * self.horiz,
                         cz * self.up], dtype=float)

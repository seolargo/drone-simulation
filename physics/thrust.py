"""
İtki (thrust) modeli.

İtki, drone'un gövde-yukarı ekseni boyunca etki eder. Gövde eğildiğinde
(roll/pitch) bu eksen yana yatar ve itkinin bir bileşeni yatay olur —
gerçek bir quadcopter'ın nasıl ilerlediğinin temeli budur.

    body_up  : gövde-yukarı ekseninin dünya koordinatındaki yönü (birim vektör)
    throttle : 0..1 gaz seviyesi
"""

import numpy as np

from config import THRUST_MAX


class Thrust:
    def __init__(self, max_accel=THRUST_MAX):
        self.max_accel = max_accel

    def acceleration(self, body_up, throttle):
        return np.asarray(body_up, dtype=float) * (throttle * self.max_accel)

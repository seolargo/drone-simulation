"""
Drone varlığı (3 boyutlu quadcopter).

Yalnızca yerçekimine maruz kalır, yukarıdan (yüksek z) aşağı düşer ve
zeminde (z = 0) durur. Geometrisini dünya koordinatlarında üretir;
çizim katmanı bu noktaları ekrana yansıtır.
"""

import numpy as np

from config import DRONE_ARM, DRONE_ROTOR_R, DRONE_START_Z, ROTOR_SPIN
from physics import Gravity, semi_implicit_euler

# X-konfigürasyonu: dört kol köşegen yönlerde
_ARM_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]


class Drone:
    def __init__(self, gravity=None):
        self.gravity = gravity or Gravity()
        self.reset()

    def reset(self):
        """Drone'u tepe-ortaya, hareketsiz olarak yerleştirir."""
        self.pos = np.array([0.0, 0.0, DRONE_START_Z], dtype=float)
        self.vel = np.zeros(3, dtype=float)
        self.spin = 0.0
        self.landed = False

    def update(self, dt):
        if self.landed:
            return

        acc = self.gravity.acceleration()
        self.pos, self.vel = semi_implicit_euler(self.pos, self.vel, acc, dt)
        self.spin += ROTOR_SPIN * dt

        # Zemine (z = 0) değince dur
        if self.pos[2] <= 0.0:
            self.pos[2] = 0.0
            self.vel[:] = 0.0
            self.landed = True

    # --- Geometri (dünya koordinatları) ---------------------------------
    def world_parts(self):
        """
        Çizim için drone parçalarını dünya koordinatlarında döndürür:
            center : gövde merkezi
            arms   : [(p0, p1), ...] kol çizgileri
            rotors : [(circle_pts, blade_segs), ...] her pervane için
        """
        c = self.pos
        arms = []
        rotors = []
        for dx, dy in _ARM_DIRS:
            d = np.array([dx, dy, 0.0])
            d = d / np.linalg.norm(d) * DRONE_ARM
            tip = c + d
            arms.append((c, tip))
            rotors.append((self._circle(tip, DRONE_ROTOR_R),
                           self._blades(tip, DRONE_ROTOR_R, self.spin)))
        return {"center": c, "arms": arms, "rotors": rotors}

    @staticmethod
    def _circle(center, r, n=20):
        pts = []
        for i in range(n + 1):
            a = 2.0 * np.pi * i / n
            pts.append(center + np.array([r * np.cos(a), r * np.sin(a), 0.0]))
        return pts

    @staticmethod
    def _blades(center, r, spin):
        segs = []
        for k in range(2):          # iki çapraz kanat
            a = spin + k * np.pi / 2
            v = np.array([r * np.cos(a), r * np.sin(a), 0.0])
            segs.append((center - v, center + v))
        return segs

"""
Drone varlığı (3 boyutlu quadcopter).

Yerçekimi + kontrol edilebilen itkiye maruz kalır. Zemin (z = 0) bir tabandır:
drone üzerine konabilir, ama yeterli dikey itkiyle tekrar havalanabilir.
Geometrisini dünya koordinatlarında üretir; çizim katmanı bu noktaları yansıtır.
"""

import numpy as np

from config import (
    DRONE_ARM, DRONE_ROTOR_R, DRONE_START_Z, ROTOR_SPIN, GROUND_HALF,
)
from physics import Gravity, Thrust, semi_implicit_euler

# X-konfigürasyonu: dört kol köşegen yönlerde
_ARM_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]


class Drone:
    def __init__(self, gravity=None, thrust=None):
        self.gravity = gravity or Gravity()
        self.thrust = thrust or Thrust()
        self.reset()

    def reset(self):
        """Drone'u tepe-ortaya, hareketsiz olarak yerleştirir."""
        self.pos = np.array([0.0, 0.0, DRONE_START_Z], dtype=float)
        self.vel = np.zeros(3, dtype=float)
        self.control = np.zeros(3, dtype=float)   # [x, y, z] itki yönü
        self.spin = 0.0
        self.on_ground = False

    def update(self, dt):
        acc = self.gravity.acceleration() + self.thrust.acceleration(self.control)
        self.pos, self.vel = semi_implicit_euler(self.pos, self.vel, acc, dt)

        # Zemin tabanı: altına inemez, aşağı hızı sıfırlanır (ama yukarı serbest)
        if self.pos[2] <= 0.0:
            self.pos[2] = 0.0
            if self.vel[2] < 0.0:
                self.vel[2] = 0.0
            self.on_ground = True
        else:
            self.on_ground = False

        # Yatay sınırlar: ızgara içinde kalsın
        for i in (0, 1):
            if self.pos[i] < -GROUND_HALF:
                self.pos[i] = -GROUND_HALF
                self.vel[i] = 0.0
            elif self.pos[i] > GROUND_HALF:
                self.pos[i] = GROUND_HALF
                self.vel[i] = 0.0

        # Pervaneler: yerde boştayken dursun, aksi halde dönsün
        if not (self.on_ground and not self.control.any()):
            self.spin += ROTOR_SPIN * dt

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

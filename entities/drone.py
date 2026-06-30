"""
Drone varlığı (3 boyutlu quadcopter, tam yönelimli).

Durum:
    pos, vel            -> öteleme (dünya koordinatı)
    roll, pitch, yaw    -> yönelim (Euler açıları)
    throttle            -> gaz seviyesi (0..1)

İtki gövde-yukarı ekseni boyunca uygulanır; drone eğildiğinde (roll/pitch)
yatay uçuş oluşur. Roll/pitch tuş bırakılınca kendiliğinden düzlenir; yaw
döndüğü yerde kalır. Zemin (z = 0) havalanılabilir bir tabandır.

Kontrol girdisi (app tarafından doldurulur): self.control = [roll, pitch, yaw, throttle]
her biri genelde {-1, 0, +1}.
"""

import numpy as np

from config import (
    DRONE_ARM, DRONE_ROTOR_R, DRONE_START_Z, ROTOR_SPIN, GROUND_HALF,
    MAX_TILT, TILT_SLEW, YAW_RATE, THROTTLE_RATE,
)
from physics import Gravity, Thrust, rotation_matrix, semi_implicit_euler

# X-konfigürasyonu: dört kol köşegen yönlerde (gövde frame'i)
_ARM_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]


def _approach(cur, target, max_step):
    """cur değerini target'a doğru en fazla max_step kadar yaklaştırır."""
    d = target - cur
    if abs(d) <= max_step:
        return target
    return cur + max_step * np.sign(d)


class Drone:
    def __init__(self, gravity=None, thrust=None):
        self.gravity = gravity or Gravity()
        self.thrust = thrust or Thrust()
        self.reset()

    def reset(self):
        self.pos = np.array([0.0, 0.0, DRONE_START_Z], dtype=float)
        self.vel = np.zeros(3, dtype=float)
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        self.throttle = 0.0
        self.control = np.zeros(4, dtype=float)   # [roll, pitch, yaw, throttle]
        self.spin = 0.0
        self.R = np.eye(3)
        self.on_ground = False

    def update(self, dt):
        c_roll, c_pitch, c_yaw, c_throttle = self.control

        # Yönelim: roll/pitch hedefe doğru dengelenir, yaw entegre edilir
        self.roll = _approach(self.roll, c_roll * MAX_TILT, TILT_SLEW * dt)
        self.pitch = _approach(self.pitch, c_pitch * MAX_TILT, TILT_SLEW * dt)
        self.yaw += c_yaw * YAW_RATE * dt
        self.throttle = float(np.clip(self.throttle + c_throttle * THROTTLE_RATE * dt, 0.0, 1.0))

        self.R = rotation_matrix(self.roll, self.pitch, self.yaw)
        body_up = self.R[:, 2]   # gövde-yukarı ekseni dünya koordinatında

        acc = self.gravity.acceleration() + self.thrust.acceleration(body_up, self.throttle)
        self.pos, self.vel = semi_implicit_euler(self.pos, self.vel, acc, dt)

        # Zemin tabanı
        if self.pos[2] <= 0.0:
            self.pos[2] = 0.0
            if self.vel[2] < 0.0:
                self.vel[2] = 0.0
            self.on_ground = True
        else:
            self.on_ground = False

        # Yatay sınırlar
        for i in (0, 1):
            if self.pos[i] < -GROUND_HALF:
                self.pos[i] = -GROUND_HALF
                self.vel[i] = 0.0
            elif self.pos[i] > GROUND_HALF:
                self.pos[i] = GROUND_HALF
                self.vel[i] = 0.0

        # Pervane dönüşü gaz ile orantılı (yerde boştayken dursun)
        if self.throttle > 0.01 or not self.on_ground:
            self.spin += ROTOR_SPIN * (0.4 + self.throttle) * dt

    # --- Geometri (dünya koordinatları, yönelim uygulanmış) -------------
    def world_parts(self):
        R, c = self.R, self.pos

        def tf(local):
            return R @ np.asarray(local, dtype=float) + c

        arms = []
        rotors = []
        for dx, dy in _ARM_DIRS:
            d = np.array([dx, dy, 0.0])
            tip = d / np.linalg.norm(d) * DRONE_ARM
            arms.append((tf((0, 0, 0)), tf(tip)))
            circle = [tf(p) for p in self._circle(tip, DRONE_ROTOR_R)]
            blades = [(tf(a), tf(b)) for a, b in self._blades(tip, DRONE_ROTOR_R, self.spin)]
            rotors.append((circle, blades))

        # Burun göstergesi (gövde +y = ileri yön) — yaw/pitch'i görünür kılar
        nose = (tf((0, 0, 0)), tf((0, DRONE_ARM * 1.4, 0)))

        return {"center": tf((0, 0, 0)), "arms": arms, "rotors": rotors, "nose": nose}

    @staticmethod
    def _circle(center, r, n=20):
        pts = []
        for i in range(n + 1):
            a = 2.0 * np.pi * i / n
            pts.append(np.asarray(center, float) + np.array([r * np.cos(a), r * np.sin(a), 0.0]))
        return pts

    @staticmethod
    def _blades(center, r, spin):
        center = np.asarray(center, float)
        segs = []
        for k in range(2):
            a = spin + k * np.pi / 2
            v = np.array([r * np.cos(a), r * np.sin(a), 0.0])
            segs.append((center - v, center + v))
        return segs

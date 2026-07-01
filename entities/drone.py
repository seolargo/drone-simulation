"""
Drone varlığı (3 boyutlu quadcopter, PID otopilotlu).

Kontrol artık doğrudan eğim vermez; tuşlar PID kontrolcülere HEDEF verir:
    ok tuşları -> hedef yatay hız (dünya x/y)
        -> yatay hız PID'leri eğim açısını (roll/pitch) üretir
    W/S        -> hedef irtifa (z) değişir
        -> irtifa PID'i gazı üretir (hover üstüne düzeltme)
    A/D        -> yaw (manuel)

Tuş bırakıldığında hedef hız sıfırlanır; PID drone'u frenleyip olduğu
yerde askıda tutar. İrtifa PID'i, eğilince düşen dikey itkiyi telafi eder.
"""

import numpy as np

from config import (
    DRONE_ARM, DRONE_ROTOR_R, DRONE_START_Z, ROTOR_SPIN, BOUND_XY, CEIL_Z,
    MAX_TILT, YAW_RATE, CLIMB_RATE, HOVER_THROTTLE, CMD_SPEED, POS_KP,
    VEL_KP, VEL_KI, VEL_KD, ALT_KP, ALT_KI, ALT_KD, PID_DERIV_TAU,
    WIND_ACCEL, WIND_TAU, SENSOR_VEL_NOISE, SENSOR_POS_NOISE,
    ANTIWINDUP, AW_KB,
)
from physics import Gravity, Thrust, rotation_matrix, PID, Wind, semi_implicit_euler

# X-konfigürasyonu: dört kol köşegen yönlerde (gövde frame'i)
_ARM_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]


class Drone:
    def __init__(self, gravity=None, thrust=None, antiwindup=None):
        self.gravity = gravity or Gravity()
        self.thrust = thrust or Thrust()
        self.antiwindup = antiwindup or ANTIWINDUP
        aw = dict(antiwindup=self.antiwindup, kb=AW_KB)
        # Yatay hız -> eğim açısı PID'leri (çıkış MAX_TILT ile sınırlı)
        self.vx_pid = PID(VEL_KP, VEL_KI, VEL_KD, out_limit=MAX_TILT, integral_limit=3.0, deriv_tau=PID_DERIV_TAU, **aw)
        self.vy_pid = PID(VEL_KP, VEL_KI, VEL_KD, out_limit=MAX_TILT, integral_limit=3.0, deriv_tau=PID_DERIV_TAU, **aw)
        # İrtifa -> gaz düzeltmesi PID'i
        self.alt_pid = PID(ALT_KP, ALT_KI, ALT_KD, out_limit=0.45, integral_limit=2.0, deriv_tau=PID_DERIV_TAU, **aw)
        # Bozucu etkiler: türbülans + sensör gürültüsü (gerçekçi hover titremesi)
        self.wind = Wind(WIND_ACCEL, WIND_TAU)
        self.rng = np.random.default_rng(7)
        self.reset()

    def reset(self):
        self.pos = np.array([0.0, 0.0, DRONE_START_Z], dtype=float)
        self.vel = np.zeros(3, dtype=float)
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        self.throttle = HOVER_THROTTLE
        self.z_target = DRONE_START_Z

        # Kontrol girdileri (app tarafından doldurulur)
        self.cmd_vel = np.zeros(2, dtype=float)   # hedef yatay hız [vx, vy] (dünya)
        self.cmd_climb = 0.0                      # W/S -> irtifa hedefi değişimi
        self.cmd_yaw = 0.0                        # A/D -> yaw
        self.pos_target = np.zeros(2, dtype=float)  # komut yokken tutulan konum (x, y)

        self.spin = 0.0
        self.R = np.eye(3)
        self.on_ground = False
        for pid in (self.vx_pid, self.vy_pid, self.alt_pid):
            pid.reset()
        self.wind.reset()

    @property
    def pid_active(self):
        """Yön tuşlarıyla hız komutu verildi mi (PID 'devrede' göstergesi)."""
        return bool(np.any(self.cmd_vel))

    def update(self, dt):
        # --- Yaw: manuel ---
        self.yaw += self.cmd_yaw * YAW_RATE * dt

        # --- İrtifa hedefi (W/S ile kayar) ---
        self.z_target = float(np.clip(self.z_target + self.cmd_climb * CLIMB_RATE * dt,
                                      0.0, CEIL_Z))

        # --- Sensör ölçümleri (gürültülü) — PID gerçek değeri değil, bunları görür ---
        vx_meas = self.vel[0] + self.rng.normal(0.0, SENSOR_VEL_NOISE)
        vy_meas = self.vel[1] + self.rng.normal(0.0, SENSOR_VEL_NOISE)
        x_meas = self.pos[0] + self.rng.normal(0.0, SENSOR_POS_NOISE)
        y_meas = self.pos[1] + self.rng.normal(0.0, SENSOR_POS_NOISE)
        z_meas = self.pos[2] + self.rng.normal(0.0, SENSOR_POS_NOISE)

        # --- Dış konum döngüsü -> hız hedefi ---
        # Komut varsa o hızı izle (ve konum hedefini sürükle); yoksa konumu tut.
        if np.any(self.cmd_vel):
            vel_sp = self.cmd_vel.copy()
            self.pos_target[:] = self.pos[:2]
        else:
            err = self.pos_target - np.array([x_meas, y_meas])
            vel_sp = np.clip(POS_KP * err, -CMD_SPEED, CMD_SPEED)

        # --- İç yatay hız PID -> eğim açısı (türev hız ölçümü üzerinden) ---
        # roll(+) gövde-yukarıyı +x'e yatırır; pitch(-) +y'ye yatırır.
        self.roll = self.vx_pid.update(vel_sp[0] - vx_meas, dt, measurement=vx_meas)
        self.pitch = -self.vy_pid.update(vel_sp[1] - vy_meas, dt, measurement=vy_meas)

        # --- İrtifa PID -> gaz (hover ileri beslemesi + düzeltme) ---
        self.throttle = float(np.clip(
            HOVER_THROTTLE + self.alt_pid.update(self.z_target - z_meas, dt, measurement=z_meas),
            0.0, 1.0))

        # --- Dinamik (rüzgâr türbülansı dahil) ---
        self.R = rotation_matrix(self.roll, self.pitch, self.yaw)
        body_up = self.R[:, 2]
        acc = (self.gravity.acceleration()
               + self.thrust.acceleration(body_up, self.throttle)
               + self.wind.acceleration(dt))
        self.pos, self.vel = semi_implicit_euler(self.pos, self.vel, acc, dt)

        # --- Sınırlar: drone ekran/oyun alanından çıkamaz ---
        if self.pos[2] <= 0.0:
            self.pos[2] = 0.0
            if self.vel[2] < 0.0:
                self.vel[2] = 0.0
            self.on_ground = True
        else:
            self.on_ground = False
            if self.pos[2] >= CEIL_Z:
                self.pos[2] = CEIL_Z
                if self.vel[2] > 0.0:
                    self.vel[2] = 0.0

        for i in (0, 1):
            if self.pos[i] < -BOUND_XY:
                self.pos[i] = -BOUND_XY
                self.vel[i] = 0.0
            elif self.pos[i] > BOUND_XY:
                self.pos[i] = BOUND_XY
                self.vel[i] = 0.0

        # Pervane dönüşü gaz ile orantılı
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

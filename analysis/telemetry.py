"""
Telemetri kaydı — simülasyon boyunca drone durumunu kare kare biriktirir.

Grafik üretimi için gereken tüm zaman serilerini tutar. Açılar dereceye çevrilir.
"""

import numpy as np


class Telemetry:
    def __init__(self):
        self.t = []
        self.x = []; self.y = []; self.z = []          # gerçek konum
        self.tx = []; self.ty = []; self.tz = []        # hedef konum (pos_target, z_target)
        self.roll = []; self.pitch = []; self.yaw = []  # yönelim (derece)
        self.throttle = []
        # Kontrol girdisi u(t) — x ekseni hız PID'inin çıkışı ve P/I/D terimleri (derece)
        self.u = []; self.up = []; self.ui = []; self.ud = []
        # Fiziksel seviye: torklar (τφ,τθ,τψ) ve rotor hızları (ω1..ω4)
        self.tphi = []; self.ttheta = []; self.tpsi = []
        self.w1 = []; self.w2 = []; self.w3 = []; self.w4 = []
        # Gövde çerçevesi hızlar (u, v, w)
        self.bu = []; self.bv = []; self.bw = []

    def record(self, t, d):
        self.t.append(float(t))
        self.x.append(float(d.pos[0]))
        self.y.append(float(d.pos[1]))
        self.z.append(float(d.pos[2]))
        self.tx.append(float(d.pos_target[0]))
        self.ty.append(float(d.pos_target[1]))
        self.tz.append(float(d.z_target))
        self.roll.append(float(np.degrees(d.roll)))
        self.pitch.append(float(np.degrees(d.pitch)))
        self.yaw.append(float(np.degrees(d.yaw)))
        self.throttle.append(float(d.throttle))
        # u(t): x ekseni PID çıkışı (drone.roll = vx_pid.out) ve terimleri
        pid = d.vx_pid
        self.u.append(float(np.degrees(pid.out)))
        self.up.append(float(np.degrees(pid.p_term)))
        self.ui.append(float(np.degrees(pid.i_term)))
        self.ud.append(float(np.degrees(pid.d_term)))
        # Torklar ve rotor hızları
        self.tphi.append(d.torque[0]); self.ttheta.append(d.torque[1]); self.tpsi.append(d.torque[2])
        self.w1.append(d.rotor[0]); self.w2.append(d.rotor[1]); self.w3.append(d.rotor[2]); self.w4.append(d.rotor[3])
        self.bu.append(float(d.vel_body[0])); self.bv.append(float(d.vel_body[1])); self.bw.append(float(d.vel_body[2]))

    def __len__(self):
        return len(self.t)

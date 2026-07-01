"""
IMU sensör modeli (MPU-6050) — 3 ivmeölçer + 3 jiroskop.

İvmeölçer: yerçekimini (statik) + dinamik ivmeyi ölçer. Bias (gerçek değerle ölçüm
farkı; ör. 9.81 yerine 9.75) + yüksek-frekans gürültü içerir; gürültü alçak-geçiren
filtreyle azaltılır.

Jiroskop: açısal hızı ölçer. Düşük-frekans rastgele-yürüyüş (random-walk) biası
zamanla birikir; entegre edilip açı elde edilince drift oluşur.

g^n = [0, 0, g]^T,  g = 9.80665 m/s² (standart yerçekimi).
"""

import numpy as np

from physics import rotation_matrix

G = 9.80665

# İvmeölçer
ACC_BIAS_Z = -0.06      # z bias (9.81 -> ~9.75)
ACC_NOISE = 0.18        # yüksek-frekans gürültü (m/s²)
ACC_CUTOFF = 5.0        # alçak-geçiren kesim frekansı (Hz)

# Jiroskop
GYRO_BIAS0 = 0.5        # başlangıç biası (°/s)
GYRO_RW = 0.25          # rastgele-yürüyüş şiddeti (°/s / sqrt(s))
GYRO_NOISE = 0.4        # beyaz gürültü (°/s)


def _lowpass(x, dt, fc):
    rc = 1.0 / (2.0 * np.pi * fc)
    alpha = dt / (rc + dt)
    y = x[0] if len(x) else 0.0
    out = []
    for v in x:
        y += alpha * (v - y)
        out.append(y)
    return out


def accel_z(roll_deg, pitch_deg, yaw_deg, dt, seed=11):
    """Gövde z-ivmeölçeri: gerçek (≈g·cosφcosθ), ham (bias+gürültü), filtreli."""
    rng = np.random.default_rng(seed)
    g_world = np.array([0.0, 0.0, G])
    true, raw = [], []
    for r, p, y in zip(roll_deg, pitch_deg, yaw_deg):
        R = rotation_matrix(np.radians(r), np.radians(p), np.radians(y))
        az = float((R.T @ g_world)[2])          # gövde z bileşeni
        true.append(az)
        raw.append(az + ACC_BIAS_Z + rng.normal(0.0, ACC_NOISE))
    filt = _lowpass(raw, dt, ACC_CUTOFF)
    return true, raw, filt


def gyro_drift(angle_deg, dt, seed=13):
    """Jiroskop entegrasyonu: gerçek açı vs bias+random-walk ile biriken drift."""
    rng = np.random.default_rng(seed)
    n = len(angle_deg)
    true = list(map(float, angle_deg))
    bias = GYRO_BIAS0
    est = true[0] if n else 0.0
    out = [est]
    for i in range(1, n):
        true_rate = (true[i] - true[i - 1]) / dt
        bias += GYRO_RW * np.sqrt(dt) * rng.normal()      # rastgele-yürüyüş
        meas_rate = true_rate + bias + rng.normal(0.0, GYRO_NOISE)
        est += meas_rate * dt                              # entegrasyon -> drift
        out.append(est)
    return true, out

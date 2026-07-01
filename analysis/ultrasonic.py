"""
Ultrasonik mesafe sensörü modeli (HC-SR04).

Ses dalgası gönderilir, yansıyan dalganın dönüşü ölçülür; mesafe:

    d = (t_end - t_start) / 2 * 340   (340 m/s ≈ 20°C'de sesin hızı)

Zamanlama gürültüsü (yüksek frekans) ve ara sıra hatalı eko (spike) eklenir.
Gürültüyü bastırmak için 1. mertebe alçak-geçiren filtre uygulanır (kesim
frekansının üstündeki bileşenleri zayıflatır).
"""

import numpy as np

SOUND_SPEED = 340.0     # m/s
NOISE_STD = 0.05        # m — ölçüm gürültüsü (zamanlama kaynaklı)
SPIKE_PROB = 0.02       # ara sıra hatalı eko olasılığı
SPIKE_MAG = 0.5         # m — hatalı eko büyüklüğü
CUTOFF_HZ = 3.0         # alçak-geçiren filtre kesim frekansı


def simulate(z_true, dt, seed=5):
    """
    z_true : gerçek mesafe (drone irtifası) zaman serisi
    dt     : örnekleme adımı (s)
    -> (raw, filtered) ölçüm serileri
    """
    rng = np.random.default_rng(seed)
    rc = 1.0 / (2.0 * np.pi * CUTOFF_HZ)
    alpha = dt / (rc + dt)              # EMA katsayısı (kesim frekansından)

    raw, filt = [], []
    y = float(z_true[0]) if len(z_true) else 0.0
    for z in z_true:
        # zaman-uçuş ölçümü: d = (Δt/2)·c ; zamanlama gürültüsü -> mesafe gürültüsü
        d = float(z) + rng.normal(0.0, NOISE_STD)
        if rng.random() < SPIKE_PROB:
            d += rng.choice([-1.0, 1.0]) * SPIKE_MAG * rng.random()
        d = max(0.0, d)
        y += alpha * (d - y)           # 1. mertebe alçak-geçiren filtre
        raw.append(d)
        filt.append(y)
    return raw, filt

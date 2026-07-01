"""
GPS alıcısı — yalancı-menzil (pseudorange) çoklu-konumlama.

Her uydu için: ρ_i = ||pos - sat_i|| + c·b + gürültü  (c·b = saat biası, B).
En az 4 uydudan (x, y, z, B) Gauss-Newton en-küçük-kareler ile çözülür. GPS
düşük hızlıdır (~8 Hz) ve mutlak konum verir (IMU/manyetometre veremez).
"""

import numpy as np

# Yayılmış uydu geometrisi (yerel yalancı-GPS, birim koordinat)
SATS = np.array([
    [60.0, 40.0, 80.0],
    [-70.0, 50.0, 90.0],
    [30.0, -80.0, 100.0],
    [-50.0, -60.0, 85.0],
    [10.0, 90.0, 95.0],
])
PSEUDO_NOISE = 0.15     # yalancı-menzil gürültüsü
CLOCK_BIAS = 2.5        # B = c·b (bilinmeyen saat biası)
RATE_HZ = 8.0           # GPS güncelleme hızı


def _solve(guess, ranges):
    x = np.array([guess[0], guess[1], guess[2], 0.0])
    for _ in range(8):
        p = x[:3]
        d = np.linalg.norm(SATS - p, axis=1)
        res = ranges - (d + x[3])
        J = np.empty((len(SATS), 4))
        J[:, :3] = (p - SATS) / d[:, None]
        J[:, 3] = 1.0
        dx = np.linalg.lstsq(J, res, rcond=None)[0]
        x = x + dx
        if np.linalg.norm(dx) < 1e-7:
            break
    return x[:3]


def run(x_true, y_true, z_true, dt, seed=21):
    rng = np.random.default_rng(seed)
    step = max(1, int(round(1.0 / (RATE_HZ * dt))))
    ex, ey = [], []
    last = (x_true[0], y_true[0])
    for i in range(len(x_true)):
        if i % step == 0:
            pos = np.array([x_true[i], y_true[i], z_true[i]])
            ranges = np.linalg.norm(SATS - pos, axis=1) + CLOCK_BIAS + rng.normal(0, PSEUDO_NOISE, len(SATS))
            est = _solve(pos + rng.normal(0, 1.0, 3), ranges)
            last = (est[0], est[1])
        ex.append(last[0])
        ey.append(last[1])
    return ex, ey

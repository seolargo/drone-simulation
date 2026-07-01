"""
Optik akış sensörü — yer dokusunun kayması ile yatay hız.

İki kare arasında yer deseni (Δx_px) piksel kayarsa:
    v_x = (h/f) · (Δx_px / Δt)
h yerden yükseklik (ultrasonik/barometre), f piksel cinsinden odak uzaklığı.
GPS yokken (kapalı alan) IMU'yu tamamlar. Piksel kuantizasyonu + gürültü içerir.
"""

import numpy as np

F_PX = 220.0        # odak uzaklığı (piksel)
FLOW_NOISE = 0.5    # piksel gürültüsü


def run(x_true, z_true, dt, seed=25):
    rng = np.random.default_rng(seed)
    vx_true = [0.0]
    vx_of = [0.0]
    for i in range(1, len(x_true)):
        vt = (x_true[i] - x_true[i - 1]) / dt
        h = max(0.2, float(z_true[i]))
        dpx = vt * F_PX / h * dt                          # gerçek piksel kayması
        dpx_meas = round(dpx + rng.normal(0.0, FLOW_NOISE))  # kuantize + gürültü
        v = (h / F_PX) * (dpx_meas / dt)
        vx_true.append(vt)
        vx_of.append(v)
    return vx_true, vx_of

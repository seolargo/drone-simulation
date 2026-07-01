"""
Time-of-Flight / Lidar mesafe sensörü.

Ultrasonik sensöre alternatif: ses yerine ışık (kızılötesi/lazer) gönderir,
yansımanın dönüş süresini ölçer:
    d = c·(t_end - t_start) / 2
Işık sesten çok daha hızlı olduğundan ToF/Lidar daha doğru ve uzun menzilli;
engelden kaçınma ve sürü içinde göreli mesafe için uygundur.
"""

import numpy as np

TOF_NOISE = 0.008   # çok düşük gürültü (ultrasoniğe göre)


def run(z_true, seed=27):
    rng = np.random.default_rng(seed)
    return [float(z) + rng.normal(0.0, TOF_NOISE) for z in z_true]

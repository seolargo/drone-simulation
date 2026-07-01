"""
Barometre — atmosfer basıncından irtifa.

Basınç irtifayla düşer; barometrik formülle yüksekliğe çevrilir:
    h = (T0/L) · (1 - (P/P0)^(R·L/(g·M)))
Ham basınç gürültülü olduğundan tahmini irtifa alçak-geçiren filtreyle yumuşatılır.
"""

import numpy as np

P0 = 101325.0       # deniz seviyesi basıncı (Pa)
T0 = 288.15         # referans sıcaklık (K)
L = 0.0065          # sıcaklık düşüş oranı (K/m)
G = 9.80665
M = 0.0289644       # havanın molar kütlesi (kg/mol)
R = 8.31447         # evrensel gaz sabiti
PRESS_NOISE = 4.0   # basınç gürültüsü (Pa)
CUTOFF = 0.8        # alçak-geçiren kesim (Hz)

_EXP = R * L / (G * M)


def _pressure(h):
    return P0 * (1.0 - L * h / T0) ** (G * M / (R * L))


def _altitude(P):
    return (T0 / L) * (1.0 - (P / P0) ** _EXP)


def run(z_true, dt, seed=23):
    rng = np.random.default_rng(seed)
    raw = [_altitude(_pressure(float(z)) + rng.normal(0.0, PRESS_NOISE)) for z in z_true]
    rc = 1.0 / (2.0 * np.pi * CUTOFF)
    alpha = dt / (rc + dt)
    filt = []
    y = raw[0] if raw else 0.0
    for v in raw:
        y += alpha * (v - y)
        filt.append(y)
    return raw, filt

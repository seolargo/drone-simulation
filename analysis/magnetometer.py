"""
Manyetometre sensör modeli + hard/soft iron kalibrasyonu.

Dünya manyetik alanı m^n (enleme bağlı eğim açısıyla) gövdeye döndürülür,
sonra bozulmalar eklenir:

    m_meas = D^{-1} (R_n^b m^n + b) + w

  R_n^b : dünya->gövde dönüşü ( = R(roll,pitch,yaw)^T )
  b     : hard iron ofseti (yerel manyetik bozulma — motor mıknatısı vb.)
  D     : soft iron matrisi (köşegen) — çemberi elipse çevirir
  w     : ölçüm gürültüsü

Kalibrasyon: seviyede yaw taraması yapılıp eksen min/max'larından merkez (b) ve
yarı-genişlikler (d_i) bulunur; d_ii = d̄/d̄_i ile soft iron kestirilir. Düzeltilmiş
ölçümden yaw (heading) geri kazanılır.
"""

import numpy as np

from physics import rotation_matrix

INCL = np.radians(60.0)                                  # manyetik eğim (orta enlem)
M_N = np.array([0.0, np.cos(INCL), -np.sin(INCL)])       # kuzey(+y), aşağı(-z)

HARD_IRON = np.array([0.35, -0.22, 0.18])                # b — ofset (illüstratif)
SOFT_IRON = np.array([1.0, 0.62, 0.82])                  # D köşegen — elips
NOISE_STD = 0.008


def _measure(roll, pitch, yaw, rng):
    R = rotation_matrix(roll, pitch, yaw)                # gövde->dünya
    m_true = R.T @ M_N                                   # dünya->gövde
    m = (m_true + HARD_IRON) / SOFT_IRON                 # D^{-1}(m_true + b), D köşegen
    return m + rng.normal(0.0, NOISE_STD, 3)


def _heading(mx, my):
    return float(np.degrees(np.arctan2(mx, my)) % 360.0)


def run(seed=3, n=260):
    """Seviyede yaw taraması + kalibrasyon. Grafik verisi döndürür."""
    rng = np.random.default_rng(seed)
    yaws = np.linspace(0.0, 2.0 * np.pi, n)

    raw = np.array([_measure(0.0, 0.0, y, rng) for y in yaws])   # (n,3)

    # 2D (x,y) hard/soft iron kalibrasyonu — yatay düzlem çemberi
    mn = raw[:, :2].min(axis=0)
    mx = raw[:, :2].max(axis=0)
    b = (mx + mn) / 2.0                     # hard iron merkezi
    d_i = (mx - mn) / 2.0                   # yarı-genişlikler
    dbar = float(d_i.mean())               # ortalama yarıçap
    D = dbar / d_i                          # soft iron köşegen (d_ii)

    cal = (raw[:, :2] - b) * D             # düzeltilmiş (merkezli çember)

    yaw_true = [float(np.degrees(y)) for y in yaws]
    head_raw = [_heading(raw[i, 0], raw[i, 1]) for i in range(n)]
    head_cal = [_heading(cal[i, 0], cal[i, 1]) for i in range(n)]

    return {
        "raw_xy": raw[:, :2].tolist(),
        "cal_xy": cal.tolist(),
        "yaw_true": yaw_true,
        "head_raw": head_raw,
        "head_cal": head_cal,
        "b": b.tolist(),
        "D": D.tolist(),
        "dbar": dbar,
    }

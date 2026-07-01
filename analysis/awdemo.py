"""
Anti-windup gösterimi — simülasyondaki gerçek PID sınıfını, doygunluğu zorlayan
basit bir sistemde çalıştırır.

Sistem: çift-integratör (konum), dar aktüatör limiti (out_limit). Referansa büyük
bir adım verilince aktüatör uzun süre doyar; "none" modunda integral sarar ve büyük
aşım oluşur. "clamp" ve "backcalc" bu sarmayı engelleyip aşımı giderir.
"""

from physics import PID

# Windup'ı belirgin kılan parametreler (deneysel ayarlandı)
KP, KI, KD = 1.2, 0.6, 1.5
UMAX = 0.35          # aktüatör doygunluk sınırı (out_limit)
KB = 4.0             # back-calculation izleme kazancı
REF = 1.0            # referans adımı
DT = 0.02
DURATION = 14.0


def run(mode):
    """mode: 'none' | 'clamp' | 'backcalc' -> (t, x, i_term) listeleri."""
    pid = PID(KP, KI, KD, out_limit=UMAX, deriv_tau=0.05, antiwindup=mode, kb=KB)
    x = 0.0
    v = 0.0
    t = 0.0
    ts, xs, it = [], [], []
    for _ in range(int(DURATION / DT)):
        u = pid.update(REF - x, DT, measurement=x)   # u zaten UMAX'e kırpılı
        v += u * DT
        x += v * DT
        t += DT
        ts.append(t)
        xs.append(x)
        it.append(pid.i_term)
    return ts, xs, it

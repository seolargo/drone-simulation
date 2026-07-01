"""
Relay feedback auto-tune (Åström-Hägglund).

Geri besleme döngüsüne geçici bir röle (on-off) konur; sistem kontrollü, sürekli
bir salınıma girer. Salınımın genliği (a) ve periyodundan (Tu) kritik kazanç
    Ku = 4d / (pi * a)          (röle tanımlayıcı fonksiyonu)
kestirilir (h = röle genliği, a = ölçülen salınım genliği). Sistemi elle
kararsızlığa itmeye gerek kalmaz.

Burada yatay hız döngüsü ayarlanır: röle çıkışı = eğim komutu; plant = eğim iç
dinamiği (2. mertebe) + hız integratörü (vx' = g·sin(eğim)). Ölçülen Ku, Tu'dan
PID kazançları Tyreus-Luyben kuralıyla bulunur (relay auto-tune için Z-N'den daha
muhafazakâr, daha az aşımlı):
    Kp = Ku / 3.2,   Ti = 2.2 Tu,   Td = Tu / 6.3
"""

import numpy as np

from config import GRAVITY, ATT_WN, ATT_ZETA
from physics import attitude_step

RELAY_D = 0.10       # röle eğim genliği (rad ~ 5.7°)
DT = 1.0 / 240.0     # deney zaman adımı (ince — periyot ölçümü için)
DURATION = 8.0       # deney süresi (s)


def relay_tune(d=RELAY_D, dt=DT, duration=DURATION):
    """Relay deneyini koşturur; (kp, ki, kd, info) döndürür."""
    roll = rate = vx = 0.0
    relay = d
    t = 0.0
    ts, vxs, us, rel = [], [], [], []
    crossings = []
    prev_vx = 0.0

    for _ in range(int(duration / dt)):
        e = -vx                       # hedef hız 0; hata = -vx
        if e > 0.0:
            relay = d
        elif e < 0.0:
            relay = -d                # ideal röle (histerezissiz); periyodu eğim dinamiği belirler
        roll, rate = attitude_step(roll, rate, relay, ATT_WN, ATT_ZETA, dt)
        vx += GRAVITY * np.sin(roll) * dt
        t += dt
        ts.append(t); vxs.append(vx); us.append(np.degrees(roll)); rel.append(relay)
        if prev_vx < 0.0 <= vx:       # yükselen sıfır geçişi
            crossings.append(t)
        prev_vx = vx

    # Kararlı hâl (ikinci yarı) üzerinden genlik ve periyot
    seg = np.array(vxs[len(vxs) // 2:])
    a = (seg.max() - seg.min()) / 2.0
    late = [c for c in crossings if c > duration * 0.5]
    Tu = (late[-1] - late[0]) / (len(late) - 1) if len(late) > 1 else float("nan")
    Ku = 4.0 * d / (np.pi * a) if a > 1e-9 else float("nan")

    # Tyreus-Luyben (relay auto-tune için Z-N'den daha muhafazakâr, daha az aşımlı)
    kp = Ku / 3.2
    Ti = 2.2 * Tu
    Td = Tu / 6.3
    ki = kp / Ti if Ti > 0 else 0.0
    kd = kp * Td

    info = {
        "Ku": float(Ku), "Tu": float(Tu), "d": float(d), "amplitude": float(a),
        "kp": float(kp), "ki": float(ki), "kd": float(kd), "rule": "Tyreus-Luyben",
        "t": ts, "vx": vxs, "u": us, "relay": rel,
    }
    return kp, ki, kd, info

"""
Telsiz haberleşme modeli — APC-220 (434 MHz, 9600 bps, -112 dBm duyarlılık).

Link bütçesi: alınan güç mesafeyle log-uzaklık path-loss ile düşer:
    RSSI(d) = P_tx - [PL(1m) + 10·n·log10(d)]
Duyarlılığın (-112 dBm) altına inince bağlantı kopar → menzil ~1000 m.

Downlink: telemetri (sensör değerleri) 9600 bps'lik UART üzerinden gönderilir;
çerçeve hızıyla örnek-tut (sample-and-hold) uygulanır ve ara sıra paket kaybı olur.
GFSK/modülasyon detayı paket-kaybı olasılığına soyutlanmıştır.
"""

import numpy as np

BITRATE = 9600          # bps
SENSITIVITY = -112      # dBm
TX_POWER = 13           # dBm (~20 mW)
PL_1M = 25.2            # dB — 434 MHz'de 1 m serbest-uzay yol kaybı
PLE = 3.3               # yol-kaybı üsteli (görüş hattı ~1000 m için)

FRAME_BYTES = 40        # bir telemetri çerçevesi (birkaç sensör, ASCII)
LOSS = 0.04             # paket kaybı olasılığı


def link_budget(dmax=1200.0, n=220):
    """RSSI(d) ve duyarlılığı geçtiği menzil (m)."""
    ds = np.linspace(1.0, dmax, n)
    rssi = TX_POWER - (PL_1M + 10.0 * PLE * np.log10(ds))
    idx = int(np.argmin(np.abs(rssi - SENSITIVITY)))
    return ds.tolist(), rssi.tolist(), float(ds[idx])


def downlink(signal, dt, seed=17):
    """
    signal : gönderilecek telemetri serisi (ör. irtifa z)
    -> (received, frame_rate) — COM-port'ta görülen (rate-limitli + kayıplı) seri
    """
    rng = np.random.default_rng(seed)
    frame_rate = BITRATE / (FRAME_BYTES * 8)     # çerçeve/s
    interval = 1.0 / frame_rate
    recv = []
    last = float(signal[0]) if len(signal) else 0.0
    t = 0.0
    t_next = 0.0
    for v in signal:
        if t >= t_next:
            if rng.random() > LOSS:
                last = float(v)                  # başarılı çerçeve
            # kayıpsa eski değer tutulur (stale)
            t_next += interval
        recv.append(last)
        t += dt
    return recv, frame_rate

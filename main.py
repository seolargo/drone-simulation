"""
Drone simülasyonu — giriş noktası.

Drone'a yalnızca yerçekimi etki eder ve yukarıdan aşağıya düşer.

Çalıştırma:
    ~/Downloads/simulation/.venv/bin/python main.py
    ... main.py --antiwindup {none|clamp|backcalc}   (varsayılan: backcalc)

Kontroller:
    BOŞLUK : duraklat / devam et
    R      : sıfırla (drone'u tepeye geri al)
    ESC/Q  : çıkış

Kod yapısı:
    config.py    -> ayarlar/sabitler
    physics/     -> fizik modelleri (yerçekimi, entegrasyon)
    entities/    -> drone gibi nesneler
    rendering/   -> çizim
    simulation/  -> uygulama döngüsü
"""

import argparse

from simulation import App
from config import ANTIWINDUP


def main():
    ap = argparse.ArgumentParser(description="3B PID drone simülasyonu")
    ap.add_argument("--antiwindup", choices=["none", "clamp", "backcalc"],
                    default=ANTIWINDUP,
                    help="integral anti-windup yöntemi (varsayılan: %(default)s)")
    args = ap.parse_args()
    App(antiwindup=args.antiwindup).run()


if __name__ == "__main__":
    main()

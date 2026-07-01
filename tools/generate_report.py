"""
Scriptli senaryo — pencere açmadan sabit bir uçuş dizisi koşturup
web/outputs/ grafiklerini üretir. Tekrarlanabilir (deterministik tohum).

Çalıştırma:
    ~/Downloads/simulation/.venv/bin/python tools/generate_report.py

Konum kontrolü doğrudan pos_target / z_target adım komutlarıyla sürülür; böylece
"hedef vs gerçek" grafikleri klasik adım-tepkisi (state tracking) biçiminde çıkar.
"""

import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from entities import Drone            # noqa: E402  (pygame'e bağımlı değil)
from analysis.telemetry import Telemetry  # noqa: E402
from analysis import report           # noqa: E402

DT = 1.0 / 60.0


def main():
    drone = Drone()
    tel = Telemetry()
    t = 0.0

    def run(dur, pos=None, z=None, yaw=0.0):
        nonlocal t
        if pos is not None:
            drone.pos_target[:] = pos    # doğrudan konum hedefi (cmd_vel = 0 iken tutulur)
        if z is not None:
            drone.z_target = z
        for _ in range(int(dur / DT)):
            drone.cmd_vel[:] = (0.0, 0.0)
            drone.cmd_climb = 0.0
            drone.cmd_yaw = yaw
            drone.update(DT)
            t += DT
            tel.record(t, drone)

    run(2.0)                       # yerleşme / hover
    run(3.0, pos=(3.0, 0.0))       # X adımı  -> state tracking
    run(3.0, pos=(3.0, 2.5))       # Y adımı
    run(2.0, z=2.5)                # irtifa adımı
    run(2.0, yaw=1.0)              # yaw dönüşü
    run(2.0, yaw=0.0)              # hover / titreme

    out = ROOT / "web" / "outputs"
    when = datetime.now().strftime("%Y-%m-%d %H:%M")
    ok = report.generate(tel, out, source="scriptli senaryo", when=when)
    print(("OK, " + str(len(tel)) + " örnek -> ") if ok else "yetersiz veri -> ", out)


if __name__ == "__main__":
    main()

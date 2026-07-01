"""
Rapor üretimi — telemetriden 4 SVG grafik + manifest.js yazar.

Grafikler web/outputs/ altına yazılır; web sayfası bunları manifest.js üzerinden
okuyup gösterir. Her koşuda üzerine yazılır (yeniden generate).
"""

import json
from pathlib import Path

from .svgchart import line_chart
from . import awdemo


def _series(t, v, label, color, dashed=False):
    return {"label": label, "color": color, "pts": list(zip(t, v)), "dashed": dashed}


def generate(tel, out_dir, source="", when=""):
    """Yeterli örnek varsa grafikleri üretir; True/False döner."""
    if len(tel) < 2:
        return False

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    t = tel.t
    charts = []

    def write(name, svg, title, group=None):
        (out / name).write_text(svg, encoding="utf-8")
        entry = {"file": name, "title": title}
        if group:
            entry["group"] = group
        charts.append(entry)

    # 1) Position tracking
    write("konum.svg", line_chart("Position tracking", "t (s)", "birim", [
        _series(t, tel.tx, "hedef x", "#8a93ac", dashed=True),
        _series(t, tel.x, "x", "#6fa8e6"),
        _series(t, tel.ty, "hedef y", "#c0895a", dashed=True),
        _series(t, tel.y, "y", "#f0b446"),
    ]), "Position tracking")

    # 2) Tracking error
    ex = [a - b for a, b in zip(tel.tx, tel.x)]
    ey = [a - b for a, b in zip(tel.ty, tel.y)]
    write("hata.svg", line_chart("Tracking error  e(t) = x_d - x", "t (s)", "hata", [
        _series(t, ex, "e_x", "#e0685f"),
        _series(t, ey, "e_y", "#f0b446"),
    ]), "Tracking error e(t)")

    # 3) Attitude (PID output)
    write("yonelim.svg", line_chart("Attitude (PID output)", "t (s)", "derece", [
        _series(t, tel.roll, "roll", "#6fa8e6"),
        _series(t, tel.pitch, "pitch", "#f0b446"),
        _series(t, tel.yaw, "yaw", "#8ad0a0"),
    ]), "Attitude (roll/pitch/yaw)")

    # 4) Altitude & throttle (gaz, grafik y-aralığına ölçeklenir)
    zmin = min(min(tel.z), min(tel.tz))
    zmax = max(max(tel.z), max(tel.tz))
    if zmax - zmin < 1e-9:
        zmax = zmin + 1.0
    thr = [zmin + th * (zmax - zmin) for th in tel.throttle]
    write("irtifa.svg", line_chart("Altitude & throttle", "t (s)", "z (birim)", [
        _series(t, tel.tz, "hedef z", "#8a93ac", dashed=True),
        _series(t, tel.z, "z", "#6fa8e6"),
        _series(t, thr, "gaz % (olcekli)", "#e0685f", dashed=True),
    ]), "Altitude & throttle")

    # 5) Control input u(t) = Kp*e + Ki*∫e + Kd*de/dt  (x ekseni PID çıkışı)
    write("kontrol.svg", line_chart("Control input  u(t) = Kp*e + Ki*Ie + Kd*de/dt", "t (s)", "u (derece)", [
        _series(t, tel.u, "u (toplam)", "#6fa8e6"),
        _series(t, tel.up, "P", "#f0b446"),
        _series(t, tel.ui, "I", "#8ad0a0"),
        _series(t, tel.ud, "D", "#e0685f"),
    ]), "Control input u(t)")

    # 6-7) Anti-windup karşılaştırması (aynı PID sınıfı, doygun sistemde)
    tn, xn, in_ = awdemo.run("none")
    tc, xc, ic = awdemo.run("clamp")
    tb, xb, ib = awdemo.run("backcalc")
    write("aw_output.svg", line_chart("Anti-windup - system output x(t)", "t (s)", "x", [
        _series(tn, [awdemo.REF] * len(tn), "target", "#8a93ac", dashed=True),
        _series(tn, xn, "no anti-windup", "#e0685f"),
        _series(tc, xc, "clamp", "#f0b446"),
        _series(tb, xb, "back-calculation", "#8ad0a0"),
    ]), "Anti-windup: system output", group="antiwindup")
    write("aw_integral.svg", line_chart("Anti-windup - integral term", "t (s)", "I", [
        _series(tn, in_, "no anti-windup", "#e0685f"),
        _series(tc, ic, "clamp", "#f0b446"),
        _series(tb, ib, "back-calculation", "#8ad0a0"),
    ]), "Anti-windup: integral term", group="antiwindup")

    manifest = {
        "generatedAt": when,
        "durationSec": round(t[-1] - t[0], 1),
        "samples": len(tel),
        "source": source,
        "charts": charts,
    }
    (out / "manifest.js").write_text(
        "window.SIM_OUTPUTS = " + json.dumps(manifest, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    return True

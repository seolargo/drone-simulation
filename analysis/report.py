"""
Rapor üretimi — telemetriden 4 SVG grafik + manifest.js yazar.

Grafikler web/outputs/ altına yazılır; web sayfası bunları manifest.js üzerinden
okuyup gösterir. Her koşuda üzerine yazılır (yeniden generate).
"""

import json
from pathlib import Path

from .svgchart import line_chart, relay_chart, xy_chart
from . import awdemo
from . import magnetometer


def _series(t, v, label, color, dashed=False):
    return {"label": label, "color": color, "pts": list(zip(t, v)), "dashed": dashed}


def generate(tel, out_dir, source="", when="", tune=None):
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

    # 6) Gövde torkları (PD kontrol -> τ = I·açısal ivme)
    write("tork.svg", line_chart("Body torques  τ = I·(angular accel)", "t (s)", "τ (N·m)", [
        _series(t, tel.tphi, "τφ (roll)", "#6fa8e6"),
        _series(t, tel.ttheta, "τθ (pitch)", "#f0b446"),
        _series(t, tel.tpsi, "τψ (yaw)", "#8ad0a0"),
    ]), "Body torques (τφ, τθ, τψ)")

    # 7) Rotor hızları (mixing denklemleri: ω_i² = T/4k ± τ/2kL ± τψ/4b)
    write("rotor.svg", line_chart("Rotor speeds  ω1..ω4", "t (s)", "ω (rad/s)", [
        _series(t, tel.w1, "ω1", "#6fa8e6"),
        _series(t, tel.w2, "ω2", "#f0b446"),
        _series(t, tel.w3, "ω3", "#8ad0a0"),
        _series(t, tel.w4, "ω4", "#e0685f"),
    ]), "Rotor speeds (ω1..ω4)")

    # 8-9) Anti-windup karşılaştırması (aynı PID sınıfı, doygun sistemde)
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

    # 10-11) Manyetometre — hard/soft iron kalibrasyonu
    mg = magnetometer.run()
    write("mag_cal.svg", xy_chart("Magnetometer  m_x - m_y", "m_x", "m_y", [
        {"label": "ham (hard/soft iron)", "color": "#e0685f", "pts": mg["raw_xy"]},
        {"label": "kalibre", "color": "#8ad0a0", "pts": mg["cal_xy"]},
    ]), "Magnetometer: hard/soft iron", group="mag")
    write("mag_head.svg", line_chart("Heading — kalibrasyon etkisi", "gercek yaw (derece)", "kestirim (derece)", [
        _series(mg["yaw_true"], mg["yaw_true"], "ideal (y=x)", "#8a93ac", dashed=True),
        _series(mg["yaw_true"], mg["head_raw"], "ham", "#e0685f"),
        _series(mg["yaw_true"], mg["head_cal"], "kalibre", "#8ad0a0"),
    ]), "Magnetometer: heading", group="mag")
    mag_meta = {"b": [round(v, 3) for v in mg["b"]], "D": [round(v, 3) for v in mg["D"]]}

    # 8) Relay feedback auto-tune deneyi (varsa) — açıklamalı salınım diyagramı
    tune_meta = None
    if tune and tune.get("vx"):
        t_end = tune["t"][-1]
        idx = [i for i, tt in enumerate(tune["t"]) if tt >= t_end - 2.2]
        t0 = tune["t"][idx[0]]
        tw = [tune["t"][i] - t0 for i in idx]
        vw = [tune["vx"][i] for i in idx]
        rw = [tune["relay"][i] for i in idx]
        write("autotune.svg",
              relay_chart(tw, vw, rw, a=tune["amplitude"], Tu=tune["Tu"],
                          Ku=tune["Ku"], d=tune["d"]),
              "Relay feedback experiment", group="autotune")
        tune_meta = {k: round(tune[k], 4) for k in ("Ku", "Tu", "kp", "ki", "kd")}
        tune_meta["rule"] = tune["rule"]

    manifest = {
        "generatedAt": when,
        "durationSec": round(t[-1] - t[0], 1),
        "samples": len(tel),
        "source": source,
        "tune": tune_meta,
        "mag": mag_meta,
        "charts": charts,
    }
    (out / "manifest.js").write_text(
        "window.SIM_OUTPUTS = " + json.dumps(manifest, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    return True

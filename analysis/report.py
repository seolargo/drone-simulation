"""
Rapor üretimi — telemetriden 4 SVG grafik + manifest.js yazar.

Grafikler web/outputs/ altına yazılır; web sayfası bunları manifest.js üzerinden
okuyup gösterir. Her koşuda üzerine yazılır (yeniden generate).
"""

import json
from pathlib import Path

from .svgchart import line_chart, relay_chart, xy_chart
from physics import air_density
from config import THRUST_COEF
from . import awdemo
from . import magnetometer
from . import motor
from . import ultrasonic
from . import imu
from . import comm
from . import gps as gpsmod
from . import barometer
from . import opticalflow
from . import tof as tofmod
from . import geodetic as geo
from . import rotcheck
from . import compfilter


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

    # 12) Ultrasonik mesafe sensörü (HC-SR04) — gerçek irtifadan (z) ölçüm + filtre
    dt_s = (t[1] - t[0]) if len(t) > 1 else 1.0 / 60.0
    us_raw, us_filt = ultrasonic.simulate(tel.z, dt_s)
    write("ultra.svg", line_chart("Ultrasonic distance (HC-SR04)", "t (s)", "mesafe (m)", [
        _series(t, tel.z, "gercek mesafe", "#8a93ac", dashed=True),
        _series(t, us_raw, "ham (gurultulu)", "#e0685f"),
        _series(t, us_filt, "alcak-geciren filtre", "#6fa8e6"),
    ]), "Ultrasonic distance (HC-SR04)", group="ultrasonic")

    # 13-14) IMU (MPU-6050) — ivmeölçer (bias+gürültü+filtre) ve jiroskop drifti
    acc_t, acc_r, acc_f = imu.accel_z(tel.roll, tel.pitch, tel.yaw, dt_s)
    write("imu_acc.svg", line_chart("Accelerometer z (MPU-6050)", "t (s)", "a_z (m/s²)", [
        _series(t, acc_t, "gercek (g·cosφcosθ)", "#8a93ac", dashed=True),
        _series(t, acc_r, "ham (bias+gurultu)", "#e0685f"),
        _series(t, acc_f, "alcak-geciren filtre", "#6fa8e6"),
    ]), "Accelerometer (bias + noise)", group="imu")
    gyro_t, gyro_e = imu.gyro_drift(tel.yaw, dt_s)
    write("imu_gyro.svg", line_chart("Gyroscope integration drift (yaw)", "t (s)", "yaw (derece)", [
        _series(t, gyro_t, "gercek yaw", "#8a93ac", dashed=True),
        _series(t, gyro_e, "jiroskop (entegre, drift)", "#f0b446"),
    ]), "Gyroscope drift", group="imu")

    # 15-16) Telsiz haberleşme (APC-220) — link bütçesi + telemetri downlink
    ds, rssi, rng_m = comm.link_budget()
    write("comm_link.svg", line_chart("APC-220 link budget", "mesafe (m)", "RSSI (dBm)", [
        _series(ds, rssi, "alinan guc (RSSI)", "#6fa8e6"),
        _series(ds, [comm.SENSITIVITY] * len(ds), "duyarlilik (-112 dBm)", "#e0685f", dashed=True),
    ]), "APC-220 link budget", group="comm")
    recv, frate = comm.downlink(tel.z, dt_s)
    write("comm_down.svg", line_chart("Telemetry downlink (9600 bps)", "t (s)", "z (m)", [
        _series(t, tel.z, "gonderilen (60 Hz)", "#8a93ac", dashed=True),
        _series(t, recv, "alinan (COM-port)", "#f0b446"),
    ]), "Telemetry downlink", group="comm")

    # 17) GPS — çoklu-konumlama ile mutlak yatay konum
    gx, gy = gpsmod.run(tel.x, tel.y, tel.z, dt_s)
    write("gps.svg", xy_chart("GPS position (multilateration)", "x", "y", [
        {"label": "gercek yol", "color": "#8a93ac", "pts": list(zip(tel.x, tel.y)), "dashed": True},
        {"label": "GPS kestirimi", "color": "#f0b446", "pts": list(zip(gx, gy))},
    ]), "GPS position", group="gps")

    # 18) Barometre — basınçtan irtifa (+ alçak-geçiren filtre)
    b_raw, b_filt = barometer.run(tel.z, dt_s)
    write("baro.svg", line_chart("Barometric altitude", "t (s)", "irtifa (m)", [
        _series(t, tel.z, "gercek irtifa", "#8a93ac", dashed=True),
        _series(t, b_raw, "ham (basinc gurultusu)", "#e0685f"),
        _series(t, b_filt, "alcak-geciren filtre", "#6fa8e6"),
    ]), "Barometric altitude", group="baro")

    # 19) Optik akış — yatay hız (piksel kaymasından)
    of_true, of_est = opticalflow.run(tel.x, tel.z, dt_s)
    write("flow.svg", line_chart("Optical flow velocity (vx)", "t (s)", "vx (m/s)", [
        _series(t, of_true, "gercek vx", "#8a93ac", dashed=True),
        _series(t, of_est, "optik akis kestirimi", "#6fa8e6"),
    ]), "Optical flow velocity", group="flow")

    # 20) ToF / Lidar — ultrasoniğe göre daha doğru
    us_raw2, _ = ultrasonic.simulate(tel.z, dt_s, seed=9)
    tof_vals = tofmod.run(tel.z)
    write("tof.svg", line_chart("ToF / Lidar distance", "t (s)", "mesafe (m)", [
        _series(t, tel.z, "gercek mesafe", "#8a93ac", dashed=True),
        _series(t, us_raw2, "ultrasonik (gurultulu)", "#e0685f"),
        _series(t, tof_vals, "ToF / Lidar", "#6fa8e6"),
    ]), "ToF / Lidar distance", group="tof")

    # 21) Hava yoğunluğu — irtifayla değişim (itki ∝ ρ)
    alts = [h * 100.0 for h in range(0, 51)]        # 0..5000 m
    write("atmos.svg", line_chart("Air density vs altitude", "irtifa (m)", "ρ (kg/m³)", [
        _series(alts, [air_density(h) for h in alts], "hava yogunlugu ρ", "#6fa8e6"),
    ]), "Air density vs altitude", group="atmos")

    # 22) Pervane thrust — blade element sonucu T_i = k·ω_i² (uçuş boyunca rotor başına)
    write("prop.svg", line_chart("Propeller thrust  T_i = k·ω_i²", "t (s)", "T_i (N)", [
        _series(t, [THRUST_COEF * w * w for w in tel.w1], "T1", "#6fa8e6"),
        _series(t, [THRUST_COEF * w * w for w in tel.w2], "T2", "#f0b446"),
        _series(t, [THRUST_COEF * w * w for w in tel.w3], "T3", "#8ad0a0"),
        _series(t, [THRUST_COEF * w * w for w in tel.w4], "T4", "#e0685f"),
    ]), "Propeller thrust (T = k·ω²)", group="prop")

    # 23) DC motor dinamiği — gerilim adımına back-EMF tepkisi
    mt, mw, mi = motor.run()
    wmax = max(mw) or 1.0
    imax = max(mi) or 1.0
    write("motor.svg", line_chart("DC motor step response (back-EMF)", "t (s)", "normalize", [
        _series(mt, [w / wmax for w in mw], "ω (hiz)", "#6fa8e6"),
        _series(mt, [i / imax for i in mi], "akim I", "#e0685f"),
    ]), "DC motor (back-EMF)", group="motor")

    # 24) Rotation matrix doğrulaması: R Rᵀ = I, det(R) = 1
    dets, orth = rotcheck.run()
    ridx = list(range(len(dets)))
    write("rotcheck.svg", line_chart("Rotation matrix: det(R)=1, ||R Rt - I|| = 0", "ornek", "deger", [
        _series(ridx, dets, "det(R)", "#6fa8e6"),
        _series(ridx, orth, "||R Rt - I|| (~0)", "#e0685f"),
    ]), "Rotation matrix verification", group="rotcheck")

    # 25) Geodetic (enlem/boylam) — GPS uçuş yörüngesinin geodetic dönüşümü
    lats, lons = geo.run(tel.x, tel.y, tel.z)
    write("geo.svg", xy_chart("GPS trajectory (geodetic)", "boylam (derece)", "enlem (derece)", [
        {"label": "ucus yorungesi", "color": "#f0b446", "pts": list(zip(lons, lats))},
    ]), "GPS geodetic (lat/lon)", group="geo")

    # 26) Complementary filter — jiroskop + ivmeölçer füzyonu (pitch)
    c_true, c_gyro, c_acc, c_comp = compfilter.run(tel.pitch, dt_s)
    write("compfilter.svg", line_chart("Complementary filter (pitch)", "t (s)", "aci (derece)", [
        _series(t, c_true, "gercek", "#8a93ac", dashed=True),
        _series(t, c_gyro, "sadece jiroskop (drift)", "#f0b446"),
        _series(t, c_acc, "sadece ivmeolcer (gurultu)", "#e0685f"),
        _series(t, c_comp, "complementary (fuzyon)", "#6fa8e6"),
    ]), "Complementary filter", group="fusion")

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

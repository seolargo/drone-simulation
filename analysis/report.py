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
from . import kalman


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
    write("konum.svg", line_chart("Position tracking", "t (s)", "position", [
        _series(t, tel.tx, "target x", "#8a93ac", dashed=True),
        _series(t, tel.x, "x", "#6fa8e6"),
        _series(t, tel.ty, "target y", "#c0895a", dashed=True),
        _series(t, tel.y, "y", "#f0b446"),
    ]), "Position tracking", group="flight")

    # 2) Tracking error
    ex = [a - b for a, b in zip(tel.tx, tel.x)]
    ey = [a - b for a, b in zip(tel.ty, tel.y)]
    write("hata.svg", line_chart("Tracking error", "t (s)", "error", [
        _series(t, ex, "error x", "#e0685f"),
        _series(t, ey, "error y", "#f0b446"),
    ]), "Tracking error", group="flight")

    # 3) Attitude
    write("yonelim.svg", line_chart("Attitude", "t (s)", "degrees", [
        _series(t, tel.roll, "roll", "#6fa8e6"),
        _series(t, tel.pitch, "pitch", "#f0b446"),
        _series(t, tel.yaw, "yaw", "#8ad0a0"),
    ]), "Attitude", group="flight")

    # 4) Altitude & throttle
    zmin = min(min(tel.z), min(tel.tz))
    zmax = max(max(tel.z), max(tel.tz))
    if zmax - zmin < 1e-9:
        zmax = zmin + 1.0
    thr = [zmin + th * (zmax - zmin) for th in tel.throttle]
    write("irtifa.svg", line_chart("Altitude & throttle", "t (s)", "z", [
        _series(t, tel.tz, "target z", "#8a93ac", dashed=True),
        _series(t, tel.z, "z", "#6fa8e6"),
        _series(t, thr, "throttle (scaled)", "#e0685f", dashed=True),
    ]), "Altitude & throttle", group="flight")

    # 5) Control input (P, I, D terms)
    write("kontrol.svg", line_chart("Control input", "t (s)", "degrees", [
        _series(t, tel.u, "total", "#6fa8e6"),
        _series(t, tel.up, "P", "#f0b446"),
        _series(t, tel.ui, "I", "#8ad0a0"),
        _series(t, tel.ud, "D", "#e0685f"),
    ]), "Control input", group="flight")

    # 6) Body torques
    write("tork.svg", line_chart("Body torques", "t (s)", "torque (N·m)", [
        _series(t, tel.tphi, "roll", "#6fa8e6"),
        _series(t, tel.ttheta, "pitch", "#f0b446"),
        _series(t, tel.tpsi, "yaw", "#8ad0a0"),
    ]), "Body torques", group="flight")

    # 7) Rotor speeds
    write("rotor.svg", line_chart("Rotor speeds", "t (s)", "rad/s", [
        _series(t, tel.w1, "rotor 1", "#6fa8e6"),
        _series(t, tel.w2, "rotor 2", "#f0b446"),
        _series(t, tel.w3, "rotor 3", "#8ad0a0"),
        _series(t, tel.w4, "rotor 4", "#e0685f"),
    ]), "Rotor speeds", group="flight")

    # 8-9) Anti-windup karşılaştırması (aynı PID sınıfı, doygun sistemde)
    tn, xn, in_ = awdemo.run("none")
    tc, xc, ic = awdemo.run("clamp")
    tb, xb, ib = awdemo.run("backcalc")
    write("aw_output.svg", line_chart("Anti-windup: system output", "t (s)", "output", [
        _series(tn, [awdemo.REF] * len(tn), "target", "#8a93ac", dashed=True),
        _series(tn, xn, "no anti-windup", "#e0685f"),
        _series(tc, xc, "clamp", "#f0b446"),
        _series(tb, xb, "back-calculation", "#8ad0a0"),
    ]), "Anti-windup: system output", group="antiwindup")
    write("aw_integral.svg", line_chart("Anti-windup: integral term", "t (s)", "integral", [
        _series(tn, in_, "no anti-windup", "#e0685f"),
        _series(tc, ic, "clamp", "#f0b446"),
        _series(tb, ib, "back-calculation", "#8ad0a0"),
    ]), "Anti-windup: integral term", group="antiwindup")

    # Magnetometer — hard/soft iron calibration
    mg = magnetometer.run()
    write("mag_cal.svg", xy_chart("Magnetometer calibration", "m_x", "m_y", [
        {"label": "raw", "color": "#e0685f", "pts": mg["raw_xy"]},
        {"label": "calibrated", "color": "#8ad0a0", "pts": mg["cal_xy"]},
    ]), "Magnetometer calibration", group="mag")
    write("mag_head.svg", line_chart("Magnetometer heading", "true yaw (deg)", "estimate (deg)", [
        _series(mg["yaw_true"], mg["yaw_true"], "ideal", "#8a93ac", dashed=True),
        _series(mg["yaw_true"], mg["head_raw"], "raw", "#e0685f"),
        _series(mg["yaw_true"], mg["head_cal"], "calibrated", "#8ad0a0"),
    ]), "Magnetometer heading", group="mag")
    mag_meta = {"b": [round(v, 3) for v in mg["b"]], "D": [round(v, 3) for v in mg["D"]]}

    # Ultrasonic distance sensor (HC-SR04)
    dt_s = (t[1] - t[0]) if len(t) > 1 else 1.0 / 60.0
    us_raw, us_filt = ultrasonic.simulate(tel.z, dt_s)
    write("ultra.svg", line_chart("Ultrasonic distance", "t (s)", "distance (m)", [
        _series(t, tel.z, "true distance", "#8a93ac", dashed=True),
        _series(t, us_raw, "raw (noisy)", "#e0685f"),
        _series(t, us_filt, "low-pass filter", "#6fa8e6"),
    ]), "Ultrasonic distance", group="ultrasonic")

    # IMU (MPU-6050) — accelerometer & gyroscope
    acc_t, acc_r, acc_f = imu.accel_z(tel.roll, tel.pitch, tel.yaw, dt_s)
    write("imu_acc.svg", line_chart("Accelerometer", "t (s)", "a_z (m/s²)", [
        _series(t, acc_t, "true", "#8a93ac", dashed=True),
        _series(t, acc_r, "raw (bias + noise)", "#e0685f"),
        _series(t, acc_f, "low-pass filter", "#6fa8e6"),
    ]), "Accelerometer", group="imu")
    gyro_t, gyro_e = imu.gyro_drift(tel.yaw, dt_s)
    write("imu_gyro.svg", line_chart("Gyroscope drift", "t (s)", "yaw (deg)", [
        _series(t, gyro_t, "true yaw", "#8a93ac", dashed=True),
        _series(t, gyro_e, "gyroscope (integrated)", "#f0b446"),
    ]), "Gyroscope drift", group="imu")

    # Radio link (APC-220) — link budget + telemetry downlink
    ds, rssi, rng_m = comm.link_budget()
    write("comm_link.svg", line_chart("Link budget", "distance (m)", "RSSI (dBm)", [
        _series(ds, rssi, "received power", "#6fa8e6"),
        _series(ds, [comm.SENSITIVITY] * len(ds), "sensitivity", "#e0685f", dashed=True),
    ]), "Link budget", group="comm")
    recv, frate = comm.downlink(tel.z, dt_s)
    write("comm_down.svg", line_chart("Telemetry downlink", "t (s)", "z (m)", [
        _series(t, tel.z, "sent", "#8a93ac", dashed=True),
        _series(t, recv, "received", "#f0b446"),
    ]), "Telemetry downlink", group="comm")

    # GPS — multilateration (absolute position)
    gx, gy = gpsmod.run(tel.x, tel.y, tel.z, dt_s)
    write("gps.svg", xy_chart("GPS position", "x", "y", [
        {"label": "true path", "color": "#8a93ac", "pts": list(zip(tel.x, tel.y)), "dashed": True},
        {"label": "GPS estimate", "color": "#f0b446", "pts": list(zip(gx, gy))},
    ]), "GPS position", group="gps")

    # Barometer — altitude from pressure
    b_raw, b_filt = barometer.run(tel.z, dt_s)
    write("baro.svg", line_chart("Barometric altitude", "t (s)", "altitude (m)", [
        _series(t, tel.z, "true altitude", "#8a93ac", dashed=True),
        _series(t, b_raw, "raw (noisy)", "#e0685f"),
        _series(t, b_filt, "low-pass filter", "#6fa8e6"),
    ]), "Barometric altitude", group="baro")

    # Optical flow — horizontal velocity
    of_true, of_est = opticalflow.run(tel.x, tel.z, dt_s)
    write("flow.svg", line_chart("Optical flow velocity", "t (s)", "vx (m/s)", [
        _series(t, of_true, "true vx", "#8a93ac", dashed=True),
        _series(t, of_est, "optical flow estimate", "#6fa8e6"),
    ]), "Optical flow velocity", group="flow")

    # ToF / Lidar — more accurate than ultrasonic
    us_raw2, _ = ultrasonic.simulate(tel.z, dt_s, seed=9)
    tof_vals = tofmod.run(tel.z)
    write("tof.svg", line_chart("ToF / Lidar distance", "t (s)", "distance (m)", [
        _series(t, tel.z, "true distance", "#8a93ac", dashed=True),
        _series(t, us_raw2, "ultrasonic (noisy)", "#e0685f"),
        _series(t, tof_vals, "ToF / Lidar", "#6fa8e6"),
    ]), "ToF / Lidar distance", group="tof")

    # Air density vs altitude
    alts = [h * 100.0 for h in range(0, 51)]        # 0..5000 m
    write("atmos.svg", line_chart("Air density vs altitude", "altitude (m)", "ρ (kg/m³)", [
        _series(alts, [air_density(h) for h in alts], "air density", "#6fa8e6"),
    ]), "Air density vs altitude", group="atmos")

    # Propeller thrust (per rotor)
    write("prop.svg", line_chart("Propeller thrust", "t (s)", "thrust (N)", [
        _series(t, [THRUST_COEF * w * w for w in tel.w1], "rotor 1", "#6fa8e6"),
        _series(t, [THRUST_COEF * w * w for w in tel.w2], "rotor 2", "#f0b446"),
        _series(t, [THRUST_COEF * w * w for w in tel.w3], "rotor 3", "#8ad0a0"),
        _series(t, [THRUST_COEF * w * w for w in tel.w4], "rotor 4", "#e0685f"),
    ]), "Propeller thrust", group="prop")

    # DC motor step response (back-EMF)
    mt, mw, mi = motor.run()
    wmax = max(mw) or 1.0
    imax = max(mi) or 1.0
    write("motor.svg", line_chart("DC motor step response", "t (s)", "normalized", [
        _series(mt, [w / wmax for w in mw], "speed", "#6fa8e6"),
        _series(mt, [i / imax for i in mi], "current", "#e0685f"),
    ]), "DC motor step response", group="motor")

    # Rotation matrix verification
    dets, orth = rotcheck.run()
    ridx = list(range(len(dets)))
    write("rotcheck.svg", line_chart("Rotation matrix verification", "sample", "value", [
        _series(ridx, dets, "determinant", "#6fa8e6"),
        _series(ridx, orth, "orthogonality error", "#e0685f"),
    ]), "Rotation matrix verification", group="rotcheck")

    # GPS geodetic (latitude / longitude)
    lats, lons = geo.run(tel.x, tel.y, tel.z)
    write("geo.svg", xy_chart("GPS geodetic", "longitude (deg)", "latitude (deg)", [
        {"label": "trajectory", "color": "#f0b446", "pts": list(zip(lons, lats))},
    ]), "GPS geodetic", group="geo")

    # Complementary filter
    c_true, c_gyro, c_acc, c_comp = compfilter.run(tel.pitch, dt_s)
    write("compfilter.svg", line_chart("Complementary filter", "t (s)", "angle (deg)", [
        _series(t, c_true, "true", "#8a93ac", dashed=True),
        _series(t, c_gyro, "gyroscope only", "#f0b446"),
        _series(t, c_acc, "accelerometer only", "#e0685f"),
        _series(t, c_comp, "complementary", "#6fa8e6"),
    ]), "Complementary filter", group="fusion")

    # Kalman filter
    k_true, k_gyro, k_est, _ = kalman.run(tel.pitch, dt_s)
    write("kalman.svg", line_chart("Kalman filter", "t (s)", "angle (deg)", [
        _series(t, k_true, "true", "#8a93ac", dashed=True),
        _series(t, k_gyro, "gyroscope only", "#f0b446"),
        _series(t, k_est, "Kalman estimate", "#6fa8e6"),
    ]), "Kalman filter", group="kalman")

    # State-space: body-frame velocity (u, v, w)
    write("bodyvel.svg", line_chart("Body-frame velocity", "t (s)", "velocity (m/s)", [
        _series(t, tel.bu, "u", "#6fa8e6"),
        _series(t, tel.bv, "v", "#f0b446"),
        _series(t, tel.bw, "w", "#8ad0a0"),
    ]), "Body-frame velocity", group="state")

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

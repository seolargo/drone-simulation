/* Sekme geçişi + simülasyon çıktıları galerisi. */

const tabs = document.querySelectorAll(".tab");
const panels = {
  overview: document.getElementById("overview"),
  axes: document.getElementById("axes"),
  outputs: document.getElementById("outputs"),
};

tabs.forEach((btn) => {
  btn.addEventListener("click", () => {
    tabs.forEach((b) => b.classList.toggle("active", b === btn));
    Object.entries(panels).forEach(([k, el]) => el.classList.toggle("hidden", k !== btn.dataset.tab));
  });
});

// Tüm grafik grupları (sıra + İngilizce başlık)
const GROUP_SECTIONS = [
  ["flight", "Flight telemetry"],
  ["autotune", "Auto-tune (relay feedback)"],
  ["antiwindup", "Anti-windup comparison"],
  ["motor", "DC motor (back-EMF)"],
  ["prop", "Propeller thrust"],
  ["atmos", "Air density"],
  ["state", "State-space (body velocity)"],
  ["imu", "IMU (MPU-6050)"],
  ["fusion", "Sensor fusion (complementary filter)"],
  ["kalman", "Kalman filter"],
  ["mag", "Magnetometer"],
  ["gps", "GPS receiver"],
  ["geo", "GPS geodetic (lat/lon)"],
  ["baro", "Barometer"],
  ["ultrasonic", "Ultrasonic (HC-SR04)"],
  ["tof", "ToF / Lidar"],
  ["flow", "Optical flow"],
  ["comm", "Radio link (APC-220)"],
  ["rotcheck", "Rotation matrix verification"],
];

// Çıktı galerisi — outputs/manifest.js varsa (window.SIM_OUTPUTS) doldur
(function renderOutputs() {
  const data = window.SIM_OUTPUTS;
  const empty = document.getElementById("outempty");
  const meta = document.getElementById("runmeta");
  if (!data || !Array.isArray(data.charts) || !data.charts.length) return; // placeholder kalır

  empty.style.display = "none";
  meta.textContent =
    `Kaynak: ${data.source} · ${data.generatedAt} · süre ${data.durationSec}s · ${data.samples} örnek`;

  const buildFigures = (container, charts) => {
    charts.forEach((c) => {
      const fig = document.createElement("figure");
      const h = document.createElement("h4");
      h.textContent = c.title;
      const img = document.createElement("img");
      img.src = "outputs/" + c.file;
      img.alt = c.title;
      img.loading = "lazy";
      fig.append(h, img);
      container.appendChild(fig);
    });
  };

  const host = document.getElementById("groupsections");
  host.innerHTML = "";
  GROUP_SECTIONS.forEach(([g, heading]) => {
    const charts = data.charts.filter((c) => c.group === g);
    if (!charts.length) return;
    const sec = document.createElement("div");
    sec.className = "aw-section";
    const head = document.createElement("h3");
    head.className = "aw-head";
    head.textContent = heading;
    const gal = document.createElement("div");
    gal.className = "outgallery";
    sec.append(head, gal);
    host.appendChild(sec);
    buildFigures(gal, charts);
  });
})();

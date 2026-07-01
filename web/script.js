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

// Gruplu bölümlerin sırası ve başlıkları
const GROUP_SECTIONS = [
  ["motor", "DC motor dinamiği — back-EMF"],
  ["prop", "Pervane — thrust (blade element, T = k·ω²)"],
  ["atmos", "Hava yoğunluğu — irtifayla değişim"],
  ["gps", "GPS alıcısı"],
  ["geo", "GPS — geodetic (enlem/boylam) dönüşümü"],
  ["rotcheck", "Rotation matrix — RRᵀ=I, det=1 doğrulaması"],
  ["baro", "Barometre — basınçtan irtifa"],
  ["flow", "Optik akış sensörü"],
  ["tof", "ToF / Lidar mesafe sensörü"],
  ["ultrasonic", "Ultrasonik mesafe sensörü (HC-SR04)"],
  ["imu", "IMU (MPU-6050) — ivmeölçer & jiroskop"],
  ["fusion", "Sensör füzyonu — complementary filter"],
  ["mag", "Manyetometre — hard/soft iron kalibrasyonu"],
  ["comm", "Telsiz haberleşme (APC-220)"],
  ["antiwindup", "Anti-windup karşılaştırması"],
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

  const fill = (container, charts) => {
    container.innerHTML = "";
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

  // Auto-tune (özel: Ku/Tu/gain bilgi satırı)
  const at = data.charts.filter((c) => c.group === "autotune");
  const atSection = document.getElementById("autotunesection");
  if (data.tune && at.length) {
    const t = data.tune;
    document.getElementById("tuneinfo").textContent =
      `Relay deneyi → Ku=${t.Ku}, Tu=${t.Tu}s  ⇒  Kp=${t.kp}, Ki=${t.ki}, Kd=${t.kd}  (${t.rule})`;
    fill(document.getElementById("autotunegallery"), at);
    atSection.style.display = "";
  } else {
    atSection.style.display = "none";
  }

  // Ana uçuş grafikleri (grupsuz)
  fill(document.getElementById("outgallery"), data.charts.filter((c) => !c.group));

  // Gruplu bölümler (generic)
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
    fill(gal, charts);
  });
})();

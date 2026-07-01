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

// Çıktı galerisi — outputs/manifest.js varsa (window.SIM_OUTPUTS) doldur
(function renderOutputs() {
  const data = window.SIM_OUTPUTS;
  const gallery = document.getElementById("outgallery");
  const awSection = document.getElementById("awsection");
  const awGallery = document.getElementById("awgallery");
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

  const at = data.charts.filter((c) => c.group === "autotune");
  const aw = data.charts.filter((c) => c.group === "antiwindup");
  const mg = data.charts.filter((c) => c.group === "mag");
  const main = data.charts.filter((c) => !c.group);

  // Auto-tune bölümü + Ku/Tu/gain bilgisi
  const atSection = document.getElementById("autotunesection");
  const tuneInfo = document.getElementById("tuneinfo");
  if (data.tune && at.length) {
    const t = data.tune;
    tuneInfo.textContent =
      `Relay deneyi → Ku=${t.Ku}, Tu=${t.Tu}s  ⇒  Kp=${t.kp}, Ki=${t.ki}, Kd=${t.kd}  (${t.rule})`;
    fill(document.getElementById("autotunegallery"), at);
    atSection.style.display = "";
  } else {
    atSection.style.display = "none";
  }

  fill(gallery, main);

  // Manyetometre bölümü
  const magSection = document.getElementById("magsection");
  if (data.mag && mg.length) {
    document.getElementById("maginfo").textContent =
      `Kestirilen hard iron b=[${data.mag.b}]  ·  soft iron D=[${data.mag.D}]  ·  heading hatası: ham ~69° → kalibre ~3°`;
    fill(document.getElementById("maggallery"), mg);
    magSection.style.display = "";
  } else {
    magSection.style.display = "none";
  }

  if (aw.length) {
    fill(awGallery, aw);
    awSection.style.display = "";
  } else {
    awSection.style.display = "none";
  }
})();

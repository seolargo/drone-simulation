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
  const empty = document.getElementById("outempty");
  const meta = document.getElementById("runmeta");
  if (!data || !Array.isArray(data.charts) || !data.charts.length) return; // placeholder kalır

  empty.style.display = "none";
  meta.textContent =
    `Kaynak: ${data.source} · ${data.generatedAt} · süre ${data.durationSec}s · ${data.samples} örnek`;

  gallery.innerHTML = "";
  data.charts.forEach((c) => {
    const fig = document.createElement("figure");
    const h = document.createElement("h4");
    h.textContent = c.title;
    const img = document.createElement("img");
    img.src = "outputs/" + c.file;
    img.alt = c.title;
    img.loading = "lazy";
    fig.append(h, img);
    gallery.appendChild(fig);
  });
})();

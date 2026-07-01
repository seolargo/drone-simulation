"""
Bağımsız SVG çizgi grafiği üretici (dış bağımlılık yok).

line_chart(...) tek bir SVG dizesi döndürür: eksenler, hafif ızgara, birkaç
tik etiketi, lejant ve her seri için polyline. Uzun seriler otomatik indirgenir.
"""


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _fmt(v):
    a = abs(v)
    if a >= 100:
        return f"{v:.0f}"
    if a >= 10:
        return f"{v:.1f}"
    return f"{v:.2f}"


def _downsample(pts, maxn=600):
    n = len(pts)
    if n <= maxn:
        return pts
    step = n / maxn
    return [pts[min(n - 1, int(i * step))] for i in range(maxn)]


def line_chart(title, xlabel, ylabel, series, width=560, height=240):
    """
    series: [{"label", "color", "pts": [(t, v), ...], "dashed"?}]
    """
    L, R, T, B = 50, 16, 30, 34
    px0, px1 = L, width - R
    py0, py1 = T, height - B

    xs = [t for s in series for (t, _) in s["pts"]]
    ys = [v for s in series for (_, v) in s["pts"]]
    if not xs:
        xs, ys = [0.0, 1.0], [0.0, 1.0]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    if xmax - xmin < 1e-9:
        xmax = xmin + 1.0
    if ymax - ymin < 1e-9:
        ymin -= 1.0
        ymax += 1.0
    pad = (ymax - ymin) * 0.08
    ymin -= pad
    ymax += pad

    def sx(t):
        return px0 + (t - xmin) / (xmax - xmin) * (px1 - px0)

    def sy(v):
        return py1 - (v - ymin) / (ymax - ymin) * (py1 - py0)

    title = _esc(title)
    xlabel = _esc(xlabel)
    ylabel = _esc(ylabel)

    o = []
    o.append(f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
             f'class="chart" role="img" aria-label="{title}">')
    o.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#161b2b"/>')

    # ızgara + tik etiketleri
    g = []
    for i in range(5):
        gx = px0 + (px1 - px0) * i / 4
        tv = xmin + (xmax - xmin) * i / 4
        g.append(f'<line x1="{gx:.1f}" y1="{py0}" x2="{gx:.1f}" y2="{py1}" stroke="#222a40"/>')
        g.append(f'<text x="{gx:.1f}" y="{py1 + 15}" fill="#8a93ac" font-size="10" '
                 f'text-anchor="middle" font-family="Menlo,monospace">{_fmt(tv)}</text>')
    for i in range(5):
        gy = py1 - (py1 - py0) * i / 4
        vv = ymin + (ymax - ymin) * i / 4
        g.append(f'<line x1="{px0}" y1="{gy:.1f}" x2="{px1}" y2="{gy:.1f}" stroke="#222a40"/>')
        g.append(f'<text x="{px0 - 6}" y="{gy + 3:.1f}" fill="#8a93ac" font-size="10" '
                 f'text-anchor="end" font-family="Menlo,monospace">{_fmt(vv)}</text>')
    o.append('<g stroke-width="1">' + "".join(g) + '</g>')

    # eksenler
    o.append(f'<g stroke="#46506e" stroke-width="1.4">'
             f'<line x1="{px0}" y1="{py0}" x2="{px0}" y2="{py1}"/>'
             f'<line x1="{px0}" y1="{py1}" x2="{px1}" y2="{py1}"/></g>')

    # seriler
    for s in series:
        pts = _downsample(s["pts"])
        d = " ".join(f"{sx(t):.1f},{sy(v):.1f}" for (t, v) in pts)
        dash = ' stroke-dasharray="6 4"' if s.get("dashed") else ""
        o.append(f'<polyline fill="none" stroke="{s["color"]}" stroke-width="2"{dash} points="{d}"/>')

    # başlık + eksen etiketleri
    o.append(f'<text x="{px0}" y="18" fill="#ffffff" font-size="13" '
             f'font-family="Menlo,monospace">{title}</text>')
    o.append(f'<text x="{(px0 + px1) / 2:.0f}" y="{height - 5}" fill="#8a93ac" '
             f'font-size="10" text-anchor="middle">{xlabel}</text>')
    ymid = (py0 + py1) / 2
    o.append(f'<text x="14" y="{ymid:.0f}" fill="#8a93ac" font-size="10" '
             f'text-anchor="middle" transform="rotate(-90 14 {ymid:.0f})">{ylabel}</text>')

    # lejant (sağ üst)
    lx = px1 - 6
    for i, s in enumerate(series):
        yy = py0 + 8 + i * 15
        dash = ' stroke-dasharray="6 4"' if s.get("dashed") else ""
        o.append(f'<line x1="{lx - 24:.1f}" y1="{yy}" x2="{lx - 4:.1f}" y2="{yy}" '
                 f'stroke="{s["color"]}" stroke-width="2.5"{dash}/>')
        o.append(f'<text x="{lx - 28:.1f}" y="{yy + 3}" fill="#c8cddc" font-size="10" '
                 f'text-anchor="end" font-family="Menlo,monospace">{_esc(s["label"])}</text>')

    o.append('</svg>')
    return "\n".join(o)

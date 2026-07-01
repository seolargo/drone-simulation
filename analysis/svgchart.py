"""
Bağımsız SVG çizgi grafiği üretici (dış bağımlılık yok).

line_chart(...) tek bir SVG dizesi döndürür: eksenler, hafif ızgara, birkaç
tik etiketi, lejant ve her seri için polyline. Uzun seriler otomatik indirgenir.
"""


import math


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


def relay_chart(t, vx, relay, a, Tu, Ku, d, width=640, height=310):
    """
    Açıklayıcı relay-feedback diyagramı: süreç çıkışı (vx) salınımı + röle (aç/kapa)
    kare dalgası; salınım genliği (a) ve periyodu (Tu) ok/etiketle işaretlenir; sağda
    Ku = 4d/(pi*a) formülü ve değerleri gösterilir.
    """
    L, R, T, B = 56, 168, 40, 40
    px0, px1 = L, width - R
    py0, py1 = T, height - B
    mid = (py0 + py1) / 2.0
    half = (py1 - py0) / 2.0

    n = len(t)
    if n < 2 or a <= 1e-9:
        return line_chart("Relay feedback experiment", "t (s)", "vx", [])

    xmin, xmax = t[0], t[-1]
    ymax = a * 1.35
    d_deg = math.degrees(d)

    def sx(tt):
        return px0 + (tt - xmin) / (xmax - xmin) * (px1 - px0)

    def sy(v):
        return mid - (v / ymax) * half

    def poly(xs_ys, color, w, dash=False):
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in xs_ys)
        dd = ' stroke-dasharray="7 5"' if dash else ""
        return f'<polyline fill="none" stroke="{color}" stroke-width="{w}"{dd} points="{pts}"/>'

    o = [f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
         f'class="chart" role="img" aria-label="Relay feedback deneyi">',
         f'<rect x="0" y="0" width="{width}" height="{height}" fill="#161b2b"/>']

    # ızgara + sıfır çizgisi + +a/-a seviyeleri
    for lv in (a, -a):
        o.append(f'<line x1="{px0}" y1="{sy(lv):.1f}" x2="{px1}" y2="{sy(lv):.1f}" '
                 f'stroke="#222a40" stroke-dasharray="3 4"/>')
    o.append(f'<line x1="{px0}" y1="{sy(0):.1f}" x2="{px1}" y2="{sy(0):.1f}" stroke="#46506e" stroke-width="1.4"/>')
    o.append(f'<line x1="{px0}" y1="{py0}" x2="{px0}" y2="{py1}" stroke="#46506e" stroke-width="1.4"/>')

    # röle kare dalgası (aç/kapa) — ±a ölçeğine getirilir (arka planda)
    relay_xy = [(sx(t[i]), sy(relay[i] / d * a)) for i in range(n)]
    o.append(poly(relay_xy, "#f0b446", 2, dash=True))
    # süreç çıkışı vx (salınım)
    vx_xy = [(sx(t[i]), sy(vx[i])) for i in range(n)]
    o.append(poly(vx_xy, "#6fa8e6", 2.4))

    # --- tepe noktaları (Tu ve a işaretleri için) ---
    peaks = []
    for i in range(1, n - 1):
        if vx[i] > vx[i - 1] and vx[i] >= vx[i + 1] and vx[i] > 0.55 * a:
            peaks.append(i)
    peaks = [p for k, p in enumerate(peaks) if k == 0 or t[p] - t[peaks[k - 1]] > Tu * 0.5]

    acc = "#e7edf7"      # işaret rengi (açık)
    # Periyot Tu: iki komşu tepe arası çift-yönlü ok
    if len(peaks) >= 2:
        p0, p1 = peaks[0], peaks[1]
        x0, x1 = sx(t[p0]), sx(t[p1])
        yb = sy(a) - 16
        o.append(f'<line x1="{x0:.1f}" y1="{sy(vx[p0]):.1f}" x2="{x0:.1f}" y2="{yb-3:.1f}" stroke="{acc}" stroke-width="1" stroke-dasharray="2 3"/>')
        o.append(f'<line x1="{x1:.1f}" y1="{sy(vx[p1]):.1f}" x2="{x1:.1f}" y2="{yb-3:.1f}" stroke="{acc}" stroke-width="1" stroke-dasharray="2 3"/>')
        o.append(f'<line x1="{x0:.1f}" y1="{yb:.1f}" x2="{x1:.1f}" y2="{yb:.1f}" stroke="{acc}" stroke-width="1.4"/>')
        o.append(f'<polygon points="{x0:.1f},{yb:.1f} {x0+7:.1f},{yb-3.5:.1f} {x0+7:.1f},{yb+3.5:.1f}" fill="{acc}"/>')
        o.append(f'<polygon points="{x1:.1f},{yb:.1f} {x1-7:.1f},{yb-3.5:.1f} {x1-7:.1f},{yb+3.5:.1f}" fill="{acc}"/>')
        o.append(f'<text x="{(x0+x1)/2:.1f}" y="{yb-5:.1f}" fill="{acc}" font-size="12" text-anchor="middle" '
                 f'font-family="Menlo,monospace">Tu = {Tu:.2f} s</text>')

    # Genlik a: sol iç kenarda dikey çift-yönlü ok (0 -> a)
    xa = px0 + 16
    y0, ya = sy(0), sy(a)
    o.append(f'<line x1="{xa:.1f}" y1="{y0:.1f}" x2="{xa:.1f}" y2="{ya:.1f}" stroke="{acc}" stroke-width="1.4"/>')
    o.append(f'<polygon points="{xa:.1f},{ya:.1f} {xa-3.5:.1f},{ya+7:.1f} {xa+3.5:.1f},{ya+7:.1f}" fill="{acc}"/>')
    o.append(f'<polygon points="{xa:.1f},{y0:.1f} {xa-3.5:.1f},{y0-7:.1f} {xa+3.5:.1f},{y0-7:.1f}" fill="{acc}"/>')
    o.append(f'<text x="{xa+7:.1f}" y="{(y0+ya)/2+4:.1f}" fill="{acc}" font-size="12" font-family="Menlo,monospace">a</text>')

    # --- sağ panel: formül + değerler ---
    rx = px1 + 16
    lines = [
        ("Ku = 4h / (π·a)", "#c8cddc", 13),
        (f"h  = {d_deg:.1f}°", "#8a93ac", 11),
        (f"a  = {a:.3f} m/s", "#8a93ac", 11),
        (f"Ku = {Ku:.2f}", "#f0b446", 13),
        (f"Tu = {Tu:.2f} s", "#f0b446", 13),
    ]
    yy = py0 + 14
    for txt, col, fs in lines:
        o.append(f'<text x="{rx}" y="{yy}" fill="{col}" font-size="{fs}" font-family="Menlo,monospace">{_esc(txt)}</text>')
        yy += 22 if fs >= 13 else 18

    # legend
    yy += 6
    o.append(f'<line x1="{rx}" y1="{yy-4}" x2="{rx+20}" y2="{yy-4}" stroke="#6fa8e6" stroke-width="2.4"/>')
    o.append(f'<text x="{rx+26}" y="{yy}" fill="#c8cddc" font-size="10" font-family="Menlo,monospace">vx (çıkış)</text>')
    yy += 16
    o.append(f'<line x1="{rx}" y1="{yy-4}" x2="{rx+20}" y2="{yy-4}" stroke="#f0b446" stroke-width="2.4" stroke-dasharray="7 5"/>')
    o.append(f'<text x="{rx+26}" y="{yy}" fill="#c8cddc" font-size="10" font-family="Menlo,monospace">röle (aç/kapa)</text>')

    # başlık + eksen
    o.append(f'<text x="{px0}" y="20" fill="#ffffff" font-size="13" font-family="Menlo,monospace">Relay feedback deneyi</text>')
    o.append(f'<text x="{(px0+px1)/2:.0f}" y="{height-6}" fill="#8a93ac" font-size="10" text-anchor="middle">t (s)</text>')
    o.append(f'<text x="16" y="{mid:.0f}" fill="#8a93ac" font-size="10" text-anchor="middle" transform="rotate(-90 16 {mid:.0f})">vx (m/s)</text>')

    o.append('</svg>')
    return "\n".join(o)

"""
Geodetic ↔ ECEF ↔ NED dönüşümleri.

GPS alıcısı konumu geodetic (enlem φ, boylam λ, yükseklik h) verir; navigasyon
NED çerçevesinde yapılır. Elipsoid (r_e, r_p) üzerinden:
    ECEF:  p^e = f(φ, λ, h)   (N = birinci dikey eğrilik yarıçapı)
    NED:   p^n = R_e^n(φ, λ) · (p^e - p_ref^e)

Burada drone'un yerel NED yörüngesi geodetic'e (enlem/boylam) geri çevrilir —
gerçek bir GPS'in verdiği "harita" görünümü.
"""

import numpy as np

RE = 6378137.0        # ekvator yarıçapı (m)
RP = 6356752.0        # kutup yarıçapı (m)
_E2 = 1.0 - (RP * RP) / (RE * RE)
_EP2 = (RE * RE) / (RP * RP) - 1.0

# NED referans orijini (kalkış noktası) — İstanbul civarı
REF_LAT = np.radians(41.015)
REF_LON = np.radians(28.979)
REF_H = 100.0


def _N(lat):
    return RE * RE / np.sqrt(RE * RE * np.cos(lat) ** 2 + RP * RP * np.sin(lat) ** 2)


def geodetic_to_ecef(lat, lon, h):
    N = _N(lat)
    return np.array([
        (N + h) * np.cos(lat) * np.cos(lon),
        (N + h) * np.cos(lat) * np.sin(lon),
        (RP * RP / (RE * RE) * N + h) * np.sin(lat),
    ])


def R_e_n(lat, lon):
    sl, cl = np.sin(lat), np.cos(lat)
    so, co = np.sin(lon), np.cos(lon)
    return np.array([
        [-sl * co, -sl * so, cl],
        [-so, co, 0.0],
        [-cl * co, -cl * so, -sl],
    ])


def ecef_to_geodetic(x, y, z):
    p = np.hypot(x, y)
    th = np.arctan2(z * RE, p * RP)
    lon = np.arctan2(y, x)
    lat = np.arctan2(z + _EP2 * RP * np.sin(th) ** 3, p - _E2 * RE * np.cos(th) ** 3)
    return lat, lon


def ned_to_geodetic(pn):
    """NED konumu (m) -> (enlem°, boylam°), referans orijine göre."""
    pref = geodetic_to_ecef(REF_LAT, REF_LON, REF_H)
    pe = pref + R_e_n(REF_LAT, REF_LON).T @ pn
    lat, lon = ecef_to_geodetic(*pe)
    return np.degrees(lat), np.degrees(lon)


def run(x_north, y_east, z_up):
    """Yörüngeyi geodetic'e çevirir. x=Kuzey, y=Doğu, z=yukarı (Down=-z)."""
    lats, lons = [], []
    for xn, ye, zu in zip(x_north, y_east, z_up):
        lat, lon = ned_to_geodetic(np.array([xn, ye, -zu]))
        lats.append(lat)
        lons.append(lon)
    return lats, lons

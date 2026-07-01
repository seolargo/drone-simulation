"""
Hava yoğunluğu — irtifaya bağlı (Standart Atmosfer).

    ρ = P·M / (R·T),   T = T0 - L·h,   P = P0 (1 - L·h/T0)^(gM/RL)

İtki hava yoğunluğuyla orantılıdır (T ∝ ρ·ω²); yükseklikte yoğunluk düşünce itki
azalır. Çoğu model ρ'yu sabit alır; biz irtifayla değişimini hesaba katıyoruz.
"""

P0 = 101325.0       # deniz seviyesi basıncı (Pa)
T0 = 288.15         # referans sıcaklık (K)
L = 0.0065          # sıcaklık düşüş oranı (K/m)
G = 9.80665
M = 0.0289644       # havanın molar kütlesi (kg/mol)
R = 8.31447

_EXP = G * M / (R * L)


def density(h):
    """h (m) yükseklikte hava yoğunluğu (kg/m³)."""
    T = T0 - L * h
    P = P0 * (1.0 - L * h / T0) ** _EXP
    return P * M / (R * T)


RHO0 = density(0.0)   # deniz seviyesi yoğunluğu (~1.225)

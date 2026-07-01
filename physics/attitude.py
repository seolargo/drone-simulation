"""
Eğim (attitude) iç dinamiği.

Gerçek bir drone'un eğimi anında değişmez; motor/attitude döngüsü sonlu bir
hızla komuta ulaşır. Bunu 2. mertebe (kütle-yay-sönüm) bir tepkiyle modelleriz:

    angle'' = wn^2 (cmd - angle) - 2 zeta wn angle'

Bu ek dinamik, hız plant'ine gereken faz gecikmesini kazandırır; böylece relay
feedback auto-tune anlamlı bir salınım (Ku, Tu) üretebilir.
"""


def attitude_step(angle, rate, cmd, wn, zeta, dt):
    """2. mertebe tepkiyi bir adım ilerletir; (yeni_açı, yeni_hız) döndürür."""
    acc = wn * wn * (cmd - angle) - 2.0 * zeta * wn * rate
    rate = rate + acc * dt
    angle = angle + rate * dt
    return angle, rate

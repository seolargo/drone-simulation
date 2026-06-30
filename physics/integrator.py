"""
Hareket entegrasyonu.

Yarı-örtük (semi-implicit) Euler: önce hızı, sonra konumu günceller.
Basit ve yerçekimi gibi durumlarda kararlıdır.
"""


def semi_implicit_euler(pos, vel, acc, dt):
    """
    pos, vel : numpy dizileri (yerinde değiştirilmez, yenisi döndürülür)
    acc      : ivme vektörü
    dt       : zaman adımı (saniye)
    """
    new_vel = vel + acc * dt
    new_pos = pos + new_vel * dt
    return new_pos, new_vel

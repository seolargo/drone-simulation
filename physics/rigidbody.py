"""
Rijit cisim dönme dinamiği — Euler denklemleri.

    I·ω̇ + ω × (I·ω) = τ   =>   ω̇ = I⁻¹ (τ - ω × (I·ω))

Köşegen atalet (Ix, Iy, Iz) için çapraz çarpım açılırsa (klasik Euler):
    Ix·ω̇x = τx + (Iy - Iz) ωy ωz
    Iy·ω̇y = τy + (Iz - Ix) ωz ωx
    Iz·ω̇z = τz + (Ix - Iy) ωx ωy

ω × (I·ω) jiroskopik çapraz-bağlaşım terimidir (yüksek açısal hızlarda önemli).
"""


def euler_step(omega, torque, inertia, dt):
    """Açısal hızı (ωx, ωy, ωz) bir adım ilerletir."""
    wx, wy, wz = omega
    tx, ty, tz = torque
    ix, iy, iz = inertia
    wx += (tx + (iy - iz) * wy * wz) / ix * dt
    wy += (ty + (iz - ix) * wz * wx) / iy * dt
    wz += (tz + (ix - iy) * wx * wy) / iz * dt
    return wx, wy, wz

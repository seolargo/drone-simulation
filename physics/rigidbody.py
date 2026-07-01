"""
Rijit cisim dönme dinamiği — Euler denklemleri.

    I·ω̇ + ω × (I·ω) = τ   =>   ω̇ = I⁻¹ (τ - ω × (I·ω))

Köşegen atalet (Ix, Iy, Iz) için çapraz çarpım açılırsa (klasik Euler):
    Ix·ω̇x = τx + (Iy - Iz) ωy ωz
    Iy·ω̇y = τy + (Iz - Ix) ωz ωx
    Iz·ω̇z = τz + (Ix - Iy) ωx ωy

ω × (I·ω) jiroskopik çapraz-bağlaşım terimidir (yüksek açısal hızlarda önemli).

euler_kinematics: gövde açısal hızlarını (p, q, r) Euler-açı türevlerine bağlayan
kinematik matris T(φ,θ) ile [φ̇, θ̇, ψ̇] hesaplar.
"""

import math


def euler_step(omega, torque, inertia, dt):
    """Açısal hızı (ωx, ωy, ωz) bir adım ilerletir."""
    wx, wy, wz = omega
    tx, ty, tz = torque
    ix, iy, iz = inertia
    wx += (tx + (iy - iz) * wy * wz) / ix * dt
    wy += (ty + (iz - ix) * wz * wx) / iy * dt
    wz += (tz + (ix - iy) * wx * wy) / iz * dt
    return wx, wy, wz


def euler_kinematics(phi, theta, p, q, r):
    """
    [φ̇, θ̇, ψ̇] = T(φ,θ) · [p, q, r]   — gövde açısal hızlarından Euler türevleri.
        φ̇ = p + sinφ·tanθ·q + cosφ·tanθ·r
        θ̇ = cosφ·q - sinφ·r
        ψ̇ = (sinφ·q + cosφ·r) / cosθ
    """
    sphi, cphi = math.sin(phi), math.cos(phi)
    ttheta, ctheta = math.tan(theta), math.cos(theta)
    phid = p + sphi * ttheta * q + cphi * ttheta * r
    thetad = cphi * q - sphi * r
    psid = (sphi * q + cphi * r) / ctheta
    return phid, thetad, psid

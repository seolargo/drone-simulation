"""
Complementary filter — jiroskop + ivmeölçer füzyonu (açı kestirimi).

Jiroskop kısa vadede doğru ama entegre edilince drift eder; ivmeölçer sürüklenmez
ama harekette gürültülüdür. Complementary filter jiroskopu yüksek-geçiren,
ivmeölçeri alçak-geçiren süzgeçle birleştirir:

    θ_k = α (θ_{k-1} + θ̇_gyro·Δt) + (1-α) θ_acc,     α = τ / (τ + Δt)

α'ya yakın ağırlık jiroskopa (pürüzsüz, kısa vade), (1-α) ivmeölçere (kararlı,
uzun vade — drift'i sürekli düzeltir) verilir.
"""

import numpy as np

GYRO_BIAS0 = 0.5     # jiroskop başlangıç biası (°/s)
GYRO_RW = 0.25       # rastgele-yürüyüş (°/s / sqrt(s))
GYRO_NOISE = 0.4     # jiroskop beyaz gürültü (°/s)
ACC_NOISE = 3.0      # ivmeölçer açı gürültüsü (°)
TAU = 0.5            # filtre zaman sabiti (s)


def run(angle_deg, dt, seed=33):
    """(gerçek, sadece-jiroskop, sadece-ivmeölçer, complementary) döndürür."""
    rng = np.random.default_rng(seed)
    n = len(angle_deg)
    true = list(map(float, angle_deg))
    alpha = TAU / (TAU + dt)
    bias = GYRO_BIAS0

    gyro = [true[0]]
    acc = [true[0]]
    comp = [true[0]]
    for i in range(1, n):
        rate = (true[i] - true[i - 1]) / dt
        bias += GYRO_RW * np.sqrt(dt) * rng.normal()
        grate = rate + bias + rng.normal(0.0, GYRO_NOISE)     # gürültülü/biaslı jiro
        a = true[i] + rng.normal(0.0, ACC_NOISE)              # gürültülü mutlak (ivmeölçer)
        gyro.append(gyro[-1] + grate * dt)                    # sadece jiro -> drift
        acc.append(a)
        comp.append(alpha * (comp[-1] + grate * dt) + (1.0 - alpha) * a)   # füzyon
    return true, gyro, acc, comp

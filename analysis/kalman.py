"""
Kalman filtresi — açı + jiroskop bias kestirimi (2 durumlu).

Durum x = [θ, b] (açı, jiroskop biası). Jiroskop hızı kontrol girdisi, ivmeölçer
açısı ölçümdür. Filtre bias'ı da kestirerek jiroskop driftini optimal biçimde
temizler.

    Tahmin:  x̂⁻ = A x̂ + B·(gyro),   P⁻ = A P Aᵀ + Q
    Düzeltme: K = P⁻Hᵀ(HP⁻Hᵀ+R)⁻¹,  x̂ = x̂⁻ + K(z - Hx̂⁻),  P = (I-KH)P⁻

A = [[1, -Δt], [0, 1]],  B = [Δt, 0]ᵀ,  H = [1, 0]
"""

import numpy as np

GYRO_BIAS0 = 0.5     # gerçek jiroskop biası (°/s)
GYRO_RW = 0.25       # bias rastgele-yürüyüş
GYRO_NOISE = 0.4     # jiroskop gürültü (°/s)
ACC_NOISE = 3.0      # ivmeölçer açı gürültüsü (°)

Q = np.array([[1e-3, 0.0], [0.0, 1e-4]])   # süreç gürültü kovaryansı
R = np.array([[ACC_NOISE ** 2]])            # ölçüm gürültü kovaryansı


def run(angle_deg, dt, seed=37):
    rng = np.random.default_rng(seed)
    n = len(angle_deg)
    true = list(map(float, angle_deg))

    A = np.array([[1.0, -dt], [0.0, 1.0]])
    B = np.array([[dt], [0.0]])
    H = np.array([[1.0, 0.0]])
    I2 = np.eye(2)

    x = np.array([[true[0]], [0.0]])    # [açı, bias]
    P = np.eye(2) * 1.0

    bias = GYRO_BIAS0
    gyro_only = [true[0]]
    est = [true[0]]
    bias_est = [0.0]
    for i in range(1, n):
        rate = (true[i] - true[i - 1]) / dt
        bias += GYRO_RW * np.sqrt(dt) * rng.normal()
        gyro = rate + bias + rng.normal(0.0, GYRO_NOISE)     # ölçülen jiroskop hızı
        acc = true[i] + rng.normal(0.0, ACC_NOISE)           # ölçülen ivmeölçer açısı

        gyro_only.append(gyro_only[-1] + gyro * dt)          # ham entegrasyon -> drift

        # Tahmin
        x = A @ x + B * gyro
        P = A @ P @ A.T + Q
        # Düzeltme (ivmeölçer ölçümü)
        S = H @ P @ H.T + R
        K = P @ H.T @ np.linalg.inv(S)
        x = x + K @ (np.array([[acc]]) - H @ x)
        P = (I2 - K @ H) @ P

        est.append(float(x[0, 0]))
        bias_est.append(float(x[1, 0]))
    return true, gyro_only, est, bias_est

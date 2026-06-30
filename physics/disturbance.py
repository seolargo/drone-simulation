"""
Bozucu etkiler — gerçekçilik için.

Wind: yumuşak, zaman-korelasyonlu türbülans ivmesi (Ornstein-Uhlenbeck süreci).
Beyaz gürültü değil; gerçek rüzgâr gibi yavaşça değişen "gust"lar üretir.
PID bu itmelere karşı sürekli düzeltme yapar → hover'da doğal salınım/titreme.
"""

import numpy as np


class Wind:
    def __init__(self, strength, tau, seed=1234):
        self.strength = strength          # kararlı-hal ivme std'i (birim/s^2)
        self.tau = max(tau, 1e-3)         # gust korelasyon süresi (s)
        self.rng = np.random.default_rng(seed)
        self.reset()

    def reset(self):
        self.accel = np.zeros(3, dtype=float)

    def acceleration(self, dt):
        # OU: d a = -(a/tau) dt + sigma sqrt(dt) N ; kararlı-hal std = strength
        sigma = self.strength * np.sqrt(2.0 / self.tau)
        # dikey eksende türbülans daha zayıf
        n = self.rng.normal(0.0, 1.0, 3) * np.array([1.0, 1.0, 0.3])
        self.accel += -self.accel * (dt / self.tau) + sigma * np.sqrt(dt) * n
        return self.accel

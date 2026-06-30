"""
Genel PID kontrolcü.

Bir hata sinyalini (hedef - ölçülen) alır, orantı (P), integral (I) ve
türev (D) terimlerinin toplamını döndürür. Integral sarması (windup) ve
çıkış, isteğe bağlı sınırlarla bastırılır.
"""


def _clip(x, lim):
    if lim is None:
        return x
    return max(-lim, min(lim, x))


class PID:
    def __init__(self, kp, ki, kd, out_limit=None, integral_limit=None, deriv_tau=0.0):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.out_limit = out_limit
        self.integral_limit = integral_limit
        self.deriv_tau = deriv_tau        # türev alçak-geçiren zaman sabiti (s)
        self.reset()

    def reset(self):
        self.integral = 0.0
        self.prev_error = None
        self.prev_meas = None
        self.deriv = 0.0

    def update(self, error, dt, measurement=None):
        """
        error       : hedef - ölçülen
        measurement : verilirse türev ölçüm üzerinden alınır (derivative on
                      measurement) — setpoint sıçramalarında türev darbesini
                      önler, daha yumuşak tepki verir.
        """
        if dt <= 0.0:
            return _clip(self.kp * error, self.out_limit)

        self.integral = _clip(self.integral + error * dt, self.integral_limit)

        if measurement is not None:
            d_meas = 0.0 if self.prev_meas is None else (measurement - self.prev_meas) / dt
            raw_deriv = -d_meas
            self.prev_meas = measurement
        else:
            raw_deriv = 0.0 if self.prev_error is None else (error - self.prev_error) / dt
            self.prev_error = error

        # Türev alçak-geçiren filtresi: sensör gürültüsünün türevde patlamasını önler
        if self.deriv_tau > 0.0:
            alpha = dt / (self.deriv_tau + dt)
            self.deriv += (raw_deriv - self.deriv) * alpha
        else:
            self.deriv = raw_deriv

        out = self.kp * error + self.ki * self.integral + self.kd * self.deriv
        return _clip(out, self.out_limit)

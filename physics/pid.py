"""
Genel PID kontrolcü — anti-windup destekli.

Bir hata sinyalini (hedef - ölçülen) alır, orantı (P), integral (I) ve
türev (D) terimlerinin toplamını döndürür.

Anti-windup (aktüatör out_limit'e doyduğunda integralin kontrolsüz birikmesini
önleme) için iki yöntem seçilebilir:
    "clamp"    : koşullu integrasyon — çıkış doygunken ve integrasyon doygunluğu
                 artıracak yöndeyse integratör dondurulur.
    "backcalc" : geri-hesaplama — istenen (u_raw) ile doymuş (u_sat) çıkış farkı
                 kb kazancıyla integratöre geri beslenir; fazlalık pürüzsüzce erir.
    "none"     : yalnız statik integral_limit (varsa) uygulanır.
"""


def _clip(x, lim):
    if lim is None:
        return x
    return max(-lim, min(lim, x))


class PID:
    def __init__(self, kp, ki, kd, out_limit=None, integral_limit=None,
                 deriv_tau=0.0, antiwindup="none", kb=0.0):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.out_limit = out_limit
        self.integral_limit = integral_limit
        self.deriv_tau = deriv_tau        # türev alçak-geçiren zaman sabiti (s)
        self.antiwindup = antiwindup      # "none" | "clamp" | "backcalc"
        self.kb = kb                      # back-calculation izleme kazancı
        self.reset()

    def reset(self):
        self.integral = 0.0
        self.prev_error = None
        self.prev_meas = None
        self.deriv = 0.0
        # Son çıktı ve terim katkıları (u(t) grafiği için dışa açık)
        self.p_term = 0.0
        self.i_term = 0.0
        self.d_term = 0.0
        self.out = 0.0

    def update(self, error, dt, measurement=None):
        """
        error       : hedef - ölçülen
        measurement : verilirse türev ölçüm üzerinden alınır (derivative on
                      measurement) — setpoint sıçramalarında türev darbesini
                      önler, daha yumuşak tepki verir.
        """
        if dt <= 0.0:
            return _clip(self.kp * error, self.out_limit)

        # --- türev (ölçüm üzerinden, alçak-geçiren filtreli) ---
        if measurement is not None:
            d_meas = 0.0 if self.prev_meas is None else (measurement - self.prev_meas) / dt
            raw_deriv = -d_meas
            self.prev_meas = measurement
        else:
            raw_deriv = 0.0 if self.prev_error is None else (error - self.prev_error) / dt
            self.prev_error = error
        if self.deriv_tau > 0.0:
            alpha = dt / (self.deriv_tau + dt)
            self.deriv += (raw_deriv - self.deriv) * alpha
        else:
            self.deriv = raw_deriv

        p = self.kp * error
        d = self.kd * self.deriv

        # --- integratör güncelleme (anti-windup moduna göre) ---
        if self.antiwindup == "clamp":
            # Koşullu integrasyon: çıkış doygun ve integrasyon doygunluğu
            # artıracak yöndeyse integratörü dondur.
            tentative = self.integral + error * dt
            u_test = p + self.ki * tentative + d
            saturating = self.out_limit is not None and abs(u_test) > self.out_limit
            if not (saturating and (u_test > 0) == (error > 0)):
                self.integral = tentative
        else:
            self.integral += error * dt

        self.integral = _clip(self.integral, self.integral_limit)

        self.p_term = p
        self.i_term = self.ki * self.integral
        self.d_term = d
        u_raw = self.p_term + self.i_term + self.d_term
        self.out = _clip(u_raw, self.out_limit)

        # --- back-calculation: doygunluk fazlasını integratöre geri besle ---
        if self.antiwindup == "backcalc" and self.ki > 1e-9 and self.out_limit is not None:
            self.integral += self.kb * (self.out - u_raw) / self.ki * dt
            self.integral = _clip(self.integral, self.integral_limit)
            self.i_term = self.ki * self.integral

        return self.out

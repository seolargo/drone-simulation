"""
DC (fırçasız) motor dinamiği — back-EMF.

Gerilim geri-EMK ve dirençsel kayıp toplamıdır:  V = I·R_m + k_v·ω
Tork akımla orantılı:                           τ = k_t·(I - I_o)
Rotor:                                          J·ω̇ = τ - τ_yük   (τ_yük = c·ω²)

Gerilim adımı verildiğinde ω yükselirken geri-EMK (E = k_v·ω) artar, akım düşer;
V - E → 0 olunca tork sıfırlanır ve motor son hızına ulaşır.
"""

R_M = 0.6       # motor direnci (ohm)
K_V = 0.02      # geri-EMK sabiti (V·s/rad)
K_T = 0.02      # tork sabiti (N·m/A)
I_O = 0.4       # boşta akım (A)
J = 8.0e-5      # rotor ataleti (kg·m²)
LOAD = 2.3e-7   # aerodinamik yük katsayısı (τ = c·ω²)
V_STEP = 12.0   # uygulanan gerilim adımı (V)


def run(dt=0.0004, duration=0.5):
    """Gerilim adımına motor tepkisi -> (t, ω, akım I)."""
    w = 0.0
    ts, ws, cur = [], [], []
    n = int(duration / dt)
    for i in range(n):
        current = (V_STEP - K_V * w) / R_M
        tau = K_T * (current - I_O)
        w += (tau - LOAD * w * w) / J * dt
        ts.append(i * dt)
        ws.append(w)
        cur.append(max(0.0, current))
    return ts, ws, cur

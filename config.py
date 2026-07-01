"""
Simülasyon ayarları — tüm sabitler tek yerde.

Dünya koordinatları (sağ-el, z yukarı):
    x -> sağ, y -> ileri (derinlik), z -> yukarı
    Zemin z = 0 düzleminde; drone yüksek z'den düşer.
"""

import math

# Pencere / zamanlama
WIDTH, HEIGHT = 900, 600
FPS = 60

# Fizik (dünya birimi / saniye^2), -z yönünde uygulanır
GRAVITY = 12.0

# İtki (thrust) — gövde-yukarı ekseni boyunca
THRUST_MAX = 22.0        # tam gazda ivme (yerçekimini yenmeli: > GRAVITY)
THROTTLE_RATE = 0.9      # gaz seviyesinin saniyedeki değişimi (W/S)

# Yönelim (attitude)
MAX_TILT = math.radians(18)     # PID'in komut edebileceği maksimum roll/pitch açısı (yumuşak)
YAW_RATE = math.radians(75)     # yaw dönüş hızı (rad/s, manuel)

# Eğim iç dinamiği (2. mertebe) — komuta sonlu hızda ulaşır (gerçekçilik + relay auto-tune için gerekli)
# PD yasasıyla eşdeğer: tau = I(Kp(θc-θ) - Kd·θ'),  Kp = ATT_WN^2,  Kd = 2·ATT_ZETA·ATT_WN
ATT_WN = 12.0                   # doğal frekans (rad/s)
ATT_ZETA = 0.7                  # sönüm oranı
YAW_TAU = 0.15                  # yaw hızı 1. mertebe gecikmesi (s) — τ_ψ transientleri için

# Fiziksel model sabitleri — tork (τ) ve rotor hızı (ω) gösterimi için
MASS = 1.0                      # kütle
I_XX = 0.01                     # atalet momentleri (roll/pitch/yaw)
I_YY = 0.01
I_ZZ = 0.02
ARM_L = 0.25                    # L — kol uzunluğu
THRUST_COEF = 1.2e-5            # k — itki katsayısı  (F_i = k·ω_i^2)
DRAG_COEF = 3.0e-7             # b — sürükleme/yaw katsayısı

# Otomatik uçuş kontrolü (PID)
CMD_SPEED = 3.0          # ok tuşlarının komut verdiği maksimum yatay hız (birim/s)
CLIMB_RATE = 2.0         # W/S ile irtifa hedefinin değişim hızı (birim/s)
HOVER_THROTTLE = GRAVITY / THRUST_MAX   # asılı kalma gazı (ileri besleme)

# Dış konum döngüsü: hata (hedef konum - gerçek konum) -> hız hedefi
# (komut yokken devreye girer; drone'u bir noktada tutar)
POS_KP = 1.6

# Yatay hız PID kazançları.
# AUTOTUNE=True iken bunlar yok sayılır ve relay feedback ile otomatik hesaplanır;
# False iken bu elle-ayarlı değerler kullanılır.
AUTOTUNE = True
VEL_KP = 0.09
VEL_KI = 0.02
VEL_KD = 0.03
# İrtifa PID: hata (hedef z - gerçek z) -> gaz düzeltmesi (hover üstüne eklenir)
ALT_KP = 0.11
ALT_KI = 0.03
ALT_KD = 0.16

PID_DERIV_TAU = 0.06     # PID türev alçak-geçiren zaman sabiti (s) — gürültüyü yumuşatır

# Anti-windup (integral sarma önleme) — main.py --antiwindup ile değişir
ANTIWINDUP = "backcalc"  # "none" | "clamp" (koşullu integrasyon) | "backcalc" (geri-hesaplama)
AW_KB = 3.0              # back-calculation izleme kazancı (1/Tt)

# Bozucu etkiler (gerçekçilik) — PID'in duruşta sürekli düzeltme yapmasını sağlar
WIND_ACCEL = 0.8         # türbülans ivmesi (birim/s^2, kararlı-hal std)
WIND_TAU = 0.45          # gust korelasyon süresi (s) — gust'ların değişim hızı
SENSOR_VEL_NOISE = 0.05  # hız ölçüm gürültüsü (birim/s, std) — ince titreme
SENSOR_POS_NOISE = 0.012 # konum ölçüm gürültüsü (birim, std)

# Drone
DRONE_ARM = 0.7          # kol uzunluğu (merkezden pervaneye)
DRONE_ROTOR_R = 0.32     # pervane yarıçapı
DRONE_START_Z = 5.0      # başlangıç yüksekliği (oyun alanı içinde)
ROTOR_SPIN = 28.0        # pervane dönüş hızı (rad/s, görsel)

# Oyun alanı sınırları — drone bu kutudan (ve ekrandan) çıkamaz
BOUND_XY = 3.7           # yatay sınır (±)
CEIL_Z = 6.0             # dikey tavan

# Kamera — oyun alanını tam çerçeveler
CAM_EYE = (8.0, -13.0, 8.0)
CAM_TARGET = (0.0, 0.0, 1.5)
CAM_UP = (0.0, 0.0, 1.0)
CAM_FOV_DEG = 58.0

# Zemin ızgarası
GROUND_HALF = 5          # ızgara -5..5 arası
GROUND_STEP = 1.0

# Renkler
BG_COLOR = (15, 18, 28)
GRID_COLOR = (45, 55, 75)
GRID_AXIS_COLOR = (70, 85, 115)
HUD_COLOR = (200, 205, 220)
SHADOW_COLOR = (8, 10, 16)
DRONE_ARM_COLOR = (90, 150, 220)
DRONE_HUB_COLOR = (70, 130, 200)
DRONE_ROTOR_COLOR = (170, 200, 235)
DRONE_BLADE_COLOR = (230, 235, 245)
DRONE_NOSE_COLOR = (240, 180, 70)

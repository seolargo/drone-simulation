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
MAX_TILT = math.radians(28)     # maksimum roll/pitch açısı
TILT_SLEW = math.radians(140)   # açının hedefe yaklaşma hızı (rad/s, kendiliğinden dengeleme)
YAW_RATE = math.radians(100)    # yaw dönüş hızı (rad/s)

# Drone
DRONE_ARM = 0.7          # kol uzunluğu (merkezden pervaneye)
DRONE_ROTOR_R = 0.32     # pervane yarıçapı
DRONE_START_Z = 7.0      # başlangıç yüksekliği
ROTOR_SPIN = 28.0        # pervane dönüş hızı (rad/s, görsel)

# Kamera
CAM_EYE = (8.0, -11.0, 6.0)
CAM_TARGET = (0.0, 0.0, 2.5)
CAM_UP = (0.0, 0.0, 1.0)
CAM_FOV_DEG = 60.0

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

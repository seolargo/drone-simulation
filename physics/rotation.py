"""
Dönüş (attitude) yardımcıları.

Roll-pitch-yaw açılarından gövde->dünya dönüş matrisi üretir.

Gövde ekseni: x = sağ, y = ileri (burun), z = yukarı.
    pitch -> sağ eksen (x) etrafında dönüş (burun yukarı/aşağı)
    roll  -> ileri eksen (y) etrafında dönüş (yana yatış)
    yaw   -> yukarı eksen (z) etrafında dönüş (burun yönü)

Bileşim sırası: R = Rz(yaw) @ Ry(roll) @ Rx(pitch)
"""

import numpy as np


def rotation_matrix(roll, pitch, yaw):
    cr, sr = np.cos(roll), np.sin(roll)
    cp, sp = np.cos(pitch), np.sin(pitch)
    cy, sy = np.cos(yaw), np.sin(yaw)

    Rx = np.array([[1, 0, 0],          # pitch (x ekseni)
                   [0, cp, -sp],
                   [0, sp, cp]])
    Ry = np.array([[cr, 0, sr],        # roll (y ekseni)
                   [0, 1, 0],
                   [-sr, 0, cr]])
    Rz = np.array([[cy, -sy, 0],       # yaw (z ekseni)
                   [sy, cy, 0],
                   [0, 0, 1]])
    return Rz @ Ry @ Rx

"""
Kamera — 3B dünya noktalarını 2B ekran koordinatlarına yansıtır.

Basit iğne deliği (pinhole) perspektif modeli: look-at ile kamera ekseni
kurulur, ardından perspektif bölme uygulanır.
"""

import numpy as np

from config import (
    WIDTH, HEIGHT, CAM_EYE, CAM_TARGET, CAM_UP, CAM_FOV_DEG,
)


def _normalize(v):
    n = np.linalg.norm(v)
    return v / n if n else v


class Camera:
    def __init__(self):
        self.eye = np.array(CAM_EYE, dtype=float)
        target = np.array(CAM_TARGET, dtype=float)
        up = np.array(CAM_UP, dtype=float)

        self.forward = _normalize(target - self.eye)
        self.right = _normalize(np.cross(self.forward, up))
        self.up = np.cross(self.right, self.forward)

        fov = np.radians(CAM_FOV_DEG)
        self.focal = (WIDTH / 2) / np.tan(fov / 2)

    def project(self, p):
        """
        Dünya noktası p -> (sx, sy, depth) veya None (kamera arkasındaysa).
        depth, derinlik sıralaması için kullanılabilir.
        """
        d = np.asarray(p, dtype=float) - self.eye
        depth = float(np.dot(d, self.forward))
        if depth <= 1e-6:
            return None
        cx = float(np.dot(d, self.right))
        cy = float(np.dot(d, self.up))
        sx = WIDTH / 2 + self.focal * cx / depth
        sy = HEIGHT / 2 - self.focal * cy / depth
        return (sx, sy, depth)

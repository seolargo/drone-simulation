"""
Çizim — 3B sahneyi kamera projeksiyonuyla ekrana resmeder.

Sahne: zemin ızgarası, drone gölgesi, drone (kollar + dönen pervaneler), HUD.
Fizikten bağımsızdır; yalnızca verilen durumu çizer.
"""

import numpy as np
import pygame

from config import (
    WIDTH, HEIGHT, GROUND_HALF, GROUND_STEP,
    BG_COLOR, GRID_COLOR, GRID_AXIS_COLOR, HUD_COLOR, SHADOW_COLOR,
    DRONE_ARM_COLOR, DRONE_HUB_COLOR, DRONE_ROTOR_COLOR, DRONE_BLADE_COLOR,
)
from .camera import Camera


class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.camera = Camera()
        self.font = pygame.font.SysFont("menlo", 16)

    def draw(self, drone, paused):
        self.screen.fill(BG_COLOR)
        self._draw_grid()
        self._draw_shadow(drone)
        self._draw_drone(drone)
        self._draw_hud(drone, paused)
        pygame.display.flip()

    # --- yardımcılar -----------------------------------------------------
    def _p(self, world_point):
        """Tek noktayı ekran (x, y) ikilisine yansıtır; arkadaysa None."""
        r = self.camera.project(world_point)
        return None if r is None else (r[0], r[1])

    def _line(self, a, b, color, width=1):
        pa, pb = self._p(a), self._p(b)
        if pa and pb:
            pygame.draw.line(self.screen, color, pa, pb, width)

    def _polyline(self, points, color, width=1):
        screen_pts = [self._p(p) for p in points]
        if all(sp is not None for sp in screen_pts) and len(screen_pts) >= 2:
            pygame.draw.lines(self.screen, color, False, screen_pts, width)

    # --- sahne parçaları -------------------------------------------------
    def _draw_grid(self):
        h, step = GROUND_HALF, GROUND_STEP
        coords = np.arange(-h, h + step, step)
        for c in coords:
            axis = abs(c) < 1e-9
            color = GRID_AXIS_COLOR if axis else GRID_COLOR
            w = 2 if axis else 1
            self._line((c, -h, 0.0), (c, h, 0.0), color, w)   # y boyunca
            self._line((-h, c, 0.0), (h, c, 0.0), color, w)   # x boyunca

    def _draw_shadow(self, drone):
        x, y, z = drone.pos
        center = self._p((x, y, 0.0))
        edge = self._p((x + 0.6, y, 0.0))
        if not center or not edge:
            return
        rx = max(3, int(abs(edge[0] - center[0])))
        # yükseklik arttıkça gölge biraz büyür ve yassılaşır
        ry = max(2, int(rx * 0.45))
        rect = pygame.Rect(0, 0, rx * 2, ry * 2)
        rect.center = (int(center[0]), int(center[1]))
        pygame.draw.ellipse(self.screen, SHADOW_COLOR, rect)

    def _draw_drone(self, drone):
        parts = drone.world_parts()

        # Kollar
        for p0, p1 in parts["arms"]:
            self._line(p0, p1, DRONE_ARM_COLOR, 3)

        # Pervaneler: disk konturu + dönen kanatlar
        for circle_pts, blades in parts["rotors"]:
            self._polyline(circle_pts, DRONE_ROTOR_COLOR, 1)
            for b0, b1 in blades:
                self._line(b0, b1, DRONE_BLADE_COLOR, 2)

        # Gövde merkezi
        c = self._p(parts["center"])
        if c:
            pygame.draw.circle(self.screen, DRONE_HUB_COLOR, (int(c[0]), int(c[1])), 6)

    def _draw_hud(self, drone, paused):
        if paused:
            durum = "DURAKLADI"
        elif drone.control.any():
            durum = "itki AKTİF"
        elif drone.on_ground:
            durum = "yerde"
        else:
            durum = "serbest düşüş"

        vz = drone.vel[2]
        line1 = (f"yükseklik z={drone.pos[2]:5.2f} | "
                 f"düşey hız vz={vz:7.2f} | {durum}")
        line2 = "ok tuşları: yukarı/aşağı + sol/sağ | W/S: ileri/geri | BOŞLUK dur | R sıfırla | Q çıkış"
        self.screen.blit(self.font.render(line1, True, HUD_COLOR), (10, 10))
        self.screen.blit(self.font.render(line2, True, HUD_COLOR), (10, 30))

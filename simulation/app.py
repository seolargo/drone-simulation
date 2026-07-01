"""
Uygulama — pygame'i kurar, olayları işler ve ana döngüyü çalıştırır.
"""

import sys
from pathlib import Path
from datetime import datetime

import pygame

from config import WIDTH, HEIGHT, FPS, CMD_SPEED
from entities import Drone
from rendering import Renderer
from analysis.telemetry import Telemetry
from analysis import report

OUTPUTS_DIR = Path(__file__).resolve().parents[1] / "web" / "outputs"


class App:
    def __init__(self, antiwindup=None):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.drone = Drone(antiwindup=antiwindup)
        pygame.display.set_caption(f"Simülasyon — 3B drone (PID · anti-windup: {self.drone.antiwindup})")
        self.clock = pygame.time.Clock()
        self.renderer = Renderer(self.screen)
        self.paused = False
        self.running = True

        self.telemetry = Telemetry()
        self.time = 0.0

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    self.drone.reset()

    def poll_control(self):
        """Basılı tuşlardan PID hedeflerini oku."""
        k = pygame.key.get_pressed()
        # Ok tuşları -> hedef yatay hız (PID eğimi kendisi hesaplar)
        vx = (k[pygame.K_RIGHT] - k[pygame.K_LEFT]) * CMD_SPEED   # ← / → : sol / sağ
        vy = (k[pygame.K_UP] - k[pygame.K_DOWN]) * CMD_SPEED      # ↑ / ↓ : ileri / geri
        self.drone.cmd_vel[:] = (vx, vy)
        self.drone.cmd_climb = k[pygame.K_w] - k[pygame.K_s]      # W / S : yüksel / alçal
        self.drone.cmd_yaw = k[pygame.K_a] - k[pygame.K_d]        # A / D : sola / sağa dön

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            self.handle_events()
            if not self.paused:
                self.poll_control()
                self.drone.update(dt)
                self.time += dt
                self.telemetry.record(self.time, self.drone)
            self.renderer.draw(self.drone, self.paused)

        # Bu oturumun telemetrisinden web çıktılarını üret
        try:
            when = datetime.now().strftime("%Y-%m-%d %H:%M")
            src = f"canlı oturum · anti-windup: {self.drone.antiwindup}"
            report.generate(self.telemetry, OUTPUTS_DIR, source=src, when=when,
                            tune=self.drone.tune_info)
        except Exception:
            pass

        pygame.quit()
        sys.exit()

"""
Uygulama — pygame'i kurar, olayları işler ve ana döngüyü çalıştırır.
"""

import sys

import pygame

from config import WIDTH, HEIGHT, FPS
from entities import Drone
from rendering import Renderer


class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Simülasyon — 3B drone (roll/pitch/yaw)")
        self.clock = pygame.time.Clock()
        self.renderer = Renderer(self.screen)

        self.drone = Drone()
        self.paused = False
        self.running = True

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
        """Basılı tuşlardan yönelim + gaz kontrolünü oku."""
        k = pygame.key.get_pressed()
        roll = k[pygame.K_RIGHT] - k[pygame.K_LEFT]   # ← / → : roll (sola/sağa yat → yana uç)
        pitch = k[pygame.K_DOWN] - k[pygame.K_UP]     # ↑ / ↓ : pitch (↑ burun aşağı → ileri uç)
        yaw = k[pygame.K_a] - k[pygame.K_d]           # A / D : yaw (sola/sağa dön)
        throttle = k[pygame.K_w] - k[pygame.K_s]      # W / S : gaz artır/azalt
        self.drone.control[:] = (roll, pitch, yaw, throttle)

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            self.handle_events()
            if not self.paused:
                self.poll_control()
                self.drone.update(dt)
            self.renderer.draw(self.drone, self.paused)

        pygame.quit()
        sys.exit()

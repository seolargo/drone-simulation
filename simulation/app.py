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
        pygame.display.set_caption("Simülasyon — 3B itkili drone")
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
        """Basılı tuşlardan itki yön vektörünü oku."""
        k = pygame.key.get_pressed()
        cx = k[pygame.K_RIGHT] - k[pygame.K_LEFT]   # x: sağ / sol
        cy = k[pygame.K_w] - k[pygame.K_s]          # y: ileri / geri (derinlik)
        cz = k[pygame.K_UP] - k[pygame.K_DOWN]       # z: yukarı / aşağı
        self.drone.control[:] = (cx, cy, cz)

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

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
        pygame.display.set_caption("Simülasyon — 3B düşen drone")
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

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            self.handle_events()
            if not self.paused:
                self.drone.update(dt)
            self.renderer.draw(self.drone, self.paused)

        pygame.quit()
        sys.exit()

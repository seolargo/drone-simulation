"""
Başlangıç simülasyonu — ekranda zıplayan toplar (yerçekimi + duvar sekmesi).
Ortamın çalıştığını doğrulamak ve üstüne geliştirmek için temel bir iskelet.

Çalıştırma:
    ~/Downloads/simulation/.venv/bin/python main.py

Kontroller:
    BOŞLUK : duraklat / devam et
    R      : sıfırla
    ESC/Q  : çıkış
"""

import sys
import numpy as np
import pygame

# --- Ayarlar -------------------------------------------------------------
WIDTH, HEIGHT = 900, 600
FPS = 60
N_BALLS = 30
GRAVITY = 600.0          # piksel / saniye^2
RESTITUTION = 0.85       # sekme enerji korunumu (1 = kayıpsız)
BG_COLOR = (15, 18, 28)


class Ball:
    def __init__(self, rng):
        self.r = rng.uniform(8, 22)
        self.pos = np.array(
            [rng.uniform(self.r, WIDTH - self.r),
             rng.uniform(self.r, HEIGHT / 2)],
            dtype=float,
        )
        self.vel = np.array([rng.uniform(-200, 200), rng.uniform(-100, 100)], dtype=float)
        self.color = tuple(int(c) for c in rng.integers(80, 256, size=3))

    def update(self, dt):
        self.vel[1] += GRAVITY * dt
        self.pos += self.vel * dt

        # Duvar sekmeleri
        for i, limit in enumerate((WIDTH, HEIGHT)):
            if self.pos[i] - self.r < 0:
                self.pos[i] = self.r
                self.vel[i] *= -RESTITUTION
            elif self.pos[i] + self.r > limit:
                self.pos[i] = limit - self.r
                self.vel[i] *= -RESTITUTION

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, self.pos.astype(int), int(self.r))


def make_balls():
    rng = np.random.default_rng()
    return [Ball(rng) for _ in range(N_BALLS)]


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Simülasyon — zıplayan toplar")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("menlo", 16)

    balls = make_balls()
    paused = False
    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    balls = make_balls()

        if not paused:
            for b in balls:
                b.update(dt)

        screen.fill(BG_COLOR)
        for b in balls:
            b.draw(screen)

        hud = f"FPS {clock.get_fps():4.0f} | toplar {len(balls)} | {'DURAKLADI' if paused else 'çalışıyor'}  (BOŞLUK/R/Q)"
        screen.blit(font.render(hud, True, (200, 205, 220)), (10, 10))
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

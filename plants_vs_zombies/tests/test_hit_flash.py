"""Hit flashes brighten sprite pixels without changing the transparent lawn."""
import os
from pathlib import Path
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame
import config as C
from assets import Anim
from entities import Zombie
from game import Game


def main():
    g = Game()
    try:
        background = (23, 47, 65)
        sprite = pygame.Surface((30, 42), pygame.SRCALPHA)
        sprite.fill((90, 20, 10, 0))  # Hidden RGB must not leak into the lawn.
        pygame.draw.rect(sprite, (30, 60, 90, 255), (8, 8, 14, 26))
        z = Zombie(70, 2, 'normal')
        z.y = 100
        z.anim = Anim([sprite])
        original = pygame.image.tobytes(sprite, 'RGBA')
        canvas = pygame.Surface((140, 120))
        canvas.fill(background)
        z._hit_flash = 0.1
        z.draw(canvas)
        assert canvas.get_at((55, 58))[:3] == background
        assert canvas.get_at((70, 80))[:3] == (125, 155, 185)
        assert pygame.image.tobytes(sprite, 'RGBA') == original
        # Cover actual walk/attack/death/rage frames for all five zombie kinds.
        checked = 0
        for kind in C.ZOMBIES:
            zombie = Zombie(400, 2, kind)
            zombie.y = 400
            zombie.paper_hp = 0
            for frames in zombie._sets.values():
                if not frames:
                    continue
                image = frames[0]
                zombie.anim = Anim([image])
                zombie._hit_flash = 0.1
                canvas = pygame.Surface((900, 600))
                canvas.fill(background)
                zombie.draw(canvas)
                left, top = 400 - image.get_width() // 2, 400 - image.get_height()
                for x in range(0, image.get_width(), 3):
                    for y in range(0, image.get_height(), 3):
                        if image.get_at((x, y)).a == 0:
                            assert canvas.get_at((left + x, top + y))[:3] == background, (kind, x, y)
                            checked += 1
        assert checked > 100
        print(f'PASS: sprite-only hit flash, unchanged cached art and {checked} transparent pixel samples')
    finally:
        pygame.quit()


if __name__ == '__main__':
    main()

"""Every road turn remains connected, with no order-dependent overlapping tiles."""
import os
from pathlib import Path
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame
import config as C
from scenery import road_image, field_image


def main():
    pygame.init()
    try:
        for index, level in enumerate(C.LEVELS):
            points = tuple((col * C.TILE + C.TILE // 2, row * C.TILE + C.TILE // 2)
                           for col, row in level['path'])
            road = road_image(points, level['theme'])
            reversed_road = road_image(tuple(reversed(points)), level['theme'])
            assert pygame.image.tobytes(road, 'RGBA') == pygame.image.tobytes(reversed_road, 'RGBA')
            assert len(pygame.mask.from_surface(road).connected_components()) == 1
            cells = C.path_cells(level['path'])
            for row in range(C.GRID_ROWS):
                for col in range(C.GRID_COLS):
                    x, y = col * C.TILE + C.TILE // 2, row * C.TILE + C.TILE // 2
                    assert bool(road.get_at((x, y)).a) == ((col, row) in cells)
            # Follow the actual route pixel by pixel, including each turn.
            for (x0, y0), (x1, y1) in zip(points, points[1:]):
                steps = max(abs(x1 - x0), abs(y1 - y0))
                for step in range(steps + 1):
                    x = round(x0 + (x1 - x0) * step / steps)
                    y = round(y0 + (y1 - y0) * step / steps)
                    if 0 <= x < C.FIELD_W and 0 <= y < C.FIELD_H:
                        # Smoothscale can quantize opaque alpha to 253;
                        # the route interior must remain fully covered.
                        assert road.get_at((x, y)).a >= 250
            assert field_image(index).get_size() == (C.FIELD_W, C.FIELD_H)
        print('PASS: all eight map routes, all turns, connected surfaces, buildable cell boundaries and direction-independent road textures')
    finally:
        pygame.quit()


if __name__ == '__main__':
    main()

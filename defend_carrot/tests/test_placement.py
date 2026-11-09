"""Placement feedback shares the purchase rules and never spends on failure."""
import os
from pathlib import Path
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame
import config as C
from game import Game
from entities import tile_center


def main():
    g = Game()
    try:
        for level in range(len(C.LEVELS)):
            g.reset()
            g._load_level(level)
            g.coins = 500
            g.selected = 'apple'
            before = g.coins
            path_cell = next(cell for cell in g.path_cells if 0 <= cell[0] < C.GRID_COLS and 0 <= cell[1] < C.GRID_ROWS and cell != g.carrot_tile)
            for cell, fragment in ((path_cell, '道路'), (g.carrot_tile, '萝卜')):
                g._on_click(tile_center(*cell))
                assert fragment in g.notice and g.coins == before and not g.fruits
                assert g.selected == 'apple'
                g.draw()
                g.ui.draw_placement(tile_center(*cell))
            assert g.field_cell((0, C.HUD_H - 1)) is None
            assert g.field_cell((0, C.HUD_H + C.FIELD_H)) is None
            assert g.field_cell((C.SCREEN_W, C.HUD_H)) is None
            g._on_click((-1, C.HUD_H))
            assert '草地' in g.notice and g.coins == before
            cell = next((c, r) for r in range(C.GRID_ROWS) for c in range(C.GRID_COLS) if g.can_build(c, r))
            g.coins = C.FRUITS['apple']['cost'] - 1
            g._on_click(tile_center(*cell))
            assert '还差 1' in g.notice and not g.fruits
            g.coins += 1
            assert not g.building_error(cell)
            g.draw()
            g.ui.draw_placement(tile_center(*cell))
            g.ui.draw_battle_info(tile_center(*cell))
            g._on_click(tile_center(*cell))
            assert len(g.fruits) == 1 and g.coins == 0 and g.notice_timer == 0
            g.selected = 'orange'
            g._on_click(tile_center(*cell))
            assert '防御塔' in g.notice and len(g.fruits) == 1 and g.coins == 0
            g.selected = None
            g.ui.draw_placement(tile_center(*cell))
            g.update(3)
            assert g.notice_timer == 0
        print('PASS: eight-map previews, field bounds, path/goal/occupancy/coins feedback and purchase consistency')
    finally:
        pygame.quit()


if __name__ == '__main__':
    main()

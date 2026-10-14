# -*- coding: utf-8 -*-
"""Exercise every plant class headless: place it, run a while, no crash."""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config as C  # noqa: E402
from game import Game  # noqa: E402


def main():
    game = Game()
    game.owned_plants = list(C.SHOP_ORDER)
    game.start_level(len(C.LEVELS) - 1, "select")   # widest lawn
    game.seeds = list(C.SHOP_ORDER)[:C.MAX_SEEDS]
    game.state = "playing"
    game.sun = 9999
    dt = 1.0 / C.FPS

    # Place one of every plant in the shop across distinct cells.
    for i, kind in enumerate(game.seeds):
        col, row = i % C.GRID_COLS, i // C.GRID_COLS
        game.selected = kind
        game._on_click((C.LAWN_X + col * C.CELL_W + C.CELL_W // 2,
                        C.LAWN_Y + row * C.CELL_H + C.CELL_H // 2))
    placed = len(game.plants)
    print("placed:", placed, "of", len(game.seeds), "rows:", game.rows)
    assert placed == len(game.seeds), "not every plant could be placed"

    # Spawn one of each zombie and let the sim run.
    for row, kind in enumerate(list(C.ZOMBIES)[:game.rows]):
        from entities import Zombie
        game.zombies.append(Zombie(C.SCREEN_W - 40, row, kind))

    for _ in range(int(60 / dt)):
        game.update(dt)
        game.draw()
    print("after 60s -> state:", game.state, "zombies:", len(game.zombies))
    print("PASS: all plant and zombie classes ran without error")


if __name__ == "__main__":
    main()

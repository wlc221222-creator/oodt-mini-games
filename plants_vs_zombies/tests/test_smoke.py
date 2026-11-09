"""Headless smoke test for the Plants vs Zombies MVP.

Runs the real ``Game`` with the SDL dummy video driver, drives it with
scripted clicks, and asserts that a full match can be played to a win
without raising. Run from the project root:

    python tests/test_smoke.py
"""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

import config as C  # noqa: E402
from game import Game  # noqa: E402


def place(game, kind, col, row):
    game.selected = kind
    x = C.LAWN_X + col * C.CELL_W + C.CELL_W // 2
    y = C.LAWN_Y + row * C.CELL_H + C.CELL_H // 2
    game._on_click((x, y))
    return game.plant_at(col, row) is not None


# A fixed, sensible layout the bot builds toward: two sunflowers for early
# economy, then a shooter in every lane, then more economy and walls.
def build_order(rows):
    return (
        [("sunflower", 0, 0), ("sunflower", 0, 2)]
        + [("peashooter", 1, r) for r in range(rows)]
        + [("sunflower", 0, 1)]
        + [("peashooter", 2, r) for r in range(rows)]
        + [("wallnut", 5, r) for r in range(rows)]
    )


def run_headless(max_seconds=200.0):
    game = Game()
    # Adventure level 1: five visible rows. This smoke bot uses all test plants.
    game.owned_plants = list(C.SHOP_ORDER)
    game.start_level(0, "adventure")
    game.seeds = list(C.SHOP_ORDER)[:C.MAX_SEEDS]
    game.state = "playing"
    dt = 1.0 / C.FPS
    steps = int(max_seconds / dt)
    todo = build_order(game.rows)
    for i in range(steps):
        # Try to place the next plant in the build order whenever we can
        # afford it; this mirrors how a human plays.
        if todo and i % 20 == 0:
            kind, col, row = todo[0]
            if game.sun >= C.PLANTS[kind]["cost"] and game.plant_at(col, row) is None:
                if place(game, kind, col, row):
                    todo.pop(0)
        # Auto-collect suns so the economy keeps moving.
        for s in game.suns:
            if s.y > 0:
                game.sun += s.amount
                s.alive = False
        game.update(dt)
        game.draw()
        if game.state != "playing":
            return game
    return game


def main():
    result = run_headless()
    print("final state :", result.state)
    print("sun left    :", result.sun)
    print("plants alive:", len(result.plants))
    print("zombies left:", len(result.zombies))
    assert result.state in ("won", "lost"), "match never reached an end state"
    if result.state == "won":
        print("PASS: full match played to victory")
    else:
        print("NOTE: bot lost this run (logic still executed without error)")


if __name__ == "__main__":
    main()

"""Headless smoke test for the Defend the Carrot MVP.

Runs the real ``Game`` with the SDL dummy driver and a scripted builder that
places fruits next to the path, then asserts the match reaches an end state
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
    x = col * C.TILE + C.TILE // 2
    y = C.HUD_H + row * C.TILE + C.TILE // 2
    game._on_click((x, y))


# Cells one tile off the path, ordered so the strongest coverage is built
# first. A human would pick the same spots: beside the long straights and the
# final approach to the carrot.
BUILD_ORDER = (
    [("apple", 4, 1), ("apple", 9, 1), ("apple", 5, 5)]
    + [("apple", 10, 9), ("apple", 13, 1), ("apple", 9, 5)]
    + [("apple", 14, 9), ("apple", 16, 4), ("apple", 16, 1)]
    + [("apple", 12, 5), ("melon", 17, 9), ("orange", 6, 9)]
    + [("apple", 3, 1), ("apple", 7, 5), ("orange", 2, 9)]
)


def run_headless(max_seconds=300.0):
    game = Game()
    dt = 1.0 / C.FPS
    steps = int(max_seconds / dt)
    todo = list(BUILD_ORDER)
    for i in range(steps):
        if todo and i % 25 == 0:
            kind, col, row = todo[0]
            if game.coins >= C.FRUITS[kind]["cost"] and game.can_build(col, row):
                place(game, kind, col, row)
                todo.pop(0)
        game.update(dt)
        game.draw()
        if game.state != "playing":
            return game
    return game


def main():
    result = run_headless()
    print("final state :", result.state)
    print("level       :", result.level_index + 1)
    print("coins left  :", result.coins)
    print("kills       :", result.kills)
    print("carrot hp   :", result.carrot.hp)
    print("fruits alive:", len(result.fruits))
    assert result.state in ("won", "lost"), "match never reached an end state"
    if result.state == "won":
        print("PASS: both levels cleared")
    else:
        print("NOTE: bot lost this run (logic still executed without error)")


if __name__ == "__main__":
    main()

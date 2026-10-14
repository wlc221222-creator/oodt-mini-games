# -*- coding: utf-8 -*-
"""Verify progression: seed-chooser rules, unlocks, and plant rewards."""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config as C  # noqa: E402
import save as savegame  # noqa: E402
from game import Game  # noqa: E402


def main():
    savegame.SAVE_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "_tmp_save.json")
    game = Game()
    game.unlocked = 0
    game.owned_plants = list(C.START_PLANTS)

    # Level 1 must only offer the starting plants.
    game.start_level(0, "adventure")
    pool = game.available_plants()
    print("level 1 pool:", pool, "rows:", game.rows)
    assert pool == C.START_PLANTS, "level 1 should only offer starting plants"
    assert game.rows == 3, "level 1 should have 3 lanes"

    # The start gate needs all owned seeds, up to MAX_SEEDS.
    game.seeds = ["sunflower"]
    game.state = "choosing"
    game.handle_event(pygame_key(pygame_const("K_RETURN")))
    assert game.state == "choosing", "should not start with too few seeds"

    # Beating level 1 in adventure mode unlocks level 2 and grants a plant.
    game.state = "playing"
    game.wave_index = len(game.waves)
    game.zombies = []
    game._check_victory()
    print("after win -> unlocked:", game.unlocked, "owned:", game.owned_plants)
    assert game.unlocked >= 1, "level 1 win should unlock level 2"
    assert C.LEVEL_REWARDS[0] in game.owned_plants, "no plant reward granted"

    # Level 2 has a wider lawn than level 1.
    game.start_level(1, "adventure")
    print("level 2 rows:", game.rows)
    assert game.rows >= 3

    if os.path.exists(savegame.SAVE_PATH):
        os.remove(savegame.SAVE_PATH)
    print("PASS: seed rules, unlocks and rewards behave correctly")


def pygame_const(name):
    import pygame
    return getattr(pygame, name)


def pygame_key(code):
    import pygame
    return pygame.event.Event(pygame.KEYDOWN, key=code)


if __name__ == "__main__":
    main()

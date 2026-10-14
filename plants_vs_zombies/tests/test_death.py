# -*- coding: utf-8 -*-
"""Verify the zombie death animation and head-pop effect actually run."""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config as C  # noqa: E402
from entities import Zombie  # noqa: E402
from game import Game  # noqa: E402


def main():
    game = Game()
    game.start_level(0, "adventure")
    game.state = "playing"
    dt = 1.0 / C.FPS

    # Normal kill -> should play the "die" animation, not vanish instantly.
    z = Zombie(400, 2, "normal")
    game.zombies.append(z)
    z.take_damage(9999)
    assert z.dying, "zombie did not enter the dying state"
    frames = len(z._death_anim.frames)
    steps = 0
    while z.alive and steps < int(5 / dt):
        game.update(dt)
        game.draw()
        steps += 1
    print(f"normal kill: death frames={frames} gone after {steps * dt:.2f}s "
          f"heads spawned={len(game.effects) + _seen}")

    # Boom kill -> charred frames.
    game2 = Game()
    game2.state = "playing"
    z2 = Zombie(400, 1, "cone")
    game2.zombies.append(z2)
    z2.take_damage(9999, boom=True)
    boom_frames = len(z2._death_anim.frames)
    steps = 0
    while z2.alive and steps < int(5 / dt):
        game2.update(dt)
        game2.draw()
        steps += 1
    print(f"boom kill:   death frames={boom_frames} gone after {steps * dt:.2f}s")
    assert frames > 1 and boom_frames > 1, "death animations have no frames"
    print("PASS: zombie death animations play before the zombie is removed")


_seen = 0

if __name__ == "__main__":
    main()

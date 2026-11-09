"""Regress escape rewards, terminal outcomes, score and guide input isolation."""
import os
from pathlib import Path
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame
import config as C
from entities import Slime
from game import Game


def escape(game):
    monster = Slime(game)
    monster.x, monster.y = game.path[-1]
    monster.seg = len(game.path) - 1
    game.monsters = [monster]
    return monster


def main():
    g = Game()
    try:
        g.reset()
        coins = g.coins
        escape(g)
        g.update(1 / 60)
        assert g.carrot.hp == C.CARROT_HP - 1
        assert (g.coins, g.kills, g.score) == (coins, 0, 0)

        g.reset()
        coins = g.coins
        monster = Slime(g)
        monster.take_damage(monster.hp)
        # A dead monster at the exit must not move, bite, or reward twice.
        monster.x, monster.y = g.path[-1]
        monster.seg = len(g.path) - 1
        g.monsters = [monster]
        g.update(1 / 60)
        g._reap()
        assert (g.coins, g.kills, g.score) == (coins + monster.reward, 1, monster.reward)
        assert g.carrot.hp == C.CARROT_HP
        g.selected = 'orange'
        g._on_click((4 * C.TILE + 20, C.HUD_H + C.TILE + 20))
        assert len(g.fruits) == 1 and g.score == monster.reward
        assert g.coins == coins + monster.reward - C.FRUITS['orange']['cost']

        for hp, expected in ((1, 'lost'), (2, 'won')):
            g.reset()
            g._load_level(len(C.LEVELS) - 1)
            g.wave_index = len(C.LEVELS[-1]['waves']) - 1
            g.spawn_queue = []
            g.carrot.hp = hp
            escape(g)
            g.update(1 / 60)
            g._check_victory()
            assert g.state == expected, (hp, g.state)
            assert g.kills == g.score == 0
            g.draw()

        g.reset()
        g.selected = 'apple'
        snapshot = (g.elapsed, g.wave_timer, g.coins, g.score)
        g.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=g.guide.button_rect.center))
        assert g.guide_open
        g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_3))
        g.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(180, 116)))
        g.update(20)
        g.draw()
        assert snapshot == (g.elapsed, g.wave_timer, g.coins, g.score)
        assert g.selected == 'apple' and not g.fruits
        g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        assert not g.guide_open and g.state == 'playing'
        g.update(1 / 60)
        assert g.elapsed > snapshot[0]
        print('PASS: escape rewards, kill-only score, failure precedence, guide pause and input isolation')
    finally:
        pygame.quit()


if __name__ == '__main__':
    main()

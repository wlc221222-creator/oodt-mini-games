"""Presentation animates independently, with real navigation and frozen battles."""
import os
from pathlib import Path
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame
from game import Game
from entities import Slime


def main():
    game = Game()
    try:
        def click(rect):
            game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center))

        def key(value):
            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=value))

        def snapshot():
            return (game.state, game.elapsed, game.wave_timer, game.coins, game.carrot.hp,
                    tuple(tuple(item) for item in game.spawn_queue),
                    tuple((m.x, m.y, m.hp, m.walk_animation.elapsed) for m in game.monsters))

        def frame():
            game.draw()
            return pygame.image.tobytes(game.screen, 'RGB')

        # The menu has its own scene and animated characters; drawing is read-only.
        before = snapshot()
        initial = frame()
        assert frame() == initial
        game.update(.31)
        assert frame() != initial and snapshot() == before
        # A hidden battle toolbar must not act as a home-screen button.
        click(game.guide.button_rect)
        assert not game.guide_open
        click(game.ui.level_button_rect)
        assert game.level_select_open
        frame()
        click(game.ui.level_rect(7))
        assert game.level_select_open and game.state == 'menu'
        click(game.ui.back_rect)
        assert not game.level_select_open and game.state == 'menu'
        click(game.ui.secondary_rect)
        assert game.guide_open
        click(game.guide.monsters_rect)
        image = frame()
        before = snapshot()
        game.update(.25)
        assert frame() != image and snapshot() == before
        click(game.guide.close_rect)
        assert not game.guide_open
        click(game.ui.primary_rect)
        assert game.state == 'playing'

        game.monsters = [Slime(game)]
        for state, guide in (('paused', False), ('paused', True), ('playing', True)):
            game.state, game.guide_open = state, guide
            before = snapshot()
            game.update(.7)
            image = frame()
            assert frame() == image and snapshot() == before
            if guide:
                click(game.guide.close_rect)
                assert not game.guide_open and game.state == state
        game.state = 'paused'
        click(game.ui.primary_rect)
        assert game.state == 'playing'
        game.update(.1)
        assert game.monsters[0].walk_animation.elapsed > 0

        for state in ('levelclear', 'won', 'lost'):
            game.state = state
            if state == 'lost':
                game.carrot.hp = 0
            frame()
            if state == 'lost':
                click(game.ui.primary_rect)
                assert game.state == 'playing' and game.carrot.hp == 3
            else:
                click(game.ui.secondary_rect)
                assert game.state == 'menu'
        print('PASS: animated menu/guide, visible navigation, result controls and independent paused simulation')
    finally:
        pygame.quit()


if __name__ == '__main__':
    main()

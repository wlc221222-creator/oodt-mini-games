"""Pause must freeze the real battlefield and isolate input at scaled sizes."""
import os
from pathlib import Path
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame
from game import Game
from entities import Zombie
from garden_ui import PAUSE_BUTTON_RECT, PAUSE_RESUME_RECT, PAUSE_MENU_RECT


def main():
    g = Game()
    try:
        def key(value):
            g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=value))

        def click(rect):
            v = g.viewport()
            pos = (round(v.x + rect.centerx * v.w / 800), round(v.y + rect.centery * v.h / 600))
            g.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))

        g.start_adventure()
        key(pygame.K_a)
        key(pygame.K_RETURN)
        g.zombies = [Zombie(600, 2, 'normal')]
        g.spawn_sun(300, 200, 25, falls=False)
        g.cooldowns['sunflower'] = 5
        g.selected = 'peashooter'

        def snapshot():
            return (g.elapsed, g.sun, g.wave_timer, g.sky_sun_timer,
                    dict(g.cooldowns), g.zombies[0].x, len(g.plants),
                    g.suns[0].alive, g.suns[0].life, g.selected)

        for size in ((800, 600), (1200, 700), (400, 300)):
            g.handle_event(pygame.event.Event(pygame.VIDEORESIZE, w=size[0], h=size[1]))
            click(PAUSE_BUTTON_RECT)
            assert g.state == 'paused'
            before = snapshot()
            g.update(30)
            key(pygame.K_1)
            g.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=3, pos=(200, 200)))
            g._on_click((300, 200))
            g._on_click((200, 250))
            assert snapshot() == before
            g.draw()
            key(pygame.K_i)
            g.update(20)
            key(pygame.K_ESCAPE)
            assert g.state == 'paused' and not g.almanac.opened
            assert snapshot() == before
            click(PAUSE_RESUME_RECT)
            assert g.state == 'playing'

        key(pygame.K_p)
        key(pygame.K_RETURN)
        assert g.state == 'playing'
        g.update(1 / 60)
        assert g.elapsed > before[0] and g.zombies[0].x < before[5]
        assert g.cooldowns['sunflower'] < before[4]['sunflower']
        key(pygame.K_p)
        key(pygame.K_ESCAPE)
        assert g.state == 'playing'
        key(pygame.K_p)
        click(PAUSE_MENU_RECT)
        assert g.state == 'menu' and g.selected is None
        print('PASS: paused timers/entities/input, guide return, scaled controls and resume')
    finally:
        pygame.quit()


if __name__ == '__main__':
    main()

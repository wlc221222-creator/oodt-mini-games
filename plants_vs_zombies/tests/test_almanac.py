"""Exercise the guide through real keyboard and scaled mouse events."""
import os
from pathlib import Path
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame
import config as C
from game import Game


def main():
    g = Game()
    try:
        def key(value):
            g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=value))

        def click(rect):
            viewport = g.viewport()
            pos = (round(viewport.x + rect.centerx * viewport.w / C.SCREEN_W),
                   round(viewport.y + rect.centery * viewport.h / C.SCREEN_H))
            g.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))

        assert set(C.PLANTS) == set(C.PLANT_HELP)
        assert set(C.ZOMBIES) == set(C.ZOMBIE_HELP)
        for size in ((800, 600), (1200, 700), (400, 300)):
            g.handle_event(pygame.event.Event(pygame.VIDEORESIZE, w=size[0], h=size[1]))
            click(g.almanac.menu_rect)
            assert g.almanac.opened and g.state == 'menu'
            seen = set()
            for category, registry in enumerate((C.PLANTS, C.ZOMBIES)):
                click(g.almanac.tabs[category])
                for page in range(g.almanac.page_count()):
                    assert g.almanac.page == page
                    start = page * g.almanac.page_size
                    seen.update(g.almanac.entries()[start:start + g.almanac.page_size])
                    g.draw()
                    key(pygame.K_RIGHT)
                assert set(registry) <= seen
                assert g.almanac.page == g.almanac.page_count() - 1
            click(g.almanac.close_rect)
            assert not g.almanac.opened and g.state == 'menu'

        g.start_adventure()
        key(pygame.K_a)
        key(pygame.K_RETURN)
        assert g.state == 'playing'
        selected, snapshot = g.selected, (g.elapsed, g.sun, g.wave_timer, dict(g.cooldowns))
        key(pygame.K_i)
        g.update(30)
        key(pygame.K_1)
        key(pygame.K_RETURN)
        click(g._seed_slot_rect(0))
        assert g.selected == selected and g.state == 'playing'
        assert snapshot == (g.elapsed, g.sun, g.wave_timer, g.cooldowns)
        key(pygame.K_TAB)
        assert g.almanac.page == 0
        key(pygame.K_ESCAPE)
        assert not g.almanac.opened and g.state == 'playing'
        g.update(1 / 60)
        assert g.elapsed > snapshot[0]
        print('PASS: complete introductions, guide pagination, scaled clicks, battle pause and resume')
    finally:
        pygame.quit()


if __name__ == '__main__':
    main()

"""Regress real mouse placement, authored waves and day/night resources."""
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame
import config as C
import save
from game import Game
from entities import Sunflower, Sun


def drag_canvas(g, start, end):
    for event_type, pos, extra in (
            (pygame.MOUSEBUTTONDOWN, start, {'button': 1}),
            (pygame.MOUSEMOTION, end, {'buttons': (1, 0, 0)}),
            (pygame.MOUSEBUTTONUP, end, {'button': 1})):
        rect = g.viewport()
        window = (round(rect.x + pos[0] * rect.w / C.SCREEN_W),
                  round(rect.y + pos[1] * rect.h / C.SCREEN_H))
        g.handle_event(pygame.event.Event(event_type, pos=window, **extra))


def main():
    original = save.SAVE_PATH
    try:
        with tempfile.TemporaryDirectory() as temp:
            save.SAVE_PATH = str(Path(temp) / 'save.json')
            g = Game()
            for size in ((800, 600), (1200, 800), (1001, 777), (1920, 1080)):
                g.screen = pygame.display.set_mode(size)
                for level in range(len(C.LEVELS)):
                    g.start_level(level, 'select')
                    g.state = 'playing'
                    g.seeds = ['sunflower']
                    g.sun = 10000
                    for row in range(5):
                        for col in range(9):
                            g.cooldowns['sunflower'] = 0
                            drag_canvas(g, g._card_rect(0).center,
                                        (C.LAWN_X + col * C.CELL_W + 40,
                                         C.LAWN_Y + row * C.CELL_H + 50))
                            plant = g.plant_at(col, row)
                            assert plant is not None, (size, level, col, row)
                            assert isinstance(plant.row, int) and isinstance(plant.col, int)
                    assert len(g.plants) == 45
            print(f'PASS: all 45 cells, {len(C.LEVELS)} levels, four viewport sizes ({45 * len(C.LEVELS) * 4} drag placements)')

            g.start_level(0, 'select')
            g.state = 'playing'
            g.seeds = ['sunflower']
            g.selected = 'sunflower'
            g.sun = 0
            g._on_click((75, 450))
            assert not g.plants and '阳光不足' in g.notice
            g.sun = 100
            g.cooldowns['sunflower'] = 3
            g._on_click((75, 450))
            assert not g.plants and '冷却' in g.notice
            g.cooldowns['sunflower'] = 0
            g._on_click((75, 450))
            assert g.plant_at(0, 3) is not None and g.sun == 50
            g.selected = 'sunflower'
            g._on_click((75, 450))
            assert len(g.plants) == 1 and g.sun == 50 and '已经' in g.notice
            for pos in ((34, 350), (755, 350), (75, 99), (75, 600)):
                g._on_click(pos)
                assert len(g.plants) == 1 and g.sun == 50
            sun = Sun(600, 400, 25, False)
            g.suns = [sun]
            g._on_click((600, 400))
            g._on_click((600, 400))
            assert g.sun == 75, 'one sun must only pay once'
            print('PASS: insufficient sun, recharge, occupied cell, lawn bounds, single collection')

            for index, level in enumerate(C.LEVELS):
                assert level['rows'] == 5
                assert len(level['wave_names']) == len(level['waves'])
                g.start_level(index, 'select')
                for wave, entries in enumerate(g.waves):
                    g._load_wave(wave)
                    assert [tuple(x) for x in g.spawn_queue] == entries
                    for kind, delay, row in entries:
                        assert kind in C.ZOMBIES and delay >= 0 and 0 <= row < 5
                g._load_wave(0)
                g._update_waves(level['waves'][0][0][1])
                z = g.zombies[0]
                assert abs(z.speed - C.ZOMBIES[z.kind]['speed'] * level.get('speed_multiplier', 1)) < 1e-8
                g.state = 'choosing'
                g.draw()
            print(f'PASS: authored lanes, wave names, speed rules and chooser rendering for all {len(C.LEVELS)} levels')

            for index in (0, 5):
                g.start_level(index, 'select')
                g.state = 'playing'
                g.sky_sun_timer = 0
                g.update(0.1)
                assert bool(g.suns) == C.LEVELS[index]['sky_sun']
                if g.suns:
                    assert C.LAWN_Y + 60 <= g.suns[0].target_y <= C.SCREEN_H - 50
                g.plants = [Sunflower(0, 3)]
                g.plants[0].timer = 0
                g.update(0.1)
                assert any(not s.falls for s in g.suns), 'night must retain sunflower income'
            g.start_level(4, 'select')
            g.state = 'playing'
            g.spawn_queue = []
            initial_sun = g.sun
            g._update_waves(0.1)
            assert g.sun == initial_sun + 75 and g.wave_index == 1
            g._update_waves(0.1)
            assert g.sun == initial_sun + 75, 'bonus must only be paid once'
            g.wave_index = len(g.waves) - 1
            g.spawn_queue = []
            g.zombies = []
            g._update_waves(0.1)
            g._check_victory()
            assert g.state == 'won' and g.sun == initial_sun + 150
            g._update_waves(0.1)
            assert g.sun == initial_sun + 150
            print('PASS: day/night economy, visible sun landing and exactly-once wave supplies')
    finally:
        save.SAVE_PATH = original
        pygame.quit()


if __name__ == '__main__':
    main()

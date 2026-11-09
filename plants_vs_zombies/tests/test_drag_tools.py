"""Real drag/drop events, cancellation and shovel behavior across viewports."""
import os
from pathlib import Path
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame
import config as C
from game import Game
from entities import Peashooter, Sun
from garden_ui import SHOVEL_RECT


def main():
    g = Game()
    try:
        def event(kind, pos, button=1):
            v = g.viewport()
            window = (round(v.x + pos[0] * v.w / 800), round(v.y + pos[1] * v.h / 600))
            extra = {'buttons': (1, 0, 0)} if kind == pygame.MOUSEMOTION else {'button': button}
            g.handle_event(pygame.event.Event(kind, pos=window, **extra))

        def key(value):
            g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=value))

        target = (C.LAWN_X + 2 * C.CELL_W + 40, C.LAWN_Y + 3 * C.CELL_H + 50)
        for size in ((800, 600), (1200, 800), (1001, 777), (1920, 1080)):
            g.screen = pygame.display.set_mode(size)
            g.start_level(0, 'select')
            g.state = 'playing'
            g.seeds = ['sunflower', 'peashooter']
            g.sun = 500
            card = g._card_rect(0).center
            event(pygame.MOUSEBUTTONDOWN, card)
            assert g.drag_kind == 'sunflower' and g.sun == 500 and not g.plants
            event(pygame.MOUSEMOTION, target)
            assert abs(g.drag_pos[0] - target[0]) < 1 and abs(g.drag_pos[1] - target[1]) < 1
            g.draw()
            assert not g.plants and g.cooldowns['sunflower'] == 0
            event(pygame.MOUSEBUTTONUP, target)
            assert g.plant_at(2, 3).kind == 'sunflower'
            assert g.sun == 450 and g.cooldowns['sunflower'] == C.PLANTS['sunflower']['recharge']
            event(pygame.MOUSEBUTTONUP, target)
            assert len(g.plants) == 1 and g.drag_kind is None and g.selected is None
            # A cooling card cannot be picked up. Invalid drops cost nothing.
            event(pygame.MOUSEBUTTONDOWN, card)
            assert g.drag_kind is None and '冷却' in g.notice
            g.cooldowns['sunflower'] = 0
            for invalid in ((780, 110), (40, 50), target, (-10, 200)):
                event(pygame.MOUSEBUTTONDOWN, card)
                event(pygame.MOUSEBUTTONUP, invalid)
                assert len(g.plants) == 1 and g.sun == 450 and g.cooldowns['sunflower'] == 0
                assert g.selected is None and g.drag_kind is None
            g.sun = 49
            event(pygame.MOUSEBUTTONDOWN, card)
            assert g.drag_kind is None and '阳光不足' in g.notice
            # The same rules are checked again on drop if resources changed.
            g.sun = 100
            event(pygame.MOUSEBUTTONDOWN, card)
            g.sun = 0
            event(pygame.MOUSEBUTTONUP, (target[0] + 80, target[1]))
            assert len(g.plants) == 1 and g.cooldowns['sunflower'] == 0
            g.sun = 450
            g.plants.append(Peashooter(3, 3))
            neighbor = g.plant_at(3, 3)
            g.suns = [Sun(*target, 25, falls=False)]
            before = (g.sun, dict(g.cooldowns))
            event(pygame.MOUSEBUTTONDOWN, SHOVEL_RECT.center)
            event(pygame.MOUSEMOTION, target)
            g.draw()
            assert g.plant_at(2, 3) is not None
            event(pygame.MOUSEBUTTONUP, target)
            assert g.plant_at(2, 3) is None and g.plants == [neighbor]
            assert before == (g.sun, g.cooldowns) and g.suns[0].alive
            assert g.drag_kind is None
            # A released shovel is not sticky and an empty drop changes nothing.
            event(pygame.MOUSEBUTTONUP, (target[0] + 80, target[1]))
            assert neighbor.alive
            event(pygame.MOUSEBUTTONDOWN, SHOVEL_RECT.center)
            event(pygame.MOUSEBUTTONUP, target)
            assert neighbor.alive and g.drag_kind is None

            for source in (card, SHOVEL_RECT.center):
                for cancel in ('right', 'escape', 'pause', 'guide', 'focus', 'resize'):
                    event(pygame.MOUSEBUTTONDOWN, source)
                    assert g.drag_kind is not None
                    if cancel == 'right':
                        event(pygame.MOUSEBUTTONDOWN, target, button=3)
                    elif cancel == 'escape':
                        key(pygame.K_ESCAPE)
                    elif cancel == 'pause':
                        key(pygame.K_p)
                        key(pygame.K_p)
                    elif cancel == 'guide':
                        key(pygame.K_i)
                        key(pygame.K_i)
                    elif cancel == 'focus':
                        g.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
                    else:
                        g.handle_event(pygame.event.Event(pygame.VIDEORESIZE, w=size[0], h=size[1]))
                    event(pygame.MOUSEBUTTONUP, (target[0] + 80, target[1]))
                    assert g.drag_kind is None and g.selected is None and neighbor.alive
                    assert before == (g.sun, g.cooldowns)
            # Dropping a plant onto a sun plants; sun collection remains a click.
            event(pygame.MOUSEBUTTONDOWN, card)
            event(pygame.MOUSEBUTTONUP, target)
            assert g.plant_at(2, 3) and g.suns[0].alive and g.sun == 400
            event(pygame.MOUSEBUTTONDOWN, target)
            assert not g.suns[0].alive and g.sun == 425
            event(pygame.MOUSEBUTTONDOWN, SHOVEL_RECT.center)
            neighbor.alive = False
            g._reap()
            event(pygame.MOUSEBUTTONUP, (target[0] + 80, target[1]))
            assert g.plant_at(2, 3) and len(g.plants) == 1 and g.sun == 425

        for index in (0, 7):
            for kind, spec in C.PLANTS.items():
                g.start_level(index, 'select')
                g.state = 'playing'
                g.seeds = [kind]
                g.sun = 1000
                event(pygame.MOUSEBUTTONDOWN, g._card_rect(0).center)
                event(pygame.MOUSEMOTION, target)
                event(pygame.MOUSEBUTTONUP, target)
                plant = g.plant_at(2, 3)
                assert plant and plant.kind == kind and g.sun == 1000 - spec['cost']
                assert plant.sleeping == bool(spec.get('mushroom') and index == 0)
                recharge = g.cooldowns[kind]
                event(pygame.MOUSEBUTTONDOWN, SHOVEL_RECT.center)
                event(pygame.MOUSEBUTTONUP, target)
                assert not g.plants and g.cooldowns[kind] == recharge and g.sun == 1000 - spec['cost']
        g.start_level(0, 'select')
        g.state = 'playing'
        g.seeds = ['sunflower']
        g.sun = 50
        key(pygame.K_1)
        event(pygame.MOUSEBUTTONDOWN, target)
        assert g.plant_at(2, 3) and g.sun == 0
        print('PASS: scaled plant/shovel drag, costs, cooldowns, sun overlap, one-shot removal and cancellation')
    finally:
        pygame.quit()


if __name__ == '__main__':
    main()

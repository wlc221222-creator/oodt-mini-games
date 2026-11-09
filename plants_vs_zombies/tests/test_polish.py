"""Input feedback and visual motion must preserve gameplay and alpha."""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pygame
import save
from game import Game
from entities import Sunflower, Sun
from assets import Anim, tween_frame


def main():
    old_save = save.SAVE_PATH
    try:
        with tempfile.TemporaryDirectory() as temp:
            save.SAVE_PATH = str(Path(temp) / 'save.json')
            g = Game()
            def mouse(kind, pos):
                view = g.viewport()
                p = (round(view.x + pos[0] * view.w / 800), round(view.y + pos[1] * view.h / 600))
                g.handle_event(pygame.event.Event(kind, pos=p, button=1))
            def finger(kind, pos, ident=17):
                view = g.viewport()
                w, h = g.screen.get_size()
                x = (view.x + pos[0] * view.w / 800) / w
                y = (view.y + pos[1] * view.h / 600) / h
                g.handle_event(pygame.event.Event(kind, x=x, y=y, finger_id=ident, touch_id=1))

            for size in ((800, 600), (1200, 800), (1001, 777)):
                g.screen = pygame.display.set_mode(size)
                g.state = 'menu'
                center = g._mode_rect(0).center
                mouse(pygame.MOUSEBUTTONDOWN, center)
                assert g.state == 'menu' and g.ui.menu_press == 0
                g.draw()
                mouse(pygame.MOUSEBUTTONUP, (50, 300))
                assert g.state == 'menu' and g.ui.menu_press is None
                mouse(pygame.MOUSEBUTTONDOWN, center)
                mouse(pygame.MOUSEBUTTONUP, center)
                assert g.state == 'choosing'
                g.state = 'menu'
                finger(pygame.FINGERDOWN, center)
                finger(pygame.FINGERDOWN, g._mode_rect(1).center, 18)
                assert g.ui.touch_id == 17 and g.ui.menu_press == 0
                finger(pygame.FINGERUP, center)
                assert g.state == 'choosing' and g.ui.touch_id is None
                g.seeds = ['sunflower', 'peashooter']
                g.state = 'playing'
                g.sun = 500
                finger(pygame.FINGERDOWN, g._card_rect(0).center)
                finger(pygame.FINGERMOTION, (315, 450))
                assert g.drag_kind == 'sunflower'
                finger(pygame.FINGERUP, (315, 450))
                assert g.plant_at(3, 3) and g.sun == 450
                g.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(315, 450), touch=True))
                assert g.sun == 450 and len(g.plants) == 1
                finger(pygame.FINGERDOWN, g._card_rect(1).center)
                g.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
                finger(pygame.FINGERUP, (400, 450))
                assert g.drag_kind is None and len(g.plants) == 1
                g.suns = [Sun(500, 350, 25, falls=False)]
                finger(pygame.FINGERDOWN, (500, 350))
                finger(pygame.FINGERUP, (500, 350))
                assert g.sun == 475 and not g.suns[0].alive
                assert any(e.kind == 'sun' for e in g.ui.feedback)
                age = g.ui.feedback[-1].age
                g.state = 'paused'
                g.update(0.2)
                assert g.ui.feedback[-1].age == age
                g.state = 'playing'
                g.update(1)
                assert not g.ui.feedback
            print('PASS: release-to-activate/cancel, single-finger drag/collect, duplicate-event suppression, focus cancellation, pause in 3 viewports')

            g.state = 'menu'
            rect = g._mode_rect(0)
            g.ui.motion.clear()
            g.ui.button_motion(rect)
            wpos = (round(g.viewport().x + rect.centerx * g.viewport().w / 800),
                    round(g.viewport().y + rect.centery * g.viewport().h / 600))
            with patch('pygame.mouse.get_pos', return_value=wpos):
                g.update(1 / 60)
                value = g.ui.motion[tuple(rect)]
                assert 0 < value < 1
                g.update(0.2)
                assert g.ui.motion[tuple(rect)] > value
            first, second = [pygame.Surface((30, 40), pygame.SRCALPHA) for _ in range(2)]
            first.fill((255, 100, 100, 0))
            second.fill((0, 0, 255, 0))
            first.set_at((10, 10), (200, 50, 20, 255))
            second.set_at((10, 10), (20, 50, 200, 255))
            data = [pygame.image.tobytes(s, 'RGBA') for s in (first, second)]
            mid = tween_frame(first, second, 2)
            assert mid.get_at((0, 0)).a == 0
            assert mid.get_at((10, 10)) == (110, 50, 110, 255)
            assert data == [pygame.image.tobytes(s, 'RGBA') for s in (first, second)]
            a, b = Sunflower(0, 0), Sunflower(1, 0)
            a.anim = Anim([first, second])
            a.anim.t = 0.06
            assert a.anim.smooth_image().get_at((10, 10)) == mid.get_at((10, 10))
            assert a.visual_phase != b.visual_phase
            original = (a.x, a.baseline, a.hp, a.timer)
            a.draw(g.canvas)
            a.draw(g.canvas)
            assert original == (a.x, a.baseline, a.hp, a.timer)
            assert tween_frame.cache_info().currsize <= 384
            print('PASS: time-based hover easing, alpha-correct cached frame blending and render-only flower motion')
    finally:
        save.SAVE_PATH = old_save
        pygame.quit()


if __name__ == '__main__':
    main()

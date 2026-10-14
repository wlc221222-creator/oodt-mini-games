"""Exercise the real UI event path: new save, locks, navigation and resizing."""
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame
import config as C
from game import Game
from garden_ui import CHOOSER_BACK_RECT, BACK_RECT


def main():
    g = Game()
    g.unlocked = 0
    g.owned_plants = list(C.START_PLANTS)

    def click(rect):
        w, h = g.screen.get_size()
        scale = min(w / 800, h / 600)
        x = (w - 800 * scale) / 2 + rect.centerx * scale
        y = (h - 600 * scale) / 2 + rect.centery * scale
        g.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(round(x), round(y))))

    click(g._mode_rect(1))
    assert g.state == "levelselect"
    click(g._level_rect(6))
    assert g.state == "levelselect", "locked level should not start"
    click(g._level_rect(0))
    assert g.state == "choosing"
    click(g._chooser_rect(0))
    click(g._start_button_rect())
    assert g.state == "choosing", "incomplete selection should not start"
    click(g._chooser_rect(1))
    click(g._seed_slot_rect(0))
    assert g.seeds == ["peashooter"], "preview click should remove its card"
    click(g._chooser_rect(0))
    g.draw()
    click(g._start_button_rect())
    assert g.state == "playing", "first level must start with both owned plants"
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert g.state == "menu"
    g.handle_event(pygame.event.Event(pygame.VIDEORESIZE, w=1200, h=800))
    click(g._mode_rect(1))
    click(g._level_rect(0))
    click(CHOOSER_BACK_RECT)
    assert g.state == "levelselect"
    click(BACK_RECT)
    assert g.state == "menu", "scaled hit rectangles should match displayed controls"
    g.owned_plants = list(C.SHOP_ORDER)
    g.start_level(6, "select")
    g.seeds = []
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a))
    assert len(g.seeds) == 8
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    assert g.state == "playing"
    assert g.assets.background(0) is not g.assets.background(1)
    g.owned_plants.remove(C.LEVEL_REWARDS[6])
    assert not g.ui.completed(6)
    g.owned_plants.append(C.LEVEL_REWARDS[6])
    assert g.ui.completed(6)
    g.draw()
    pygame.quit()
    print("PASS: UI start gate, locked levels, seed removal, returns and scaled clicks")


if __name__ == "__main__":
    main()

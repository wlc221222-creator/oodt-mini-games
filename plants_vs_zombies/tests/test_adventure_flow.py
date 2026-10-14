"""Cover adventure navigation, saved unlocks, retries and the final level."""
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame
import config as C
import save
from game import Game
from garden_ui import RESULT_PRIMARY_RECT


def key(g, code):
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=code))


def main():
    original_path = save.SAVE_PATH
    try:
        with tempfile.TemporaryDirectory(prefix="pvz_adventure_flow_") as temp:
            save.SAVE_PATH = str(Path(temp) / "save.json")
            g = Game()
            assert g.unlocked == 0 and g.owned_plants == C.START_PLANTS
            g._on_mode_click(g._mode_rect(0).center)
            assert g.state == "choosing" and g.level_index == 0
            # A failed attempt cannot grant progress or plants.
            g.state = "lost"
            key(g, pygame.K_RETURN)
            assert g.state == "choosing" and g.level_index == 0
            assert g.unlocked == 0 and g.owned_plants == C.START_PLANTS
            for index in range(len(C.LEVELS)):
                assert g.level_index == index and g.state == "choosing"
                key(g, pygame.K_a)
                key(g, pygame.K_RETURN)
                assert g.state == "playing"
                g.wave_index = len(g.waves)
                g.zombies = []
                g._check_victory()
                assert g.state == "won"
                assert g.unlocked == min(index + 1, len(C.LEVELS) - 1)
                assert g.owned_plants == C.START_PLANTS + C.LEVEL_REWARDS[:index + 1]
                saved = save.load()
                assert saved["unlocked"] == g.unlocked and saved["plants"] == g.owned_plants
                g.draw()  # All result labels must render, including final win.
                if index == 1:
                    # R explicitly retries; the primary action still advances.
                    key(g, pygame.K_r)
                    assert g.level_index == index and g.state == "choosing"
                    g.state = "won"
                if index % 2 == 0:
                    g.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                   button=1, pos=RESULT_PRIMARY_RECT.center))
                else:
                    key(g, pygame.K_RETURN)
            assert g.state == "levelselect" and g.adventure_completed()
            g.state = "menu"
            key(g, pygame.K_RETURN)
            assert g.state == "levelselect", "completed adventure should show the map"
            # A selected-level victory must not grant adventure rewards.
            g.unlocked = 0
            g.owned_plants = list(C.START_PLANTS)
            g.start_level(0, "select")
            g.state = "playing"
            g.wave_index = len(g.waves)
            g._check_victory()
            assert g.unlocked == 0 and g.owned_plants == C.START_PLANTS
            # A reloaded save resumes the latest unlocked adventure level.
            save.save({"unlocked": 2, "plants": C.START_PLANTS + C.LEVEL_REWARDS[:2]})
            resumed = Game()
            key(resumed, pygame.K_RETURN)
            assert resumed.state == "choosing" and resumed.level_index == 2
            resumed.seeds = resumed.available_plants()[:C.MAX_SEEDS]
            key(resumed, pygame.K_ESCAPE)
            key(resumed, pygame.K_RETURN)
            assert resumed.state == "choosing", "menu Enter must not skip seed selection"
            print("PASS: 1-1 to 2-2 progression, next-level click/Enter, rewards, retries and save resume")
    finally:
        save.SAVE_PATH = original_path
        pygame.quit()


if __name__ == "__main__":
    main()

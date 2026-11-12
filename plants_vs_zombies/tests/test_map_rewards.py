"""Cover first-clear rewards, introductory plants and unrestricted replays."""
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
from garden_ui import RESULT_PRIMARY_RECT, RESULT_MAP_RECT


def click(g, rect):
    viewport = g.viewport()
    pos = (round(viewport.x + rect.centerx * viewport.w / 800),
           round(viewport.y + rect.centery * viewport.h / 600))
    for event in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
        g.handle_event(pygame.event.Event(event, button=1, pos=pos))


def win(g):
    # Exercise the actual end-of-wave controller, not a hand-set won state.
    g.wave_index = len(g.waves) - 1
    g.spawn_queue = []
    g.zombies = []
    g.state = 'playing'
    g.update(1 / 60)
    assert g.state == 'won'
    g.draw()


def main():
    original = save.SAVE_PATH
    try:
        with tempfile.TemporaryDirectory(prefix='pvz_map_rewards_') as temp:
            for size in ((800, 600), (1200, 800), (1001, 777)):
                for route in ('adventure', 'select'):
                    save.SAVE_PATH = str(Path(temp) / f'{size[0]}_{route}.json')
                    g = Game()
                    g.screen = pygame.display.set_mode(size)
                    if route == 'select':
                        click(g, g._mode_rect(1))
                        click(g, g._level_rect(0))
                    else:
                        click(g, g._mode_rect(0))
                    assert g.available_plants() == C.START_PLANTS
                    win(g)
                    assert g.unlocked == 1 and g.reward_earned == 'wallnut'
                    assert g.next_level_unlocked
                    assert save.load()['plants'] == C.START_PLANTS + ['wallnut']
                    click(g, RESULT_PRIMARY_RECT)
                    assert g.level_index == 1 and g.state == 'choosing'
                    assert g.mode == route
                    assert g.available_plants() == C.START_PLANTS + ['wallnut']
                    assert g.reward_earned is None
                    win(g)
                    assert g.unlocked == 2 and g.reward_earned == 'snowpea'
                    assert g.next_level_unlocked
                    assert save.load()['unlocked'] == 2
                    click(g, RESULT_MAP_RECT)
                    click(g, g._level_rect(2))
                    assert g.state == 'choosing' and g.level_index == 2
                    assert g.available_plants() == C.START_PLANTS + ['wallnut', 'snowpea']
                    resumed = Game()
                    assert resumed.unlocked == 2 and 'snowpea' in resumed.owned_plants
                    # Replaying cleared levels allows all later-earned plants.
                    resumed.seeds = ['wallnut', 'snowpea', 'sunflower']
                    resumed.start_level(0, 'select')
                    assert resumed.available_plants() == C.START_PLANTS + ['wallnut', 'snowpea']
                    assert resumed.seeds == ['wallnut', 'snowpea', 'sunflower']
                    resumed.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a))
                    assert resumed.seeds == resumed.available_plants()
                    resumed.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
                    assert resumed.state == 'playing'
                    resumed.sun = 500
                    resumed.selected = 'snowpea'
                    resumed._on_click((C.LAWN_X + C.CELL_W // 2, C.LAWN_Y + C.CELL_H // 2))
                    assert resumed.plant_at(0, 0).kind == 'snowpea'
                    before = save.load()
                    win(resumed)
                    assert resumed.reward_earned is None and not resumed.next_level_unlocked
                    assert save.load() == before
                    resumed.start_level(1, 'select')
                    assert 'snowpea' in resumed.available_plants()
            print('PASS: both menu routes, first-clear plant pools, reward screens, third-level unlock, saved progress and later plants usable in replays in 3 viewports')

            save.SAVE_PATH = str(Path(temp) / 'map_campaign.json')
            g = Game()
            for index in range(len(C.LEVELS)):
                g.state = 'levelselect'
                g.level_page = index // 7
                click(g, g._level_rect(index))
                assert g.level_index == index and g.state == 'choosing'
                win(g)
                assert g.reward_earned == C.LEVEL_REWARDS[index]
                assert g.unlocked == min(index + 1, len(C.LEVELS) - 1)
                assert g.owned_plants == C.START_PLANTS + C.LEVEL_REWARDS[:index + 1]
                saved = save.load()
                g._check_victory()
                assert save.load() == saved
            assert g.adventure_completed()
            g._continue_result()
            assert g.state == 'levelselect'
            g.start_level(len(C.LEVELS) - 1, 'select')
            assert 'iceshroom' in g.available_plants()
            g.start_level(0, 'select')
            assert g.available_plants() == C.SHOP_ORDER
            g.start_level(1, 'select')
            assert g.available_plants() == C.SHOP_ORDER
            before = save.load()
            g.start_level(0, 'select')
            g.state = 'lost'
            g._check_victory()
            assert save.load() == before and g.reward_earned is None
            print('PASS: all 14 map clears grant first-clear rewards once; final reward remains playable; losing changes no progress')
    finally:
        save.SAVE_PATH = original
        pygame.quit()


if __name__ == '__main__':
    main()

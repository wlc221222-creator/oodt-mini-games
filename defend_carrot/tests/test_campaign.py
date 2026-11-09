"""Content progression, tower restrictions, overlapping waves and durable unlocks."""
import json
import os
from pathlib import Path
import sys
import tempfile
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pygame
import config as C
import progress
from game import Game, MONSTER_CLASSES
from entities import tile_center
from art import ATTACK_FRAMES, character_image


def main():
    assert len(C.LEVELS) == len(C.FRUITS) == len(C.MONSTERS) == 8
    assert len({tuple(level['path']) for level in C.LEVELS}) == 8
    assert {level['theme'] for level in C.LEVELS} == {1, 2, 3}
    for before, after in zip(C.LEVELS, C.LEVELS[1:]):
        assert len(before['waves']) < len(after['waves'])
        assert sum(map(len, before['waves'])) < sum(map(len, after['waves']))
        assert set(before['towers']) <= set(after['towers'])
        assert before['start_coins'] < after['start_coins'] and before['hp_scale'] < after['hp_scale']
    for level in C.LEVELS:
        assert 15 <= len(level['waves']) <= 25
        used = {kind for wave in level['waves'] for kind, _ in wave}
        assert used == set(level['monsters'])
        for wave in level['waves']:
            assert wave[0][1] == 0 and all(a[1] < b[1] for a, b in zip(wave, wave[1:]))
    for kind, frames in ATTACK_FRAMES.items():
        for tier in (1, 2, 3):
            assert all(character_image(kind, frame=frame, level=tier) is not None for frame in frames)
    old = os.environ.get('OODT_CARROT_SAVE_PATH')
    with tempfile.TemporaryDirectory(prefix='carrot_progress_') as folder:
        path = Path(folder) / 'progress.json'
        os.environ['OODT_CARROT_SAVE_PATH'] = str(path)
        try:
            assert progress.load() == {'unlocked': 1, 'best': {}}
            path.write_text('{bad json', encoding='utf-8')
            assert progress.load()['unlocked'] == 1
            for data in ([], {'unlocked': True}, {'unlocked': '8'}):
                path.write_text(json.dumps(data), encoding='utf-8')
                assert progress.load()['unlocked'] == 1
            g = Game()
            g.reset()
            cell = next((c, r) for r in range(C.GRID_ROWS) for c in range(C.GRID_COLS) if g.can_build(c, r))
            g.selected = 'snow'
            coins = g.coins
            g._on_click(tile_center(*cell))
            assert not g.fruits and g.coins == coins and '尚未开放' in g.notice
            g._load_wave(0)
            g._update_waves(0)
            assert g.monsters
            g._update_waves(C.LEVELS[0]['waves'][0][-1][1] + C.WAVE_BREAK + .01)
            assert g.wave_index == 1 and g.monsters  # Next wave does not wait for every previous monster.
            g._load_level(0)
            g.carrot.hp = 2
            g._save_completion()
            restored = Game()
            assert restored.progress == {'unlocked': 2, 'best': {'0': 2}}
            g.level_saved = False
            g.carrot.hp = 1
            g._save_completion()
            assert progress.load()['best']['0'] == 2
            restored.reset(7)
            restored.carrot.hp = 3
            restored._save_completion()
            assert progress.load()['unlocked'] == 8
            assert progress.load()['best']['7'] == 3
            blocker = Path(folder) / 'file'
            blocker.write_text('x')
            os.environ['OODT_CARROT_SAVE_PATH'] = str(blocker / 'progress.json')
            assert not progress.save({'unlocked': 1, 'best': {}})
            print('PASS: eight-stage progression, locked tower rejection, wave overlap, all tower animation tiers and resilient independent save')
        finally:
            if old is None:
                os.environ.pop('OODT_CARROT_SAVE_PATH', None)
            else:
                os.environ['OODT_CARROT_SAVE_PATH'] = old
            pygame.quit()


if __name__ == '__main__':
    main()

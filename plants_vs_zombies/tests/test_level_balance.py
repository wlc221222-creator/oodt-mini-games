import os
import sys
import random
import tempfile
from pathlib import Path

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
import pygame
import config as C
import save
from game import Game

temporary_save = tempfile.TemporaryDirectory(prefix='pvz_balance_')
original_save = save.SAVE_PATH
save.SAVE_PATH = str(Path(temporary_save.name) / 'save.json')
g = Game()
results = []


def place(kind, col, row):
    if kind not in g.seeds or g.plant_at(col, row):
        return False
    if g.sun < C.PLANTS[kind]['cost'] or g.cooldowns[kind] > 0:
        return False
    g.selected = kind
    n = len(g.plants)
    g._on_click((C.LAWN_X + col * C.CELL_W + 40, C.LAWN_Y + row * C.CELL_H + 50))
    return len(g.plants) > n


def build():
    alive = [z for z in g.zombies if z.alive and not z.dying]
    threats = sorted(range(5), key=lambda row: min([z.x for z in alive if z.row == row] or [9999]))
    flowers = [p for p in g.plants if p.kind == 'sunflower' and p.alive]
    if not flowers:
        if place('sunflower', 0, 0): return
    for row in threats:
        enemies = [z for z in alive if z.row == row]
        if not enemies: continue
        near = min(z.x for z in enemies)
        shooters = [p for p in g.plants if p.row == row and p.alive and p.kind in ('peashooter', 'repeater', 'snowpea')]
        if near < 440:
            for col in (3, 2, 4):
                if C.LAWN_X + col * C.CELL_W + 40 < near - 30:
                    if place('wallnut', col, row): return
        if not shooters:
            if place('peashooter', 1, row): return
    if len(flowers) < 4:
        for row in (0, 4, 2, 1):
            if place('sunflower', 0, row): return
    for row in threats:
        enemies = [z for z in alive if z.row == row]
        count = sum(p.alive and p.row == row and p.kind in ('peashooter', 'repeater', 'snowpea') for p in g.plants)
        if not enemies: continue
        if count < 3:
            for col in (1, 2, 3):
                if place('peashooter', col, row): return
    # Build coverage before the next assault; save scarce night sun for shooters.
    for row in threats:
        if place('peashooter', 1, row): return
    for row in threats:
        if place('snowpea', 4, row): return
    for row in threats:
        if place('wallnut', 5, row): return


for index, level in enumerate(C.LEVELS):
    random.seed(100 + index)
    g.owned_plants = C.START_PLANTS + C.LEVEL_REWARDS[:index]
    g.start_level(index, 'select')
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a))
    g.draw()
    g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    for tick in range(60 * 600):
        for sun in list(g.suns):
            if sun.alive and sun.y >= 115:
                g._on_click((sun.x, sun.y))
        if tick % 12 == 0:
            build()
        g.update(1 / 60)
        if tick % 600 == 0:
            g.draw()
        if g.state != 'playing': break
    result = dict(level=level['id'], state=g.state, seconds=round(g.elapsed, 1),
                  sun=g.sun, plants=len(g.plants), wave=g.wave_index + 1)
    print(result, flush=True)
    results.append(result)
pygame.quit()
save.SAVE_PATH = original_save
temporary_save.cleanup()
assert all(r['state'] == 'won' for r in results), results
print(f'PASS: all {len(C.LEVELS)} levels won with earned plants, normal costs and cooldowns')

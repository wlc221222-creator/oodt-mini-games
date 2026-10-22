"""Win every complete stage with normal coins; unbuilt/sparse defenses lose later."""
import os
from pathlib import Path
import sys
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pygame
import config as C
from game import Game
from campaign_builder import Builder


def run(stage, active=True, cap=None):
    game = Game()
    game.reset(stage)
    builder = Builder(game)
    for tick in range(24000):
        if active and tick % 12 == 0 and (cap is None or len(game.fruits) < cap):
            builder.tick()
        game.update(1 / 30)
        if tick % 600 == 0:
            game.draw()
        if game.state in ('won', 'lost', 'levelclear'):
            break
    return game


def main():
    results = []
    for stage in range(len(C.LEVELS)):
        game = run(stage)
        result = dict(stage=stage + 1, state=game.state, seconds=round(game.elapsed, 1),
                      hp=game.carrot.hp, kills=game.kills, waves=game.wave_index + 1,
                      towers=len(game.fruits), invested=sum(t.invested for t in game.fruits), coins=game.coins)
        results.append(result)
        print(result, flush=True)
        assert game.state == ('won' if stage == len(C.LEVELS) - 1 else 'levelclear'), result
    idle = run(0, active=False)
    assert idle.state == 'lost' and idle.carrot.hp == 0
    sparse = run(len(C.LEVELS) - 1, cap=3)
    assert sparse.state == 'lost', 'three unupgraded towers must not clear the final stage'
    assert results[-1]['invested'] > results[0]['invested']
    print('PASS: all eight full stages won on earned coins, idle first stage and sparse final stage lose')
    pygame.quit()


if __name__ == '__main__':
    main()

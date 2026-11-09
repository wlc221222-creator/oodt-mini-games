"""Three leaks end a match, damaged art persists and an idle player loses."""
import os
from pathlib import Path
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame
import config as C
from art import character_image, CARROT_HEALTH_FRAMES
from game import Game, MONSTER_CLASSES


def main():
    game = Game()
    try:
        assert C.CARROT_HP == 3
        assert C.CARROT_ESCAPE_DAMAGE == 1
        for level in range(len(C.LEVELS)):
            for kind in MONSTER_CLASSES:
                game.reset()
                game._load_level(level)
                game.spawn_queue = [('slime', 999)]
                coins = game.coins
                for expected in (2, 1, 0):
                    monster = MONSTER_CLASSES[kind](game)
                    monster.seg = len(game.path) - 1
                    monster.x, monster.y = game.path[-1]
                    game.monsters = [monster]
                    game.update(1 / 60)
                    assert game.carrot.hp == expected, (kind, expected)
                    assert game.carrot.sprite_frame == CARROT_HEALTH_FRAMES[expected]
                    assert game.state == ('playing' if expected else 'lost')
                    assert (game.coins, game.score, game.kills) == (coins, 0, 0)
                    # Each escaped monster can damage the objective only once.
                    monster.advance(1, game)
                    assert game.carrot.hp == expected
                    game.carrot.update(5, game)
                    game.draw()
                    assert game.carrot.sprite_frame == CARROT_HEALTH_FRAMES[expected]
                game.update(100)
                assert game.state == 'lost' and game.carrot.hp == 0
                game.reset()
                assert game.carrot.hp == 3 and game.carrot.sprite_frame == 'hlb10.png'

        images = [character_image('carrot', C.CARROT_SPRITE_SIZE,
                                  frame=CARROT_HEALTH_FRAMES[hp]) for hp in (3, 2, 1)]
        assert len({pygame.image.tobytes(image, 'RGBA') for image in images}) == 3
        # Preserve the original common canvas; severe damage makes the body
        # shorter instead of enlarging the remaining leaf to the healthy size.
        assert len({image.get_bounding_rect().bottom for image in images}) == 1
        areas = [pygame.mask.from_surface(image).count() for image in images]
        assert areas[0] > areas[1] > areas[2]

        for level in range(len(C.LEVELS)):
            game.reset()
            game._load_level(level)
            for _ in range(6000):
                game.update(.05)
                if game.state != 'playing':
                    break
            assert game.state == 'lost', (level, game.state)
            assert game.carrot.hp == 0 and game.kills == game.score == 0
            assert game.level_index == level
        print('PASS: all monster types consume one life, third leak loses, damage sprites persist, idle play loses all eight maps')
    finally:
        pygame.quit()


if __name__ == '__main__':
    main()

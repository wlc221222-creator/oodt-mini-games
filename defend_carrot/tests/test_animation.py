"""Original atlas decoding, real poses and simulation/pause timing."""
import hashlib
import json
import os
from pathlib import Path
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame
from animation import Animation
from art import (ASSET_DIR, WALK_FRAMES, ATTACK_FRAMES, MONSTER_ATLAS,
                 atlas_data, atlas_frame, character_image)
from entities import Apple, Orange, Melon, Slime, tile_center
from game import Game, MONSTER_CLASSES


def pixels(image):
    return pygame.image.tobytes(image, 'RGBA')


def main():
    game = Game()
    try:
        root = ASSET_DIR / 'original'
        entries = [entry for name in ('source-manifest.json', 'expansion-manifest.json')
                   for entry in json.loads((root / name).read_text())['files']]
        for entry in entries:
            data = (root / entry['local']).read_bytes()
            digest = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
            assert digest == entry['sha'], entry['local']

        for kind, frames in {**WALK_FRAMES, **ATTACK_FRAMES}.items():
            images = [character_image(kind, 64, frame=frame) for frame in frames]
            assert all(image is not None and image.get_bounding_rect().w for image in images)
            assert len({pixels(image) for image in images}) >= 2, kind
        # This frame is rotated in the packed sheet. Its canvas and trim origin
        # must be restored instead of cropping its unrotated rectangle.
        name = 'fat_boss_green02.png'
        spec = atlas_data(MONSTER_ATLAS)[name]
        assert spec['rotated']
        frame = atlas_frame(MONSTER_ATLAS, name)
        assert frame.get_size() == (150, 150)
        assert frame.get_bounding_rect() == pygame.Rect(23, 15, 102, 120)
        normal = character_image('bat', 64)
        flash = character_image('bat', 64, flash=True)
        assert pygame.image.tobytes(normal, 'RGBA')[3::4] == pygame.image.tobytes(flash, 'RGBA')[3::4]
        assert pixels(normal) != pixels(flash)

        animation = Animation(('a', 'b'))
        animation.update(.15)
        assert animation.frame == 'b'
        animation.update(.15)
        assert animation.frame == 'a'
        one_shot = Animation(('a', 'b'), .1, loop=False)
        one_shot.update(10)
        assert one_shot.finished and one_shot.frame == 'b'

        game.reset()
        game.spawn_queue = [('slime', 999)]
        game.monsters = [cls(game) for cls in MONSTER_CLASSES.values()]
        before = [m.walk_animation.frame for m in game.monsters]
        game.update(.16)
        assert all(m.walk_animation.frame != old for m, old in zip(game.monsters, before))
        for kind, cls in (('apple', Apple), ('orange', Orange), ('melon', Melon)):
            tower = cls(5, 1)
            target = Slime(game)
            target.x, target.y = tile_center(5, 2)
            game.monsters = [target]
            tower.timer = 0
            game.bullets = []
            tower.update(.01, game)
            count = 0 if kind == 'melon' else 1
            assert len(game.bullets) == count and tower._attacking
            if kind == 'melon':
                assert target.hp == target.max_hp - tower.damage
            start = tower.attack_animation.frame
            tower.update(.09, game)
            assert tower.attack_animation.frame != start
            assert len(game.bullets) == count  # animation must not generate extra damage
            tower.update(.4, game)
            assert not tower._attacking
            game.fruits = [tower]

        def snapshot():
            return (game.fruits[0].attack_animation.elapsed,
                    game.monsters[0].walk_animation.elapsed,
                    game.carrot.expression.elapsed, game.carrot.expression_timer,
                    game.monsters[0].x, game.monsters[0].y, game.coins)

        game.carrot.expression.restart()
        game.carrot.expressing = True
        for state, guide in (('paused', False), ('playing', True), ('menu', False)):
            game.state, game.guide_open = state, guide
            before = snapshot()
            game.update(20)
            game.draw()
            game.draw()
            assert snapshot() == before
        game.state, game.guide_open = 'playing', False
        game.update(.13)
        assert game.carrot.expression.elapsed > 0
        game.draw()
        print('PASS: original asset hashes, rotated/trimmed frames, real animation poses, attack and pause timing')
    finally:
        pygame.quit()


if __name__ == '__main__':
    main()

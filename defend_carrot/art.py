"""Original-game TexturePacker atlases, shared by entities and interface icons."""
from functools import lru_cache
from pathlib import Path
import plistlib
import re

import pygame

import config as C

ASSET_DIR = Path(__file__).resolve().parent / 'assets'
TOWER_ATLASES = {
    'apple': 'Themes/Towers/TBottle-hd',
    'orange': 'Themes/Towers/TFan-hd',
    'melon': 'Themes/Towers/TSun-hd',
    'star': 'Themes/Towers/TStar-hd', 'ice': 'Themes/Towers/TBlueStar-hd',
    'poison': 'Themes/Towers/TPin-hd', 'rocket': 'Themes/Towers/TRocket-hd',
    'snow': 'Themes/Towers/TSnow-hd',
}
MONSTER_ATLAS = 'Themes/Theme1/Items/Monsters01-hd'
CARROT_ATLAS = 'Themes/Items/Items01-hd'
WALK_FRAMES = {
    'slime': ('land_pink01.png', 'land_pink02.png'),
    'bat': ('fly_blue01.png', 'fly_blue02.png'),
    'golem': ('fat_green01.png', 'fat_green02.png'),
    'thrower': ('land_nima01.png', 'land_nima02.png'),
    'yellow': ('fly_yellow01.png', 'fly_yellow02.png'),
    'starling': ('land_star01.png', 'land_star02.png'),
    'elite': ('fat_boss_green01.png', 'fat_boss_green02.png'),
    'boss': ('boss_big01.png', 'boss_big02.png'),
}
ATTACK_FRAMES = {
    'apple': ('Bottle11.png', 'Bottle12.png', 'Bottle13.png', 'Bottle11.png'),
    'orange': ('Fan11.png', 'Fan12.png', 'Fan13.png', 'Fan11.png'),
    # Sun uses a separate expanding attack layer over its static centre.
    'melon': tuple(f'PSun1{i}.png' for i in range(1, 6)),
}
for kind, prefix in (('star', 'Star'), ('ice', 'BStar'), ('poison', 'Pin'),
                     ('rocket', 'Rocket'), ('snow', 'Snow')):
    ATTACK_FRAMES[kind] = tuple(f'{prefix}1{i}.png' for i in (1, 2, 3, 1))
IDLE_FRAMES = {'apple': 'Bottle11.png', 'orange': 'Fan11.png', 'melon': 'Sun11.png'}
IDLE_FRAMES.update({kind: ATTACK_FRAMES[kind][0] for kind in ('star', 'ice', 'poison', 'rocket', 'snow')})
CARROT_FRAMES = ('hlb10.png', 'hlb21.png', 'hlb22.png', 'hlb10.png')
CARROT_HEALTH_FRAMES = {3: 'hlb10.png', 2: 'hlb6.png', 1: 'hlb2.png', 0: 'hlb1.png'}
CHARACTERS = (*TOWER_ATLASES, *WALK_FRAMES, 'carrot')


@lru_cache(maxsize=20)
def load_image(name):
    path = ASSET_DIR / name
    if not path.is_file():
        return None
    return pygame.image.load(str(path))


def _numbers(value):
    return tuple(map(int, re.findall(r'-?\d+', value)))


@lru_cache(maxsize=20)
def atlas_data(base):
    path = ASSET_DIR / 'original' / (base + '.plist')
    if not path.is_file():
        return None
    with path.open('rb') as stream:
        return plistlib.load(stream)['frames']


@lru_cache(maxsize=256)
def atlas_frame(base, name):
    """Undo packed rotation and restore the source canvas and trim offset.

    Frames retain their common source canvas, so feet and leaves stay aligned
    across poses. In format 2, the stored width/height are unrotated dimensions.
    """
    data = atlas_data(base)
    atlas = load_image('original/' + base + '.png')
    if data is None or atlas is None or name not in data:
        return None
    spec = data[name]
    x, y, w, h = _numbers(spec['frame'])
    packed = (h, w) if spec['rotated'] else (w, h)
    sprite = atlas.subsurface((x, y, *packed))
    if spec['rotated']:
        sprite = pygame.transform.rotate(sprite, 90)
    image = pygame.Surface(_numbers(spec['sourceSize']), pygame.SRCALPHA)
    left, top, _, _ = _numbers(spec['sourceColorRect'])
    image.blit(sprite, (left, top))
    return image


@lru_cache(maxsize=512)
def sprite_image(base, name, size=40, flash=False, flip=False):
    frame = atlas_frame(base, name)
    if frame is None:
        return None
    scale = size / max(frame.get_size())
    dimensions = tuple(max(1, round(value * scale)) for value in frame.get_size())
    image = pygame.Surface((size, size), pygame.SRCALPHA)
    sprite = pygame.transform.smoothscale(frame, dimensions)
    if flip:
        sprite = pygame.transform.flip(sprite, True, False)
    if flash:
        sprite.fill((80, 80, 80), special_flags=pygame.BLEND_RGB_ADD)
    image.blit(sprite, sprite.get_rect(center=(size // 2, size // 2)))
    return image


def character_image(kind, size=40, flash=False, frame=None, flip=False, level=1):
    if kind in TOWER_ATLASES:
        base, default = TOWER_ATLASES[kind], IDLE_FRAMES[kind]
    elif kind in WALK_FRAMES:
        base, default = MONSTER_ATLAS, WALK_FRAMES[kind][0]
    else:
        base, default = CARROT_ATLAS, CARROT_FRAMES[0]
    name = frame or default
    if kind in TOWER_ATLASES and level > 1:
        name = re.sub(r'1(\d)\.png$', lambda m: f'{level}{m[1]}.png', name)
    return sprite_image(base, name, size, flash, flip)


def fruit_image(kind, size=40, flash=False):
    image = character_image(kind, size, flash)
    return image if image is not None else _fallback_fruit_image(kind, size, flash)


@lru_cache(maxsize=24)
def _fallback_fruit_image(kind, size=40, flash=False):
    image = pygame.Surface((48, 48), pygame.SRCALPHA)
    pygame.draw.ellipse(image, (20, 40, 24, 70), (6, 36, 36, 9))
    color = (255, 247, 222) if flash else C.FRUITS[kind]['color']
    edge = (44, 78, 37)
    if kind == 'apple':
        pygame.draw.ellipse(image, edge, (6, 12, 36, 30))
        pygame.draw.ellipse(image, color, (8, 13, 32, 26))
        pygame.draw.line(image, (91, 62, 33), (24, 15), (26, 6), 3)
        pygame.draw.ellipse(image, (116, 181, 70), (26, 5, 12, 7))
    elif kind == 'orange':
        pygame.draw.circle(image, edge, (24, 25), 18)
        pygame.draw.circle(image, color, (24, 25), 16)
        pygame.draw.ellipse(image, (86, 154, 59), (23, 5, 13, 8))
        for pos in ((13, 29), (34, 21), (31, 35)):
            pygame.draw.circle(image, (212, 116, 28), pos, 1)
    else:
        pygame.draw.ellipse(image, edge, (4, 10, 40, 32))
        pygame.draw.ellipse(image, color, (6, 12, 36, 28))
        for x in (14, 23, 32):
            pygame.draw.arc(image, (42, 117, 63), (x - 6, 12, 13, 28), -1.1, 1.1, 3)
    pygame.draw.ellipse(image, (255, 255, 225, 130), (11, 16, 9, 5))
    for x in (18, 29):
        pygame.draw.circle(image, (255, 253, 220), (x, 26), 4)
        pygame.draw.circle(image, (32, 45, 32), (x + 1, 26), 2)
    pygame.draw.arc(image, edge, (20, 29, 10, 7), 3.3, 6.0, 2)
    return pygame.transform.smoothscale(image, (size, size))

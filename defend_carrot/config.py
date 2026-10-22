"""Shared constants for the Defend the Carrot adventure.

The two games in this experiment share one object model: an abstract
``Entity`` base class, concrete ``Tower``/``Monster`` subclasses, and a
``Game`` coordinator. This file holds only data (the "content"), so the
classes stay generic and adding a new fruit or monster is a data change.
"""

# ---------------------------------------------------------------- window
TILE = 40
GRID_COLS = 20
GRID_ROWS = 13
HUD_H = 56
SHOP_H = 172

SCREEN_W = GRID_COLS * TILE            # 800
FIELD_W = SCREEN_W
FIELD_H = GRID_ROWS * TILE             # 520
SCREEN_H = HUD_H + FIELD_H + SHOP_H    # 692
FPS = 60
TITLE = "保卫萝卜 · 经典防线"

# ---------------------------------------------------------------- colors
COL_GRASS = (126, 176, 96)
COL_GRASS_B = (112, 162, 84)
COL_PATH = (206, 178, 128)
COL_PATH_EDGE = (170, 142, 96)
COL_TEXT = (28, 28, 28)
COL_HUD_BG = (46, 60, 40)
COL_SHOP_BG = (232, 226, 208)
COL_CARD = (240, 234, 214)
COL_CARD_SEL = (255, 250, 205)
COL_CARD_OFF = (150, 145, 130)
COL_HP_BG = (60, 60, 60)
COL_HP_FG = (220, 70, 70)

# ---------------------------------------------------------------- economy
START_COINS = 300         # Legacy default; campaign.py defines each stage budget.
PASSIVE_INCOME = 25        # coins granted at the start of every wave

# --------------------------------------------------------- fruit registry
# Legacy fruit IDs remain stable for the course's object model and saved tools.
# The displayed towers use original-game art; combat values stay unchanged.
# Each carries its own hit points so a
# ranged monster can knock it down; the intro table in the report reads
# straight off these values.
FRUITS = {
    'apple': dict(cost=100, hp=120, damage=20, interval=.55, rng=2.6, color=(110,210,60),
                  label='瓶子炮', upgrades=(180,260), role='单体速射', unlock=1),
    'orange': dict(cost=160, hp=90, damage=15, interval=1.8, rng=3.0, color=(60,210,130),
                   label='风扇', upgrades=(220,260), role='直线穿透', unlock=1),
    'melon': dict(cost=180, hp=170, damage=35, interval=2.0, rng=2.8, color=(250,170,30),
                  label='太阳', upgrades=(260,320), role='周身群攻', unlock=1),
    'star': dict(cost=160, hp=120, damage=26, interval=1.25, rng=3.0, color=(255,200,70),
                 label='星星', upgrades=(220,260), role='爆炸溅射', unlock=2),
    'ice': dict(cost=180, hp=100, damage=10, interval=1.5, rng=3.0, color=(120,215,255),
                label='冰冻星星', upgrades=(260,320), role='群体减速', unlock=3),
    'poison': dict(cost=160, hp=100, damage=10, interval=1.25, rng=2.8, color=(180,100,220),
                   label='毒针', upgrades=(260,320), role='持续中毒', unlock=4),
    'rocket': dict(cost=220, hp=150, damage=45, interval=2.0, rng=3.8, color=(240,100,60),
                   label='火箭', upgrades=(260,380), role='穿透爆炸', unlock=5),
    'snow': dict(cost=160, hp=110, damage=6, interval=4.0, rng=2.65, color=(170,235,255),
                 label='雪花', upgrades=(220,320), role='周身冰冻', unlock=6),
}
from campaign import TOWER_ORDER
SHOP_ORDER = list(TOWER_ORDER)

MONSTERS = {
    'slime': dict(hp=60, speed=1.7, reward=12, bite=1, color=(240,170,160), label='粉红怪'),
    'bat': dict(hp=45, speed=2.7, reward=15, bite=1, color=(120,200,240), label='蓝飞怪'),
    'thrower': dict(hp=110, speed=1.8, reward=18, bite=1, color=(220,110,150), label='长身怪'),
    'yellow': dict(hp=70, speed=3.15, reward=18, bite=1, color=(245,210,80), label='黄飞怪'),
    'golem': dict(hp=240, speed=1.0, reward=30, bite=1, color=(120,200,130), label='绿皮怪'),
    'starling': dict(hp=130, speed=2.0, reward=20, bite=1, color=(230,160,80), label='星形怪'),
    'elite': dict(hp=480, speed=.95, reward=55, bite=1, color=(70,170,100), label='巨型绿皮怪'),
    'boss': dict(hp=1600, speed=.7, reward=130, bite=1, color=(180,120,170), label='终极巨怪'),
}

# ------------------------------------------------------------- the map
# Corner waypoints of the walking path, in tile coordinates. The first point
# is off-screen so monsters slide in from the left edge.
PATH = [(-1, 2), (17, 2), (17, 6), (2, 6), (2, 10), (18, 10)]
CARROT_TILE = (18, 10)

# ---------------------------------------------------------------- combat
CARROT_HP = 3
CARROT_ESCAPE_DAMAGE = 1    # Every escaped monster uses one of the three lives.
BULLET_SPEED = 340.0
MONSTER_HIT_RADIUS = 16

# Display sizes are independent of targeting, occupied tiles and hit radii.
TOWER_SPRITE_SIZE = 64
MONSTER_SPRITE_SIZE = 64
LARGE_MONSTER_SPRITE_SIZE = 72
CARROT_SPRITE_SIZE = 104


def path_cells(path):
    """Every tile the path passes through, so towers cannot be built there."""
    cells = set()
    for (c0, r0), (c1, r1) in zip(path, path[1:]):
        if c0 == c1:
            for r in range(min(r0, r1), max(r0, r1) + 1):
                cells.add((c0, r))
        else:
            for c in range(min(c0, c1), max(c0, c1) + 1):
                cells.add((c, r0))
    return cells


PATH_CELLS = path_cells(PATH)

# Per-stage tower pools and wave schedules are kept separate from combat rules.
from campaign import LEVELS
WAVE_BREAK = 9.0
LEVEL_BREAK = 8.0

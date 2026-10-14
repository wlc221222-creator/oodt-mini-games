"""Shared constants for the Defend the Carrot MVP.

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
SHOP_H = 88

SCREEN_W = GRID_COLS * TILE            # 800
FIELD_W = SCREEN_W
FIELD_H = GRID_ROWS * TILE             # 520
SCREEN_H = HUD_H + FIELD_H + SHOP_H    # 664
FPS = 60
TITLE = "Defend the Carrot - OOP MVP"

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
START_COINS = 220
PASSIVE_INCOME = 25        # coins granted at the start of every wave

# --------------------------------------------------------- fruit registry
# Fruits are the defenders ("towers"). Each carries its own hit points so a
# ranged monster can knock it down; the intro table in the report reads
# straight off these values.
FRUITS = {
    "apple": dict(cost=100, hp=120, damage=22, interval=1.0, rng=2.6,
                  color=(214, 62, 62), label="Apple"),
    "orange": dict(cost=70, hp=90, damage=12, interval=0.55, rng=2.1,
                   color=(240, 150, 40), label="Orange"),
    "melon": dict(cost=180, hp=170, damage=48, interval=1.7, rng=3.2,
                  color=(70, 170, 90), label="Watermelon"),
}
SHOP_ORDER = ["orange", "apple", "melon"]

# -------------------------------------------------------- monster registry
# speed is measured in tiles per second, so it reads the same on any map.
MONSTERS = {
    "slime": dict(hp=60, speed=1.7, reward=12, bite=1, color=(120, 200, 120),
                  label="Slime"),
    "bat": dict(hp=45, speed=2.7, reward=15, bite=1, color=(150, 130, 200),
                label="Bat"),
    "golem": dict(hp=240, speed=1.0, reward=35, bite=3, color=(150, 140, 120),
                  label="Golem"),
    "thrower": dict(hp=110, speed=1.3, reward=28, bite=2, color=(190, 120, 90),
                    label="Rock Thrower", throw_interval=3.0, throw_damage=24,
                    throw_range=3.2),
}

# ------------------------------------------------------------- the map
# Corner waypoints of the walking path, in tile coordinates. The first point
# is off-screen so monsters slide in from the left edge.
PATH = [(-1, 2), (17, 2), (17, 6), (2, 6), (2, 10), (18, 10)]
CARROT_TILE = (18, 10)

# ---------------------------------------------------------------- combat
CARROT_HP = 20
BULLET_SPEED = 340.0
MONSTER_HIT_RADIUS = 16


def _path_cells():
    """Every tile the path passes through, so towers cannot be built there."""
    cells = set()
    for (c0, r0), (c1, r1) in zip(PATH, PATH[1:]):
        if c0 == c1:
            for r in range(min(r0, r1), max(r0, r1) + 1):
                cells.add((c0, r))
        else:
            for c in range(min(c0, c1), max(c0, c1) + 1):
                cells.add((c, r0))
    return cells


PATH_CELLS = _path_cells()

# --------------------------------------------------------------- levels
# Two tower-defense levels. Each level is a list of waves; each wave is a
# list of (monster_kind, delay_seconds) measured from the wave start.
LEVELS = [
    dict(
        name="Level 1 - Garden Path",
        waves=[
            [("slime", 0.0), ("slime", 3.0), ("slime", 6.0)],
            [("slime", 0.0), ("bat", 2.0), ("slime", 5.0), ("bat", 8.0)],
        ],
    ),
    dict(
        name="Level 2 - Dark Forest",
        waves=[
            [("bat", 0.0), ("slime", 3.0), ("thrower", 6.0)],
            [("slime", 0.0), ("golem", 3.0), ("bat", 6.0), ("bat", 9.0)],
            [("golem", 0.0), ("thrower", 3.0), ("bat", 6.0), ("golem", 10.0)],
        ],
    ),
]
WAVE_BREAK = 8.0
LEVEL_BREAK = 4.0

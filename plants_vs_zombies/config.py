"""Shared constants for the Plants vs Zombies port.

The geometry matches the original game exactly -- an 800x600 window, a 9x5
lawn of 80x100 cells, and the same pixel offsets -- so the extracted original
art lines up with the grid. The gameplay values are tuned so that a full match
is beatable in about two minutes, which keeps the demo short enough for the
required 5 minute video.
"""

# ---------------------------------------------------------------- window
SCREEN_W = 800
SCREEN_H = 600
FPS = 60
TITLE = "Plants vs Zombies"

# ------------------------------------------------------------- lawn grid
GRID_COLS = 9
GRID_ROWS = 5
CELL_W = 80
CELL_H = 100
LAWN_X = 35
LAWN_Y = 100
LAWN_W = GRID_COLS * CELL_W
LAWN_H = GRID_ROWS * CELL_H
PLANT_BASELINE = 60         # plants stand this far into their cell (original)

# ---------------------------------------------------------------- top bar
BAR_H = 87
CARD_X0 = 87                # first card's left edge
CARD_DX = 55                # horizontal step between cards
CARD_Y = 8

# ------------------------------------------------------- seed chooser
# The original game opens a "choose your seeds" panel before a level; only
# the chosen plants go into the top bar. Capping the selection is what keeps
# the cards from overflowing the wooden bar.
MAX_SEEDS = 8

# Seed-chooser geometry: a preview strip along the top (the original's wooden
# bar) plus a grid of every available plant below it.
CHOOSER_COLS = 5
CHOOSER_DX = 90
CHOOSER_DY = 116
CHOOSER_CARD_W = 55
CHOOSER_CARD_H = 74
CHOOSER_GRID_X = 71
CHOOSER_GRID_Y = 212            # first grid row (canvas coords)
CHOOSER_PANEL_X = 26
CHOOSER_PANEL_Y = 145
CHOOSER_PANEL_W = 510
CHOOSER_PANEL_H = 410

# ------------------------------------------------------------ progression
# Adventure mode is a linear chain of levels. Beating one unlocks the next
# and grants a new plant, which then appears in later seed choosers -- this is
# the "clear levels to earn plants" progression the demo is built around.
START_PLANTS = ["sunflower", "peashooter"]
LEVEL_REWARDS = ["wallnut", "snowpea", "cherrybomb", "repeater",
                 "potatomine", "threepeater", "jalapeno"]

# Each level: id, name, rows (the lawn grows with progress), background index,
# starting sun, and a list of waves. A wave is a list of (zombie, delay).
LEVELS = [
    dict(id="1-1", name="前院 · 初战", rows=3, bg=0, sun=150,
         waves=[[("normal", 14.0), ("normal", 22.0)]]),
    dict(id="1-2", name="前院 · 成群", rows=3, bg=0, sun=150,
         waves=[[("normal", 12.0), ("normal", 20.0)],
                [("normal", 2.0), ("cone", 9.0), ("normal", 16.0)]]),
    dict(id="1-3", name="前院 · 路障", rows=4, bg=0, sun=175,
         waves=[[("normal", 10.0), ("cone", 18.0)],
                [("normal", 2.0), ("cone", 8.0), ("normal", 14.0)],
                [("cone", 2.0), ("normal", 9.0), ("cone", 16.0)]]),
    dict(id="1-4", name="前院 · 铁桶", rows=4, bg=0, sun=175,
         waves=[[("normal", 10.0), ("cone", 18.0)],
                [("cone", 2.0), ("bucket", 9.0), ("normal", 16.0)],
                [("bucket", 2.0), ("cone", 8.0), ("normal", 14.0),
                 ("cone", 20.0)]]),
    dict(id="1-5", name="前院 · 围攻", rows=5, bg=0, sun=200,
         waves=[[("normal", 8.0), ("cone", 16.0)],
                [("cone", 2.0), ("bucket", 9.0), ("normal", 15.0)],
                [("bucket", 2.0), ("cone", 8.0), ("bucket", 14.0),
                 ("cone", 20.0)]]),
    dict(id="2-1", name="后院 · 夜战", rows=5, bg=1, sun=200,
         waves=[[("normal", 8.0), ("cone", 15.0)],
                [("cone", 2.0), ("bucket", 8.0), ("cone", 14.0)],
                [("bucket", 2.0), ("cone", 7.0), ("bucket", 13.0),
                 ("cone", 19.0)]]),
    dict(id="2-2", name="后院 · 决战", rows=5, bg=1, sun=225,
         waves=[[("normal", 8.0), ("cone", 14.0)],
                [("cone", 2.0), ("bucket", 8.0), ("cone", 14.0)],
                [("bucket", 2.0), ("cone", 7.0), ("bucket", 13.0),
                 ("cone", 19.0)],
                [("bucket", 2.0), ("bucket", 8.0), ("cone", 13.0),
                 ("bucket", 18.0), ("cone", 23.0)]]),
]

# ---------------------------------------------------------------- colors
COL_SKY = (135, 206, 235)
COL_LAWN_A = (98, 176, 76)
COL_LAWN_B = (86, 162, 66)
COL_GRID = (60, 120, 50)
COL_TEXT = (24, 24, 24)
COL_SUN = (255, 214, 51)
COL_HP_BG = (60, 60, 60)
COL_HP_FG = (220, 60, 60)
COL_CARD = (236, 226, 196)
COL_CARD_SEL = (255, 250, 210)
COL_CARD_DISABLED = (150, 145, 130)

# ------------------------------------------------------------- economy
START_SUN = 250
SKY_SUN_INTERVAL = 5.0      # seconds between falling suns
SKY_SUN_AMOUNT = 25

# ------------------------------------------------------- plant registry
# Each plant definition drives both the shop card and the spawned instance.
# ``sprite`` names the original art set used to render the plant.
# ``recharge`` is the card cooldown in seconds after planting, taken from the
# original game's fast / normal / very-slow recharge classes.
PLANTS = {
    "sunflower": dict(cost=50, hp=60, color=(255, 205, 60),
                      label="Sunflower", sprite="SunFlower", card="sunflower",
                      recharge=7.5),
    "peashooter": dict(cost=100, hp=60, color=(80, 190, 90),
                       label="Peashooter", sprite="Peashooter",
                       card="peashooter", recharge=7.5),
    "wallnut": dict(cost=50, hp=400, color=(196, 150, 92),
                    label="Wall-nut", sprite="WallNut", card="wallnut",
                    recharge=30.0),
    "snowpea": dict(cost=175, hp=60, color=(120, 200, 240),
                    label="Snow Pea", sprite="SnowPea", card="snowpea",
                    recharge=7.5),
    "cherrybomb": dict(cost=150, hp=60, color=(230, 70, 90),
                       label="Cherry Bomb", sprite="CherryBomb",
                       card="cherrybomb", recharge=50.0),
    "repeater": dict(cost=200, hp=60, color=(70, 170, 80),
                     label="Repeater", sprite="RepeaterPea",
                     card="repeaterpea", recharge=7.5),
    "threepeater": dict(cost=325, hp=60, color=(90, 200, 100),
                        label="Threepeater", sprite="Threepeater",
                        card="threepeashooter", recharge=7.5),
    "potatomine": dict(cost=25, hp=60, color=(190, 160, 110),
                       label="Potato Mine", sprite="PotatoMine",
                       card="potatomine", recharge=30.0),
    "jalapeno": dict(cost=125, hp=60, color=(230, 60, 60),
                     label="Jalapeno", sprite="Jalapeno", card="jalapeno",
                     recharge=50.0),
}
SHOP_ORDER = ["sunflower", "peashooter", "wallnut", "snowpea", "cherrybomb",
              "repeater", "threepeater", "potatomine", "jalapeno"]

# ------------------------------------------------------- zombie registry
ZOMBIES = {
    "normal": dict(hp=100, speed=20.0, damage=45.0,
                   color=(150, 150, 160), label="Zombie"),
    "cone": dict(hp=220, speed=18.0, damage=45.0,
                 color=(180, 130, 70), label="Conehead"),
    "bucket": dict(hp=380, speed=16.0, damage=45.0,
                   color=(170, 170, 190), label="Buckethead"),
}

# ------------------------------------------------------------- combat
PEA_DAMAGE = 22
PEA_SPEED = 320.0
PEA_INTERVAL = 1.2          # seconds between shots for a peashooter
SNOW_SLOW_FACTOR = 0.5
SNOW_SLOW_TIME = 3.0
CHERRY_DAMAGE = 900
CHERRY_RADIUS = CELL_W * 1.4
EAT_INTERVAL = 0.6          # seconds per bite

# --------------------------------------------------------------- waves
# Each entry is a wave: list of (zombie_type, delay_seconds) from wave start.
WAVES = [
    [("normal", 12.0), ("normal", 20.0)],
    [("normal", 2.0), ("cone", 8.0), ("normal", 14.0)],
    [("normal", 2.0), ("cone", 6.0), ("bucket", 12.0), ("cone", 18.0)],
]
WAVE_BREAK = 10.0           # seconds of calm between waves

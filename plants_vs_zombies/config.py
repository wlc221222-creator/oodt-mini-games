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
TITLE = "Plants vs Zombies - Night Expansion"

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
                 "potatomine", "threepeater", "jalapeno",
                 "puffshroom", "sunshroom", "scaredyshroom", "chomper",
                 "squash", "spikeweed", "iceshroom"]

# All visible lawn cells are plantable from the first level. Each wave entry
# is (kind, seconds, lane), with lanes numbered 0..4. Explicit lanes make
# pincer attacks and concentrated pushes deliberate rather than round-robin.
LEVELS = [
    dict(id="1-1", name="前院 · 五路初战", rows=5, bg=0, sun=200,
         brief=("五行草坪全部可种", "先种向日葵，再补齐五路火力"),
         rule="五路入门", sky_sun=True, wave_break=8.0,
         wave_names=["试探来袭", "五路防守"],
         waves=[[("normal", 20, 2), ("normal", 32, 0), ("normal", 44, 4)],
                [("normal", 2, 1), ("normal", 10, 3), ("normal", 18, 2),
                 ("normal", 26, 0), ("normal", 34, 4)]]),
    dict(id="1-2", name="前院 · 两翼夹击", rows=5, bg=0, sun=225,
         brief=("上下两路连续夹击", "坚果挡住前排，留意中路偷袭"),
         rule="两翼夹击", sky_sun=True, wave_break=9.0,
         wave_names=["两翼试探", "上下夹击", "中路偷袭"],
         waves=[[("normal", 18, 0), ("normal", 26, 4), ("normal", 36, 2)],
                [("cone", 3, 0), ("normal", 7, 0), ("cone", 13, 4), ("normal", 17, 4)],
                [("normal", 2, 1), ("normal", 8, 3), ("cone", 14, 2),
                 ("normal", 19, 0), ("normal", 24, 4)]]),
    dict(id="1-3", name="前院 · 极速突袭", rows=5, bg=0, sun=250,
         brief=("僵尸移动速度提高 30%", "寒冰减速，坚果争取输出时间"),
         rule="移速 +30%", sky_sun=True, speed_multiplier=1.3, wave_break=8.0,
         wave_names=["快步先锋", "交错冲锋", "中央突破"],
         waves=[[("normal", 20, 1), ("normal", 28, 3), ("normal", 36, 2)],
                [("normal", 2, 0), ("cone", 7, 2), ("normal", 12, 4),
                 ("normal", 17, 1), ("normal", 22, 3)],
                [("cone", 2, 2), ("normal", 6, 2), ("normal", 10, 1),
                 ("normal", 14, 3), ("cone", 20, 0), ("normal", 26, 4)]]),
    dict(id="1-4", name="前院 · 重甲攻坚", rows=5, bg=0, sun=275,
         brief=("铁桶带队，同路集群推进", "集中火力，樱桃炸弹处理重甲"),
         rule="重甲集群", sky_sun=True, wave_break=12.0,
         wave_names=["路障先遣", "铁桶纵队", "双线攻坚"],
         waves=[[("normal", 18, 2), ("cone", 28, 1), ("normal", 38, 3)],
                [("bucket", 3, 2), ("normal", 7, 2), ("cone", 11, 2),
                 ("normal", 20, 0), ("normal", 27, 4)],
                [("bucket", 3, 1), ("cone", 7, 1), ("bucket", 17, 3),
                 ("cone", 21, 3), ("normal", 30, 0), ("normal", 35, 4)]]),
    dict(id="1-5", name="前院 · 阳光补给", rows=5, bg=0, sun=275,
         brief=("每清完一波补给 75 阳光", "四波连续进攻，及时扩充火力"),
         rule="清波 +75 阳光", sky_sun=True, wave_bonus=75, wave_break=6.0,
         wave_names=["守住补给", "全线推进", "重甲护送", "五路合围"],
         waves=[[("normal", 18, 0), ("normal", 26, 2), ("normal", 34, 4)],
                [("normal", 2, 0), ("normal", 5, 1), ("cone", 8, 2),
                 ("normal", 11, 3), ("normal", 14, 4)],
                [("bucket", 2, 1), ("cone", 6, 1), ("bucket", 14, 3),
                 ("normal", 19, 3), ("normal", 25, 2)],
                [("cone", 2, 0), ("normal", 4, 1), ("bucket", 6, 2),
                 ("normal", 8, 3), ("cone", 10, 4), ("normal", 17, 0),
                 ("normal", 20, 4)]]),
    dict(id="2-1", name="后院 · 无光之夜", rows=5, bg=1, sun=350,
         brief=("夜间没有天降阳光", "优先种向日葵，用地雷省阳光"),
         rule="无天降阳光", sky_sun=False, wave_break=12.0,
         wave_names=["夜幕降临", "暗夜包围", "坚守到黎明"],
         waves=[[("normal", 26, 1), ("normal", 38, 3), ("normal", 50, 2)],
                [("normal", 3, 0), ("cone", 10, 2), ("normal", 18, 4),
                 ("normal", 26, 1), ("normal", 32, 3)],
                [("cone", 3, 0), ("bucket", 12, 2), ("cone", 22, 4),
                 ("normal", 28, 1), ("normal", 34, 3), ("normal", 40, 2)]]),
    dict(id="2-2", name="后院 · 月下决战", rows=5, bg=1, sun=400,
         brief=("无天降阳光，清波补给 50", "五波混合进攻，三线射手协防"),
         rule="夜战 · 清波 +50", sky_sun=False, wave_bonus=50,
         speed_multiplier=1.1, wave_break=9.0,
         wave_names=["夜袭前哨", "两翼施压", "中央重甲", "交错突袭", "最后的合围"],
         waves=[[("normal", 25, 2), ("normal", 35, 0), ("normal", 45, 4)],
                [("cone", 3, 0), ("normal", 7, 0), ("cone", 14, 4),
                 ("normal", 18, 4), ("normal", 25, 2)],
                [("bucket", 3, 2), ("cone", 8, 2), ("normal", 12, 2),
                 ("cone", 20, 1), ("cone", 28, 3)],
                [("normal", 2, 0), ("cone", 5, 1), ("normal", 8, 2),
                 ("cone", 11, 3), ("normal", 14, 4), ("bucket", 21, 2)],
                [("bucket", 2, 0), ("cone", 6, 1), ("bucket", 10, 2),
                 ("cone", 14, 3), ("bucket", 18, 4), ("normal", 24, 1),
                 ("normal", 28, 3), ("cone", 34, 2)]]),
]

# Expansion stays on the existing five-lane night lawn (no pretend pool).
LEVELS += [
    dict(id="2-3", name="后院 · 报纸风波", rows=5, bg=1, sun=400,
         brief=("报纸破损后，读报僵尸暴走", "用寒冰减速，坚果挡住冲锋"),
         rule="报纸破损后加速", sky_sun=False, wave_break=12.0,
         wave_names=["深夜来客", "报纸小队", "旗帜领军"],
         waves=[[("normal", 25, 2), ("newspaper", 38, 1), ("normal", 49, 3)],
                [("newspaper", 3, 0), ("normal", 11, 2), ("newspaper", 20, 4), ("cone", 30, 2)],
                [("flag", 3, 2), ("newspaper", 10, 1), ("cone", 17, 0),
                 ("newspaper", 24, 3), ("normal", 31, 4), ("cone", 38, 2)]]),
    dict(id="2-4", name="后院 · 蘑菇前哨", rows=5, bg=1, sun=300,
         brief=("小喷菇免费，但只攻击前三格", "靠前铺设，后排补远程火力"),
         rule="短程蘑菇防线", sky_sun=False, wave_break=10.0,
         wave_names=["前哨试探", "五路渗透", "夜色包围"],
         waves=[[("normal", 24, 0), ("normal", 34, 2), ("normal", 44, 4)],
                [("normal", 3, 0), ("normal", 7, 1), ("cone", 12, 2),
                 ("normal", 19, 3), ("normal", 26, 4)],
                [("flag", 3, 1), ("normal", 7, 1), ("newspaper", 14, 3),
                 ("cone", 23, 0), ("cone", 31, 4), ("normal", 38, 2)]]),
    dict(id="2-5", name="后院 · 阳光培育", rows=5, bg=1, sun=275,
         brief=("阳光菇先产 15，长大后产 25", "保护经济线，等待蘑菇成长"),
         rule="培育夜间经济", sky_sun=False, wave_break=13.0,
         wave_names=["播种之夜", "报纸来访", "护住菇田", "成熟的防线"],
         waves=[[("normal", 30, 1), ("normal", 42, 3), ("normal", 54, 2)],
                [("newspaper", 3, 2), ("normal", 13, 0), ("normal", 23, 4)],
                [("cone", 3, 1), ("cone", 13, 3), ("normal", 22, 0), ("normal", 30, 4)],
                [("flag", 3, 2), ("newspaper", 11, 0), ("cone", 19, 1),
                 ("cone", 27, 3), ("newspaper", 35, 4), ("normal", 42, 2)]]),
    dict(id="2-6", name="后院 · 胆小防线", rows=5, bg=1, sun=325,
         brief=("胆小菇远射，敌人靠近会躲藏", "种在后排，用坚果保护它"),
         rule="保护后排蘑菇", sky_sun=False, wave_break=10.0,
         wave_names=["远处的脚步", "报纸突进", "侧翼穿插", "护住后排"],
         waves=[[("normal", 25, 2), ("normal", 37, 0), ("normal", 49, 4)],
                [("newspaper", 3, 1), ("newspaper", 14, 3), ("cone", 25, 2)],
                [("flag", 3, 0), ("normal", 9, 0), ("flag", 17, 4), ("normal", 23, 4)],
                [("newspaper", 3, 1), ("cone", 11, 2), ("newspaper", 19, 3),
                 ("bucket", 28, 2), ("normal", 35, 0), ("normal", 41, 4)]]),
    dict(id="2-7", name="后院 · 吞噬重甲", rows=5, bg=1, sun=375,
         brief=("大嘴花吞噬整只僵尸", "消化期间需要其他植物掩护"),
         rule="吞噬与消化", sky_sun=False, wave_break=13.0,
         wave_names=["重甲试探", "铁桶纵队", "消化间隙", "重装合围"],
         waves=[[("normal", 25, 1), ("normal", 37, 3), ("cone", 49, 2)],
                [("bucket", 3, 0), ("normal", 12, 0), ("bucket", 25, 4), ("normal", 34, 4)],
                [("newspaper", 3, 1), ("cone", 12, 2), ("newspaper", 23, 3)],
                [("flag", 3, 2), ("bucket", 10, 1), ("cone", 18, 0),
                 ("bucket", 26, 3), ("cone", 34, 4), ("newspaper", 42, 2)]]),
    dict(id="2-8", name="后院 · 窝瓜伏击", rows=5, bg=1, sun=350,
         brief=("窝瓜会跃起压扁附近的僵尸", "等同路敌人聚集再落下伏兵"),
         rule="近身集群伏击", sky_sun=False, wave_break=12.0,
         wave_names=["小队先遣", "集中突破", "上下伏击", "旗帜冲锋"],
         waves=[[("normal", 25, 0), ("normal", 37, 2), ("normal", 49, 4)],
                [("cone", 3, 2), ("newspaper", 6, 2), ("normal", 9, 2), ("normal", 26, 1)],
                [("newspaper", 3, 0), ("normal", 7, 0), ("cone", 20, 4), ("normal", 24, 4)],
                [("flag", 3, 1), ("bucket", 8, 1), ("newspaper", 14, 3),
                 ("cone", 20, 3), ("normal", 29, 0), ("normal", 36, 4), ("cone", 43, 2)]]),
    dict(id="2-9", name="后院 · 地刺长廊", rows=5, bg=1, sun=400,
         brief=("地刺伤害路过的僵尸且不会被吃", "通关解锁寒冰菇，可重玩试用"),
         rule="地面陷阱与最终围攻", sky_sun=False, wave_break=12.0,
         wave_names=["长廊来客", "报纸奔袭", "铁桶护卫", "旗帜大军", "月夜终章"],
         waves=[[("normal", 25, 2), ("normal", 37, 0), ("normal", 49, 4)],
                [("newspaper", 3, 1), ("normal", 10, 1), ("newspaper", 21, 3), ("normal", 28, 3)],
                [("bucket", 3, 0), ("cone", 12, 2), ("bucket", 23, 4), ("normal", 33, 2)],
                [("flag", 3, 0), ("normal", 7, 0), ("newspaper", 14, 1),
                 ("flag", 23, 4), ("normal", 27, 4), ("newspaper", 34, 3)],
                [("flag", 3, 2), ("bucket", 10, 0), ("newspaper", 17, 1),
                 ("bucket", 24, 2), ("newspaper", 31, 3), ("bucket", 38, 4),
                 ("cone", 46, 2)]]),
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
# Costs and defining abilities follow the original PvZ. Combat HP and
# production intervals use this project's existing short-session scale.
PLANTS.update({
    "puffshroom": dict(cost=0, hp=60, color=(175, 125, 210), label="Puff-shroom",
                      sprite="PuffShroom", card="puffshroom", recharge=7.5, mushroom=True),
    "sunshroom": dict(cost=25, hp=60, color=(235, 190, 75), label="Sun-shroom",
                     sprite="SunShroom", card="sunshroom", recharge=7.5, mushroom=True),
    "scaredyshroom": dict(cost=25, hp=60, color=(170, 130, 200), label="Scaredy-shroom",
                         sprite="ScaredyShroom", card="scaredyshroom", recharge=7.5, mushroom=True),
    "chomper": dict(cost=150, hp=60, color=(170, 80, 190), label="Chomper",
                    sprite="Chomper", card="chomper", recharge=7.5),
    "squash": dict(cost=50, hp=60, color=(140, 185, 85), label="Squash",
                   sprite="Squash", card="squash", recharge=30.0),
    "spikeweed": dict(cost=100, hp=60, color=(140, 135, 65), label="Spikeweed",
                      sprite="Spikeweed", card="spikeweed", recharge=7.5),
    "iceshroom": dict(cost=75, hp=60, color=(145, 200, 240), label="Ice-shroom",
                      sprite="IceShroom", card="iceshroom", recharge=50.0, mushroom=True),
})
PLANT_HELP = {
    "sunflower": "每9秒生产25阳光，维持防线经济",
    "peashooter": "向同一行发射豌豆，每发造成22伤害",
    "wallnut": "400生命值的屏障，阻挡僵尸；不会攻击",
    "snowpea": "每发22伤害，并让无报纸保护的僵尸减速",
    "cherrybomb": "种下1.2秒后爆炸，对附近敌人造成900伤害",
    "repeater": "每轮同时发射两颗豌豆，每颗22伤害",
    "threepeater": "向本行及相邻行发射豌豆，每颗22伤害",
    "potatomine": "准备6秒后接触触发，对一只敌人造成900伤害",
    "jalapeno": "种下1秒后清扫本行，造成900伤害",
    "puffshroom": "免费；射程三格；白天睡觉",
    "sunshroom": "先产15阳光，120秒后产25；白天睡觉",
    "scaredyshroom": "整行射击；附近有僵尸时躲藏；白天睡觉",
    "chomper": "吞噬近处一只僵尸，随后消化42秒",
    "squash": "一次性跃起，压扁落点附近的僵尸",
    "spikeweed": "伤害踩在上面的僵尸；不会被啃食",
    "iceshroom": "一次性全屏冻结，再减速；白天睡觉",
}
SHOP_ORDER = ["sunflower", "peashooter", "wallnut", "snowpea", "cherrybomb",
              "repeater", "threepeater", "potatomine", "jalapeno",
              "puffshroom", "sunshroom", "scaredyshroom", "chomper",
              "squash", "spikeweed", "iceshroom"]

# ------------------------------------------------------- zombie registry
ZOMBIES = {
    "normal": dict(hp=100, speed=20.0, damage=45.0,
                   color=(150, 150, 160), label="Zombie"),
    "cone": dict(hp=220, speed=18.0, damage=45.0,
                 color=(180, 130, 70), label="Conehead"),
    "bucket": dict(hp=380, speed=16.0, damage=45.0,
                   color=(170, 170, 190), label="Buckethead"),
}

ZOMBIES.update({
    "flag": dict(hp=100, speed=24.0, damage=45.0, color=(155, 150, 150), label="Flag Zombie"),
    "newspaper": dict(hp=100, paper_hp=80, speed=16.0, rage_multiplier=2.5,
                       damage=45.0, color=(175, 165, 150), label="Newspaper Zombie"),
})
ZOMBIE_NAMES = {"normal": "普通", "cone": "路障", "bucket": "铁桶", "flag": "旗帜", "newspaper": "读报"}
ZOMBIE_HELP = {
    "normal": "基础敌人，靠近植物后啃食",
    "cone": "路障提高生命值，需要更多火力",
    "bucket": "铁桶提供高生命值，可用爆炸或吞噬应对",
    "flag": "波次领头单位，移动稍快，没有增益光环",
    "newspaper": "报纸耐久80，挡住寒冰豌豆减速；破损后移速变为2.5倍",
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

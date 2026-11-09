"""Eight authored stages following the original sky/jungle/desert progression.

Wave counts follow the official 15–25-wave format. Layouts and balance are
original to this three-life course project, rather than commercial level data.
"""
TOWER_ORDER = ('orange', 'apple', 'melon', 'star', 'ice', 'poison', 'rocket', 'snow')
WAVE_COUNTS = (15, 16, 18, 20, 21, 22, 24, 25)
PATHS = (
    [(-1, 2), (17, 2), (17, 6), (2, 6), (2, 10), (18, 10)],
    [(3, -1), (3, 3), (16, 3), (16, 8), (5, 8), (5, 11), (18, 11)],
    [(-1, 1), (18, 1), (18, 5), (3, 5), (3, 10), (17, 10)],
    [(-1, 1), (16, 1), (16, 5), (4, 5), (4, 9), (17, 9), (17, 11), (18, 11)],
    [(17, -1), (17, 2), (2, 2), (2, 6), (16, 6), (16, 10), (3, 10)],
    [(-1, 1), (18, 1), (18, 4), (1, 4), (1, 8), (16, 8), (16, 11), (4, 11)],
    [(-1, 2), (16, 2), (16, 6), (4, 6), (4, 10), (18, 10)],
    [(2, -1), (2, 3), (17, 3), (17, 7), (5, 7), (5, 11), (18, 11)],
)
NAMES = ('天空云径', '天际回廊', '飞翼拦截', '林间密集',
         '丛林硬壳', '深林寒潮', '沙漠疾袭', '沙海决战')
POOLS = (
    ('slime', 'bat'),
    ('slime', 'bat', 'thrower'),
    ('slime', 'bat', 'thrower', 'yellow'),
    ('slime', 'bat', 'thrower', 'yellow', 'golem'),
    ('slime', 'bat', 'thrower', 'yellow', 'golem', 'starling'),
    ('slime', 'bat', 'thrower', 'yellow', 'golem', 'starling', 'elite'),
    ('slime', 'bat', 'thrower', 'yellow', 'golem', 'starling', 'elite', 'boss'),
    ('slime', 'bat', 'thrower', 'yellow', 'golem', 'starling', 'elite', 'boss'),
)


def make_waves(stage):
    waves, labels = [], []
    pool = tuple(kind for kind in POOLS[stage] if kind != 'boss')
    for wave in range(WAVE_COUNTS[stage]):
        active_pool = tuple(kind for kind in pool if kind != 'elite' or wave >= max(5, 14 - stage))
        count = 5 + stage + wave // 4
        gap = max(.48, 1.2 - stage * .065 - wave * .012)
        kinds = [active_pool[(slot + wave * 2) % len(active_pool)] for slot in range(count)]
        label = '混合波'
        if wave < 3:
            kinds = [('slime' if slot % 3 else active_pool[min(stage, len(active_pool) - 1)])
                     for slot in range(count)]
            label = '布防波'
        elif wave % 5 == 3:
            fast = 'yellow' if 'yellow' in pool else 'bat'
            kinds = [fast if slot % 3 else 'slime' for slot in range(count)]
            label = '飞行突袭'
        elif wave % 5 == 4 and 'golem' in active_pool:
            tank = 'elite' if 'elite' in active_pool else 'golem'
            kinds = [tank if slot % 3 == 0 else active_pool[slot % len(active_pool)] for slot in range(count)]
            label = '重甲推进'
        if wave == WAVE_COUNTS[stage] - 1:
            label = '最终波'
            if stage >= 6:
                kinds[-1] = 'boss'
                if stage == 7:
                    kinds[-5] = 'boss'
                label = '巨怪决战'
        waves.append([(kind, round(slot * gap, 3)) for slot, kind in enumerate(kinds)])
        labels.append(label)
    return waves, labels


LEVELS = []
for i, name in enumerate(NAMES):
    waves, labels = make_waves(i)
    theme = 1 if i < 3 else 2 if i < 6 else 3
    LEVELS.append(dict(
        name=f'第{i + 1}关 · {name}', theme=theme, path=PATHS[i],
        grass=((126, 176, 96), (112, 162, 84)),
        towers=TOWER_ORDER[:min(8, i + 3)], monsters=POOLS[i],
        start_coins=(300, 350, 400, 500, 650, 800, 1050, 1300)[i],
        hp_scale=(1, 1.12, 1.3, 1.5, 1.75, 2.05, 2.4, 2.8)[i],
        speed_scale=1 + i * .02, waves=waves, wave_labels=labels,
        hint=('沿长直道使用穿透攻击' if i < 2 else
              '减速塔配合范围火力' if i < 5 else '升级输出塔，控制与穿透协同'),
    ))

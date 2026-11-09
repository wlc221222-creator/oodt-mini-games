"""Deterministic player using public placement/upgrade rules and earned coins."""
import math
import config as C
from entities import tile_center


class Builder:
    def __init__(self, game):
        self.game = game
        path = list(C.path_cells(C.LEVELS[game.level_index]['path']))
        self.sites = {}
        for kind in game.available_towers:
            radius = C.FRUITS[kind]['rng'] * C.TILE
            ranked = []
            for row in range(C.GRID_ROWS):
                for col in range(C.GRID_COLS):
                    if not game.can_build(col, row):
                        continue
                    x, y = tile_center(col, row)
                    covered = [(c, r) for c, r in path if math.dist((x, y), tile_center(c, r)) <= radius]
                    if covered:
                        ranked.append((len(covered), col, row))
            self.sites[kind] = sorted(ranked, reverse=True)
        self.order = [k for k in ('apple', 'apple', 'orange', 'melon', 'star', 'ice', 'poison', 'rocket', 'snow')
                      if k in game.available_towers]

    def tick(self):
        g = self.game
        core = [t for t in g.fruits if t.kind in ('apple', 'melon', 'star', 'rocket')]
        if len(g.fruits) >= min(6, 3 + g.level_index // 2):
            candidates = [t for t in core if t.level < 2 and t.upgrade_cost <= g.coins]
            if not candidates and len(g.fruits) >= 8:
                candidates = [t for t in core if t.level < 3 and t.upgrade_cost <= g.coins]
            if candidates:
                g.inspected = min(candidates, key=lambda t: (t.level, t.upgrade_cost))
                g.upgrade_tower()
                return
        desired = min(22, 3 + g.level_index * 2 + g.wave_index // 4)
        if len(g.fruits) < desired:
            count = len(g.fruits)
            kind = self.order[count] if count < len(self.order) else (
                ('rocket' if 'rocket' in g.available_towers else 'star' if 'star' in g.available_towers else 'apple')
                if count % 3 == 0 else 'apple')
            if g.coins < C.FRUITS[kind]['cost']:
                return
            options = [(score - sum(1.5 / (1 + math.dist((col, row), (t.col, t.row))) for t in g.fruits), col, row)
                       for score, col, row in self.sites[kind] if g.can_build(col, row)]
            if options:
                _, col, row = max(options)
                g.selected = kind
                g._on_click(tile_center(col, row))
                return
        candidates = [tower for tower in g.fruits if tower.upgrade_cost and g.coins >= tower.upgrade_cost]
        if candidates:
            # Upgrade output before buying repeated control effects.
            g.inspected = min(candidates, key=lambda t: (t.level + (1 if t.kind in ('ice', 'snow', 'poison') else 0), t.col))
            g.upgrade_tower()

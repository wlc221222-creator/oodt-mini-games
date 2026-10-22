"""Game loop and controller for the Defend the Carrot adventure.

``Game`` owns the entity collections, the path, the wave schedule, the coin
economy and the HUD. Entities only call back into it for shared facts such
as the path or "damage the carrot", which keeps them decoupled.

Run with:  python main.py
"""

from __future__ import annotations

import sys
from typing import List, Optional

import pygame

import config as C
import progress
from guide import FieldGuide
from ui import GameUI, load_font
from scenery import field_image
from entities import (
    Apple, Bat, Bullet, Carrot, Effect, Fruit, Golem, Melon, Monster, Orange,
    Rock, RockThrower, Slime, tile_center,
    Star, IceStar, PoisonPin, RocketTower, Snowflake,
    YellowFly, Starling, EliteGolem, BigBoss,
)

FRUIT_CLASSES = {"apple": Apple, "orange": Orange, "melon": Melon, 'star': Star,
                 'ice': IceStar, 'poison': PoisonPin, 'rocket': RocketTower, 'snow': Snowflake}
MONSTER_CLASSES = {
    "slime": Slime, "bat": Bat, "golem": Golem, "thrower": RockThrower,
    'yellow': YellowFly, 'starling': Starling, 'elite': EliteGolem, 'boss': BigBoss,
}


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((C.SCREEN_W, C.SCREEN_H))
        pygame.display.set_caption(C.TITLE)
        self.clock = pygame.time.Clock()
        self.font = load_font(19)
        self.small_font = load_font(15)
        self.guide = FieldGuide()
        self.ui = GameUI(self)
        self.progress = progress.load()
        self.reset()
        self.state = "menu"

    # ------------------------------------------------------------ lifecycle
    def reset(self, level_index=0) -> None:
        self.fruits: List[Fruit] = []
        self.monsters: List[Monster] = []
        self.bullets: List[Bullet] = []
        self.rocks: List[Rock] = []
        self.effects: List[Effect] = []

        self.coins = C.START_COINS
        self.selected: Optional[str] = None
        self.level_index = 0
        self.wave_index = 0
        self.wave_timer = 0.0
        self.spawn_queue: List[list] = []
        self.state = "playing"       # menu | playing | paused | levelclear | won | lost
        self.elapsed = 0.0
        self.kills = 0
        self.score = 0
        self.guide_open = False
        self.level_select_open = False
        self.inspected = None
        self.speed_multiplier = 1
        self._load_level(level_index)

    def path_px(self, seg: int, frac: float):
        return self.path[seg]

    def _load_level(self, index: int) -> None:
        if index >= len(C.LEVELS):
            return
        self.level_index = index
        level = C.LEVELS[index]
        self.coins = level['start_coins']
        self.available_towers = level['towers']
        self.path = [tile_center(c, r) for c, r in level["path"]]
        self.path_cells = C.path_cells(level["path"])
        self.carrot_tile = level["path"][-1]
        self.carrot = Carrot(*self.carrot_tile)
        for name in ("fruits", "monsters", "bullets", "rocks", "effects"):
            setattr(self, name, [])
        self.selected = None
        self.inspected = None
        self.level_saved = False
        self.save_error = False
        self.notice = ""
        self.notice_timer = 0.0
        self.wave_index = 0
        self._load_wave(0)
        self.wave_timer = -C.LEVEL_BREAK

    def _load_wave(self, index: int) -> None:
        waves = C.LEVELS[self.level_index]["waves"]
        self.wave_index = index
        self.coins += C.PASSIVE_INCOME
        self.spawn_queue = [[kind, delay] for (kind, delay) in waves[index]]
        self.wave_timer = 0.0

    # --------------------------------------------------------------- helpers
    def fruit_at(self, col: int, row: int) -> Optional[Fruit]:
        for f in self.fruits:
            if f.col == col and f.row == row and f.alive:
                return f
        return None

    def can_build(self, col: int, row: int) -> bool:
        if not (0 <= col < C.GRID_COLS and 0 <= row < C.GRID_ROWS):
            return False
        if (col, row) in self.path_cells:
            return False
        if (col, row) == self.carrot_tile:
            return False
        return self.fruit_at(col, row) is None

    def damage_carrot(self, amount: float) -> None:
        self.carrot.take_damage(amount)
        self.show_notice(f"有怪物突破防线！萝卜失去 {amount:g} 点生命")
        if not self.carrot.alive:
            self.state = "lost"

    # ---------------------------------------------------------------- update
    def update(self, dt: float) -> None:
        self.ui.update(dt)
        if self.state != "playing" or self.guide_open or self.level_select_open:
            return
        dt *= self.speed_multiplier
        self.elapsed += dt
        self.notice_timer = max(0.0, self.notice_timer - dt)
        self._update_waves(dt)
        if self.state != "playing":
            return
        self.carrot.update(dt, self)
        for group in (self.fruits, self.monsters, self.bullets,
                      self.rocks, self.effects):
            for e in group:
                if e.alive:
                    e.update(dt, self)
                if self.state != "playing":
                    self._reap()
                    return
        self._reap()
        self._check_victory()

    def _update_waves(self, dt: float) -> None:
        waves = C.LEVELS[self.level_index]["waves"]
        if self.wave_index >= len(waves):
            return
        self.wave_timer += dt
        pending = []
        for kind, delay in self.spawn_queue:
            if self.wave_timer >= delay:
                self.monsters.append(MONSTER_CLASSES[kind](self))
            else:
                pending.append([kind, delay])
        self.spawn_queue = pending

        if not self.spawn_queue:
            if self.wave_index + 1 < len(waves) and self.wave_timer >= waves[self.wave_index][-1][1] + C.WAVE_BREAK:
                self._load_wave(self.wave_index + 1)
            elif not self.monsters and self.wave_index + 1 >= len(waves):
                self._advance_level()

    def _advance_level(self) -> None:
        self._save_completion()
        if self.level_index + 1 < len(C.LEVELS):
            self.state = "levelclear"

    def _save_completion(self):
        if self.level_saved:
            return
        self.level_saved = True
        self.progress['unlocked'] = max(self.progress['unlocked'], min(len(C.LEVELS), self.level_index + 2))
        key = str(self.level_index)
        self.progress['best'][key] = max(self.progress['best'].get(key, 0), int(self.carrot.hp))
        self.save_error = not progress.save(self.progress)
        if self.save_error:
            self.show_notice('已通关，但进度文件暂时无法写入')

    def _continue(self) -> None:
        if self.state == "paused":
            self.state = "playing"
        elif self.state == "levelclear":
            self._load_level(self.level_index + 1)
            self.wave_timer = -C.LEVEL_BREAK
            self.state = "playing"
        elif self.state in ("won", "lost"):
            self.reset(self.level_index)
        elif self.state == 'menu':
            self.reset(min(self.progress['unlocked'] - 1, len(C.LEVELS) - 1))

    def _reap(self) -> None:
        for name in ("fruits", "monsters", "bullets", "rocks", "effects"):
            group = getattr(self, name)
            for e in group:
                if not e.alive and isinstance(e, Monster) and not e.escaped:
                    self.coins += e.reward
                    self.kills += 1
                    self.score += e.reward
            setattr(self, name, [e for e in group if e.alive])

    def _check_victory(self) -> None:
        waves = C.LEVELS[self.level_index]["waves"]
        last_level = self.level_index >= len(C.LEVELS) - 1
        if (self.state == "playing" and self.carrot.alive
                and last_level and self.wave_index >= len(waves) - 1
                and not self.spawn_queue and not self.monsters):
            self.state = "won"
            self._save_completion()

    def upgrade_tower(self):
        tower = self.inspected
        if self.state != 'playing' or self.guide_open or tower is None or not tower.alive:
            return False
        cost = tower.upgrade_cost
        if cost is None:
            self.show_notice('已升至三级')
            return False
        if self.coins < cost:
            self.show_notice(f'升级还差 {cost - self.coins} 金币')
            return False
        self.coins -= cost
        tower.upgrade()
        return True

    def sell_tower(self):
        tower = self.inspected
        if self.state != 'playing' or self.guide_open or tower is None or not tower.alive:
            return False
        self.coins += tower.sell_value
        self.fruits.remove(tower)
        tower.alive = False
        self.inspected = None
        return True

    # ----------------------------------------------------------------- input
    def handle_event(self, event: pygame.event.Event) -> None:
        if self.level_select_open:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_l):
                self.level_select_open = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.ui.back_rect.collidepoint(event.pos):
                    self.level_select_open = False
                    return
                for i in range(len(C.LEVELS)):
                    if self.ui.level_rect(i).collidepoint(event.pos) and i < self.progress['unlocked']:
                        self.reset(i)
                        break
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_i:
            self.guide_open = not self.guide_open
            return
        if self.guide_open:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                self.guide.tab = 'monsters' if self.guide.tab == 'towers' else 'towers'
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.guide.towers_rect.collidepoint(event.pos):
                self.guide.tab = 'towers'
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.guide.monsters_rect.collidepoint(event.pos):
                self.guide.tab = 'monsters'
            elif (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                    or event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                    and self.guide.close_rect.collidepoint(event.pos)):
                self.guide_open = False
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_l and self.state == 'menu':
                self.level_select_open = True
                return
            if event.key == pygame.K_ESCAPE:
                if self.state == "menu":
                    pygame.quit()
                    sys.exit(0)
                self.state = "paused" if self.state == "playing" else "menu"
                return
            if event.key == pygame.K_p:
                if self.state in ("playing", "paused"):
                    self.state = "paused" if self.state == "playing" else "playing"
                return
            if event.key == pygame.K_RETURN:
                self._continue()
                return
            if event.key == pygame.K_r and self.state in ("won", "lost"):
                self.reset(self.level_index)
                return
            if self.state != "playing":
                return
            if event.key == pygame.K_u:
                self.upgrade_tower()
            elif event.key == pygame.K_DELETE:
                self.sell_tower()
            elif event.key == pygame.K_TAB:
                self.speed_multiplier = 3 - self.speed_multiplier
            elif pygame.K_1 <= event.key <= pygame.K_8:
                idx = event.key - pygame.K_1
                if idx < len(C.SHOP_ORDER):
                    kind = C.SHOP_ORDER[idx]
                    if kind in self.available_towers:
                        self.selected, self.inspected = kind, None
                    else:
                        self.show_notice(f'第{C.FRUITS[kind]["unlock"]}关开放此塔')
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state != 'menu' and self.guide.button_rect.collidepoint(event.pos):
                self.guide_open = True
                return
            if self.state != "playing":
                if self.state == 'menu' and self.ui.level_button_rect.collidepoint(event.pos):
                    self.level_select_open = True
                elif self.ui.primary_rect.collidepoint(event.pos):
                    self._continue()
                elif self.ui.secondary_rect.collidepoint(event.pos):
                    if self.state == "menu":
                        self.guide_open = True
                    else:
                        self.state = "menu"
                return
            if self.ui.pause_rect.collidepoint(event.pos):
                self.state = "paused"
                return
            if self.ui.speed_rect.collidepoint(event.pos):
                self.speed_multiplier = 3 - self.speed_multiplier
                return
            if self.ui.upgrade_rect.collidepoint(event.pos):
                self.upgrade_tower()
                return
            if self.ui.sell_rect.collidepoint(event.pos):
                self.sell_tower()
                return
            self._on_click(event.pos)
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 3
                and self.state == "playing"):
            self.selected = None

    def _on_click(self, pos) -> None:
        if self.state != "playing" or self.guide_open:
            return
        for i, kind in enumerate(C.SHOP_ORDER):
            if self._card_rect(i).collidepoint(pos):
                if kind in self.available_towers:
                    self.selected, self.inspected = kind, None
                else:
                    self.show_notice(f'第{C.FRUITS[kind]["unlock"]}关开放此塔')
                return
        cell = self.field_cell(pos)
        if self.selected is None:
            self.inspected = self.fruit_at(*cell) if cell else None
            return
        reason = self.building_error(cell)
        if reason:
            self.show_notice(reason)
            return
        col, row = cell
        cost = C.FRUITS[self.selected]["cost"]
        self.coins -= cost
        self.fruits.append(FRUIT_CLASSES[self.selected](col, row))
        self.notice_timer = 0.0
        self.selected = None

    def field_cell(self, pos):
        col = int(pos[0] // C.TILE)
        row = int((pos[1] - C.HUD_H) // C.TILE)
        if 0 <= col < C.GRID_COLS and 0 <= row < C.GRID_ROWS:
            return col, row
        return None

    def building_error(self, cell):
        if cell is None:
            return "请在草地区域建造"
        if self.selected not in C.FRUITS:
            return "请先选择下方的防御塔卡片"
        if self.selected not in self.available_towers:
            return "本关尚未开放该防御塔"
        if cell == self.carrot_tile:
            return "这里是萝卜的位置，不能建造"
        if cell in self.path_cells:
            return "怪物道路上不能建造"
        if self.fruit_at(*cell):
            return "这里已经有防御塔了"
        shortfall = C.FRUITS[self.selected]['cost'] - self.coins
        if shortfall > 0:
            return f"金币不足，还差 {shortfall}"
        return ""

    def show_notice(self, message):
        self.notice = message
        self.notice_timer = 2.5

    # ------------------------------------------------------------------ draw
    def draw(self) -> None:
        if self.level_select_open:
            self.ui.draw_level_select()
        elif self.guide_open:
            self.guide.draw(self.screen, self.ui.time)
        elif self.state == 'menu':
            self.ui.draw_menu()
        else:
            self._draw_battle()
        pygame.display.flip()

    def _draw_battle(self) -> None:
        self.screen.fill(C.LEVELS[self.level_index]["grass"][0])
        self._draw_field()
        if self.state == "playing" and not self.guide_open:
            self.ui.draw_placement()
        for e in (self.fruits + self.monsters + self.bullets + self.rocks
                  + [self.carrot] + self.effects):
            e.draw(self.screen)
        self._draw_hud()
        self._draw_shop()
        if self.state == "playing" and not self.guide_open:
            self.ui.draw_battle_info()
        if self.state != "playing":
            self.ui.draw_overlay()
        else:
            self.ui.button(self.ui.pause_rect, "暂停 [P]")
        self.guide.draw_button(self.screen)

    def _draw_field(self) -> None:
        self.screen.blit(field_image(self.level_index), (0, C.HUD_H))

    def _card_rect(self, index: int) -> pygame.Rect:
        return pygame.Rect(12 + index % 4 * 124, C.SCREEN_H - C.SHOP_H + 36 + index // 4 * 64, 116, 58)

    def _draw_shop(self) -> None:
        self.ui.draw_shop()

    def _draw_hud(self) -> None:
        self.ui.draw_hud()

    # ------------------------------------------------------------------- run
    def run(self) -> None:
        running = True
        while running:
            dt = min(self.clock.tick(C.FPS) / 1000.0, 0.05)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.handle_event(event)
            self.update(dt)
            self.draw()
        pygame.quit()

"""Game loop and controller for the Plants vs Zombies MVP.

``Game`` is the single coordinator object: it owns the entity collections,
drives the wave schedule, resolves player input, and renders the HUD. The
entities never reach into each other directly; they ask the ``Game`` for
information such as "which plant is in front of me", which keeps the object
graph loosely coupled.

Run with:  python main.py
"""

from __future__ import annotations

import os
import random
import sys
from typing import Dict, List, Optional

import pygame

import config as C
import save as savegame
from assets import get_assets
from almanac import Almanac
from newplants import NEW_PLANT_CLASSES
from garden_ui import (GardenUI, mode_rect, level_rect, BACK_RECT,
                       CHOOSER_BACK_RECT, CHOOSER_START_RECT,
                       RESULT_PRIMARY_RECT, RESULT_MAP_RECT, PLANT_NAMES,
                       MAP_PREV_RECT, MAP_NEXT_RECT, SEED_PREV_RECT, SEED_NEXT_RECT,
                       PAUSE_BUTTON_RECT, PAUSE_RESUME_RECT, PAUSE_MENU_RECT,
                       SHOVEL_RECT)
from entities import (
    CherryBomb, Explosion, Jalapeno, LaneFire, Peashooter, Plant, PotatoMine,
    Projectile, Repeater, SnowPea, Sun, Sunflower, Threepeater, WallNut,
    Zombie, ZombieHead, cell_center,
)

PLANT_CLASSES = {
    "sunflower": Sunflower,
    "peashooter": Peashooter,
    "wallnut": WallNut,
    "snowpea": SnowPea,
    "cherrybomb": CherryBomb,
    "repeater": Repeater,
    "threepeater": Threepeater,
    "potatomine": PotatoMine,
    "jalapeno": Jalapeno,
}
PLANT_CLASSES.update(NEW_PLANT_CLASSES)


def load_font(size: int) -> pygame.font.Font:
    """A font that actually has CJK glyphs.

    pygame's bundled default font has no Chinese characters, so the retry
    hint rendered as empty boxes. Prefer a system CJK font when one exists.
    """
    for path in (r"C:\Windows\Fonts\msyh.ttc",
                 r"C:\Windows\Fonts\simhei.ttf",
                 r"C:\Windows\Fonts\simsun.ttc",
                 "/System/Library/Fonts/PingFang.ttc",
                 "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"):
        if os.path.exists(path):
            try:
                return pygame.font.Font(path, size)
            except Exception:
                pass
    return pygame.font.Font(None, size)


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.windowed_size = (C.SCREEN_W, C.SCREEN_H)
        self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        pygame.display.set_caption(C.TITLE)
        self.clock = pygame.time.Clock()
        # Use the bundled default font: pygame's SysFont enumerates the
        # Windows font registry, which is unreliable under some interpreters.
        self.font = load_font(24)
        self.big_font = load_font(56)
        self.small_font = load_font(20)
        self.assets = get_assets()
        self._bar_cache: dict = {}
        # Everything is drawn onto a fixed 800x600 canvas, then scaled to the
        # window, so fullscreen and resizing need no coordinate changes.
        self.canvas = pygame.Surface((C.SCREEN_W, C.SCREEN_H)).convert()
        self.ui = GardenUI(self, load_font)
        self.almanac = Almanac(self)
        self.fullscreen = False
        self._load_progress()

        self.reset()

    # ------------------------------------------------------------ progression
    def _load_progress(self) -> None:
        data = savegame.load()
        try:
            self.unlocked = max(0, min(int(data.get("unlocked", 0)), len(C.LEVELS) - 1))
        except (ValueError, TypeError):
            self.unlocked = 0
        earned = data.get("plants", [])
        if not isinstance(earned, list):
            earned = []
        self.owned_plants = list(C.START_PLANTS)
        for name in earned:
            if isinstance(name, str) and name in C.PLANTS and name not in self.owned_plants:
                self.owned_plants.append(name)
        # Legacy completed saves capped unlocked at 6. Earned rewards prove
        # completion and open the appended levels without replaying old ones.
        for index, reward in enumerate(C.LEVEL_REWARDS):
            if reward not in self.owned_plants:
                break
            self.unlocked = max(self.unlocked, min(index + 1, len(C.LEVELS) - 1))

    def _save_progress(self) -> None:
        savegame.save({"unlocked": self.unlocked, "plants": self.owned_plants})

    def adventure_completed(self) -> bool:
        return (self.unlocked == len(C.LEVELS) - 1
                and all(kind in self.owned_plants for kind in C.LEVEL_REWARDS))

    def start_adventure(self) -> None:
        if self.adventure_completed():
            self.state = "levelselect"
            return
        self.start_level(self.unlocked, "adventure")

    def _build_bar(self, n_cards: int) -> Optional[pygame.Surface]:
        """Wooden bar art, tiled wide enough for ``n_cards`` cards."""
        if n_cards in self._bar_cache:
            return self._bar_cache[n_cards]
        bar = self.assets.misc("bar")
        if bar is None:
            return None
        needed = C.CARD_X0 + n_cards * C.CARD_DX + 12
        if bar.get_width() >= needed:
            self._bar_cache[n_cards] = bar
            return bar
        # Extend only the seed area; preserve the sun icon and the right cap.
        extended = pygame.Surface((needed, bar.get_height())).convert_alpha()
        left, cap = C.CARD_X0 - 8, 9
        extended.blit(bar, (0, 0), (0, 0, left, bar.get_height()))
        middle = bar.subsurface((left, 0, bar.get_width() - left - cap, bar.get_height()))
        extended.blit(pygame.transform.smoothscale(middle,
                      (needed - left - cap, bar.get_height())), (left, 0))
        extended.blit(bar, (needed - cap, 0),
                      (bar.get_width() - cap, 0, cap, bar.get_height()))
        self._bar_cache[n_cards] = extended
        return extended

    # ------------------------------------------------------------ lifecycle
    def reset(self) -> None:
        self.plants: List[Plant] = []
        self.zombies: List[Zombie] = []
        self.projectiles: List[Projectile] = []
        self.suns: List[Sun] = []
        self.explosions: List[Explosion] = []
        self.effects: List[ZombieHead] = []

        self.level_index = 0
        self.level = C.LEVELS[0]
        self.rows = self.level["rows"]
        self.sun = self.level["sun"]
        self.selected: Optional[str] = None
        self.drag_kind: Optional[str] = None
        self.drag_pos = None
        self.sky_sun_timer = C.SKY_SUN_INTERVAL
        self.wave_index = 0
        self.wave_timer = 0.0
        self.spawn_queue: List[list] = []
        # Per-plant card cooldown: seconds of recharge remaining, keyed by kind.
        self.cooldowns: Dict[str, float] = {k: 0.0 for k in C.PLANTS}
        # menu | mode | levelselect | choosing | playing | won | lost
        self.state = "menu"
        self.mode = "adventure"      # adventure | select
        self.seeds: List[str] = []
        self.elapsed = 0.0
        self.level_page = self.unlocked // 7
        self.seed_page = 0
        self.frost_timer = 0.0
        self.notice = ""
        self.notice_timer = 0.0
        self._load_wave(0)

    def start_level(self, index: int, mode: str) -> None:
        """Begin ``index`` in the given mode, resetting the battlefield."""
        self.level_index = max(0, min(index, len(C.LEVELS) - 1))
        self.level = C.LEVELS[self.level_index]
        self.rows = self.level["rows"]
        self.mode = mode
        self.plants = []
        self.zombies = []
        self.projectiles = []
        self.suns = []
        self.explosions = []
        self.effects = []
        self.sun = self.level["sun"]
        self.selected = None
        self.drag_kind = None
        self.drag_pos = None
        self.sky_sun_timer = C.SKY_SUN_INTERVAL
        self.wave_index = 0
        self.wave_timer = 0.0
        self.elapsed = 0.0
        self.level_page = self.level_index // 7
        self.seed_page = 0
        self.frost_timer = 0.0
        self.notice = ""
        self.notice_timer = 0.0
        self.cooldowns = {k: 0.0 for k in C.PLANTS}
        self._load_wave(0)
        self.state = "choosing"
        self.seeds = [kind for kind in self.seeds
                      if kind in self.available_plants()][:self.required_seeds()]

    @property
    def waves(self):
        return self.level["waves"]

    def wave_progress(self) -> float:
        """0..1 progress through the whole level, for the flag bar.

        Each wave contributes an equal slice; within a wave the slice fills as
        its zombies are spawned and then cleared, so the bar advances smoothly
        and reaches 1.0 only once the last wave is wiped out.
        """
        n = len(self.waves)
        if n == 0:
            return 0.0
        if self.wave_index >= n:
            return 1.0
        total = sum(len(w) for w in self.waves) or 1
        done = sum(len(w) for w in self.waves[:self.wave_index])
        cur_total = len(self.waves[self.wave_index])
        if cur_total:
            spawned = cur_total - len(self.spawn_queue)
            alive = sum(1 for z in self.zombies if z.alive)
            killed = max(0, spawned - alive)
            # A wave is half "spawned" and half "cleared" so the bar keeps
            # moving even while the zombies are still walking in.
            done += 0.5 * spawned + 0.5 * killed
        return min(1.0, done / total)

    def available_plants(self) -> List[str]:
        """Plants the player owns, in shop order."""
        return [k for k in C.SHOP_ORDER if k in self.owned_plants]

    def seed_catalog(self):
        pool = self.available_plants()
        return pool + [kind for kind in C.SHOP_ORDER if kind not in pool]

    def visible_seeds(self):
        start = self.seed_page * 10
        return self.seed_catalog()[start:start + 10]

    def visible_levels(self):
        start = self.level_page * 7
        return range(start, min(start + 7, len(C.LEVELS)))

    def turn_page(self, direction):
        if self.state == "choosing":
            self.seed_page = max(0, min(self.seed_page + direction, (len(C.SHOP_ORDER) - 1) // 10))
        elif self.state == "levelselect":
            self.level_page = max(0, min(self.level_page + direction, (len(C.LEVELS) - 1) // 7))

    def _load_wave(self, index: int) -> None:
        if index >= len(self.waves):
            return
        # Authored lanes distinguish pincer attacks from concentrated pushes.
        # Two-item entries remain supported for older custom levels.
        self.spawn_queue = []
        offset = (index * 2) % self.rows
        for i, entry in enumerate(self.waves[index]):
            kind, delay = entry[:2]
            row = entry[2] if len(entry) == 3 else (offset + i) % self.rows
            self.spawn_queue.append([kind, delay, row])
        self.wave_timer = 0.0

    # --------------------------------------------------------------- helpers
    def lane_has_zombie(self, row: int, from_x: float) -> bool:
        return any(z.alive and not z.dying and z.row == row and z.x > from_x for z in self.zombies)

    def plant_in_front(self, row: int, zombie_x: float) -> Optional[Plant]:
        # A zombie only eats a plant it has actually walked up to. Without the
        # contact window below, a zombie would target the rightmost plant in
        # its lane from across the whole board and chew it down from range.
        best = None
        for p in self.plants:
            if (p.row == row and p.alive and getattr(p, "edible", True) and p.x <= zombie_x + 6
                    and zombie_x - p.x <= C.CELL_W * 0.55):
                if best is None or p.x > best.x:
                    best = p
        return best

    def plant_at(self, col: int, row: int) -> Optional[Plant]:
        for p in self.plants:
            if p.col == col and p.row == row and p.alive:
                return p
        return None

    def spawn_sun(self, x: float, y: float, amount: int, falls: bool = True) -> None:
        self.suns.append(Sun(x, y, amount, falls=falls))

    def on_zombie_reached_house(self) -> None:
        self.cancel_drag()
        self.state = "lost"

    # ---------------------------------------------------------------- update
    def update(self, dt: float) -> None:
        if self.state != "playing" or self.almanac.opened:
            return
        self.elapsed += dt
        self.frost_timer = max(0.0, self.frost_timer - dt)
        self.notice_timer = max(0.0, self.notice_timer - dt)

        # Tick down every card cooldown.
        for kind, t in self.cooldowns.items():
            if t > 0:
                self.cooldowns[kind] = max(0.0, t - dt)

        # Sky sun.
        if self.level.get("sky_sun", True):
            self.sky_sun_timer -= dt
            if self.sky_sun_timer <= 0:
                self.sky_sun_timer = C.SKY_SUN_INTERVAL
                x = random.uniform(C.LAWN_X + 25, C.LAWN_X + C.LAWN_W - 25)
                self.spawn_sun(x, -20, C.SKY_SUN_AMOUNT, falls=True)

        self._update_waves(dt)

        for group in (self.plants, self.zombies, self.projectiles,
                      self.suns, self.explosions, self.effects):
            for e in group:
                if e.alive:
                    e.update(dt, self)

        self._reap()
        self._check_victory()

    def _update_waves(self, dt: float) -> None:
        if self.wave_index >= len(self.waves):
            return
        self.wave_timer += dt
        pending = []
        for kind, delay, row in self.spawn_queue:
            if self.wave_timer >= delay:
                zombie = Zombie(C.SCREEN_W + 30, row, kind)
                zombie.speed *= self.level.get("speed_multiplier", 1.0)
                self.zombies.append(zombie)
            else:
                pending.append([kind, delay, row])
        self.spawn_queue = pending

        if not self.spawn_queue and not self.zombies:
            bonus = self.level.get("wave_bonus", 0)
            if bonus:
                self.sun += bonus
                self.show_notice(f"本波清空！补给 +{bonus} 阳光")
            # Wave cleared: advance after a short breather.
            self.wave_index += 1
            if self.wave_index < len(self.waves):
                self._load_wave(self.wave_index)
                self.wave_timer = -self.level.get("wave_break", C.WAVE_BREAK)

    def _reap(self) -> None:
        for name in ("plants", "zombies", "projectiles", "suns", "explosions",
                     "effects"):
            group = getattr(self, name)
            setattr(self, name, [e for e in group if e.alive])

    def _check_victory(self) -> None:
        if self.state == "playing" and self.wave_index >= len(self.waves) and not self.zombies:
            self.cancel_drag()
            self.state = "won"
            self._on_level_won()

    def _on_level_won(self) -> None:
        """Adventure mode unlocks the next level and grants a new plant."""
        if self.mode != "adventure":
            return
        if self.level_index + 1 > self.unlocked:
            self.unlocked = min(self.level_index + 1, len(C.LEVELS) - 1)
        if self.level_index < len(C.LEVEL_REWARDS):
            reward = C.LEVEL_REWARDS[self.level_index]
            if reward not in self.owned_plants:
                self.owned_plants.append(reward)
        self._save_progress()

    def _continue_result(self) -> None:
        """Advance an adventure win; retries keep their original mode/level."""
        if self.state == "won" and self.mode == "adventure":
            next_index = self.level_index + 1
            if next_index < len(C.LEVELS):
                self.start_level(next_index, "adventure")
            else:
                self.state = "levelselect"
            return
        if self.state in ("won", "lost"):
            self.start_level(self.level_index, self.mode)

    def _on_result_click(self, pos) -> None:
        if RESULT_PRIMARY_RECT.collidepoint(pos):
            self._continue_result()
        elif RESULT_MAP_RECT.collidepoint(pos):
            self.state = "levelselect"

    def _result_action_label(self) -> str:
        if self.state == "won" and self.mode == "adventure":
            if self.level_index + 1 < len(C.LEVELS):
                return f"下一关 · {C.LEVELS[self.level_index + 1]['id']}"
            return "冒险通关！返回地图"
        return "重新挑战" if self.state == "lost" else "再次挑战"

    # ----------------------------------------------------------------- input
    def toggle_fullscreen(self) -> None:
        self.cancel_drag()
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.windowed_size,
                                                  pygame.RESIZABLE)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.WINDOWFOCUSLOST:
            self.cancel_drag()
            return
        if event.type == pygame.VIDEORESIZE and not self.fullscreen:
            self.cancel_drag()
            self.windowed_size = (max(400, event.w), max(300, event.h))
            self.screen = pygame.display.set_mode(self.windowed_size,
                                                  pygame.RESIZABLE)
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_i:
            self.cancel_drag()
            self.almanac.opened = not self.almanac.opened
            return
        if self.almanac.opened:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_f:
                self.toggle_fullscreen()
            else:
                pos = self._to_canvas(event.pos) if hasattr(event, 'pos') else None
                self.almanac.handle_event(event, pos)
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
            self.cancel_drag()
            if self.state in ("playing", "paused"):
                self.state = "paused" if self.state == "playing" else "playing"
            return
        if self.state == "paused":
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    self.state = "playing"
                elif event.key == pygame.K_f:
                    self.toggle_fullscreen()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = self._to_canvas(event.pos)
                if PAUSE_RESUME_RECT.collidepoint(pos):
                    self.state = "playing"
                elif PAUSE_MENU_RECT.collidepoint(pos):
                    self.state = "menu"
                    self.selected = None
            return

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT) and self.state in ("choosing", "levelselect"):
                self.turn_page(-1 if event.key == pygame.K_LEFT else 1)
                return
            if event.key == pygame.K_ESCAPE:
                if self.drag_kind is not None:
                    self.cancel_drag()
                    return
                if self.fullscreen:
                    self.toggle_fullscreen()
                    return
                if self.state != "menu":
                    self.state = "menu"
                    self.selected = None
                    return
                pygame.quit()
                sys.exit(0)
            if event.key == pygame.K_f:
                self.toggle_fullscreen()
                return
            if event.key == pygame.K_r and self.state in ("won", "lost"):
                self.start_level(self.level_index, self.mode)
                return
            if event.key == pygame.K_RETURN and self.state in ("won", "lost"):
                self._continue_result()
                return
            if event.key == pygame.K_RETURN and self.state == "menu":
                self.start_adventure()
                return
            if event.key == pygame.K_RETURN and self.state == "choosing":
                if len(self.seeds) == self.required_seeds():
                    self.state = "playing"
            if self.state == "choosing" and event.key == pygame.K_a:
                pool = self.available_plants()
                self.seeds = pool[:C.MAX_SEEDS]
            if self.state == "playing":
                keys = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                        pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8)
                if event.key in keys:
                    idx = keys.index(event.key)
                    if idx < len(self.seeds):
                        self.cancel_drag()
                        self.selected = self.seeds[idx]

        if event.type == pygame.MOUSEMOTION and self.drag_kind is not None:
            if hasattr(event, 'buttons') and not event.buttons[0]:
                self.cancel_drag()
            else:
                self.drag_pos = self._to_canvas(event.pos)
            return
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.drag_kind is not None:
                self.finish_drag(self._to_canvas(event.pos))
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state == "menu":
                self._on_mode_click(self._to_canvas(event.pos))
                return
            if self.state == "levelselect":
                self._on_levelselect_click(self._to_canvas(event.pos))
                return
            if self.state in ("won", "lost"):
                self._on_result_click(self._to_canvas(event.pos))
                return
            if self.state == "choosing":
                self._on_choose_click(self._to_canvas(event.pos))
                return
            if self.state == "playing":
                if self.drag_kind is not None:
                    return
                pos = self._to_canvas(event.pos)
                if SHOVEL_RECT.collidepoint(pos):
                    self.selected = None
                    self.notice_timer = 0.0
                    self.drag_kind, self.drag_pos = 'shovel', pos
                    return
                for i, kind in enumerate(self.seeds):
                    if self._card_rect(i).collidepoint(pos):
                        self.begin_plant_drag(kind, pos)
                        return
            self._on_click(self._to_canvas(event.pos))

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            self.cancel_drag()
            self.selected = None

    def cancel_drag(self):
        if self.drag_kind is not None:
            self.selected = None
        self.drag_kind = None
        self.drag_pos = None

    def card_error(self, kind):
        remaining = self.cooldowns.get(kind, 0.0)
        if remaining > 0:
            return f"卡片冷却中，还需 {remaining:.1f} 秒"
        cost = C.PLANTS[kind]['cost']
        if self.sun < cost:
            return f"阳光不足，还差 {cost - self.sun}"
        return ""

    def begin_plant_drag(self, kind, pos):
        self.cancel_drag()
        self.selected = None
        if kind not in self.seeds:
            return
        reason = self.card_error(kind)
        if reason:
            self.show_notice(reason)
            return
        self.selected = self.drag_kind = kind
        self.drag_pos = pos
        self.notice_timer = 0.0

    def finish_drag(self, pos):
        kind = self.drag_kind
        self.drag_kind = None
        self.drag_pos = None
        if self.state != 'playing' or self.almanac.opened:
            self.selected = None
            return
        if kind == 'shovel':
            self.selected = None
            cell = self.lawn_cell(pos)
            plant = self.plant_at(*cell) if cell else None
            if plant:
                plant.alive = False
                self._reap()
                self.show_notice(f"已铲除{PLANT_NAMES[plant.kind]}，不返还阳光")
            return
        if kind in self.seeds:
            self.selected = kind
            self._plant_selected(pos)
        self.selected = None

    def _on_click(self, pos) -> None:
        if self.state != "playing" or self.almanac.opened:
            return
        if PAUSE_BUTTON_RECT.collidepoint(pos):
            self.cancel_drag()
            self.state = "paused"
            return
        # 1) Collect a sun if one was clicked.
        for s in reversed(self.suns):
            if s.alive and s.contains(pos):
                self.sun += s.amount
                s.alive = False
                return

        # 2) A click on the card bar selects a plant.
        for i, kind in enumerate(self.seeds):
            if self._card_rect(i).collidepoint(pos):
                self.selected = kind
                return

        # 3) Otherwise try to place the selected plant.
        self._plant_selected(pos)

    def _plant_selected(self, pos):
        if self.state != 'playing' or self.almanac.opened:
            return
        if self.selected is None:
            return
        cell = self.lawn_cell(pos)
        reason = self.planting_error(cell)
        if reason:
            self.show_notice(reason)
            return
        col, row = cell
        cost = C.PLANTS[self.selected]["cost"]
        self.sun -= cost
        self.cooldowns[self.selected] = C.PLANTS[self.selected]["recharge"]
        self.plants.append(PLANT_CLASSES[self.selected](col, row))
        # Set mushroom sleep immediately, including the placement preview frame.
        self.plants[-1].update(0.0, self)
        mushroom_asleep = self.plants[-1].sleeping
        self.selected = None
        self.notice_timer = 0.0
        if mushroom_asleep:
            self.show_notice("蘑菇白天会睡觉，请在夜间使用")

    def show_notice(self, message: str) -> None:
        self.notice = message
        self.notice_timer = 2.5

    def lawn_cell(self, pos):
        """Shared integer hit test for placement and the hover preview."""
        col = int((pos[0] - C.LAWN_X) // C.CELL_W)
        row = int((pos[1] - C.LAWN_Y) // C.CELL_H)
        if 0 <= col < C.GRID_COLS and 0 <= row < self.rows:
            return col, row
        return None

    def planting_error(self, cell) -> str:
        if cell is None:
            return "请种在草坪格子内"
        if self.selected not in self.seeds:
            return "请先选择上方的植物卡片"
        if self.plant_at(*cell) is not None:
            return "这里已经种了植物"
        return self.card_error(self.selected)

    # ------------------------------------------------------ seed chooser
    def _to_canvas(self, pos):
        """Map a window pixel to the fixed 800x600 canvas."""
        rect = self.viewport()
        return ((pos[0] - rect.x) * C.SCREEN_W / rect.w,
                (pos[1] - rect.y) * C.SCREEN_H / rect.h)

    def viewport(self):
        w, h = self.screen.get_size()
        scale = min(w / C.SCREEN_W, h / C.SCREEN_H)
        sw, sh = int(C.SCREEN_W * scale), int(C.SCREEN_H * scale)
        return pygame.Rect((w - sw) // 2, (h - sh) // 2, sw, sh)

    def _chooser_origin(self):
        """Panel top-left, and the card grid origin inside it."""
        return (C.CHOOSER_PANEL_X, C.CHOOSER_PANEL_Y,
                C.CHOOSER_GRID_X, C.CHOOSER_GRID_Y)

    def required_seeds(self) -> int:
        return min(C.MAX_SEEDS, len(self.available_plants()))

    def _chooser_rect(self, index: int) -> pygame.Rect:
        """Grid cell of the index-th plant in the pool."""
        _, _, gx, gy = self._chooser_origin()
        col, row = index % C.CHOOSER_COLS, index // C.CHOOSER_COLS
        return pygame.Rect(gx + col * C.CHOOSER_DX,
                           gy + row * C.CHOOSER_DY,
                           C.CHOOSER_CARD_W, C.CHOOSER_CARD_H)

    def _seed_slot_rect(self, index: int) -> pygame.Rect:
        """A slot in the top preview strip (the bar you fill up)."""
        return pygame.Rect(C.CARD_X0 + index * C.CARD_DX, C.CARD_Y,
                           C.CHOOSER_CARD_W, C.CHOOSER_CARD_H)

    def _on_choose_click(self, pos) -> None:
        if SEED_PREV_RECT.collidepoint(pos):
            self.turn_page(-1)
            return
        if SEED_NEXT_RECT.collidepoint(pos):
            self.turn_page(1)
            return
        if CHOOSER_BACK_RECT.collidepoint(pos):
            self.state = "levelselect"
            return
        # Early levels need every owned plant, up to the eight-slot capacity.
        if len(self.seeds) == self.required_seeds() and self._start_button_rect().collidepoint(pos):
            self.state = "playing"
            return
        # Remove a card from the preview strip.
        for i in range(len(self.seeds)):
            if self._seed_slot_rect(i).collidepoint(pos):
                self.seeds.pop(i)
                return
        # Add a plant from the pool.
        for i, kind in enumerate(self.visible_seeds()):
            if not self._chooser_rect(i).collidepoint(pos):
                continue
            if kind not in self.available_plants():
                return
            if kind in self.seeds:
                self.seeds.remove(kind)
            elif len(self.seeds) < C.MAX_SEEDS:
                self.seeds.append(kind)
            return

    def _start_button_rect(self) -> pygame.Rect:
        return CHOOSER_START_RECT.copy()

    # ------------------------------------------------- mode / level select
    def _mode_rect(self, which: int) -> pygame.Rect:
        return mode_rect(which)

    def _on_mode_click(self, pos) -> None:
        if self.almanac.menu_rect.collidepoint(pos):
            self.almanac.opened = True
            return
        if self._mode_rect(0).collidepoint(pos):
            self.start_adventure()
        elif self._mode_rect(1).collidepoint(pos):
            self.mode = "select"
            self.level_page = self.unlocked // 7
            self.state = "levelselect"

    def _level_rect(self, index: int) -> pygame.Rect:
        return level_rect(index)

    def _on_levelselect_click(self, pos) -> None:
        if MAP_PREV_RECT.collidepoint(pos):
            self.turn_page(-1)
            return
        if MAP_NEXT_RECT.collidepoint(pos):
            self.turn_page(1)
            return
        if BACK_RECT.collidepoint(pos):
            self.state = "menu"
            return
        for i in self.visible_levels():
            if self._level_rect(i).collidepoint(pos):
                # Select mode lets the player jump straight to any level they
                # have already unlocked; locked ones are ignored.
                if i <= self.unlocked:
                    self.mode = "select"
                    self.start_level(i, "select")
                return

    def _draw_chooser(self) -> None:
        self.ui.draw_chooser()

    # ----------------------------------------------------- mode / level UI
    def _draw_levelselect(self) -> None:
        self.ui.draw_levels()

    # ------------------------------------------------------------------ draw
    def draw(self) -> None:
        if self.almanac.opened:
            self.almanac.draw()
            self._present()
            return
        if self.state == "menu":
            self._draw_menu()
        elif self.state == "levelselect":
            self._draw_levelselect()
        elif self.state == "choosing":
            self._draw_chooser()
        else:
            self.canvas.fill(C.COL_SKY)
            self._draw_lawn()
            if self.state == "playing":
                self.ui.draw_placement()
            for e in (self.plants + self.zombies + self.projectiles + self.suns
                      + self.explosions + self.effects):
                e.draw(self.canvas)
            if self.frost_timer > 0:
                frost = pygame.Surface((C.SCREEN_W, C.SCREEN_H), pygame.SRCALPHA)
                frost.fill((160, 225, 255, int(80 * self.frost_timer / 0.7)))
                self.canvas.blit(frost, (0, 0))
            self._draw_shop()
            self._draw_hud()
            if self.state == "playing":
                self.ui.draw_battle_info()
                self.ui.draw_drag_cursor()
            if self.state == "paused":
                self.ui.draw_pause()
            elif self.state != "playing":
                self._draw_overlay()
        self._present()

    def _present(self) -> None:
        """Scale the fixed canvas into the (possibly fullscreen) window."""
        rect = self.viewport()
        self.screen.fill((0, 0, 0))
        self.screen.blit(pygame.transform.smoothscale(self.canvas, rect.size), rect)
        pygame.display.flip()

    def _draw_menu(self) -> None:
        self.ui.draw_menu()

    def _draw_lawn(self) -> None:
        bg = self.assets.background(self.level["bg"])
        if bg is not None:
            self.canvas.blit(bg, (0, 0))
            return
        # Fallback checkerboard if the art pack is missing.
        for row in range(self.rows):
            for col in range(C.GRID_COLS):
                x, y = C.LAWN_X + col * C.CELL_W, C.LAWN_Y + row * C.CELL_H
                col_a = C.COL_LAWN_A if (row + col) % 2 == 0 else C.COL_LAWN_B
                pygame.draw.rect(self.canvas, col_a, (x, y, C.CELL_W, C.CELL_H))
                pygame.draw.rect(self.canvas, C.COL_GRID, (x, y, C.CELL_W, C.CELL_H), 1)

    def _card_rect(self, index: int) -> pygame.Rect:
        x = C.CARD_X0 + index * C.CARD_DX
        return pygame.Rect(x, C.CARD_Y, 55, 74)

    def _draw_shop(self) -> None:
        self.ui.draw_shop()

    def _draw_hud(self) -> None:
        self.ui.draw_sun_value()
        self._draw_wave_bar()

    def _draw_wave_bar(self) -> None:
        self.ui.draw_wave()

    def _draw_overlay(self) -> None:
        art = self.assets.misc("victory" if self.state == "won" else "lose")
        self.canvas.fill((0, 0, 0))
        cx = C.SCREEN_W // 2
        msg = "战斗胜利！" if self.state == "won" else "僵尸吃掉了你的脑子！"
        if art is not None:
            # The original victory / lose art already carries its own banner.
            # Scale it to fill the window so no battlefield shows around it.
            scaled = pygame.transform.smoothscale(art, (C.SCREEN_W, C.SCREEN_H))
            self.canvas.blit(scaled, (0, 0))
            if self.state == "won":
                self._draw_result_summary(cx)
        else:
            overlay = pygame.Surface((C.SCREEN_W, C.SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            self.canvas.blit(overlay, (0, 0))
            color = (120, 255, 140) if self.state == "won" else (255, 140, 140)
            text = self.big_font.render(msg, True, color)
            self.canvas.blit(text, text.get_rect(center=(cx, C.SCREEN_H // 2 - 20)))
        self.ui.button(RESULT_PRIMARY_RECT, self._result_action_label(), size=23)
        self.ui.button(RESULT_MAP_RECT, "选关地图", size=18)
        sub = self.ui.font(16).render("Enter 继续  ·  R 重试本关  ·  Esc 返回庭院", True, (255, 255, 255))
        bar = pygame.Surface((sub.get_width() + 24, sub.get_height() + 12),
                             pygame.SRCALPHA)
        bar.fill((0, 0, 0, 150))
        rect = bar.get_rect(center=(cx, C.SCREEN_H - 23))
        self.canvas.blit(bar, rect)
        self.canvas.blit(sub, sub.get_rect(center=rect.center))

    def _draw_result_summary(self, cx: int) -> None:
        """Fill the original panel's empty middle with this match's result."""
        reward_line = "选关挑战完成 · 返回地图可再次挑战"
        if self.mode == "adventure":
            if self.level_index + 1 < len(C.LEVELS):
                reward_line = f"解锁植物：{self._reward_name()} · 下一关 {C.LEVELS[self.level_index + 1]['id']}"
            else:
                reward_line = f"解锁植物：{self._reward_name()} · 全部关卡通关！"
        lines = [
            (f"关卡 {self.level['id']}　抵御波次 {len(self.waves)} / {len(self.waves)}",
             26, (60, 40, 20)),
            (f"剩余阳光　{self.sun}", 26, (60, 40, 20)),
            (f"存活植物　{len(self.plants)}", 26, (60, 40, 20)),
            (f"用时　{self.elapsed:0.0f} 秒", 26, (60, 40, 20)),
            (reward_line, 22, (150, 40, 40)),
        ]
        # The panel's beige interior sits a little below centre, so start the
        # block low enough that no line overlaps the banner's leaf decoration.
        y = C.SCREEN_H // 2 + 20
        for text, size, color in lines:
            font = load_font(size)
            surf = font.render(text, True, color)
            self.canvas.blit(surf, surf.get_rect(center=(cx, y)))
            y += 40

    def _reward_name(self) -> str:
        if self.level_index < len(C.LEVEL_REWARDS):
            return PLANT_NAMES[C.LEVEL_REWARDS[self.level_index]]
        return "—"

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

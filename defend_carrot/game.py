"""Game loop and controller for the Defend the Carrot MVP.

``Game`` owns the entity collections, the path, the wave schedule, the coin
economy and the HUD. Entities only call back into it for shared facts such
as the path or "damage the carrot", which keeps them decoupled.

Run with:  python main.py
"""

from __future__ import annotations

import sys
from typing import List, Optional, Tuple

import pygame

import config as C
from entities import (
    Apple, Bat, Bullet, Carrot, Effect, Fruit, Golem, Melon, Monster, Orange,
    Rock, RockThrower, Slime, tile_center,
)

FRUIT_CLASSES = {"apple": Apple, "orange": Orange, "melon": Melon}
MONSTER_CLASSES = {
    "slime": Slime, "bat": Bat, "golem": Golem, "thrower": RockThrower,
}


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((C.SCREEN_W, C.SCREEN_H))
        pygame.display.set_caption(C.TITLE)
        self.clock = pygame.time.Clock()
        # pygame's default bundled font avoids SysFont's Windows registry scan.
        self.font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 56)
        self.small_font = pygame.font.Font(None, 20)
        self.reset()

    # ------------------------------------------------------------ lifecycle
    def reset(self) -> None:
        self.fruits: List[Fruit] = []
        self.monsters: List[Monster] = []
        self.bullets: List[Bullet] = []
        self.rocks: List[Rock] = []
        self.effects: List[Effect] = []

        self.carrot = Carrot(*C.CARROT_TILE)
        self.path: List[Tuple[float, float]] = [
            tile_center(c, r) for (c, r) in C.PATH
        ]

        self.coins = C.START_COINS
        self.selected: Optional[str] = None
        self.level_index = 0
        self.wave_index = 0
        self.wave_timer = 0.0
        self.spawn_queue: List[list] = []
        self.state = "playing"       # playing | won | lost
        self.elapsed = 0.0
        self.kills = 0
        self._load_level(0)

    def path_px(self, seg: int, frac: float):
        return self.path[seg]

    def _load_level(self, index: int) -> None:
        if index >= len(C.LEVELS):
            return
        self.level_index = index
        self.wave_index = 0
        self._load_wave(0)
        self.wave_timer = -2.0       # short grace before the first wave

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
        if (col, row) in C.PATH_CELLS:
            return False
        if (col, row) == C.CARROT_TILE:
            return False
        return self.fruit_at(col, row) is None

    def damage_carrot(self, amount: float) -> None:
        self.carrot.take_damage(amount)
        if not self.carrot.alive:
            self.state = "lost"

    # ---------------------------------------------------------------- update
    def update(self, dt: float) -> None:
        if self.state != "playing":
            return
        self.elapsed += dt
        self._update_waves(dt)
        for group in (self.fruits, self.monsters, self.bullets,
                      self.rocks, self.effects):
            for e in group:
                e.update(dt, self)
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

        if not self.spawn_queue and not self.monsters:
            if self.wave_index + 1 < len(waves):
                self._load_wave(self.wave_index + 1)
                self.wave_timer = -C.WAVE_BREAK
            else:
                self._advance_level()

    def _advance_level(self) -> None:
        if self.level_index + 1 < len(C.LEVELS):
            self._load_level(self.level_index + 1)
            self.wave_timer = -C.LEVEL_BREAK
            self.state = "playing"

    def _reap(self) -> None:
        for name in ("fruits", "monsters", "bullets", "rocks", "effects"):
            group = getattr(self, name)
            for e in group:
                if not e.alive and isinstance(e, Monster):
                    self.coins += e.reward
                    self.kills += 1
            setattr(self, name, [e for e in group if e.alive])

    def _check_victory(self) -> None:
        waves = C.LEVELS[self.level_index]["waves"]
        last_level = self.level_index >= len(C.LEVELS) - 1
        if (last_level and self.wave_index >= len(waves) - 1
                and not self.spawn_queue and not self.monsters):
            self.state = "won"

    # ----------------------------------------------------------------- input
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit(0)
            if event.key == pygame.K_r and self.state != "playing":
                self.reset()
            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                idx = event.key - pygame.K_1
                if idx < len(C.SHOP_ORDER):
                    self.selected = C.SHOP_ORDER[idx]
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state != "playing":
                self.reset()
                return
            self._on_click(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            self.selected = None

    def _on_click(self, pos) -> None:
        if self.selected is None:
            return
        col = pos[0] // C.TILE
        row = (pos[1] - C.HUD_H) // C.TILE
        if not self.can_build(col, row):
            return
        cost = C.FRUITS[self.selected]["cost"]
        if self.coins < cost:
            return
        self.coins -= cost
        self.fruits.append(FRUIT_CLASSES[self.selected](col, row))
        self.selected = None

    # ------------------------------------------------------------------ draw
    def draw(self) -> None:
        self.screen.fill(C.COL_GRASS)
        self._draw_field()
        for e in (self.fruits + self.monsters + self.bullets + self.rocks
                  + [self.carrot] + self.effects):
            e.draw(self.screen)
        self._draw_hud()
        self._draw_shop()
        if self.state != "playing":
            self._draw_overlay()
        pygame.display.flip()

    def _draw_field(self) -> None:
        for row in range(C.GRID_ROWS):
            for col in range(C.GRID_COLS):
                if (col, row) in C.PATH_CELLS:
                    continue
                base = C.COL_GRASS if (row + col) % 2 == 0 else C.COL_GRASS_B
                x, y = col * C.TILE, C.HUD_H + row * C.TILE
                pygame.draw.rect(self.screen, base, (x, y, C.TILE, C.TILE))
        # Path.
        pts = [(int(x), int(y)) for (x, y) in self.path]
        pygame.draw.lines(self.screen, C.COL_PATH_EDGE, False, pts, C.TILE + 4)
        pygame.draw.lines(self.screen, C.COL_PATH, False, pts, C.TILE - 6)

    def _card_rect(self, index: int) -> pygame.Rect:
        x = 12 + index * 150
        return pygame.Rect(x, C.SCREEN_H - C.SHOP_H + 8, 140, C.SHOP_H - 18)

    def _draw_shop(self) -> None:
        pygame.draw.rect(self.screen, C.COL_SHOP_BG,
                         (0, C.SCREEN_H - C.SHOP_H, C.SCREEN_W, C.SHOP_H))
        for i, kind in enumerate(C.SHOP_ORDER):
            spec = C.FRUITS[kind]
            rect = self._card_rect(i)
            affordable = self.coins >= spec["cost"]
            col = (C.COL_CARD_SEL if self.selected == kind
                   else C.COL_CARD if affordable else C.COL_CARD_OFF)
            pygame.draw.rect(self.screen, col, rect, border_radius=8)
            pygame.draw.rect(self.screen, (70, 70, 70), rect, 2, border_radius=8)
            pygame.draw.circle(self.screen, spec["color"],
                               (rect.x + 26, rect.y + 34), 17)
            name = self.small_font.render(f"{i + 1}. {spec['label']}", True, C.COL_TEXT)
            cost = self.small_font.render(f"{spec['cost']} coins", True, (150, 90, 0))
            hp = self.small_font.render(f"HP {spec['hp']}", True, (90, 90, 90))
            self.screen.blit(name, (rect.x + 48, rect.y + 12))
            self.screen.blit(cost, (rect.x + 48, rect.y + 32))
            self.screen.blit(hp, (rect.x + 48, rect.y + 50))

    def _draw_hud(self) -> None:
        pygame.draw.rect(self.screen, C.COL_HUD_BG, (0, 0, C.SCREEN_W, C.HUD_H))
        coin = self.font.render(f"Coins: {self.coins}", True, (255, 230, 120))
        self.screen.blit(coin, (14, 16))
        level = C.LEVELS[self.level_index]
        waves = len(level["waves"])
        info = self.font.render(
            f"{level['name']}   Wave {min(self.wave_index + 1, waves)}/{waves}",
            True, (240, 240, 240))
        self.screen.blit(info, (190, 8))
        kills = self.small_font.render(f"Kills: {self.kills}", True, (220, 220, 220))
        self.screen.blit(kills, (190, 34))
        # Carrot HP bar.
        bar_w = 180
        x = C.SCREEN_W - bar_w - 16
        pygame.draw.rect(self.screen, C.COL_HP_BG, (x, 20, bar_w, 16), border_radius=6)
        frac = max(0.0, self.carrot.hp / self.carrot.max_hp)
        pygame.draw.rect(self.screen, C.COL_HP_FG,
                         (x, 20, int(bar_w * frac), 16), border_radius=6)
        label = self.small_font.render("Carrot HP", True, (240, 240, 240))
        self.screen.blit(label, (x, 2))

    def _draw_overlay(self) -> None:
        overlay = pygame.Surface((C.SCREEN_W, C.SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))
        msg = "LEVEL CLEAR!" if self.state == "won" else "THE CARROT FELL!"
        color = (140, 255, 150) if self.state == "won" else (255, 130, 130)
        text = self.big_font.render(msg, True, color)
        self.screen.blit(text, text.get_rect(center=(C.SCREEN_W // 2, C.SCREEN_H // 2 - 20)))
        sub = self.font.render("Click or press R to play again", True, (240, 240, 240))
        self.screen.blit(sub, sub.get_rect(center=(C.SCREEN_W // 2, C.SCREEN_H // 2 + 40)))

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

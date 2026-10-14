"""Entity hierarchy for the Defend the Carrot MVP.

This mirrors the Plants vs Zombies object model so the two experiments can
be compared in the report:

    Entity                     (abstract base: position, update/draw contract)
    ├── Fruit                  (abstract tower: hp, range, on_tick hook)
    │   ├── Apple              (balanced single-target shooter)
    │   ├── Orange             (cheap, fast, short range)
    │   └── Melon              (slow, heavy splash damage)
    ├── Monster                (abstract walker along the shared PATH)
    │   ├── Slime              (baseline)
    │   ├── Bat                (fast, fragile)
    │   ├── Golem              (slow tank)
    │   └── RockThrower        (ranged: damages fruits from a distance)
    ├── Bullet                 (projectile fired by a Fruit)
    ├── Rock                   (projectile thrown by a RockThrower)
    ├── Carrot                 (the objective; has hit points)
    └── Effect                 (short lived visual, e.g. splash)

Only ``update`` and ``draw`` are called by the game loop, so a new fruit or
monster is added by writing a subclass plus one config entry.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING

import pygame

import config as C

if TYPE_CHECKING:
    from game import Game


def tile_center(col: int, row: int):
    return col * C.TILE + C.TILE // 2, C.HUD_H + row * C.TILE + C.TILE // 2


class Entity(ABC):
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.alive = True

    @abstractmethod
    def update(self, dt: float, game: "Game") -> None:
        ...

    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None:
        ...


# -------------------------------------------------------------------- fruits
class Fruit(Entity):
    """Abstract tower. Sits on a tile and has hit points."""

    def __init__(self, col: int, row: int, kind: str) -> None:
        cx, cy = tile_center(col, row)
        super().__init__(cx, cy)
        self.col = col
        self.row = row
        self.kind = kind
        self.spec = C.FRUITS[kind]
        self.hp = float(self.spec["hp"])
        self.max_hp = float(self.spec["hp"])
        self.damage = float(self.spec["damage"])
        self.interval = float(self.spec["interval"])
        self.rng = float(self.spec["rng"]) * C.TILE
        self.color = self.spec["color"]
        self.label = self.spec["label"]
        self.timer = 0.3
        self._hit_flash = 0.0

    def take_damage(self, amount: float) -> None:
        self.hp -= amount
        self._hit_flash = 0.12
        if self.hp <= 0:
            self.alive = False

    def update(self, dt: float, game: "Game") -> None:
        self._hit_flash = max(0.0, self._hit_flash - dt)
        target = self.acquire(game)
        if target is None:
            return
        self.timer -= dt
        if self.timer <= 0:
            self.timer = self.interval
            self.fire(target, game)

    def acquire(self, game: "Game") -> Optional["Monster"]:
        """Closest monster inside range that is not already past the carrot."""
        best, best_d = None, self.rng
        for m in game.monsters:
            if not m.alive:
                continue
            d = math.hypot(m.x - self.x, m.y - self.y)
            if d <= best_d:
                best, best_d = m, d
        return best

    @abstractmethod
    def fire(self, target: "Monster", game: "Game") -> None:
        ...

    def _body_color(self):
        return (255, 255, 255) if self._hit_flash > 0 else self.color

    def draw(self, surface: pygame.Surface) -> None:
        cx, cy = int(self.x), int(self.y)
        pygame.draw.circle(surface, self._body_color(), (cx, cy), 15)
        pygame.draw.circle(surface, (40, 70, 40), (cx, cy), 15, 2)
        self.draw_detail(surface)
        if self.hp < self.max_hp:
            w = 30
            x, y = cx - w // 2, cy - 24
            pygame.draw.rect(surface, C.COL_HP_BG, (x, y, w, 4))
            pygame.draw.rect(surface, C.COL_HP_FG,
                             (x, y, int(w * self.hp / self.max_hp), 4))

    def draw_detail(self, surface: pygame.Surface) -> None:
        ...


class Apple(Fruit):
    def __init__(self, col, row):
        super().__init__(col, row, "apple")

    def fire(self, target, game):
        game.bullets.append(Bullet(self.x, self.y, target, self.damage,
                                   (255, 210, 210)))

    def draw_detail(self, surface):
        cx, cy = int(self.x), int(self.y)
        pygame.draw.line(surface, (70, 110, 50), (cx, cy - 14), (cx + 4, cy - 20), 2)
        pygame.draw.circle(surface, (120, 180, 90), (cx + 7, cy - 19), 4)


class Orange(Fruit):
    def __init__(self, col, row):
        super().__init__(col, row, "orange")

    def fire(self, target, game):
        game.bullets.append(Bullet(self.x, self.y, target, self.damage,
                                   (255, 230, 170)))

    def draw_detail(self, surface):
        cx, cy = int(self.x), int(self.y)
        pygame.draw.circle(surface, (255, 200, 120), (cx - 4, cy - 3), 4)
        pygame.draw.circle(surface, (255, 200, 120), (cx + 4, cy + 3), 4)


class Melon(Fruit):
    """Slow but hits every monster near the impact point."""

    SPLASH = 1.6 * C.TILE

    def __init__(self, col, row):
        super().__init__(col, row, "melon")

    def fire(self, target, game):
        game.bullets.append(Bullet(self.x, self.y, target, self.damage,
                                   (200, 255, 200), splash=self.SPLASH))

    def draw_detail(self, surface):
        cx, cy = int(self.x), int(self.y)
        pygame.draw.arc(surface, (40, 120, 60),
                        pygame.Rect(cx - 14, cy - 14, 28, 28), 0, math.pi, 3)


# ------------------------------------------------------------------ monsters
class Monster(Entity):
    """Walks along ``game.path`` toward the carrot."""

    def __init__(self, kind: str, game: "Game") -> None:
        spec = C.MONSTERS[kind]
        self.spec = spec
        self.kind = kind
        self.hp = float(spec["hp"])
        self.max_hp = float(spec["hp"])
        self.speed_tiles = float(spec["speed"])
        self.reward = int(spec["reward"])
        self.bite = float(spec["bite"])
        self.color = spec["color"]
        self.label = spec["label"]
        self.seg = 0
        self.t = 0.0
        self._hit_flash = 0.0
        self.target_fruit: Optional[Fruit] = None
        self.throw_timer = float(spec.get("throw_interval", 0.0))
        # Start just off the left edge of the field.
        sx, sy = game.path_px(0, 0.0)
        super().__init__(sx, sy)

    def take_damage(self, amount: float) -> None:
        self.hp -= amount
        self._hit_flash = 0.1
        if self.hp <= 0:
            self.alive = False

    @property
    def speed(self) -> float:
        return self.speed_tiles * C.TILE

    def blocked_by(self, game: "Game") -> Optional[Fruit]:
        for f in game.fruits:
            if f.alive and math.hypot(f.x - self.x, f.y - self.y) < C.TILE * 0.9:
                return f
        return None

    def update(self, dt: float, game: "Game") -> None:
        self._hit_flash = max(0.0, self._hit_flash - dt)

        if self.target_fruit is not None and not self.target_fruit.alive:
            self.target_fruit = None

        blocker = self.blocked_by(game)
        if blocker is not None:
            # Melee: bite the blocking fruit instead of walking.
            blocker.take_damage(self.bite * dt * 12.0)
            return

        self.on_walk(dt, game)
        self.advance(dt, game)

    def on_walk(self, dt: float, game: "Game") -> None:
        """Hook for ranged monsters; default does nothing."""

    def advance(self, dt: float, game: "Game") -> None:
        dist = self.speed * dt
        while dist > 0 and self.seg < len(game.path) - 1:
            nx, ny = game.path[self.seg + 1]
            dx, dy = nx - self.x, ny - self.y
            seg_len = math.hypot(dx, dy)
            if seg_len <= dist:
                self.x, self.y = nx, ny
                self.seg += 1
                dist -= seg_len
            else:
                self.x += dx / seg_len * dist
                self.y += dy / seg_len * dist
                dist = 0
        if self.seg >= len(game.path) - 1:
            game.damage_carrot(self.bite)
            self.alive = False

    def draw(self, surface: pygame.Surface) -> None:
        cx, cy = int(self.x), int(self.y)
        body = (255, 255, 255) if self._hit_flash > 0 else self.color
        pygame.draw.circle(surface, body, (cx, cy), 13)
        pygame.draw.circle(surface, (40, 40, 40), (cx, cy), 13, 2)
        self.draw_detail(surface, cx, cy)
        w = 26
        x, y = cx - w // 2, cy - 22
        pygame.draw.rect(surface, C.COL_HP_BG, (x, y, w, 4))
        pygame.draw.rect(surface, C.COL_HP_FG,
                         (x, y, int(w * self.hp / self.max_hp), 4))

    def draw_detail(self, surface, cx, cy) -> None:
        ...


class Slime(Monster):
    def __init__(self, game):
        super().__init__("slime", game)

    def draw_detail(self, surface, cx, cy):
        pygame.draw.circle(surface, (240, 240, 240), (cx - 4, cy - 2), 2)
        pygame.draw.circle(surface, (240, 240, 240), (cx + 4, cy - 2), 2)


class Bat(Monster):
    def __init__(self, game):
        super().__init__("bat", game)

    def draw_detail(self, surface, cx, cy):
        pygame.draw.polygon(surface, (90, 70, 140),
                            [(cx - 13, cy), (cx - 24, cy - 8), (cx - 12, cy + 4)])
        pygame.draw.polygon(surface, (90, 70, 140),
                            [(cx + 13, cy), (cx + 24, cy - 8), (cx + 12, cy + 4)])


class Golem(Monster):
    def __init__(self, game):
        super().__init__("golem", game)

    def draw_detail(self, surface, cx, cy):
        pygame.draw.rect(surface, (110, 100, 85), (cx - 10, cy - 10, 20, 20), 2)


class RockThrower(Monster):
    """Stops at range and lobs rocks at the nearest fruit."""

    def __init__(self, game):
        super().__init__("thrower", game)

    def on_walk(self, dt: float, game: "Game") -> None:
        rng = self.spec["throw_range"] * C.TILE
        near = None
        for f in game.fruits:
            if f.alive and math.hypot(f.x - self.x, f.y - self.y) <= rng:
                near = f
                break
        if near is None:
            return
        self.throw_timer -= dt
        if self.throw_timer <= 0:
            self.throw_timer = self.spec["throw_interval"]
            game.rocks.append(Rock(self.x, self.y, near, self.spec["throw_damage"]))

    def draw_detail(self, surface, cx, cy):
        pygame.draw.circle(surface, (90, 70, 60), (cx + 10, cy - 8), 5)


# ---------------------------------------------------------------- projectiles
class Bullet(Entity):
    """Homing projectile; keeps its target reference so it always connects."""

    def __init__(self, x, y, target: Monster, damage: float, color,
                 splash: float = 0.0) -> None:
        super().__init__(x, y)
        self.target = target
        self.damage = damage
        self.color = color
        self.splash = splash

    def update(self, dt: float, game: "Game") -> None:
        if not self.target.alive:
            self.alive = False
            return
        dx, dy = self.target.x - self.x, self.target.y - self.y
        d = math.hypot(dx, dy)
        step = C.BULLET_SPEED * dt
        if d <= step + C.MONSTER_HIT_RADIUS:
            self.hit(game)
            self.alive = False
            return
        self.x += dx / d * step
        self.y += dy / d * step

    def hit(self, game: "Game") -> None:
        if self.splash <= 0:
            self.target.take_damage(self.damage)
            return
        game.effects.append(Effect(self.target.x, self.target.y, self.splash))
        for m in game.monsters:
            if m.alive and math.hypot(m.x - self.target.x, m.y - self.target.y) <= self.splash:
                m.take_damage(self.damage)

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), 6)


class Rock(Entity):
    """Slow projectile thrown by a RockThrower at a fruit."""

    SPEED = 170.0

    def __init__(self, x, y, target: Fruit, damage: float) -> None:
        super().__init__(x, y)
        self.target = target
        self.damage = damage

    def update(self, dt: float, game: "Game") -> None:
        if not self.target.alive:
            self.alive = False
            return
        dx, dy = self.target.x - self.x, self.target.y - self.y
        d = math.hypot(dx, dy)
        step = self.SPEED * dt
        if d <= step + 10:
            self.target.take_damage(self.damage)
            self.alive = False
            return
        self.x += dx / d * step
        self.y += dy / d * step

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.circle(surface, (110, 95, 80), (int(self.x), int(self.y)), 6)
        pygame.draw.circle(surface, (80, 70, 60), (int(self.x), int(self.y)), 6, 2)


# -------------------------------------------------------------------- carrot
class Carrot(Entity):
    def __init__(self, col: int, row: int) -> None:
        cx, cy = tile_center(col, row)
        super().__init__(cx, cy)
        self.hp = C.CARROT_HP
        self.max_hp = C.CARROT_HP

    def take_damage(self, amount: float) -> None:
        self.hp -= amount
        if self.hp <= 0:
            self.alive = False

    def update(self, dt: float, game: "Game") -> None:
        ...

    def draw(self, surface: pygame.Surface) -> None:
        cx, cy = int(self.x), int(self.y)
        pygame.draw.polygon(surface, (240, 140, 40),
                            [(cx, cy + 20), (cx - 13, cy - 8), (cx + 13, cy - 8)])
        for i in range(3):
            x = cx - 8 + i * 8
            pygame.draw.line(surface, (80, 150, 60), (x, cy - 8), (x - 2, cy - 22), 3)
        pygame.draw.circle(surface, (250, 230, 220), (cx - 5, cy - 2), 2)
        pygame.draw.circle(surface, (250, 230, 220), (cx + 5, cy - 2), 2)


class Effect(Entity):
    LIFE = 0.35

    def __init__(self, x, y, radius) -> None:
        super().__init__(x, y)
        self.radius = radius
        self.life = self.LIFE

    def update(self, dt: float, game: "Game") -> None:
        self.life -= dt
        if self.life <= 0:
            self.alive = False

    def draw(self, surface: pygame.Surface) -> None:
        t = self.life / self.LIFE
        r = int(self.radius * (1.1 - t * 0.5))
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (140, 230, 140, int(170 * t)), (r, r), r)
        surface.blit(s, (int(self.x) - r, int(self.y) - r))

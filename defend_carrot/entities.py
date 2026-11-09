"""Course entity hierarchy with original-game tower roles and sprite animation.

Fruit is the shared tower base (legacy class IDs remain compatible). Concrete
subclasses implement rapid fire, piercing, area damage, slowing, poison and
freezing. Monster owns path movement and timed effects; projectiles resolve
hits without controlling wave schedules or the shared economy.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING

import pygame

import config as C
from art import (fruit_image, character_image, sprite_image, TOWER_ATLASES,
                 ATTACK_FRAMES, WALK_FRAMES, CARROT_FRAMES, CARROT_HEALTH_FRAMES)
from animation import Animation

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
        self.attack_animation = Animation(ATTACK_FRAMES[kind], .08, loop=False)
        self._attacking = False
        self.aim_angle = 0.0
        self.level = 1
        self.invested = self.spec['cost']

    @property
    def upgrade_cost(self):
        return self.spec['upgrades'][self.level - 1] if self.level < 3 else None

    def upgrade(self):
        cost = self.upgrade_cost
        if cost is None:
            return False
        self.invested += cost
        self.level += 1
        self.damage = self.spec['damage'] * (1, 1.8, 3.2)[self.level - 1]
        self.interval = self.spec['interval'] * (1, .88, .76)[self.level - 1]
        self.rng = self.spec['rng'] * C.TILE * (1, 1.12, 1.25)[self.level - 1]
        return True

    @property
    def sell_value(self):
        return round(self.invested * .8)

    def take_damage(self, amount: float) -> None:
        self.hp -= amount
        self._hit_flash = 0.12
        if self.hp <= 0:
            self.alive = False

    def update(self, dt: float, game: "Game") -> None:
        self._hit_flash = max(0.0, self._hit_flash - dt)
        if self._attacking:
            self.attack_animation.update(dt)
            if self.attack_animation.finished:
                self._attacking = False
        target = self.acquire(game)
        if target is None:
            return
        self.aim_angle = math.degrees(math.atan2(self.y - target.y, target.x - self.x)) - 90
        self.timer -= dt
        if self.timer <= 0:
            self.timer = self.interval
            self.fire(target, game)
            self.attack_animation.restart()
            self._attacking = True

    def acquire(self, game: "Game") -> Optional["Monster"]:
        candidates = [m for m in game.monsters if m.alive
                      and math.hypot(m.x - self.x, m.y - self.y) <= self.rng]
        return max(candidates, key=lambda m: (m.seg, -math.dist(
            (m.x, m.y), game.path[min(m.seg + 1, len(game.path) - 1)])), default=None)

    @abstractmethod
    def fire(self, target: "Monster", game: "Game") -> None:
        ...

    def draw(self, surface: pygame.Surface) -> None:
        cx, cy = int(self.x), int(self.y)
        frame = self.attack_animation.frame if self._attacking and self.kind != 'melon' else None
        sprite = character_image(self.kind, C.TOWER_SPRITE_SIZE, self._hit_flash > 0, frame=frame, level=self.level)
        if sprite is None:
            sprite = fruit_image(self.kind, C.TOWER_SPRITE_SIZE, self._hit_flash > 0)
        elif self.kind in ('apple', 'poison', 'rocket'):
            sprite = pygame.transform.rotate(sprite, self.aim_angle)
        surface.blit(sprite, sprite.get_rect(center=(cx, cy)))
        if self.kind == 'melon' and self._attacking:
            halo = character_image(self.kind, C.TOWER_SPRITE_SIZE + 44, frame=self.attack_animation.frame, level=self.level)
            if halo is not None:
                surface.blit(halo, halo.get_rect(center=(cx, cy)))
        for i in range(self.level):
            pygame.draw.circle(surface, (255, 231, 101), (cx - 5 * (self.level - 1) + i * 10, cy + 23), 3)
        if self.hp < self.max_hp:
            w = 30
            x, y = cx - w // 2, cy - C.TOWER_SPRITE_SIZE // 2 - 4
            pygame.draw.rect(surface, (37, 59, 40), (x - 1, y - 1, w + 2, 6), border_radius=3)
            pygame.draw.rect(surface, C.COL_HP_FG,
                             (x, y, int(w * self.hp / self.max_hp), 4))


class Apple(Fruit):
    def __init__(self, col, row):
        super().__init__(col, row, "apple")

    def fire(self, target, game):
        game.bullets.append(Bullet(self.x, self.y, target, self.damage,
                                   (255, 210, 210), kind=self.kind, tier=self.level))


class Orange(Fruit):
    def __init__(self, col, row):
        super().__init__(col, row, "orange")

    def fire(self, target, game):
        game.bullets.append(PiercingBullet(self, target))


class Melon(Fruit):
    """Original Sun role: damage every monster around the tower."""

    SPLASH = 1.6 * C.TILE

    def __init__(self, col, row):
        super().__init__(col, row, "melon")

    def fire(self, target, game):
        for monster in game.monsters:
            if monster.alive and math.dist((self.x, self.y), (monster.x, monster.y)) <= self.rng:
                monster.take_damage(self.damage)
        game.effects.append(Effect(self.x, self.y, self.rng, (255, 187, 65)))


class Star(Fruit):
    def __init__(self, col, row):
        super().__init__(col, row, 'star')

    def fire(self, target, game):
        game.bullets.append(Bullet(self.x, self.y, target, self.damage, self.color,
                                   splash=1.15 * C.TILE, kind=self.kind, tier=self.level))


class IceStar(Fruit):
    def __init__(self, col, row):
        super().__init__(col, row, 'ice')

    def fire(self, target, game):
        game.bullets.append(Bullet(self.x, self.y, target, self.damage, self.color,
                                   splash=1.15 * C.TILE, kind=self.kind, tier=self.level))


class PoisonPin(Fruit):
    def __init__(self, col, row):
        super().__init__(col, row, 'poison')

    def fire(self, target, game):
        game.bullets.append(Bullet(self.x, self.y, target, self.damage, self.color,
                                   kind=self.kind, tier=self.level))


class RocketTower(Fruit):
    def __init__(self, col, row):
        super().__init__(col, row, 'rocket')

    def fire(self, target, game):
        game.bullets.append(PiercingBullet(self, target, explosive=True))


class Snowflake(Fruit):
    def __init__(self, col, row):
        super().__init__(col, row, 'snow')

    def fire(self, target, game):
        for monster in game.monsters:
            if monster.alive and math.dist((self.x, self.y), (monster.x, monster.y)) <= self.rng:
                monster.take_damage(self.damage)
                monster.apply_freeze(.65 + .2 * (self.level - 1))
        game.effects.append(Effect(self.x, self.y, self.rng, self.color))


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
        self.escaped = False
        self.bite = float(spec["bite"])
        self.color = spec["color"]
        self.label = spec["label"]
        self.seg = 0
        self.t = 0.0
        self._hit_flash = 0.0
        self.target_fruit: Optional[Fruit] = None
        self.throw_timer = float(spec.get("throw_interval", 0.0))
        self.walk_animation = Animation(WALK_FRAMES[kind])
        self.facing_left = False
        level = C.LEVELS[game.level_index]
        self.hp *= level['hp_scale'] * (1 + .045 * game.wave_index)
        self.max_hp = self.hp
        self.speed_tiles *= level['speed_scale']
        self.slow_effects = {}
        self.freeze_time = 0.0
        self.poison_time = 0.0
        self.poison_dps = 0.0
        # Start just off the left edge of the field.
        sx, sy = game.path_px(0, 0.0)
        super().__init__(sx, sy)

    def take_damage(self, amount: float, flash=True) -> None:
        self.hp -= amount
        if flash:
            self._hit_flash = 0.1
        if self.hp <= 0:
            self.alive = False

    @property
    def speed(self) -> float:
        if self.freeze_time > 0:
            return 0.0
        return self.speed_tiles * C.TILE * min(self.slow_effects, default=1.0)

    def apply_slow(self, factor, duration):
        factor = max(.25, min(1.0, factor))
        self.slow_effects[factor] = max(duration, self.slow_effects.get(factor, 0))

    def apply_freeze(self, duration):
        self.freeze_time = max(self.freeze_time, duration)

    def apply_poison(self, damage_per_second, duration):
        self.poison_dps = max(self.poison_dps, damage_per_second)
        self.poison_time = max(self.poison_time, duration)

    def blocked_by(self, game: "Game") -> Optional[Fruit]:
        for f in game.fruits:
            if f.alive and math.hypot(f.x - self.x, f.y - self.y) < C.TILE * 0.9:
                return f
        return None

    def update(self, dt: float, game: "Game") -> None:
        self._hit_flash = max(0.0, self._hit_flash - dt)
        self.slow_effects = {factor: time - dt for factor, time in self.slow_effects.items() if time > dt}
        self.freeze_time = max(0, self.freeze_time - dt)
        if self.poison_time > 0:
            self.take_damage(self.poison_dps * min(dt, self.poison_time), flash=False)
            self.poison_time = max(0, self.poison_time - dt)
            if not self.alive:
                return
        if self.freeze_time > 0:
            return
        self.walk_animation.update(dt)

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
        if not self.alive or self.escaped:
            return
        dist = self.speed * dt
        while dist > 0 and self.seg < len(game.path) - 1:
            nx, ny = game.path[self.seg + 1]
            dx, dy = nx - self.x, ny - self.y
            if abs(dx) > .001:
                self.facing_left = dx < 0
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
            self.escaped = True
            game.damage_carrot(C.CARROT_ESCAPE_DAMAGE)
            self.alive = False

    def draw(self, surface: pygame.Surface) -> None:
        cx, cy = int(self.x), int(self.y)
        size = (84 if self.kind == 'boss' else C.LARGE_MONSTER_SPRITE_SIZE
                if self.kind in ('golem', 'elite') else C.MONSTER_SPRITE_SIZE)
        sprite = character_image(self.kind, size,
                                 flash=self._hit_flash > 0,
                                 frame=self.walk_animation.frame, flip=self.facing_left)
        if sprite is not None:
            surface.blit(sprite, sprite.get_rect(center=(cx, cy)))
            if self.freeze_time > 0 or self.slow_effects:
                pygame.draw.ellipse(surface, (138, 228, 255), (cx - 20, cy + 12, 40, 10), 2)
            if self.poison_time > 0:
                pygame.draw.circle(surface, (193, 93, 226), (cx + 18, cy + 8), 4)
        else:
            body = (255, 255, 255) if self._hit_flash > 0 else self.color
            pygame.draw.circle(surface, body, (cx, cy), 13)
            self.draw_detail(surface, cx, cy)
        w = 26
        x, y = cx - w // 2, cy - size // 2 - 5
        fraction = max(0, min(1, self.hp / self.max_hp))
        pygame.draw.rect(surface, (40, 52, 42), (x - 1, y - 1, w + 2, 6), border_radius=3)
        pygame.draw.rect(surface, (161, 199, 105) if fraction > .35 else (233, 122, 91),
                         (x, y, round(w * fraction), 4), border_radius=2)

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
    """Original long-body walker, preserving the old class name."""

    def __init__(self, game):
        super().__init__("thrower", game)

    def on_walk(self, dt, game):
        # Legacy class name retained; the original long-body monster is a walker.
        pass


    def draw_detail(self, surface, cx, cy):
        pygame.draw.circle(surface, (90, 70, 60), (cx + 10, cy - 8), 5)


class YellowFly(Monster):
    def __init__(self, game):
        super().__init__('yellow', game)


class Starling(Monster):
    def __init__(self, game):
        super().__init__('starling', game)


class EliteGolem(Monster):
    def __init__(self, game):
        super().__init__('elite', game)


class BigBoss(Monster):
    def __init__(self, game):
        super().__init__('boss', game)


# ---------------------------------------------------------------- projectiles
class Bullet(Entity):
    """Homing projectile; keeps its target reference so it always connects."""

    def __init__(self, x, y, target: Monster, damage: float, color,
                 splash: float = 0.0, kind=None, tier=1) -> None:
        super().__init__(x, y)
        self.target = target
        self.damage = damage
        self.color = color
        self.splash = splash
        self.kind = kind
        self.tier = tier
        self.angle = 0.0
        self.elapsed = 0.0

    def update(self, dt: float, game: "Game") -> None:
        self.elapsed += dt
        if not self.target.alive:
            self.alive = False
            return
        dx, dy = self.target.x - self.x, self.target.y - self.y
        self.angle = math.degrees(math.atan2(-dy, dx)) - 90
        d = math.hypot(dx, dy)
        step = C.BULLET_SPEED * dt
        if d <= step + C.MONSTER_HIT_RADIUS:
            self.hit(game)
            self.alive = False
            return
        self.x += dx / d * step
        self.y += dy / d * step

    def hit(self, game: "Game") -> None:
        targets = [self.target] if self.splash <= 0 else [m for m in game.monsters
            if m.alive and math.dist((m.x, m.y), (self.target.x, self.target.y)) <= self.splash]
        if self.splash:
            game.effects.append(Effect(self.target.x, self.target.y, self.splash, self.color))
        for monster in targets:
            if not monster.alive:
                continue
            monster.take_damage(self.damage)
            if self.kind == 'ice':
                monster.apply_slow(.55 - .05 * (self.tier - 1), 2 + .4 * (self.tier - 1))
            elif self.kind == 'poison':
                monster.apply_poison(self.damage * .4, 2 + self.tier)

    def draw(self, surface: pygame.Surface) -> None:
        frames = {'apple': 'PBottle11.png', 'orange': 'PFan11.png', 'melon': 'PSun01.png',
                  'star': 'PStar11.png', 'ice': 'PBStar11.png', 'poison': 'PPin11.png',
                  'rocket': 'PRocket11.png'}
        if self.kind in frames:
            name = frames[self.kind]
            if self.tier > 1 and self.kind != 'melon':
                name = name.replace('11.png', f'{self.tier}1.png')
            image = sprite_image(TOWER_ATLASES[self.kind], name, 24)
            if image is not None:
                image = pygame.transform.rotate(image, self.elapsed * 720 if self.kind == 'orange' else self.angle)
                surface.blit(image, image.get_rect(center=(int(self.x), int(self.y))))
                return
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), 6)


class PiercingBullet(Entity):
    """Fixed-direction projectile; one hit per monster, with optional end blast."""
    def __init__(self, tower, target, explosive=False):
        super().__init__(tower.x, tower.y)
        direction = pygame.Vector2(target.x - tower.x, target.y - tower.y)
        self.distance = direction.length() + C.TILE if explosive else C.TILE * 28
        self.direction = direction.normalize() if direction.length_squared() else pygame.Vector2(1, 0)
        self.damage = tower.damage
        self.kind = tower.kind
        self.tier = tower.level
        self.explosive = explosive
        self.hit_monsters = set()
        self.elapsed = 0.0

    def update(self, dt, game):
        self.elapsed += dt
        step = min(self.distance, 280 * dt)
        start = pygame.Vector2(self.x, self.y)
        end = start + self.direction * step
        for monster in game.monsters:
            if not monster.alive or monster in self.hit_monsters:
                continue
            rel = pygame.Vector2(monster.x, monster.y) - start
            along = max(0, min(step, rel.dot(self.direction)))
            if (rel - self.direction * along).length() <= C.MONSTER_HIT_RADIUS:
                self.hit_monsters.add(monster)
                monster.take_damage(self.damage)
        self.x, self.y = end
        self.distance -= step
        if self.distance <= .001 or not (-50 < self.x < C.SCREEN_W + 50 and C.HUD_H - 50 < self.y < C.HUD_H + C.FIELD_H + 50):
            self.alive = False
            if self.explosive:
                radius = C.TILE * 1.4
                game.effects.append(Effect(self.x, self.y, radius, (255, 151, 60)))
                for monster in game.monsters:
                    if monster.alive and math.dist((self.x, self.y), (monster.x, monster.y)) <= radius:
                        monster.take_damage(self.damage * .65)

    def draw(self, surface):
        name = f'PRocket{self.tier}1.png' if self.explosive else f'PFan{self.tier}1.png'
        image = sprite_image(TOWER_ATLASES[self.kind], name, 28)
        if image is not None:
            angle = math.degrees(math.atan2(-self.direction.y, self.direction.x)) - 90
            image = pygame.transform.rotate(image, angle if self.explosive else self.elapsed * 720)
            surface.blit(image, image.get_rect(center=(round(self.x), round(self.y))))


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
        self.expression = Animation(CARROT_FRAMES, .12, loop=False)
        self.expression_timer = 0.0
        self.expressing = False
        self.hurt_timer = 0.0

    def take_damage(self, amount: float) -> None:
        if not self.alive:
            return
        self.hp = max(0, self.hp - amount)
        self.expressing = False
        self.hurt_timer = .25
        if self.hp <= 0:
            self.alive = False

    def update(self, dt: float, game: "Game") -> None:
        self.hurt_timer = max(0, self.hurt_timer - dt)
        if self.hp < self.max_hp:
            self.expressing = False
            return
        self.expression_timer += dt
        if self.expressing:
            self.expression.update(dt)
            self.expressing = not self.expression.finished
        elif self.expression_timer >= 4.0:
            self.expression_timer %= 4.0
            self.expression.restart()
            self.expressing = True

    @property
    def sprite_frame(self):
        if self.hp == self.max_hp and self.expressing:
            return self.expression.frame
        return CARROT_HEALTH_FRAMES[max(0, min(C.CARROT_HP, int(self.hp)))]

    def draw(self, surface: pygame.Surface) -> None:
        cx, cy = int(self.x), int(self.y)
        if self.hurt_timer:
            cx += round(math.sin(self.hurt_timer * 55) * 3)
        sprite = character_image('carrot', C.CARROT_SPRITE_SIZE, frame=self.sprite_frame)
        if sprite is not None:
            surface.blit(sprite, sprite.get_rect(center=(cx, cy - 16)))
            return
        pygame.draw.polygon(surface, (240, 140, 40),
                            [(cx, cy + 20), (cx - 13, cy - 8), (cx + 13, cy - 8)])
        for i in range(3):
            x = cx - 8 + i * 8
            pygame.draw.line(surface, (80, 150, 60), (x, cy - 8), (x - 2, cy - 22), 3)
        pygame.draw.circle(surface, (250, 230, 220), (cx - 5, cy - 2), 2)
        pygame.draw.circle(surface, (250, 230, 220), (cx + 5, cy - 2), 2)


class Effect(Entity):
    LIFE = 0.35

    def __init__(self, x, y, radius, color=(140, 230, 140)) -> None:
        super().__init__(x, y)
        self.radius = radius
        self.life = self.LIFE
        self.color = color

    def update(self, dt: float, game: "Game") -> None:
        self.life -= dt
        if self.life <= 0:
            self.alive = False

    def draw(self, surface: pygame.Surface) -> None:
        t = self.life / self.LIFE
        r = int(self.radius * (1.1 - t * 0.5))
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, int(90 * t)), (r, r), r)
        pygame.draw.circle(s, (*self.color, int(190 * t)), (r, r), r, 2)
        surface.blit(s, (int(self.x) - r, int(self.y) - r))

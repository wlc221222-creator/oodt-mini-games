"""Entity hierarchy for the Plants vs Zombies port.

The class tree is the main object-oriented talking point of this project:

    Entity                     (abstract base: position, draw contract)
    ├── Plant                  (abstract: hp, grid cell, on_tick hook)
    │   ├── Sunflower          (economy behaviour)
    │   ├── Shooter            (abstract attacker, owns Projectile objects)
    │   │   ├── Peashooter
    │   │   └── SnowPea        (attacker + slow debuff: polymorphism)
    │   ├── WallNut            (pure tank, cracks as it is eaten)
    │   └── CherryBomb         (one-shot area damage)
    ├── Zombie                 (mover + eater + debuffable)
    ├── Projectile             (pea / snow pea)
    ├── Sun                    (collectable resource)
    └── Explosion              (short lived visual effect)

Every subclass overrides ``update`` and ``draw``; the game loop only ever
calls those two methods, so new plants or zombies can be added without
touching the loop itself. Rendering uses the original game's art pack through
the :mod:`assets` helper, and every entity degrades gracefully to a flat shape
if a sprite is missing.
"""

from __future__ import annotations

import math
import random
from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING

import pygame

import config as C
from assets import Anim, get_assets

if TYPE_CHECKING:
    from game import Game


def lane_baseline(row: int) -> int:
    return C.LAWN_Y + row * C.CELL_H + C.PLANT_BASELINE


def cell_center(col: int, row: int):
    """Centre-x and stand-on baseline-y of a grid cell."""
    return C.LAWN_X + col * C.CELL_W + C.CELL_W // 2, lane_baseline(row)


def blit_bottom(surface: pygame.Surface, image: pygame.Surface,
                x: float, bottom: float) -> None:
    surface.blit(image, image.get_rect(midbottom=(int(x), int(bottom))))


class Entity(ABC):
    """Base class for everything that lives on the field."""

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.alive = True

    @abstractmethod
    def update(self, dt: float, game: "Game") -> None:
        """Advance internal state by ``dt`` seconds."""

    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None:
        """Render the entity onto ``surface``."""


# --------------------------------------------------------------------- plants
class Plant(Entity):
    """Abstract plant. Occupies one grid cell and has hit points."""

    ANIM_INTERVAL = 0.12

    def __init__(self, col: int, row: int, kind: str) -> None:
        cx, baseline = cell_center(col, row)
        super().__init__(cx, baseline)
        self.col = col
        self.row = row
        self.kind = kind
        self.spec = C.PLANTS[kind]
        self.hp = float(self.spec["hp"])
        self.max_hp = float(self.spec["hp"])
        self.color = self.spec["color"]
        self.label = self.spec["label"]
        self.cost = self.spec["cost"]
        self.baseline = baseline
        self._hit_flash = 0.0
        self.anim = Anim(get_assets().plant(self.spec["sprite"]),
                         self.ANIM_INTERVAL)

    def take_damage(self, amount: float) -> None:
        self.hp -= amount
        self._hit_flash = 0.12
        if self.hp <= 0:
            self.alive = False

    def update(self, dt: float, game: "Game") -> None:
        self._hit_flash = max(0.0, self._hit_flash - dt)
        self.anim.update(dt)
        self.on_tick(dt, game)

    def on_tick(self, dt: float, game: "Game") -> None:
        """Hook for subclasses; the default plant does nothing."""

    def draw(self, surface: pygame.Surface) -> None:
        image = self.anim.image()
        if image is None:
            self._draw_fallback(surface)
        else:
            blit_bottom(surface, image, self.x, self.baseline)
            if self._hit_flash > 0:
                ghost = image.copy()
                ghost.fill((80, 80, 80, 0), special_flags=pygame.BLEND_RGBA_ADD)
                surface.blit(ghost, ghost.get_rect(
                    midbottom=(int(self.x), int(self.baseline))),
                    special_flags=pygame.BLEND_RGBA_ADD)
        self._draw_hp(surface)

    def _draw_fallback(self, surface: pygame.Surface) -> None:
        cx, cy = int(self.x), int(self.baseline) - 30
        col = (255, 255, 255) if self._hit_flash > 0 else self.color
        pygame.draw.circle(surface, col, (cx, cy), 26)
        pygame.draw.circle(surface, (30, 60, 30), (cx, cy), 26, 2)

    def _draw_hp(self, surface: pygame.Surface) -> None:
        if self.hp >= self.max_hp:
            return
        w = 46
        x, y = int(self.x) - w // 2, int(self.baseline) - 78
        pygame.draw.rect(surface, C.COL_HP_BG, (x, y, w, 5))
        pygame.draw.rect(surface, C.COL_HP_FG, (x, y, int(w * self.hp / self.max_hp), 5))


class Sunflower(Plant):
    """Produces a sun every few seconds."""

    PRODUCE_INTERVAL = 9.0

    def __init__(self, col: int, row: int) -> None:
        super().__init__(col, row, "sunflower")
        self.timer = self.PRODUCE_INTERVAL * 0.5

    def on_tick(self, dt: float, game: "Game") -> None:
        self.timer -= dt
        if self.timer <= 0:
            self.timer = self.PRODUCE_INTERVAL
            game.spawn_sun(self.x, self.baseline - 20, C.SKY_SUN_AMOUNT,
                           falls=False)


class Shooter(Plant):
    """Abstract attacker that fires projectiles down its lane."""

    FIRE_INTERVAL = C.PEA_INTERVAL
    SHOTS_PER_VOLLEY = 1
    PROJECTILE = "PeaNormal"

    def __init__(self, col: int, row: int, kind: str) -> None:
        super().__init__(col, row, kind)
        self.timer = 0.5

    def on_tick(self, dt: float, game: "Game") -> None:
        if not game.lane_has_zombie(self.row, self.x):
            return
        self.timer -= dt
        if self.timer <= 0:
            self.timer = self.FIRE_INTERVAL
            for _ in range(self.SHOTS_PER_VOLLEY):
                game.projectiles.append(self.make_projectile())

    @abstractmethod
    def make_projectile(self) -> "Projectile":
        """Create the projectile this shooter fires."""


class Peashooter(Shooter):
    def __init__(self, col: int, row: int) -> None:
        super().__init__(col, row, "peashooter")

    def make_projectile(self) -> "Projectile":
        return Projectile(self.x + 26, self.baseline - 46, C.PEA_DAMAGE,
                          "PeaNormal", self.row)


class Repeater(Shooter):
    """Fires two peas per volley -- a one-line subclass tweak."""

    SHOTS_PER_VOLLEY = 2
    FIRE_INTERVAL = C.PEA_INTERVAL * 1.5

    def __init__(self, col: int, row: int) -> None:
        super().__init__(col, row, "repeater")

    def make_projectile(self) -> "Projectile":
        return Projectile(self.x + 26, self.baseline - 46, C.PEA_DAMAGE,
                          "PeaNormal", self.row)


class Threepeater(Shooter):
    """Fires into its own lane plus the two adjacent lanes."""

    FIRE_INTERVAL = C.PEA_INTERVAL * 1.4

    def __init__(self, col: int, row: int) -> None:
        super().__init__(col, row, "threepeater")

    def on_tick(self, dt: float, game: "Game") -> None:
        rows = [self.row - 1, self.row, self.row + 1]
        rows = [r for r in rows if 0 <= r < game.rows]
        if not any(game.lane_has_zombie(r, self.x) for r in rows):
            return
        self.timer -= dt
        if self.timer <= 0:
            self.timer = self.FIRE_INTERVAL
            for r in rows:
                game.projectiles.append(
                    Projectile(self.x + 26, self.baseline - 46, C.PEA_DAMAGE,
                               "PeaNormal", r))

    def make_projectile(self) -> "Projectile":
        return Projectile(self.x + 26, self.baseline - 46, C.PEA_DAMAGE,
                          "PeaNormal", self.row)


class SnowPea(Shooter):
    """Same firing contract as Peashooter but applies a slow effect."""

    def __init__(self, col: int, row: int) -> None:
        super().__init__(col, row, "snowpea")

    def make_projectile(self) -> "Projectile":
        return Projectile(self.x + 26, self.baseline - 46, C.PEA_DAMAGE,
                          "PeaIce", self.row, slow=True)


class WallNut(Plant):
    """Tank that visibly cracks as it takes damage (three art states)."""

    def __init__(self, col: int, row: int) -> None:
        super().__init__(col, row, "wallnut")
        self._stage = 0

    def on_tick(self, dt: float, game: "Game") -> None:
        ratio = self.hp / self.max_hp
        stage = 0 if ratio > 0.66 else (1 if ratio > 0.33 else 2)
        if stage != self._stage:
            self._stage = stage
            name = "WallNut" + (f"_cracked{stage}" if stage else "")
            self.anim.set_frames(get_assets().plant(name), reset=True)


class CherryBomb(Plant):
    """One-shot area damage. Detonates shortly after being placed."""

    FUSE = 1.2

    def __init__(self, col: int, row: int) -> None:
        super().__init__(col, row, "cherrybomb")
        self.timer = self.FUSE

    def on_tick(self, dt: float, game: "Game") -> None:
        self.timer -= dt
        if self.timer <= 0:
            game.explosions.append(Explosion(self.x, self.baseline - 40,
                                             C.CHERRY_RADIUS))
            for z in game.zombies:
                if math.hypot(z.x - self.x, z.y - self.baseline) <= C.CHERRY_RADIUS:
                    z.take_damage(C.CHERRY_DAMAGE, boom=True)
            self.alive = False


class PotatoMine(Plant):
    """Cheap one-shot mine: arms after a delay, then explodes on contact."""

    ARM_TIME = 6.0

    def __init__(self, col: int, row: int) -> None:
        super().__init__(col, row, "potatomine")
        self.armed = False
        self.timer = self.ARM_TIME
        self.anim.set_frames(get_assets().plant("PotatoMineInit"), reset=True)

    def on_tick(self, dt: float, game: "Game") -> None:
        if not self.armed:
            self.timer -= dt
            if self.timer <= 0:
                self.armed = True
                self.anim.set_frames(get_assets().plant("PotatoMine"), reset=True)
            return
        for z in game.zombies:
            if z.alive and z.row == self.row and abs(z.x - self.x) < C.CELL_W * 0.6:
                game.explosions.append(
                    Explosion(self.x, self.baseline - 30, C.CELL_W))
                z.take_damage(C.CHERRY_DAMAGE, boom=True)
                self.alive = False
                return


class Jalapeno(Plant):
    """One-shot that torches its entire lane with a fire sweep."""

    FUSE = 1.0

    def __init__(self, col: int, row: int) -> None:
        super().__init__(col, row, "jalapeno")
        self.timer = self.FUSE

    def on_tick(self, dt: float, game: "Game") -> None:
        self.timer -= dt
        if self.timer > 0:
            return
        # Kill every zombie in the lane and play the original's full-width
        # fire-sweep animation across that lane.
        for z in game.zombies:
            if z.row == self.row:
                z.take_damage(C.CHERRY_DAMAGE, boom=True)
        game.effects.append(LaneFire(self.row))
        self.alive = False


# -------------------------------------------------------------------- zombie
class Zombie(Entity):
    """Walks left, eats plants, and can be slowed by snow peas."""

    WALK_INTERVAL = 0.15
    DIE_INTERVAL = 0.1

    def __init__(self, x: float, row: int, kind: str) -> None:
        super().__init__(x, lane_baseline(row))
        self.row = row
        self.kind = kind
        self.spec = C.ZOMBIES[kind]
        self.hp = float(self.spec["hp"])
        self.max_hp = float(self.spec["hp"])
        self.speed = float(self.spec["speed"])
        self.color = self.spec["color"]
        self.label = self.spec["label"]
        self.slow_timer = 0.0
        self.eat_timer = 0.0
        self.target: Optional[Plant] = None
        self._hit_flash = 0.0
        self._sets = get_assets().zombie(kind)
        self.anim = Anim(self._sets["walk"], self.WALK_INTERVAL)
        self.dying = False
        self._death_anim: Optional[Anim] = None
        self._head_spawned = False

    def take_damage(self, amount: float, boom: bool = False) -> None:
        if self.dying:
            return
        self.hp -= amount
        self._hit_flash = 0.1
        if self.hp <= 0:
            self.start_dying(boom=boom)

    def start_dying(self, boom: bool = False) -> None:
        """Enter the death animation instead of vanishing instantly.

        A cherry-bomb / jalapeno kill uses the charred ``BoomDie`` frames,
        an ordinary kill uses the falling-apart ``ZombieDie`` frames -- both
        taken from the original art pack.
        """
        if self.dying:
            return
        self.dying = True
        self.target = None
        frames = self._sets["boom"] if boom else self._sets["die"]
        self._death_anim = Anim(frames, self.DIE_INTERVAL, loop=False)
        self.anim = self._death_anim
        self._head_spawned = False

    def apply_slow(self) -> None:
        self.slow_timer = C.SNOW_SLOW_TIME

    @property
    def current_speed(self) -> float:
        return self.speed * (C.SNOW_SLOW_FACTOR if self.slow_timer > 0 else 1.0)

    def update(self, dt: float, game: "Game") -> None:
        self._hit_flash = max(0.0, self._hit_flash - dt)

        if self.dying:
            self._death_anim.update(dt)
            # Pop the head off once, a little way into the animation.
            if not self._head_spawned and self._death_anim.i >= 2:
                self._head_spawned = True
                game.effects.append(ZombieHead(self.x, self.y - 70))
            if self._death_anim.done:
                self.alive = False
            return

        if self.slow_timer > 0:
            self.slow_timer -= dt

        if self.target is None or not self.target.alive:
            self.target = game.plant_in_front(self.row, self.x)
            self.eat_timer = 0.0

        if self.target is not None:
            self.anim.set_frames(self._sets["attack"])
            self.eat_timer -= dt
            if self.eat_timer <= 0:
                self.eat_timer = C.EAT_INTERVAL
                self.target.take_damage(self.spec["damage"])
        else:
            self.anim.set_frames(self._sets["walk"])
            self.x -= self.current_speed * dt

        if self.x < C.LAWN_X - 40:
            game.on_zombie_reached_house()
            self.alive = False
        self.anim.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        image = self.anim.image()
        if image is None:
            self._draw_fallback(surface)
        else:
            blit_bottom(surface, image, self.x, self.y)
            if self._hit_flash > 0 and not self.dying:
                ghost = image.copy()
                ghost.fill((90, 90, 90, 0), special_flags=pygame.BLEND_RGBA_ADD)
                surface.blit(ghost, ghost.get_rect(
                    midbottom=(int(self.x), int(self.y))),
                    special_flags=pygame.BLEND_RGBA_ADD)
        if self.slow_timer > 0 and not self.dying:
            pygame.draw.circle(surface, (150, 220, 255),
                               (int(self.x), int(self.y) - 50), 32, 2)
        if not self.dying:
            self._draw_hp(surface)

    def _draw_fallback(self, surface: pygame.Surface) -> None:
        cx, cy = int(self.x), int(self.y)
        body = (200, 220, 255) if self._hit_flash > 0 else self.color
        pygame.draw.rect(surface, body, (cx - 18, cy - 60, 36, 52),
                         border_radius=8)
        pygame.draw.circle(surface, (225, 220, 205), (cx, cy - 64), 14)

    def _draw_hp(self, surface: pygame.Surface) -> None:
        if self.hp >= self.max_hp:
            return
        w = 40
        x, y = int(self.x) - w // 2, int(self.y) - 104
        pygame.draw.rect(surface, C.COL_HP_BG, (x, y, w, 5))
        pygame.draw.rect(surface, C.COL_HP_FG, (x, y, int(w * self.hp / self.max_hp), 5))


# ---------------------------------------------------------------- projectile
class Projectile(Entity):
    def __init__(self, x: float, y: float, damage: int, sprite: str,
                 row: int, slow: bool = False) -> None:
        super().__init__(x, y)
        self.damage = damage
        self.sprite = sprite
        self.row = row
        self.slow = slow
        self.image = get_assets().bullet(sprite)

    def update(self, dt: float, game: "Game") -> None:
        self.x += C.PEA_SPEED * dt
        if self.x > C.SCREEN_W:
            self.alive = False
            return
        for z in game.zombies:
            if z.alive and z.row == self.row and abs(z.x - self.x) < 26:
                z.take_damage(self.damage)
                if self.slow:
                    z.apply_slow()
                self.alive = False
                return

    def draw(self, surface: pygame.Surface) -> None:
        if self.image is not None:
            surface.blit(self.image,
                         self.image.get_rect(center=(int(self.x), int(self.y))))
        else:
            col = (150, 220, 255) if self.slow else (110, 220, 110)
            pygame.draw.circle(surface, col, (int(self.x), int(self.y)), 8)


# ----------------------------------------------------------------------- sun
class Sun(Entity):
    """Collectable sun. Falls from the sky or pops out of a sunflower."""

    RADIUS = 24
    LIFE = 9.0
    FALL_SPEED = 60.0

    def __init__(self, x: float, y: float, amount: int, falls: bool = True) -> None:
        super().__init__(x, y)
        self.amount = amount
        self.falls = falls
        self.life = self.LIFE
        self.target_y = y + random.uniform(60, 120) if falls else y
        self.anim = Anim(get_assets().sun_frames, 0.1)

    def update(self, dt: float, game: "Game") -> None:
        if self.falls and self.y < self.target_y:
            self.y = min(self.target_y, self.y + self.FALL_SPEED * dt)
        self.life -= dt
        if self.life <= 0:
            self.alive = False
        self.anim.update(dt)

    def contains(self, pos) -> bool:
        return math.hypot(pos[0] - self.x, pos[1] - self.y) <= self.RADIUS + 8

    def draw(self, surface: pygame.Surface) -> None:
        image = self.anim.image()
        if image is None:
            pygame.draw.circle(surface, C.COL_SUN, (int(self.x), int(self.y)),
                               self.RADIUS)
            return
        if self.life < 1.5:
            image = image.copy()
            image.set_alpha(int(255 * max(0.2, self.life / 1.5)))
        surface.blit(image, image.get_rect(center=(int(self.x), int(self.y))))


class Explosion(Entity):
    """Purely visual, fades out over a fraction of a second."""

    LIFE = 0.4

    def __init__(self, x: float, y: float, radius: float) -> None:
        super().__init__(x, y)
        self.radius = radius
        self.life = self.LIFE
        self.image = get_assets().misc("boom")

    def update(self, dt: float, game: "Game") -> None:
        self.life -= dt
        if self.life <= 0:
            self.alive = False

    def draw(self, surface: pygame.Surface) -> None:
        t = max(0.0, self.life / self.LIFE)
        size = max(1, int(self.radius * 2 * (1.1 - t * 0.4)))
        if self.image is not None:
            img = pygame.transform.smoothscale(self.image, (size, size))
            img = img.copy()
            img.set_alpha(int(255 * t))
            surface.blit(img, img.get_rect(center=(int(self.x), int(self.y))))
        else:
            s = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 120, 60, int(180 * t)),
                               (size // 2, size // 2), size // 2)
            surface.blit(s, (int(self.x) - size // 2, int(self.y) - size // 2))


class ZombieHead(Entity):
    """A detached head that pops off a dying zombie and arcs to the ground.

    Purely cosmetic -- it never interacts with anything.
    """

    LIFE = 0.9
    GRAVITY = 900.0

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y)
        self.life = self.LIFE
        self.vx = random.uniform(20, 70)
        self.vy = random.uniform(-260, -170)
        self.angle = 0.0
        self.spin = random.uniform(-420, 420)
        self.image = None
        frames = get_assets().zombie("normal").get("body") or []
        if frames:
            # The head sits in the top portion of the full-body frame.
            body = frames[0]
            w, h = body.get_size()
            head = body.subsurface(pygame.Rect(0, 0, w, max(1, h // 3))).copy()
            self.image = head

    def update(self, dt: float, game: "Game") -> None:
        self.life -= dt
        self.vy += self.GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.angle += self.spin * dt
        if self.life <= 0 or self.y > C.LAWN_Y + C.LAWN_H + 40:
            self.alive = False

    def draw(self, surface: pygame.Surface) -> None:
        if self.image is None:
            return
        img = self.image
        if self.angle:
            img = pygame.transform.rotate(img, self.angle)
        alpha = 255 if self.life > 0.3 else int(255 * self.life / 0.3)
        img = img.copy()
        img.set_alpha(max(0, alpha))
        surface.blit(img, img.get_rect(center=(int(self.x), int(self.y))))


class LaneFire(Entity):
    """The jalapeno's fire sweep: one long animation covering a whole lane.

    Uses the original's 755-px ``JalapenoExplode`` frames, scaled to span the
    lawn and drawn along the lane's baseline.
    """

    FRAME_INTERVAL = 0.06

    def __init__(self, row: int) -> None:
        super().__init__(C.LAWN_X, lane_baseline(row))
        self.row = row
        self.anim = Anim(get_assets().plant("JalapenoExplode"),
                         self.FRAME_INTERVAL, loop=False)

    def update(self, dt: float, game: "Game") -> None:
        self.anim.update(dt)
        if self.anim.done or not self.anim.frames:
            self.alive = False

    def draw(self, surface: pygame.Surface) -> None:
        image = self.anim.image()
        if image is None:
            return
        w, h = image.get_size()
        target_w = int(C.LAWN_W * 1.05)
        scale = target_w / w
        img = pygame.transform.smoothscale(image, (target_w, max(1, int(h * scale))))
        rect = img.get_rect(midleft=(int(C.LAWN_X - 10), int(self.y - 20)))
        surface.blit(img, rect)

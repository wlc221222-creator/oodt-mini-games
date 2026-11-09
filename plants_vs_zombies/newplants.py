"""Original PvZ plant abilities, scaled to this game's short battles."""
import math

import pygame

import config as C
from assets import get_assets
from entities import Plant, Projectile, Sunflower


def living_zombies(game):
    return (z for z in game.zombies if z.alive and not z.dying)


class PuffShroom(Plant):
    RANGE = 3 * C.CELL_W
    FIRE_INTERVAL = C.PEA_INTERVAL

    def __init__(self, col, row):
        super().__init__(col, row, 'puffshroom')
        self.timer = 0.3

    def on_tick(self, dt, game):
        if not any(z.row == self.row and 0 <= z.x - self.x <= self.RANGE
                   for z in living_zombies(game)):
            return
        self.timer -= dt
        if self.timer <= 0:
            self.timer = self.FIRE_INTERVAL
            game.projectiles.append(Projectile(self.x + 16, self.baseline - 24,
                C.PEA_DAMAGE, 'BulletMushRoom', self.row, max_x=self.x + self.RANGE))


class SunShroom(Plant):
    GROW_TIME = 120.0
    PRODUCE_INTERVAL = Sunflower.PRODUCE_INTERVAL

    def __init__(self, col, row):
        super().__init__(col, row, 'sunshroom')
        self.age = 0.0
        self.grown = False
        self.timer = self.PRODUCE_INTERVAL * 0.5

    def on_tick(self, dt, game):
        self.age += dt
        if not self.grown and self.age >= self.GROW_TIME:
            self.grown = True
            self.anim.set_frames(get_assets().plant('SunShroomBig'), reset=True)
        self.timer -= dt
        if self.timer <= 0:
            self.timer = self.PRODUCE_INTERVAL
            game.spawn_sun(self.x, self.baseline - 20, 25 if self.grown else 15, falls=False)


class ScaredyShroom(Plant):
    FEAR_RADIUS = 1.5 * C.CELL_W

    def __init__(self, col, row):
        super().__init__(col, row, 'scaredyshroom')
        self.timer = 0.5
        self.afraid = False

    def on_tick(self, dt, game):
        scared = any(math.hypot(z.x - self.x, z.y - self.baseline) < self.FEAR_RADIUS
                     for z in living_zombies(game))
        if scared != self.afraid:
            self.afraid = scared
            self.anim.set_frames(get_assets().plant('ScaredyShroomCry' if scared else 'ScaredyShroom'), reset=True)
        if scared or not game.lane_has_zombie(self.row, self.x):
            return
        self.timer -= dt
        if self.timer <= 0:
            self.timer = C.PEA_INTERVAL
            game.projectiles.append(Projectile(self.x + 20, self.baseline - 42,
                                               C.PEA_DAMAGE, 'BulletMushRoom', self.row))


class Chomper(Plant):
    DIGEST_TIME = 42.0
    RANGE = 1.5 * C.CELL_W

    def __init__(self, col, row):
        super().__init__(col, row, 'chomper')
        self.digest_timer = 0.0
        self.bite_timer = 0.0

    def on_tick(self, dt, game):
        if self.digest_timer > 0:
            self.digest_timer = max(0, self.digest_timer - dt)
            self.bite_timer = max(0, self.bite_timer - dt)
            name = 'ChomperAttack' if self.bite_timer > 0 else ('ChomperDigest' if self.digest_timer > 0 else 'Chomper')
            self.anim.set_frames(get_assets().plant(name))
            return
        targets = [z for z in living_zombies(game)
                   if z.row == self.row and -20 <= z.x - self.x <= self.RANGE]
        if targets:
            target = min(targets, key=lambda z: abs(z.x - self.x))
            target.alive = False  # Swallowed whole: no detached head or corpse.
            self.digest_timer = self.DIGEST_TIME
            self.bite_timer = 0.7
            self.anim.set_frames(get_assets().plant('ChomperAttack'), reset=True)

    def draw(self, surface):
        super().draw(surface)
        if self.digest_timer > 0:
            self.draw_status(surface, f'{math.ceil(self.digest_timer)}s')


class Squash(Plant):
    RANGE = 1.5 * C.CELL_W
    AIM_TIME = 0.6
    JUMP_TIME = 0.5

    def __init__(self, col, row):
        super().__init__(col, row, 'squash')
        self.target_x = None
        self.action_timer = 0.0
        self.jump_progress = 0.0
        self.edible = True

    def on_tick(self, dt, game):
        if self.target_x is None:
            targets = [z for z in living_zombies(game)
                       if z.row == self.row and abs(z.x - self.x) <= self.RANGE]
            if targets:
                self.target_x = min(targets, key=lambda z: abs(z.x - self.x)).x
                self.action_timer = self.AIM_TIME + self.JUMP_TIME
                self.anim.set_frames(get_assets().plant('SquashAim'), reset=True)
            return
        self.action_timer -= dt
        if self.action_timer <= self.JUMP_TIME:
            self.edible = False
            self.jump_progress = min(1.0, 1 - max(0, self.action_timer) / self.JUMP_TIME)
        if self.action_timer <= 0:
            for z in living_zombies(game):
                if z.row == self.row and abs(z.x - self.target_x) <= C.CELL_W * 0.85:
                    z.take_damage(C.CHERRY_DAMAGE, bypass_paper=True)
            self.alive = False

    def draw(self, surface):
        if self.jump_progress <= 0:
            super().draw(surface)
            return
        image = self.anim.image()
        if image:
            t = self.jump_progress
            x = self.x + (self.target_x - self.x) * t
            y = self.baseline - math.sin(t * math.pi) * 105
            pygame.draw.ellipse(surface, (45, 55, 25), (int(self.target_x) - 25, int(self.baseline) - 6, 50, 10))
            surface.blit(image, image.get_rect(midbottom=(int(x), int(y))))


class Spikeweed(Plant):
    edible = False

    def __init__(self, col, row):
        super().__init__(col, row, 'spikeweed')
        self.timer = 0.0

    def on_tick(self, dt, game):
        self.timer -= dt
        if self.timer > 0:
            return
        targets = [z for z in living_zombies(game)
                   if z.row == self.row and abs(z.x - self.x) <= C.CELL_W * 0.5]
        if targets:
            self.timer = 1.0
            for z in targets:
                z.take_damage(10, bypass_paper=True)


class IceShroom(Plant):
    def __init__(self, col, row):
        super().__init__(col, row, 'iceshroom')
        self.timer = 1.0

    def on_tick(self, dt, game):
        self.timer -= dt
        if self.timer > 0:
            return
        for z in living_zombies(game):
            if 0 <= z.x <= C.SCREEN_W:
                z.take_damage(10, bypass_paper=True)
                z.freeze()
        game.frost_timer = 0.7
        self.alive = False


NEW_PLANT_CLASSES = {
    'puffshroom': PuffShroom, 'sunshroom': SunShroom, 'scaredyshroom': ScaredyShroom,
    'chomper': Chomper, 'squash': Squash, 'spikeweed': Spikeweed, 'iceshroom': IceShroom,
}

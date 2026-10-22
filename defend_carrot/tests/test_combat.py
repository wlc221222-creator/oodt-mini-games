"""Actual hit, status, control resistance and upgrade/sale economy behavior."""
import os
from pathlib import Path
import sys
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pygame
import config as C
from game import Game
from entities import (Orange, Melon, IceStar, PoisonPin, RocketTower, Snowflake,
                      Bullet, Golem, BigBoss, tile_center)
from art import character_image


def main():
    g = Game()
    g.reset(7)
    try:
        def targets(positions):
            g.monsters = []
            g.bullets = []
            for x, y in positions:
                m = Golem(g)
                m.x, m.y = x, y
                m.hp = m.max_hp = 10000
                g.monsters.append(m)
            return g.monsters

        tower = Orange(3, 4)
        y = tower.y
        monsters = targets([(200, y), (240, y), (260, y)])
        tower.fire(monsters[0], g)
        shot = g.bullets[0]
        shot.update(.5, g)
        assert all(m.hp == 10000 - tower.damage for m in monsters)
        shot.update(.01, g)
        assert all(m.hp == 10000 - tower.damage for m in monsters)

        tower = Melon(5, 5)
        inside, neighbor, outside = targets([(tower.x + 40, tower.y),
                                            (tower.x - 40, tower.y), (tower.x + 200, tower.y)])
        tower.fire(inside, g)
        assert inside.hp == neighbor.hp == 10000 - tower.damage and outside.hp == 10000
        assert not g.bullets  # Sun attacks around the tower rather than firing a homing shot.

        tower = IceStar(5, 5)
        inside, neighbor, outside = targets([(300, 300), (330, 300), (400, 300)])
        tower.fire(inside, g)
        g.bullets[0].hit(g)
        normal = inside.speed_tiles * C.TILE
        assert abs(inside.speed - normal * .55) < 1e-6
        assert neighbor.slow_effects and not outside.slow_effects
        inside.apply_slow(.7, 3)
        assert abs(inside.speed - normal * .55) < 1e-6
        inside.update(2.1, g)
        assert abs(inside.speed - normal * .7) < 1e-6

        tower = PoisonPin(5, 5)
        monster, = targets([(300, 300)])
        tower.fire(monster, g)
        g.bullets[0].hit(g)
        monster.update(1, g)
        assert abs(monster.hp - (10000 - tower.damage * 1.4)) < 1e-6
        monster.update(5, g)
        expected = 10000 - tower.damage - tower.damage * .4 * 3
        assert abs(monster.hp - expected) < 1e-6
        monster.update(1, g)
        assert abs(monster.hp - expected) < 1e-6

        tower = Snowflake(5, 5)
        monster, = targets([(tower.x + 30, tower.y)])
        tower.fire(monster, g)
        position = monster.x, monster.y
        monster.update(.2, g)
        assert (monster.x, monster.y) == position and monster.speed == 0
        remaining = monster.freeze_time
        monster.apply_freeze(.1)
        assert monster.freeze_time == remaining
        monster.update(.5, g)
        assert monster.speed > 0
        boss = BigBoss(g)
        boss.apply_freeze(1)
        assert boss.freeze_time == 1
        boss.apply_slow(.4, 2)
        assert min(boss.slow_effects) == .4

        tower = RocketTower(3, 4)
        monsters = targets([(200, tower.y), (230, tower.y)])
        tower.fire(monsters[0], g)
        g.bullets[0].update(1, g)
        assert all(abs(m.hp - (10000 - tower.damage * 1.65)) < 1e-6 for m in monsters)

        g.reset(7)
        cell = next((c, r) for r in range(C.GRID_ROWS) for c in range(C.GRID_COLS) if g.can_build(c, r))
        g.selected = 'apple'
        g._on_click(tile_center(*cell))
        g.inspected = tower = g.fruits[0]
        first_image = pygame.image.tobytes(character_image('apple', level=1), 'RGBA')
        g.coins = tower.upgrade_cost - 1
        assert not g.upgrade_tower() and tower.level == 1
        for expected in (2, 3):
            g.coins = tower.upgrade_cost
            assert g.upgrade_tower() and tower.level == expected and g.coins == 0
        assert not g.upgrade_tower()
        assert tower.damage > C.FRUITS['apple']['damage'] and tower.rng > C.FRUITS['apple']['rng'] * C.TILE
        assert pygame.image.tobytes(character_image('apple', level=3), 'RGBA') != first_image
        g.state = 'paused'
        assert not g.sell_tower() and tower in g.fruits
        g.state = 'playing'
        value = tower.sell_value
        assert g.sell_tower() and g.coins == value and not g.fruits
        assert not g.sell_tower() and g.coins == value
        print('PASS: piercing, sun area attack, splash slow, finite poison, freeze, rocket blast, three-tier upgrades and sale accounting')
    finally:
        pygame.quit()


if __name__ == '__main__':
    main()

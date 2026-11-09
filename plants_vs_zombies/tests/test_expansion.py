"""Behavioural regression tests for original-PvZ expansion and old saves."""
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pygame
import config as C
import save
from game import Game, PLANT_CLASSES
from entities import Zombie, Projectile, Peashooter
from newplants import PuffShroom, SunShroom, ScaredyShroom, Chomper, Squash, Spikeweed, IceShroom
from garden_ui import MAP_NEXT_RECT, MAP_PREV_RECT, SEED_NEXT_RECT


def main():
    original = save.SAVE_PATH
    try:
        with tempfile.TemporaryDirectory() as temp:
            save.SAVE_PATH = str(Path(temp) / 'save.json')
            legacy = {'unlocked': 6, 'plants': C.START_PLANTS + C.LEVEL_REWARDS[:7]}
            save.save(legacy)
            original_bytes = Path(save.SAVE_PATH).read_bytes()
            g = Game()
            assert g.unlocked == 7 and not g.adventure_completed()
            assert g.owned_plants == legacy['plants']
            assert Path(save.SAVE_PATH).read_bytes() == original_bytes
            g.start_adventure()
            assert g.level['id'] == '2-3'
            save.save({'unlocked': 2, 'plants': C.START_PLANTS + C.LEVEL_REWARDS[:2]})
            g._load_progress()
            assert g.unlocked == 2
            g.start_level(0, 'select')
            g.seed_page = 1
            g.seeds = []
            g._on_choose_click(g._chooser_rect(0).center)
            assert not g.seeds, 'locked second-page seeds must not be selectable'
            print('PASS: completed seven-level save resumes at 2-3; partial saves preserve progress')

            def click(rect):
                view = g.viewport()
                pos = (round(view.x + rect.centerx * view.w / 800),
                       round(view.y + rect.centery * view.h / 600))
                g.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))

            g.screen = pygame.display.set_mode((1200, 800))
            g.state = 'levelselect'
            g.level_page = 0
            click(MAP_NEXT_RECT)
            assert g.level_page == 1
            click(g._level_rect(7))
            assert g.state == 'levelselect', 'locked second-page level must stay locked'
            g.unlocked = 13
            g.owned_plants = list(C.SHOP_ORDER)
            click(g._level_rect(7))
            assert g.level_index == 7 and g.state == 'choosing'
            g.seeds = []
            click(SEED_NEXT_RECT)
            assert g.seed_page == 1
            for i, kind in enumerate(g.visible_seeds()):
                click(g._chooser_rect(i))
                assert kind in g.seeds
            for kind in g.seeds:
                assert kind in C.SHOP_ORDER[10:]
            g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT))
            assert g.seed_page == 0 and len(g.seeds) == 6
            click(g._chooser_rect(0))
            click(g._chooser_rect(1))
            assert len(g.seeds) == 8
            g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
            assert g.state == 'playing'
            g.state = 'levelselect'
            click(MAP_PREV_RECT)
            click(g._level_rect(0))
            assert g.level_index == 0
            print('PASS: scaled map/seed pagination, locked levels, cross-page selections and battle start')

            def fresh(index=7):
                g.start_level(index, 'select')
                g.state = 'playing'
                g.owned_plants = list(C.SHOP_ORDER)
                g.seeds = list(C.SHOP_ORDER)
                return g

            for kind in ('puffshroom', 'sunshroom', 'scaredyshroom', 'chomper', 'squash', 'spikeweed', 'iceshroom'):
                fresh()
                g.sun = 500
                g.selected = kind
                g._on_click((75, 450))
                assert g.plant_at(0, 3).kind == kind
                assert g.sun == 500 - C.PLANTS[kind]['cost']
                assert g.cooldowns[kind] == C.PLANTS[kind]['recharge']
            print('PASS: all seven new plants can be purchased and planted with correct costs and recharge')

            fresh()
            puff = PuffShroom(2, 2)
            far = Zombie(puff.x + puff.RANGE + 35, 2, 'normal')
            g.zombies = [far]
            puff.update(1, g)
            assert not g.projectiles
            far.x = puff.x + puff.RANGE - 5
            puff.update(1, g)
            assert len(g.projectiles) == 1 and g.projectiles[0].max_x == puff.x + puff.RANGE
            shot = g.projectiles[0]
            shot.update(2, g)
            assert not shot.alive
            for kind in ('puffshroom', 'sunshroom', 'scaredyshroom', 'iceshroom'):
                fresh(0)
                plant = PLANT_CLASSES[kind](2, 2)
                g.zombies = [Zombie(plant.x + 40, 2, 'normal')]
                plant.update(4, g)
                assert plant.sleeping and plant.alive and not g.projectiles and not g.suns
                assert g.zombies[0].freeze_timer == 0
            print('PASS: puff short range and all four mushrooms sleep during daytime')

            fresh()
            sun = SunShroom(0, 2)
            sun.timer = 0
            sun.update(0.1, g)
            assert g.suns[-1].amount == 15
            sun.age = sun.GROW_TIME - 0.1
            sun.timer = 0.05
            sun.update(0.2, g)
            assert sun.grown and g.suns[-1].amount == 25
            scared = ScaredyShroom(1, 2)
            g.projectiles = []
            far = Zombie(650, 2, 'normal')
            g.zombies = [far]
            scared.update(1, g)
            assert len(g.projectiles) == 1
            near = Zombie(scared.x + 10, 1, 'normal')
            g.zombies.append(near)
            scared.update(2, g)
            assert scared.afraid and len(g.projectiles) == 1
            near.alive = False
            scared.update(2, g)
            assert not scared.afraid and len(g.projectiles) == 2
            print('PASS: sun-shroom matures from 15 to 25; scaredy detects adjacent lanes and recovers')

            fresh()
            chomp = Chomper(2, 2)
            first = Zombie(chomp.x + 80, 2, 'bucket')
            second = Zombie(chomp.x + 100, 2, 'newspaper')
            g.zombies = [first, second]
            chomp.update(0.1, g)
            assert not first.alive and second.alive and chomp.digest_timer == 42
            chomp.update(41, g)
            assert second.alive
            chomp.update(1, g)
            chomp.update(0.1, g)
            assert not second.alive
            fresh()
            squash = Squash(4, 2)
            targets = [Zombie(squash.x - 45, 2, 'bucket'), Zombie(squash.x - 20, 2, 'newspaper')]
            other = Zombie(squash.x - 45, 1, 'normal')
            g.zombies = targets + [other]
            squash.update(0.1, g)
            assert squash.target_x is not None and not any(z.dying for z in targets)
            squash.update(0.8, g)
            assert 0 < squash.jump_progress < 1
            squash.draw(g.canvas)
            squash.update(0.5, g)
            assert not squash.alive and all(z.dying for z in targets) and not other.dying
            print('PASS: chomper consumes one armoured zombie with 42s digestion; squash hits nearby group in its lane')

            fresh()
            spikes = Spikeweed(3, 2)
            reader = Zombie(spikes.x, 2, 'newspaper')
            g.plants = [spikes]
            g.zombies = [reader]
            hp, paper = reader.hp, reader.paper_hp
            spikes.update(0.1, g)
            assert reader.hp == hp - 10 and reader.paper_hp == paper
            assert g.plant_in_front(2, reader.x) is None
            reader.update(0.1, g)
            assert reader.x < spikes.x and spikes.hp == spikes.max_hp
            reader.apply_slow()
            assert reader.slow_timer == 0
            reader.take_damage(paper + 5)
            assert reader.paper_hp == 0 and reader.hp == hp - 15 and reader.rage_timer > 0
            old_x = reader.x
            reader.update(0.4, g)
            assert reader.x == old_x
            reader.update(0.5, g)
            assert reader.current_speed == reader.speed * 2.5
            reader.apply_slow()
            assert reader.current_speed == reader.speed * 2.5 * C.SNOW_SLOW_FACTOR
            print('PASS: inedible ground damage bypasses paper; broken newspaper pauses then enrages and can be slowed')

            fresh()
            ice = IceShroom(0, 0)
            guard = Peashooter(3, 2)
            enemies = [Zombie(400, 0, 'normal'), Zombie(guard.x + 10, 2, 'newspaper'), Zombie(830, 4, 'bucket')]
            g.plants = [guard]
            g.zombies = enemies
            ice.update(1.1, g)
            assert not ice.alive and all(z.freeze_timer > 0 for z in enemies[:2])
            assert enemies[2].freeze_timer == 0
            hp = guard.hp
            old_x = enemies[1].x
            enemies[1].update(1, g)
            assert guard.hp == hp and enemies[1].x == old_x
            enemies[1].update(3, g)
            assert enemies[1].freeze_timer == 0 and enemies[1].slow_timer > 0
            dead = Zombie(300, 1, 'normal')
            dead.start_dying()
            g.zombies = [dead]
            shot = Projectile(300, 100, 22, 'PeaNormal', 1)
            shot.update(0, g)
            assert shot.alive, 'death animations must not consume projectiles'
            print('PASS: ice freezes all visible lanes, stops attacks, leaves later spawns unaffected; corpses do not block shots')

            for name in ('ChomperAttack', 'ChomperDigest', 'PuffShroomSleep', 'SunShroomBig',
                         'ScaredyShroomCry', 'IceShroomSleep', 'SquashAim'):
                assert g.assets.plant(name), name
            assert g.assets.bullet('BulletMushRoom') is not None
            for kind in ('flag', 'newspaper'):
                assert g.assets.zombie(kind)['walk'] and g.assets.zombie(kind)['attack']
            assert g.assets.zombie('newspaper')['rage_walk']
            for index in range(len(C.LEVELS)):
                fresh(index)
                g.seed_page = 1
                g.state = 'choosing'
                g.draw()
            for page in (0, 1):
                g.level_page = page
                g.state = 'levelselect'
                g.draw()
            print('PASS: expansion animations, all 14 choosers and both map pages render')
    finally:
        save.SAVE_PATH = original
        pygame.quit()


if __name__ == '__main__':
    main()

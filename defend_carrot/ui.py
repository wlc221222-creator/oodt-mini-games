"""Chinese typography and menu/pause/result screens for the fruit defense game."""
import os
import math
from functools import lru_cache

import pygame

import config as C
from art import fruit_image, character_image, WALK_FRAMES, CARROT_FRAMES, CARROT_HEALTH_FRAMES
from entities import tile_center
from scenery import field_image
from presentation import INK, PAPER, MUTED, GOLD, panel, button, scene, motes, leaves, star, lock


def load_font(size):
    for path in (r'C:\Windows\Fonts\msyh.ttc', r'C:\Windows\Fonts\simhei.ttf',
                 '/System/Library/Fonts/PingFang.ttc',
                 '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'):
        if os.path.exists(path):
            try:
                return pygame.font.Font(path, size)
            except (OSError, pygame.error):
                continue
    return pygame.font.Font(None, size)


@lru_cache(maxsize=8)
def panel_background(size, dark=False):
    image = pygame.Surface(size)
    top, bottom = ((48, 80, 57), (27, 54, 40)) if dark else ((249, 242, 215), (220, 206, 163))
    for y in range(size[1]):
        t = y / max(1, size[1] - 1)
        color = tuple(round(a + (b - a) * t) for a, b in zip(top, bottom))
        pygame.draw.line(image, color, (0, y), (size[0], y))
    pygame.draw.line(image, (181, 159, 93), (0, 0), (size[0], 0), 2)
    return image


class GameUI:
    primary_rect = pygame.Rect(245, 365, 310, 48)
    secondary_rect = pygame.Rect(245, 425, 310, 42)
    level_button_rect = pygame.Rect(245, 480, 310, 40)
    pause_rect = pygame.Rect(520, C.HUD_H + C.FIELD_H + 4, 120, 28)
    speed_rect = pygame.Rect(650, C.HUD_H + C.FIELD_H + 40, 130, 28)
    upgrade_rect = pygame.Rect(520, C.HUD_H + C.FIELD_H + 128, 125, 32)
    sell_rect = pygame.Rect(655, C.HUD_H + C.FIELD_H + 128, 125, 32)
    back_rect = pygame.Rect(24, 24, 120, 34)

    def __init__(self, game):
        self.game = game
        self.fonts = {size: load_font(size) for size in (13, 15, 18, 22, 28, 32, 38, 60)}
        for size in (28, 32, 38, 60):
            self.fonts[size].set_bold(True)
        self.time = 0.0

    def update(self, dt):
        # Presentation keeps breathing in menus, while the simulation stays paused.
        self.time = (self.time + max(0.0, dt)) % 3600

    def text(self, value, center, size=18, color=(245, 235, 204)):
        image = self.fonts[size].render(value, True, color)
        self.game.screen.blit(image, image.get_rect(center=center))

    def button(self, rect, label, tone='green', enabled=True):
        button(self.game.screen, rect, label, self.fonts[15 if rect.h < 40 else 22], tone, enabled)

    def heading(self, value, center):
        glyph = self.fonts[60].render(value, True, (255, 221, 111))
        outline = self.fonts[60].render(value, True, (255, 253, 220))
        shadow = self.fonts[60].render(value, True, (65, 109, 61))
        rect = glyph.get_rect(center=center)
        for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, -2), (-2, 2), (2, 2)):
            self.game.screen.blit(shadow, rect.move(dx, dy + 5))
            self.game.screen.blit(outline, rect.move(dx, dy))
        self.game.screen.blit(glyph, rect)

    def draw_shop(self):
        g = self.game
        base = C.SCREEN_H - C.SHOP_H
        g.screen.blit(panel_background((C.SCREEN_W, C.SHOP_H)), (0, base))
        panel(g.screen, (514, base + 34, 274, 132), fill=(238, 233, 195), radius=10, shadow=2)
        for i, kind in enumerate(C.SHOP_ORDER):
            spec, rect = C.FRUITS[kind], g._card_rect(i)
            opened = kind in g.available_towers
            selected = g.selected == kind
            affordable = opened and g.coins >= spec['cost']
            color = (255, 243, 184) if selected else (255, 251, 232) if affordable else (218, 218, 201)
            hovered = rect.collidepoint(pygame.mouse.get_pos())
            panel(g.screen, rect, color, GOLD if selected or hovered and opened else (153, 155, 109),
                  radius=8, shadow=2)
            sprite = fruit_image(kind, 46)
            if not affordable:
                sprite = pygame.transform.grayscale(sprite)
            g.screen.blit(sprite, sprite.get_rect(center=(rect.x + 23, rect.y + 30)))
            for value, y in ((spec['label'], 3),
                             (f"{spec['cost']}金币" if opened else f"第{spec['unlock']}关开放", 22),
                             (spec['role'], 39)):
                text = self.fonts[13].render(value, True, (44, 70, 40) if opened else (111, 114, 98))
                g.screen.blit(text, (rect.x + 45, rect.y + y))
            self.text(str(i + 1), (rect.x + 8, rect.y + 8), 13, (74, 104, 51))
            if not opened:
                lock(g.screen, (rect.x + 25, rect.y + 35), 16)
        self.button(self.speed_rect, f'速度 {g.speed_multiplier}倍 [Tab]')
        tower = g.inspected if g.inspected and g.inspected.alive else None
        if tower:
            self.text(f'{tower.label}  {tower.level}级', (580, base + 54), 15, (44, 70, 40))
            self.text(f'伤害{tower.damage:g}  射程{tower.rng / C.TILE:.1f}格', (650, base + 87), 15, (64, 80, 46))
            self.text(f'每{tower.interval:.2f}秒攻击', (650, base + 109), 13, (94, 103, 65))
            self.button(self.upgrade_rect, f'升级 {tower.upgrade_cost} [U]' if tower.upgrade_cost else '已满三级',
                        enabled=bool(tower.upgrade_cost and g.coins >= tower.upgrade_cost))
            self.button(self.sell_rect, f'出售 {tower.sell_value}', 'cream')
        else:
            self.text(f'本关开放 {len(g.available_towers)} / 8 种塔', (580, base + 54), 13, (44, 70, 40))
            self.text('点击场上防御塔，可升级或出售', (650, base + 99), 15, (64, 80, 46))
            self.text(C.LEVELS[g.level_index]['hint'], (650, base + 132), 15, (120, 95, 37))

    def draw_hud(self):
        g = self.game
        g.screen.blit(panel_background((C.SCREEN_W, C.HUD_H), True), (0, 0))
        pygame.draw.rect(g.screen, (31, 57, 40), (9, 7, 155, 42), border_radius=10)
        pygame.draw.circle(g.screen, (165, 113, 34), (32, 28), 14)
        pygame.draw.circle(g.screen, (244, 198, 72), (32, 26), 12)
        pygame.draw.circle(g.screen, (255, 228, 135), (32, 26), 8, 2)
        self.text('金币', (82, 17), 13, (225, 224, 177))
        self.text(str(g.coins), (90, 35), 22, (255, 225, 131))
        level = C.LEVELS[g.level_index]
        image = self.fonts[18].render(level['name'], True, (247, 242, 209))
        g.screen.blit(image, (183, 5))
        self.text(f"第 {min(g.wave_index + 1, len(level['waves']))}/{len(level['waves'])} 波", (534, 19), 15)
        detail = self.fonts[13].render(f'击杀 {g.kills}    积分 {g.score}', True, (196, 216, 173))
        g.screen.blit(detail, (184, 33))
        self.text(f'萝卜生命 {max(0, g.carrot.hp):g}/{C.CARROT_HP}', (693, 13), 13)
        rect = pygame.Rect(605, 28, 176, 15)
        pygame.draw.rect(g.screen, (20, 38, 28), rect.inflate(4, 4), border_radius=8)
        color = ((160, 203, 101) if g.carrot.hp == 3 else
                 (239, 187, 75) if g.carrot.hp == 2 else (237, 117, 94))
        for i in range(C.CARROT_HP):
            left = rect.x + round(i * rect.w / C.CARROT_HP)
            right = rect.x + round((i + 1) * rect.w / C.CARROT_HP)
            slot = pygame.Rect(left + 1, rect.y, right - left - 3, rect.h)
            filled = i < g.carrot.hp
            pygame.draw.rect(g.screen, color if filled else (59, 77, 55), slot, border_radius=4)
            if filled:
                pygame.draw.line(g.screen, (255, 235, 174),
                                 (slot.x + 3, slot.y + 3), (slot.right - 4, slot.y + 3), 2)

    def draw_placement(self, pos=None):
        g = self.game
        cell = g.field_cell(pygame.mouse.get_pos() if pos is None else pos)
        tower = g.inspected if g.inspected and g.inspected.alive else (g.fruit_at(*cell) if cell else None)
        if g.selected and cell is None or not g.selected and tower is None:
            return
        if not g.selected:
            cell = tower.col, tower.row
        col, row = cell
        kind = g.selected or tower.kind
        valid = not g.building_error(cell) if g.selected else True
        color = (127, 235, 149) if valid else (255, 121, 101)
        x, y = tile_center(col, row)
        y -= C.HUD_H
        overlay = pygame.Surface((C.FIELD_W, C.FIELD_H), pygame.SRCALPHA)
        radius = round(C.FRUITS[kind]['rng'] * C.TILE if g.selected else tower.rng)
        pygame.draw.circle(overlay, (*color, 32), (x, y), radius)
        pygame.draw.circle(overlay, (*color, 170), (x, y), radius, 2)
        rect = pygame.Rect(col * C.TILE, row * C.TILE, C.TILE, C.TILE)
        pygame.draw.rect(overlay, (*color, 55), rect, border_radius=5)
        pygame.draw.rect(overlay, (*color, 230), rect, 2, border_radius=5)
        if g.selected:
            ghost = fruit_image(kind, C.TOWER_SPRITE_SIZE).copy()
            ghost.set_alpha(150)
            overlay.blit(ghost, ghost.get_rect(center=(x, y)))
        g.screen.blit(overlay, (0, C.HUD_H))

    def draw_battle_info(self, pos=None):
        g = self.game
        if g.notice_timer > 0:
            message = g.notice
        elif g.selected:
            cell = g.field_cell(pygame.mouse.get_pos() if pos is None else pos)
            reason = g.building_error(cell) if cell else "移动到草地查看射程，右键取消"
            message = f"{C.FRUITS[g.selected]['label']} · {reason or '可建造，左键确认'}"
        elif g.wave_timer < 0:
            message = f"下一波还有 {math.ceil(-g.wave_timer)} 秒 · 提前布置防线"
        else:
            message = f"{C.LEVELS[g.level_index]['wave_labels'][g.wave_index]} · 场上 {len(g.monsters)} 只 · 点击炮塔升级"
        # The last map row remains unobstructed; feedback sits above the cards.
        strip = pygame.Rect(10, C.SCREEN_H - C.SHOP_H + 4, 500, 27)
        pygame.draw.rect(g.screen, (44, 68, 45), strip, border_radius=8)
        self.text(message, (260, C.SCREEN_H - C.SHOP_H + 16), 13,
                  (255, 218, 145) if g.notice_timer > 0 else (235, 244, 211))

    def draw_menu(self):
        g = self.game
        g.screen.blit(scene(), (0, 0))
        motes(g.screen, self.time)
        # Layered type and real character sprites form the home-screen sign.
        self.heading('保卫萝卜', (400, 120))
        panel(g.screen, (257, 173, 286, 34), (82, 132, 74), (68, 108, 59), radius=15, shadow=2)
        self.text('经典防线  /  今天也要守护你', (400, 189), 15)
        panel(g.screen, (195, 235, 410, 332), border=(173, 155, 93), radius=25, shadow=8)
        leaves(g.screen, (209, 244), 35)
        leaves(g.screen, (592, 550), 32)
        self.text('小小萝卜，大大冒险', (400, 273), 28, INK)
        unlocked = g.progress['unlocked']
        completed = len(g.progress['best'])
        self.text(f'已开放 {unlocked} / 8 关  ·  已守住 {completed} 关', (400, 313), 15, MUTED)
        for i in range(8):
            pygame.draw.circle(g.screen, (223, 173, 62) if str(i) in g.progress['best'] else
                               (123, 166, 83) if i < unlocked else (205, 211, 172), (316 + i * 24, 337), 5)
        self.button(self.primary_rect, f'开始第 {unlocked} 关冒险  [Enter]', 'orange')
        self.button(self.secondary_rect, '防御塔与怪物图鉴  [I]')
        self.button(self.level_button_rect, '选择关卡 / 重玩  [L]', 'cream')
        self._menu_character('carrot', (117, 437), 235, 0)
        self._menu_character('bat', (688, 343), 100, 1.5)
        self._menu_character('slime', (685, 492), 105, 3)
        self._menu_character('golem', (745, 546), 105, 4)
        self.text('只有三滴血，也要全力守住！', (400, 603), 18, INK)
        for i, kind in enumerate(C.SHOP_ORDER):
            x = 169 + i * 66
            pygame.draw.ellipse(g.screen, (125, 160, 77), (x - 24, 681, 48, 10))
            sprite = fruit_image(kind, 55)
            g.screen.blit(sprite, sprite.get_rect(center=(x, 655 + round(3 * math.sin(self.time * 2 + i)))))
        self.text('天际云海  ·  绿色丛林  ·  金色沙海', (400, 718), 15, (66, 104, 57))
        self.text('进度自动保存到本地  ·  Esc 退出', (400, 740), 13, (84, 115, 65))

    def _menu_character(self, kind, center, size, phase):
        t = self.time
        # A brief blink, separate from the carrot's in-battle health animation.
        if kind == 'carrot':
            blink = t % 4
            frame = CARROT_FRAMES[min(3, int((blink - 3) * 8))] if blink >= 3 else CARROT_FRAMES[0]
        else:
            frames = WALK_FRAMES[kind]
            frame = frames[int(t * 4 + phase) % len(frames)]
        sprite = character_image(kind, size, frame=frame)
        x, y = center
        pygame.draw.ellipse(self.game.screen, (119, 157, 88), (x - size * .3, y + size * .37, size * .6, 12))
        if sprite:
            self.game.screen.blit(sprite, sprite.get_rect(center=(x, y + round(5 * math.sin(t * 2 + phase)))))

    def draw_overlay(self):
        g = self.game
        overlay = pygame.Surface(g.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((17, 40, 29, 172))
        g.screen.blit(overlay, (0, 0))
        panel(g.screen, (100, 123, 600, 435), radius=25, border=(185, 159, 86), shadow=8)
        banner = pygame.Rect(151, 143, 498, 63)
        pygame.draw.polygon(g.screen, (65, 103, 55), [(131, 155), (161, 155), (161, 207), (131, 207), (143, 181)])
        pygame.draw.polygon(g.screen, (65, 103, 55), [(639, 155), (669, 155), (657, 181), (669, 207), (639, 207)])
        panel(g.screen, banner, (91, 143, 72) if g.state != 'lost' else (147, 112, 82),
              (73, 107, 58), radius=12, shadow=3)
        titles = {'paused': '休息一下，再出发', 'levelclear': '本关守住了！',
                  'won': '八关通关，守护成功！', 'lost': '再试一次，守住萝卜'}
        self.text(titles[g.state], (400, 174), 32)
        sprite = character_image('carrot', 140, frame=CARROT_HEALTH_FRAMES[max(0, min(3, int(g.carrot.hp)))])
        g.screen.blit(sprite, sprite.get_rect(center=(207, 278)))
        self.text(C.LEVELS[g.level_index]['name'], (463, 231), 18, INK)
        for x, value, label in ((330, g.score, '累计积分'), (440, g.kills, '击败怪物'),
                                 (550, f'{max(0, g.carrot.hp):g} / 3', '萝卜生命')):
            panel(g.screen, (x - 46, 257, 96, 65), (239, 235, 197), (200, 192, 134), radius=10, shadow=2)
            self.text(str(value), (x + 2, 278), 22, INK)
            self.text(label, (x + 2, 305), 13, MUTED)
        self.text(f'防守用时 {g.elapsed:.1f} 秒  ·  剩余 {g.coins} 金币', (400, 344), 15, MUTED)
        if g.state in ('levelclear', 'won'):
            for i in range(3):
                star(g.screen, (177 + i * 28, 332), 12,
                     (255, 208, 71) if i < g.carrot.hp else (194, 197, 165))
        primary = ('继续防守  [P / Enter]' if g.state == 'paused' else
                   f'前往第 {g.level_index + 2} 关  [Enter]' if g.state == 'levelclear' else '重新挑战  [R / Enter]')
        self.button(self.primary_rect, primary, 'orange')
        self.button(self.secondary_rect, '返回主菜单  [Esc]', 'cream')
        tip = ('下一关恢复三血，重新分配开局金币' if g.state == 'levelclear' else
               '八关全部守住啦！可以在冒险地图挑战满血通关' if g.state == 'won' else
               '搭配减速与范围攻击，拐弯处更适合集中火力' if g.state == 'lost' else
               '喝口水，想一想下一座塔要放在哪里')
        self.text(tip, (400, 499), 15, INK)
        leaves(g.screen, (122, 538), 30)
        leaves(g.screen, (678, 538), 30)
        footnote = ('通关进度暂未写入，请检查存档目录权限' if g.save_error and g.state in ('levelclear', 'won')
                    else '通关进度已保存' if g.state in ('levelclear', 'won') else '按 I 查看防守手册')
        self.text(footnote, (400, 533), 13, (160, 96, 54) if g.save_error else MUTED)

    @staticmethod
    def level_rect(index):
        return pygame.Rect(25 + index % 4 * 190, 190 + index // 4 * 210, 175, 185)

    def draw_level_select(self):
        g = self.game
        g.screen.blit(scene(2), (0, 0))
        motes(g.screen, self.time)
        self.button(self.back_rect, '‹ 返回 [L]', 'cream')
        self.text('冒险地图', (400, 83), 38, (255, 248, 206))
        self.text('冒险地图', (400, 80), 38, INK)
        panel(g.screen, (204, 120, 392, 37), (255, 248, 213), radius=16, shadow=2)
        self.text('跨过云海，穿过丛林，守到沙海尽头', (400, 138), 18, INK)
        self.text(f"已开放 {g.progress['unlocked']} / 8", (695, 41), 15, INK)
        # A light dotted trail sits behind the cards, leaving their content clear.
        centers = [self.level_rect(i).center for i in range(8)]
        for start, end in zip(centers, centers[1:]):
            distance = math.dist(start, end)
            for step in range(0, round(distance), 15):
                t = step / distance
                pos = (round(start[0] + (end[0] - start[0]) * t),
                       round(start[1] + (end[1] - start[1]) * t))
                pygame.draw.circle(g.screen, (247, 238, 183), pos, 3)
        for i, level in enumerate(C.LEVELS):
            rect = self.level_rect(i)
            opened = i < g.progress['unlocked']
            best = g.progress['best'].get(str(i))
            hover = opened and rect.collidepoint(pygame.mouse.get_pos())
            panel(g.screen, rect, PAPER if opened else (219, 224, 187),
                  GOLD if best == 3 or hover else (114, 144, 79), shadow=7 if hover else 4)
            g.screen.blit(level_thumbnail(i, not opened), (rect.x + 5, rect.y + 5))
            pygame.draw.circle(g.screen, (63, 100, 60), (rect.x + 22, rect.y + 21), 15)
            self.text(str(i + 1).zfill(2), (rect.x + 22, rect.y + 21), 15)
            if not opened:
                lock(g.screen, (rect.centerx, rect.y + 48), 26)
            elif best:
                for n in range(3):
                    star(g.screen, (rect.right - 65 + n * 21, rect.y + 77), 9,
                         (255, 211, 75) if n < best else (198, 206, 173))
            else:
                pygame.draw.rect(g.screen, (78, 128, 67), (rect.right - 66, rect.y + 65, 56, 24), border_radius=9)
                self.text('出发 ›', (rect.right - 38, rect.y + 77), 13)
            self.text(level['name'].split(' · ')[-1], (rect.centerx, rect.y + 115), 18, INK)
            self.text(f"{len(level['waves'])} 波  ·  {len(level['towers'])} 种塔", (rect.centerx, rect.y + 143), 15, MUTED)
            label = f'最佳剩余 {best}/3 血' if best else f"开局 {level['start_coins']} 金币" if opened else '通关前一关解锁'
            self.text(label, (rect.centerx, rect.y + 168), 13, (135, 109, 47))
        panel(g.screen, (135, 619, 530, 70), border=(154, 161, 102), shadow=4)
        star(g.screen, (167, 644), 13)
        self.text('点选已开放关卡，开始守护萝卜', (413, 640), 18, INK)
        self.text('金色边框代表满血通关  ·  Esc / L 返回', (400, 671), 15, MUTED)


@lru_cache(maxsize=16)
def level_thumbnail(index, locked=False):
    image = pygame.transform.smoothscale(field_image(index), (165, 90))
    if locked:
        image = pygame.transform.grayscale(image)
        tint = pygame.Surface(image.get_size(), pygame.SRCALPHA)
        tint.fill((66, 83, 54, 82))
        image.blit(tint, (0, 0))
    rounded = pygame.Surface(image.get_size(), pygame.SRCALPHA)
    pygame.draw.rect(rounded, (255, 255, 255), rounded.get_rect(), border_radius=11)
    image = image.convert_alpha()
    image.blit(rounded, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return image

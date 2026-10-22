"""Two-page unit guide; opening it freezes the entire simulation."""
import pygame
import config as C
from ui import load_font
from art import fruit_image, character_image, WALK_FRAMES
from presentation import INK, PAPER, MUTED, panel, button, scene, leaves, star


class FieldGuide:
    button_rect = pygame.Rect(650, C.HUD_H + C.FIELD_H + 4, 130, 28)
    close_rect = pygame.Rect(642, 28, 125, 36)
    towers_rect = pygame.Rect(28, 84, 170, 34)
    monsters_rect = pygame.Rect(210, 84, 170, 34)

    def __init__(self):
        self.font = load_font(16)
        self.title_font = load_font(24)
        self.small_font = load_font(13)
        self.button_font = load_font(15)
        self.name_font = load_font(18)
        self.tab = 'towers'

    def text(self, surface, value, pos, title=False, color=(40, 57, 38)):
        surface.blit((self.title_font if title else self.font).render(value, True, color), pos)

    def draw_button(self, surface):
        button(surface, self.button_rect, '图鉴 [I]', self.button_font)

    def draw(self, surface, time=0):
        surface.blit(scene(2), (0, 0))
        panel(surface, (14, 14, 772, 717), (247, 244, 214), (153, 163, 99), radius=23)
        pygame.draw.line(surface, (211, 207, 164), (400, 165), (400, 658), 2)
        leaves(surface, (38, 34), 29)
        self.text(surface, '萝卜的防守手册', (74, 29), True, INK)
        self.text(surface, '认识伙伴，读懂每一次来袭', (300, 35), color=MUTED)
        button(surface, self.close_rect, '返回 [I / Esc]', self.button_font, 'cream')
        for rect, label, tab in ((self.towers_rect, '八种防御塔', 'towers'), (self.monsters_rect, '八类怪物', 'monsters')):
            button(surface, rect, label, self.font, 'green' if self.tab == tab else 'cream')
        self.text(surface, 'Tab 切换 · 查看时战斗暂停 · 一级 / 基础值，后关怪物逐步增强', (28, 132), color=MUTED)
        items = list(C.SHOP_ORDER) if self.tab == 'towers' else list(C.MONSTERS)
        for i, kind in enumerate(items):
            x, y = 28 + i % 2 * 390, 165 + i // 2 * 128
            panel(surface, (x, y, 365, 115), PAPER, (192, 190, 133), radius=13, shadow=3)
            portrait_color = ((231, 236, 177), (221, 236, 212), (244, 224, 180), (222, 233, 197))[i // 2]
            pygame.draw.circle(surface, (210, 211, 158), (x + 39, y + 43), 31)
            pygame.draw.circle(surface, portrait_color, (x + 39, y + 41), 30)
            sprite = (fruit_image(kind, 58) if self.tab == 'towers' else
                      character_image(kind, 64, frame=WALK_FRAMES[kind][int(time * 4) % 2]))
            if sprite:
                surface.blit(sprite, sprite.get_rect(center=(x + 39, y + 41)))
            spec = C.FRUITS[kind] if self.tab == 'towers' else C.MONSTERS[kind]
            surface.blit(self.name_font.render(spec['label'], True, INK), (x + 77, y + 6))
            pygame.draw.line(surface, (225, 218, 170), (x + 77, y + 31), (x + 347, y + 31))
            if self.tab == 'towers':
                self.text(surface, f"{spec['role']} · 攻击{spec['damage']} · {spec['cost']}金币", (x + 77, y + 33))
                self.text(surface, f"间隔{spec['interval']:g}秒 · 射程{spec['rng']:g}格", (x + 77, y + 58))
                caption = f"第 {spec['unlock']} 关开放  ·  可升级至三级"
            else:
                self.text(surface, f"生命{spec['hp']} · 速度{spec['speed']:g}格/秒", (x + 77, y + 33))
                self.text(surface, f"击杀获得{spec['reward']}金币和积分", (x + 77, y + 58))
                debut = next(n + 1 for n, level in enumerate(C.LEVELS) if kind in level['monsters'])
                caption = f"第 {debut} 关出现  ·  每只漏怪扣 1 血"
            pygame.draw.rect(surface, (236, 235, 197), (x + 10, y + 86, 345, 22), border_radius=7)
            surface.blit(self.small_font.render(caption, True, (110, 126, 75)), (x + 19, y + 88))
        star(surface, (47, 693), 12)
        self.text(surface, '点击已建炮塔可升级 / 出售；萝卜只有三血，请守好每个转角。', (70, 682), color=INK)

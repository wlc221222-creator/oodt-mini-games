"""Browsable introductions for every plant and zombie, including locked units."""
import pygame

import config as C
from garden_ui import PLANT_NAMES


class Almanac:
    menu_rect = pygame.Rect(439, 423, 266, 48)
    close_rect = pygame.Rect(650, 23, 123, 38)
    tabs = (pygame.Rect(210, 23, 160, 38), pygame.Rect(389, 23, 160, 38))
    prev_rect = pygame.Rect(220, 540, 110, 36)
    next_rect = pygame.Rect(470, 540, 110, 36)
    page_size = 6

    def __init__(self, game):
        self.game = game
        self.opened = False
        self.category = 0
        self.page = 0

    def entries(self):
        return list(C.SHOP_ORDER if self.category == 0 else C.ZOMBIES)

    def page_count(self):
        return (len(self.entries()) + self.page_size - 1) // self.page_size

    def turn_page(self, direction):
        self.page = max(0, min(self.page + direction, self.page_count() - 1))

    def handle_event(self, event, pos=None):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.opened = False
            elif event.key == pygame.K_TAB:
                self.category = 1 - self.category
                self.page = 0
            elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                self.turn_page(-1 if event.key == pygame.K_LEFT else 1)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.close_rect.collidepoint(pos):
                self.opened = False
            for i, rect in enumerate(self.tabs):
                if rect.collidepoint(pos):
                    self.category, self.page = i, 0
            if self.prev_rect.collidepoint(pos):
                self.turn_page(-1)
            elif self.next_rect.collidepoint(pos):
                self.turn_page(1)

    def draw(self):
        g, ui = self.game, self.game.ui
        g.canvas.fill((235, 226, 193))
        ui.text('庭院图鉴', (102, 42), 26, (55, 78, 38), bold=True)
        for i, label in enumerate(('植物介绍', '僵尸介绍')):
            ui.button(self.tabs[i], label, material='wood' if self.category == i else 'paper')
        ui.button(self.close_rect, '返回 [I/Esc]', size=15)
        ui.text('查看期间战斗暂停 · Tab 切换分类 · ← → 翻页', (400, 81), 15, (90, 81, 58))
        start = self.page * self.page_size
        for index, kind in enumerate(self.entries()[start:start + self.page_size]):
            y = 105 + index * 70
            rect = pygame.Rect(25, y, 750, 65)
            pygame.draw.rect(g.canvas, (247, 236, 203), rect, border_radius=10)
            pygame.draw.rect(g.canvas, (146, 113, 65), rect, 2, border_radius=10)
            if self.category == 0:
                spec = C.PLANTS[kind]
                frames = g.assets.plant(spec['sprite'])
                status = '已解锁' if kind in g.owned_plants else '冒险通关解锁'
                title = f"{PLANT_NAMES[kind]}  ·  {spec['cost']}阳光  ·  生命{spec['hp']}  ·  冷却{spec['recharge']:g}秒  ·  {status}"
                help_text = C.PLANT_HELP[kind]
            else:
                spec = C.ZOMBIES[kind]
                frames = g.assets.zombie(kind)['walk']
                title = f"{C.ZOMBIE_NAMES[kind]}僵尸  ·  生命{spec['hp']}  ·  基础移速{spec['speed']:g}像素/秒"
                help_text = C.ZOMBIE_HELP[kind]
            if frames:
                sprite = frames[0]
                scale = min(63 / sprite.get_width(), 58 / sprite.get_height())
                size = (max(1, int(sprite.get_width() * scale)), max(1, int(sprite.get_height() * scale)))
                g.canvas.blit(ui.scaled(sprite, size), (pygame.Rect(34, y + 3, 70, 59).centerx - size[0] // 2, y + 62 - size[1]))
            ui.text(title, (117, y + 10), 15, (50, 67, 35), center=False)
            ui.text(help_text, (117, y + 35), 15, (90, 71, 45), center=False)
        ui.button(self.prev_rect, '‹ 上页', enabled=self.page > 0, size=16)
        ui.text(f'{self.page + 1} / {self.page_count()}', (400, 558), 18, (55, 78, 38))
        ui.button(self.next_rect, '下页 ›', enabled=self.page + 1 < self.page_count(), size=16)

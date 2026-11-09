"""Garden, carved stone and seed-packet presentation on the 800x600 canvas.

The controller owns all game rules. This module only paints its current state;
shared hit rectangles keep painted controls and mouse input aligned.
"""
from __future__ import annotations

import math
import random

import pygame

import config as C


CREAM = (247, 230, 177)
INK = (63, 49, 31)
GREEN = (64, 91, 39)
PLANT_NAMES = {
    "sunflower": "向日葵", "peashooter": "豌豆射手", "wallnut": "坚果墙",
    "snowpea": "寒冰射手", "cherrybomb": "樱桃炸弹", "repeater": "双发射手",
    "threepeater": "三线射手", "potatomine": "土豆地雷", "jalapeno": "火爆辣椒",
    "puffshroom": "小喷菇", "sunshroom": "阳光菇", "scaredyshroom": "胆小菇",
    "chomper": "大嘴花", "squash": "窝瓜", "spikeweed": "地刺", "iceshroom": "寒冰菇",
}
LEVEL_POINTS = ((109, 235), (260, 232), (410, 255), (365, 356),
                (210, 364), (115, 471), (394, 474))


def mode_rect(index):
    return (pygame.Rect(420, 186, 302, 116) if index == 0
            else pygame.Rect(439, 310, 266, 65))


def level_rect(index):
    x, y = LEVEL_POINTS[index % len(LEVEL_POINTS)]
    return pygame.Rect(x - 39, y - 33, 78, 66)


BACK_RECT = pygame.Rect(28, 25, 116, 40)
CHOOSER_BACK_RECT = pygame.Rect(645, 25, 126, 40)
CHOOSER_START_RECT = pygame.Rect(581, 477, 170, 44)
RESULT_PRIMARY_RECT = pygame.Rect(247, 508, 305, 44)
RESULT_MAP_RECT = pygame.Rect(577, 508, 118, 44)
MAP_PREV_RECT = pygame.Rect(171, 25, 85, 34)
MAP_NEXT_RECT = pygame.Rect(560, 25, 85, 34)
SEED_PREV_RECT = pygame.Rect(46, 159, 70, 32)
SEED_NEXT_RECT = pygame.Rect(448, 159, 70, 32)
PAUSE_BUTTON_RECT = pygame.Rect(678, 570, 110, 27)
PAUSE_RESUME_RECT = pygame.Rect(255, 300, 290, 48)
PAUSE_MENU_RECT = pygame.Rect(255, 375, 290, 43)
SHOVEL_RECT = pygame.Rect(730, 8, 58, 72)


class GardenUI:
    def __init__(self, game, font_loader):
        self.game = game
        self.font_loader = font_loader
        self.fonts = {}
        self.skins = {}
        self.images = {}

    @property
    def canvas(self):
        return self.game.canvas

    def font(self, size, bold=False):
        key = (size, bold)
        if key not in self.fonts:
            self.fonts[key] = self.font_loader(size)
            self.fonts[key].set_bold(bold)
        return self.fonts[key]

    def text(self, value, pos, size=18, color=CREAM, center=True,
             outline=None, bold=False):
        font = self.font(size, bold)
        image = font.render(str(value), True, color)
        rect = image.get_rect(center=pos) if center else image.get_rect(topleft=pos)
        if outline:
            edge = font.render(str(value), True, outline)
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 2)):
                self.canvas.blit(edge, rect.move(dx, dy))
        self.canvas.blit(image, rect)
        return rect

    def hover(self, rect):
        return rect.collidepoint(self.game._to_canvas(pygame.mouse.get_pos()))

    def scaled(self, image, size):
        key = (id(image), size)
        if key not in self.images:
            self.images[key] = pygame.transform.smoothscale(image, size)
        return self.images[key]

    def skin(self, size, material="paper", lit=False):
        key = (size, material, lit)
        if key in self.skins:
            return self.skins[key]
        w, h = size
        image = pygame.Surface(size, pygame.SRCALPHA)
        rng = random.Random(w * 13 + h)
        if material == "stone":
            points = [(7, 7), (w // 3, 1), (w - 20, 4), (w - 3, 15),
                      (w - 7, h - 9), (w // 2, h - 3), (3, h - 7), (1, 20)]
            pygame.draw.polygon(image, (41, 43, 44), [(x, y + 3) for x, y in points])
            pygame.draw.polygon(image, (149, 150, 147) if lit else (120, 124, 128), points)
            pygame.draw.lines(image, (210, 210, 187) if lit else (177, 181, 178), False, points[:4], 2)
            pygame.draw.lines(image, (62, 65, 69), False, points[3:] + [points[0]], 3)
            for _ in range(w * h // 150):
                x, y = rng.randrange(9, w - 9), rng.randrange(9, h - 9)
                pygame.draw.line(image, (137, 140, 136) if lit else (112, 116, 121), (x, y), (x + 2, y + 1))
            pygame.draw.lines(image, (64, 69, 74), False,
                              [(w - 22, 7), (w - 29, 17), (w - 25, 23), (w - 33, 32)], 1)
        elif material == "wood":
            pygame.draw.rect(image, (45, 26, 14), (0, 3, w, h - 3), border_radius=6)
            pygame.draw.rect(image, (108, 62, 27) if lit else (79, 47, 25), (0, 0, w, h - 4), border_radius=6)
            pygame.draw.rect(image, (171, 111, 52), (2, 2, w - 4, h - 8), 2, border_radius=5)
            for y in range(9, h - 8, 9):
                pygame.draw.line(image, (96, 55, 24) if lit else (70, 41, 23), (6, y), (w - 6, y + 2))
            for x in (8, w - 9):
                pygame.draw.circle(image, (40, 32, 26), (x, h // 2), 3)
                pygame.draw.circle(image, (189, 167, 113), (x - 1, h // 2 - 1), 1)
        else:
            pygame.draw.rect(image, (38, 28, 15, 120), (0, 5, w, h - 5), border_radius=12)
            pygame.draw.rect(image, (126, 87, 44), (0, 0, w, h - 5), border_radius=12)
            pygame.draw.rect(image, (217, 192, 142), (4, 4, w - 8, h - 13), border_radius=9)
            pygame.draw.rect(image, (232, 215, 173), (9, 9, w - 18, h - 23), border_radius=7)
            for _ in range(w * h // 70):
                x, y = rng.randrange(11, w - 11), rng.randrange(11, h - 15)
                pygame.draw.circle(image, (222, 204, 162), (x, y), 1)
            pygame.draw.line(image, (246, 231, 187), (12, 10), (w - 12, 10), 2)
        self.skins[key] = image
        return image

    def panel(self, rect, material="paper", lit=False):
        self.canvas.blit(self.skin(rect.size, material, lit), rect)

    def button(self, rect, label, material="wood", enabled=True, size=18):
        self.panel(rect, material, enabled and self.hover(rect))
        color = (30, 33, 37) if material == "stone" else CREAM
        self.text(label, rect.center, size, color if enabled else (169, 158, 128),
                  outline=(167, 173, 162) if material == "stone" else (42, 29, 19), bold=True)
        if not enabled:
            cover = pygame.Surface(rect.size, pygame.SRCALPHA)
            cover.fill((21, 24, 20, 48))
            self.canvas.blit(cover, rect)

    def shade(self, opacity=115):
        image = pygame.Surface((800, 600), pygame.SRCALPHA)
        image.fill((14, 23, 13, opacity))
        self.canvas.blit(image, (0, 0))

    def lock(self, center, scale=1):
        x, y = center
        r = pygame.Rect(x - 7 * scale, y - 10 * scale, 14 * scale, 16 * scale)
        pygame.draw.arc(self.canvas, (71, 64, 48), r, 0, math.pi, max(2, scale * 2))
        body = pygame.Rect(x - 10 * scale, y - 2 * scale, 20 * scale, 15 * scale)
        pygame.draw.rect(self.canvas, (126, 107, 73), body, border_radius=3)
        pygame.draw.rect(self.canvas, (68, 57, 42), body, 2, border_radius=3)
        pygame.draw.circle(self.canvas, (48, 43, 34), (x, y + 4 * scale), 2 * scale)

    def check(self, center, color=(55, 97, 37)):
        x, y = center
        pygame.draw.lines(self.canvas, color, False, [(x - 6, y), (x - 1, y + 5), (x + 8, y - 6)], 3)

    def flag(self, x, y, done=False):
        pygame.draw.line(self.canvas, (70, 56, 34), (x, y), (x, y + 35), 3)
        pygame.draw.line(self.canvas, (212, 192, 132), (x - 1, y), (x - 1, y + 35), 1)
        art = self.game.assets.misc("wave_flag")
        if art is not None and not done:
            self.canvas.blit(art, (x - 1, y))
        else:
            pygame.draw.polygon(self.canvas, (62, 105, 43) if done else (174, 51, 37), [(x, y), (x + 24, y + 3), (x + 21, y + 17), (x, y + 14)])
        if done:
            self.check((x + 12, y + 8), CREAM)

    def draw_menu(self):
        g = self.game
        art = g.assets.misc("menu")
        self.canvas.blit(art, (0, 0)) if art else self.canvas.fill(GREEN)
        # Engraved title follows the empty upper half of the original stone.
        self.text("植物大战", (575, 98), 40, (215, 219, 183), outline=(50, 56, 52), bold=True)
        self.text("僵 尸", (574, 145), 40, (194, 205, 147), outline=(48, 55, 48), bold=True)
        rect = mode_rect(0)
        name = "adventure_hover" if self.hover(rect) else "adventure"
        adventure = g.assets.misc(name)
        if adventure:
            self.canvas.blit(self.scaled(adventure, rect.size), rect)
        else:
            self.button(rect, "冒险模式", "stone", size=34)
        self.button(mode_rect(1), "选 择 关 卡", "stone", size=29)
        index = min(g.unlocked, len(C.LEVELS) - 1)
        progress_label = "冒险已通关 · 进入地图重玩" if g.adventure_completed() else f"继续闯关 · {C.LEVELS[index]['id']}"
        self.text(progress_label, (572, 393), 16,
                  (214, 215, 188), outline=(63, 68, 65))
        self.button(g.almanac.menu_rect, "植物与僵尸图鉴 [I]", "stone", size=21)
        self.panel(pygame.Rect(38, 498, 312, 61), "wood")
        self.text("你的庭院，等你来守护", (194, 518), 19, bold=True, outline=(35, 28, 14))
        self.text("Enter 冒险  ·  F 全屏  ·  Esc 退出", (194, 543), 13)

    def completed(self, index):
        # Reward ownership also distinguishes the completed final level from
        # merely reaching it; no new save fields are necessary.
        return index < self.game.unlocked or C.LEVEL_REWARDS[index] in self.game.owned_plants

    def draw_levels(self):
        g = self.game
        art = g.assets.background(0)
        self.canvas.blit(art, (0, 0)) if art else self.canvas.fill(GREEN)
        self.shade(122)
        self.button(BACK_RECT, "‹ 返回庭院")
        self.button(MAP_PREV_RECT, "‹ 上一页", enabled=g.level_page > 0, size=14)
        self.button(MAP_NEXT_RECT, "下一页 ›", enabled=g.level_page < (len(C.LEVELS) - 1) // 7, size=14)
        self.text("庭院冒险地图", (411, 61), 32, bold=True, outline=(28, 37, 17))
        done = sum(self.completed(i) for i in range(len(C.LEVELS)))
        self.text(f"已通关 {done}/{len(C.LEVELS)}  ·  第 {g.level_page + 1}/{(len(C.LEVELS) + 6) // 7} 页  ·  ← → 翻页", (410, 100), 16)
        self.panel(pygame.Rect(27, 126, 497, 423))
        self.text("前院 · 阳光下的防线" if g.level_page == 0 else "夜战续篇 · 蘑菇的力量", (275, 159), 19, GREEN, bold=True)
        pygame.draw.lines(self.canvas, (151, 124, 77), False, LEVEL_POINTS, 17)
        pygame.draw.lines(self.canvas, (199, 174, 119), False, LEVEL_POINTS, 11)
        # Pebbled trail connects the same rects used by the controller.
        for a, b in zip(LEVEL_POINTS, LEVEL_POINTS[1:]):
            length = math.dist(a, b)
            for j in range(1, int(length // 18)):
                t = j / int(length // 18)
                x, y = round(a[0] + (b[0] - a[0]) * t), round(a[1] + (b[1] - a[1]) * t)
                pygame.draw.ellipse(self.canvas, (224, 204, 157), (x - 4, y - 2, 8, 4))
        # The moonlit part of the map is separate from the daytime chapter.
        pygame.draw.line(self.canvas, (179, 151, 103), (55, 416), (495, 416), 1)
        self.text("后院 · 月光下的挑战" if g.level_page == 0 else "伏击与陷阱 · 月夜终章", (277, 430), 17, (74, 76, 91), bold=True)
        visible = list(g.visible_levels())
        focus = max(visible[0], min(g.unlocked, visible[-1]))
        for i in visible:
            lv = C.LEVELS[i]
            rect = level_rect(i)
            locked = i > g.unlocked
            hovered = self.hover(rect)
            if hovered:
                focus = i
            if i == g.unlocked and not self.completed(i):
                pygame.draw.ellipse(self.canvas, (177, 123, 44), rect.inflate(14, 10), 3)
            self.panel(rect, "stone", not locked and hovered)
            if locked:
                self.text(lv["id"], (rect.centerx - 11, rect.centery), 22, (64, 64, 60), bold=True)
                self.lock((rect.right - 20, rect.centery - 2))
            else:
                self.text(lv["id"], rect.center, 26, CREAM, outline=(49, 57, 47), bold=True)
                self.flag(rect.right - 3, rect.y - 21, self.completed(i))
            self.text(lv["name"].split(" · ")[-1], (rect.centerx, rect.bottom + 11), 15,
                      (105, 97, 78) if locked else INK)
        self.draw_level_detail(focus)
        self.text("绿旗已通关    金色圆环当前关卡    锁标记待解锁", (394, 575), 15, CREAM,
                  outline=(32, 36, 20))

    def draw_level_detail(self, index):
        g = self.game
        lv = C.LEVELS[index]
        self.panel(pygame.Rect(540, 126, 232, 423))
        self.text(f"关卡 {lv['id']}", (656, 155), 24, GREEN, bold=True)
        bg = g.assets.background(lv["bg"])
        if bg:
            self.canvas.blit(self.scaled(bg, (204, 112)), (554, 180))
            pygame.draw.rect(self.canvas, (132, 102, 58), (554, 180, 204, 112), 2)
        self.text(lv["name"], (655, 313), 18, INK, bold=True)
        self.text(f"{lv['rows']} 行草坪  ·  {len(lv['waves'])} 波僵尸", (655, 343), 16, INK)
        self.text(f"初始阳光  {lv['sun']}", (655, 370), 16, INK)
        self.text(lv.get("rule", ""), (655, 390), 13, (143, 64, 35))
        reward = C.LEVEL_REWARDS[index]
        self.text("冒险通关奖励", (652, 408), 15, (116, 80, 36))
        frames = g.assets.plant(C.PLANTS[reward]["sprite"])
        if frames:
            sprite = frames[0]
            scale = min(50 / sprite.get_width(), 51 / sprite.get_height())
            image = self.scaled(sprite, (int(sprite.get_width() * scale), int(sprite.get_height() * scale)))
            self.canvas.blit(image, image.get_rect(center=(589, 447)))
        self.text(PLANT_NAMES[reward], (677, 447), 18, GREEN, bold=True)
        status = "尚未解锁" if index > g.unlocked else ("已通关 · 可再次挑战" if self.completed(index) else "已解锁 · 点击路标开始")
        self.panel(pygame.Rect(554, 483, 204, 40), "wood")
        self.text(status, (656, 501), 15, CREAM)

    def draw_chooser(self):
        g = self.game
        art = g.assets.background(g.level["bg"])
        self.canvas.blit(art, (0, 0)) if art else self.canvas.fill(GREEN)
        self.shade(112)
        bar = g._build_bar(C.MAX_SEEDS)
        if bar:
            self.canvas.blit(bar, (0, 0))
        self.draw_sun_value()
        target = g.required_seeds()
        for i in range(C.MAX_SEEDS):
            rect = g._seed_slot_rect(i)
            if i < len(g.seeds):
                card = g.assets.card(C.PLANTS[g.seeds[i]]["card"])
                if card:
                    self.canvas.blit(card, rect)
            else:
                slot = pygame.Surface(rect.size, pygame.SRCALPHA)
                slot.fill((30, 24, 13, 95 if i < target else 155))
                self.canvas.blit(slot, rect)
                self.text(str(i + 1) if i < target else "—", rect.center, 17, (193, 170, 113))
        self.button(CHOOSER_BACK_RECT, "‹ 返回地图")
        self.text(f"{g.level['id']}  {g.level['name']}", (290, 113), 23, bold=True, outline=(25, 39, 18))
        self.text("挑选你的防守阵容", (661, 112), 20, bold=True, outline=(25, 39, 18))
        self.panel(pygame.Rect(C.CHOOSER_PANEL_X, C.CHOOSER_PANEL_Y,
                               C.CHOOSER_PANEL_W, C.CHOOSER_PANEL_H))
        self.text(f"种子册 {g.seed_page + 1}/{(len(C.SHOP_ORDER) + 9) // 10}", (283, 177), 24, GREEN, bold=True)
        self.button(SEED_PREV_RECT, "‹ 上页", enabled=g.seed_page > 0, size=14)
        self.button(SEED_NEXT_RECT, "下页 ›", enabled=g.seed_page < (len(C.SHOP_ORDER) - 1) // 10, size=14)
        pool = g.available_plants()
        ordered = g.visible_seeds()
        hovered_kind = None
        for i, kind in enumerate(ordered):
            rect = g._chooser_rect(i)
            locked, picked = kind not in pool, kind in g.seeds
            if self.hover(rect):
                hovered_kind = kind
            card = g.assets.card(C.PLANTS[kind]["card"])
            if card:
                if locked or picked:
                    card = pygame.transform.grayscale(card)
                self.canvas.blit(card, rect)
            if locked:
                fog = pygame.Surface(rect.size, pygame.SRCALPHA)
                fog.fill((49, 43, 30, 135))
                self.canvas.blit(fog, rect)
                self.lock((rect.centerx, rect.centery))
            elif picked:
                pygame.draw.rect(self.canvas, (106, 135, 47), rect.inflate(6, 6), 3, border_radius=4)
                pygame.draw.circle(self.canvas, (237, 221, 155), (rect.right - 3, rect.y + 6), 11)
                self.check((rect.right - 3, rect.y + 6))
            elif self.hover(rect):
                pygame.draw.rect(self.canvas, (184, 126, 39), rect.inflate(6, 6), 2, border_radius=4)
            self.text(PLANT_NAMES[kind], (rect.centerx, rect.bottom + 15), 14,
                      (135, 121, 95) if locked else INK)
        pygame.draw.line(self.canvas, (193, 166, 111), (47, 459), (515, 459), 1)
        if hovered_kind:
            spec = C.PLANTS[hovered_kind]
            self.text(f"{PLANT_NAMES[hovered_kind]} · {spec['cost']}阳光 · 冷却{spec['recharge']:g}秒", (281, 479), 15, INK)
            self.text(C.PLANT_HELP.get(hovered_kind, "点击加入阵容，再次点击取消"), (281, 501), 13, INK)
        else:
            self.text("鼠标停在卡片上查看植物能力", (281, 489), 16, INK)
        self.text("← → 翻页  ·  A 选满  ·  Enter 开始  ·  点击上方移除", (281, 531), 13, (123, 98, 60))
        self.panel(pygame.Rect(552, 145, 221, 410))
        self.text("出发准备", (662, 176), 23, GREEN, bold=True)
        self.text(f"{g.rows} 行防线 / {len(g.waves)} 波进攻", (662, 213), 16, INK)
        for i, line in enumerate(g.level.get("brief", ())):
            self.text(line, (662, 239 + 21 * i), 13, INK)
        self.text("本关来袭", (662, 287), 15, (121, 86, 44))
        kinds = list(dict.fromkeys(entry[0] for wave in g.waves for entry in wave))
        for i, kind in enumerate(kinds):
            frames = g.assets.zombie(kind)["walk"]
            if frames:
                sprite = frames[0]
                slot_w = 198 / max(1, len(kinds))
                scale = min((slot_w - 5) / sprite.get_width(), 73 / sprite.get_height())
                image = self.scaled(sprite, (int(sprite.get_width() * scale), int(sprite.get_height() * scale)))
                x = 563 + slot_w * (i + 0.5)
                self.canvas.blit(image, image.get_rect(midbottom=(round(x), 365)))
                self.text(C.ZOMBIE_NAMES[kind], (round(x), 378), 11, INK)
        self.text(f"已选 {len(g.seeds)} / {target} 张", (662, 405), 24, GREEN, bold=True)
        ready = len(g.seeds) == target
        self.text("阵容就绪，守住庭院！" if ready else f"再选择 {target - len(g.seeds)} 张植物", (662, 442), 15, INK)
        self.button(CHOOSER_START_RECT, "开始战斗！", enabled=ready, size=23)
        self.text("后续植物通过冒险解锁", (662, 538), 13, (122, 98, 62))

    def draw_wave(self):
        g = self.game
        # An independent compact wooden HUD leaves the eight seed slots free.
        panel = pygame.Rect(550, 5, 173, 79)
        self.panel(panel, "wood")
        final = g.wave_index == len(g.waves) - 1 and g.wave_timer >= 0
        self.text(f"{g.level['id']}  " + ("最后一波！" if final else "关卡进度"),
                  (562, 12), 13, (247, 196, 108) if final else CREAM, center=False)
        wave = min(g.wave_index + 1, len(g.waves))
        self.text(f"{wave}/{len(g.waves)} 波", (691, 18), 12)
        track = pygame.Rect(565, 54, 140, 15)
        pygame.draw.rect(self.canvas, (38, 31, 20), track.inflate(6, 6), border_radius=8)
        pygame.draw.rect(self.canvas, (181, 148, 81), track.inflate(4, 4), 1, border_radius=7)
        pygame.draw.rect(self.canvas, (68, 74, 35), track, border_radius=6)
        frac = g.wave_progress()
        width = round(track.w * frac)
        if width:
            fill = pygame.Surface(track.size, pygame.SRCALPHA)
            pygame.draw.rect(fill, (118, 156, 55), (0, 0, width, track.h), border_radius=6)
            pygame.draw.line(fill, (191, 212, 109), (3, 3), (max(3, width - 4), 3), 2)
            self.canvas.blit(fill, track)
        # Match flags to the weighted zombie-count boundaries in wave_progress.
        total = sum(map(len, g.waves)) or 1
        cumulative = 0
        for wave in g.waves:
            cumulative += len(wave)
            x = track.x + round(track.w * cumulative / total)
            pygame.draw.line(self.canvas, (231, 215, 165), (x, 50), (x, 69), 2)
            flag = g.assets.misc("wave_flag")
            if flag:
                self.canvas.blit(flag, (x - 23, 36))
        head = g.assets.misc("wave_head")
        x = track.x + round(track.w * frac)
        if head:
            self.canvas.blit(head, head.get_rect(center=(x, track.centery)))

    def draw_sun_value(self):
        rect = pygame.Rect(17, 66, 43, 17)
        pygame.draw.rect(self.canvas, (234, 233, 171), rect)
        self.text(self.game.sun, rect.center, 16, (61, 55, 34), bold=True)

    def draw_shop(self):
        g = self.game
        bar = g._build_bar(max(1, len(g.seeds)))
        if bar:
            self.canvas.blit(bar, (0, 0))
        for i, kind in enumerate(g.seeds):
            spec = C.PLANTS[kind]
            rect = g._card_rect(i)
            cooling = g.cooldowns.get(kind, 0) > 0
            affordable = g.sun >= spec["cost"]
            card = g.assets.ready_card(spec["card"]) if affordable and not cooling else g.assets.card(spec["card"])
            if card:
                self.canvas.blit(pygame.transform.grayscale(card) if not affordable else card, rect)
                if cooling:
                    fraction = min(1, g.cooldowns[kind] / spec["recharge"])
                    height = max(1, round(rect.h * fraction))
                    gray = pygame.transform.grayscale(card)
                    gray.set_alpha(200)
                    self.canvas.blit(gray, rect, (0, 0, rect.w, height))
                    cover = pygame.Surface((rect.w, height), pygame.SRCALPHA)
                    for y in range(height):
                        pygame.draw.line(cover, (34, 34, 28, int(130 - 55 * y / height)), (0, y), (rect.w, y))
                    self.canvas.blit(cover, rect)
                    pygame.draw.line(self.canvas, (234, 220, 153), (rect.x + 2, rect.y + height - 1), (rect.right - 3, rect.y + height - 1))
                # The brighter _move art omits the price; add it for every card
                # after recharge shading so costs stay readable in all states.
                cost_rect = pygame.Rect(rect.x + 5, rect.bottom - 16, 33, 13)
                pygame.draw.rect(self.canvas, (221, 220, 178), cost_rect)
                self.text(spec["cost"], cost_rect.center, 12, (45, 49, 36), bold=True)
            if g.selected == kind:
                pygame.draw.rect(self.canvas, (249, 224, 110), rect.inflate(4, 4), 2, border_radius=3)
            if cooling:
                self.text(f"{math.ceil(g.cooldowns[kind])}s", rect.center, 17,
                          outline=(30, 30, 25), bold=True)
            self.text(i + 1, (rect.x + 5, rect.y + 1), 13, center=False, outline=(40, 32, 22), bold=True)
        self.panel(SHOVEL_RECT, 'wood', g.drag_kind == 'shovel')
        icon = self.shovel_image()
        self.canvas.blit(self.scaled(icon, (43, 43)), (SHOVEL_RECT.x + 8, SHOVEL_RECT.y + 3))
        self.text('铲子', (SHOVEL_RECT.centerx, SHOVEL_RECT.bottom - 15), 14)

    def pointer_pos(self):
        g = self.game
        return g.drag_pos if g.drag_pos is not None else g._to_canvas(pygame.mouse.get_pos())

    def shovel_image(self):
        key = 'shovel'
        if key not in self.images:
            source = self.game.assets.misc('shovel')
            icon = pygame.Surface((64, 64), pygame.SRCALPHA)
            if source is not None:
                source = source.subsurface(source.get_bounding_rect()).copy()
                scale = min(64 / source.get_width(), 64 / source.get_height())
                size = (round(source.get_width() * scale), round(source.get_height() * scale))
                art = self.scaled(source, size)
                icon.blit(art, art.get_rect(center=(32, 32)))
            self.images[key] = icon
        return self.images[key]

    def draw_drag_cursor(self):
        g = self.game
        if g.drag_kind is None or g.drag_pos is None:
            return
        x, y = map(round, g.drag_pos)
        if g.drag_kind == 'shovel':
            # The original shovel points down-left; keep its blade under the cursor.
            self.canvas.blit(self.shovel_image(), (x - 12, y - 55))
        else:
            frames = g.assets.plant(C.PLANTS[g.drag_kind]['sprite'])
            if frames:
                image = frames[0].copy()
                image.set_alpha(210)
                self.canvas.blit(image, image.get_rect(center=(x, y)))

    def draw_placement(self):
        g = self.game
        for row in range(g.rows):
            self.text(row + 1, (20, C.LAWN_Y + row * C.CELL_H + 50),
                      14, outline=(25, 40, 20))
        shoveling = g.drag_kind == 'shovel'
        if g.selected is None and not shoveling:
            return
        overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
        for row in range(g.rows):
            for col in range(C.GRID_COLS):
                rect = pygame.Rect(C.LAWN_X + col * C.CELL_W,
                                   C.LAWN_Y + row * C.CELL_H, C.CELL_W, C.CELL_H)
                pygame.draw.rect(overlay, (235, 245, 190, 65), rect, 1)
        cell = g.lawn_cell(self.pointer_pos())
        if cell is not None:
            col, row = cell
            rect = pygame.Rect(C.LAWN_X + col * C.CELL_W,
                               C.LAWN_Y + row * C.CELL_H, C.CELL_W, C.CELL_H)
            valid = bool(g.plant_at(*cell)) if shoveling else not g.planting_error(cell)
            color = (110, 220, 90) if valid else (245, 95, 65)
            pygame.draw.rect(overlay, (*color, 65), rect)
            pygame.draw.rect(overlay, (*color, 220), rect, 2)
            frames = g.assets.plant(C.PLANTS[g.selected]["sprite"]) if g.selected and g.drag_kind is None else []
            if frames:
                ghost = frames[0].copy()
                ghost.set_alpha(140)
                overlay.blit(ghost, ghost.get_rect(midbottom=(rect.centerx,
                             rect.y + C.PLANT_BASELINE)))
        self.canvas.blit(overlay, (0, 0))

    def draw_battle_info(self):
        g = self.game
        # Warn of imminent lane entries without covering the planting cells.
        for row in {row for _, delay, row in g.spawn_queue
                    if 0 <= delay - g.wave_timer <= 5}:
            y = C.LAWN_Y + row * C.CELL_H + 40
            pygame.draw.polygon(self.canvas, (255, 181, 66),
                                [(790, y - 10), (776, y), (790, y + 10)])
        wave = min(g.wave_index, len(g.waves) - 1)
        names = g.level.get("wave_names", [])
        name = names[wave] if wave < len(names) else f"第 {wave + 1} 波"
        text = f"{name}  ·  {g.level.get('rule', '')}"
        if g.drag_kind == 'shovel':
            cell = g.lawn_cell(self.pointer_pos())
            plant = g.plant_at(*cell) if cell else None
            text = f"松手铲除{PLANT_NAMES[plant.kind]} · 不返还阳光" if plant else '拖到植物上松手铲除，右键或 Esc 取消'
        elif g.selected:
            cell = g.lawn_cell(self.pointer_pos())
            if cell:
                hint = g.planting_error(cell)
            else:
                hint = '拖到草坪，松手种植' if g.drag_kind else '点击草坪种植'
            text = f"{PLANT_NAMES[g.selected]} · {hint or ('松手种植，右键取消' if g.drag_kind else '这里可以种植')}"
        elif g.wave_timer < 0:
            text += f"  ·  下一波 {math.ceil(-g.wave_timer)} 秒"
        else:
            text += "  ·  拖卡种植 / 点击收集阳光"
        if g.notice_timer > 0:
            text = g.notice
        panel = pygame.Surface((650, 27), pygame.SRCALPHA)
        panel.fill((20, 29, 18, 205))
        self.canvas.blit(panel, (10, 570))
        self.text(text, (335, 583), 14, (255, 225, 150) if g.notice_timer > 0 else CREAM)
        self.button(PAUSE_BUTTON_RECT, '暂停 [P]', size=14)

    def draw_pause(self):
        self.shade(160)
        self.panel(pygame.Rect(150, 165, 500, 325))
        self.text('防线已暂停', (400, 218), 32, GREEN, bold=True)
        self.text('阳光、冷却和敌人都会停在当前进度', (400, 265), 17, INK)
        self.button(PAUSE_RESUME_RECT, '继续战斗  [P / Enter]', size=22)
        self.button(PAUSE_MENU_RECT, '结束本局，返回庭院', size=19)
        self.text('I 查看图鉴  ·  Esc 继续  ·  F 全屏', (400, 455), 15, INK)

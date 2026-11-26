"""The pre-battle seed bank, packet cabinet and street preview."""
from __future__ import annotations

from dataclasses import dataclass
import pygame

import config as C
from garden_ui import CHOOSER_BACK_RECT, CHOOSER_START_RECT, PLANT_NAMES


# Original PC cabinet positions, including the gaps for species this game omits.
SLOTS = {
    'peashooter': 0, 'sunflower': 1, 'cherrybomb': 2, 'wallnut': 3,
    'potatomine': 4, 'snowpea': 5, 'chomper': 6, 'repeater': 7,
    'puffshroom': 8, 'sunshroom': 9, 'scaredyshroom': 13, 'iceshroom': 14,
    'squash': 16, 'threepeater': 18, 'jalapeno': 20, 'spikeweed': 21,
}
PACKET_SIZE = (50, 70)
STREET_SPOTS = ((641, 204), (738, 254), (562, 318), (680, 367), (599, 422), (743, 493))


def sleeve_rect(slot):
    return pygame.Rect(22 + slot % 8 * 53, 128 + slot // 8 * 73, *PACKET_SIZE)


def packet_rect(kind):
    return sleeve_rect(SLOTS[kind])


def bank_rect(index):
    return pygame.Rect(C.CARD_X0 + index * C.CARD_DX, C.CARD_Y, *PACKET_SIZE)


@dataclass
class Flight:
    start: pygame.Vector2
    end: pygame.Vector2
    began: float
    duration: float

    def position(self, now):
        t = min(1.0, max(0.0, (now - self.began) / self.duration))
        return self.start.lerp(self.end, t * (2 - t))


class SeedChooser:
    def __init__(self, game):
        self.game = game
        self.flights = {}
        self.age = 0.0
        self.preview = []

    def reset(self):
        self.age = 0.0
        self.flights.clear()
        kinds = list(dict.fromkeys(spawn[0] for wave in self.game.waves for spawn in wave))
        self.preview = kinds
        if kinds:
            extra = min(2, len(STREET_SPOTS) - len(kinds))
            self.preview = kinds + [kinds[0]] * extra

    def update(self, dt):
        self.age += dt
        self.flights = {kind: flight for kind, flight in self.flights.items()
                        if self.age < flight.began + flight.duration}

    def select(self, seeds):
        """Commit the loadout immediately; moving cards can be redirected mid-flight."""
        old = self.game.seeds
        for kind in dict.fromkeys(old + seeds):
            home = packet_rect(kind)
            src = bank_rect(old.index(kind)) if kind in old else home
            dst = bank_rect(seeds.index(kind)) if kind in seeds else home
            if src == dst:
                continue
            flight = self.flights.get(kind)
            start = flight.position(self.age) if flight else pygame.Vector2(src.topleft)
            duration = .15 if kind in old and kind in seeds else .25
            self.flights[kind] = Flight(start, pygame.Vector2(dst.topleft), self.age, duration)
        self.game.seeds = seeds

    def _packet(self, kind, dim=False):
        ui = self.game.ui
        key = ('chooser_packet', kind, dim)
        if key not in ui.skins:
            spec = C.PLANTS[kind]
            atlas = self.game.assets.misc('seeds')
            frames = self.game.assets.plant(spec['sprite'])
            if atlas and frames:
                # Cell two is the green Crazy Dave packet for ordinary plants.
                image = atlas.subsurface((100, 0, *PACKET_SIZE)).copy()
                sprite = frames[0].subsurface(frames[0].get_bounding_rect())
                scale = min(42 / sprite.get_width(), 41 / sprite.get_height(), 1)
                size = (max(1, round(sprite.get_width() * scale)), max(1, round(sprite.get_height() * scale)))
                portrait = pygame.transform.smoothscale(sprite, size)
                image.blit(portrait, portrait.get_rect(midbottom=(25, 51)))
                price = ui.font(13, True).render(str(spec['cost']), True, (35, 31, 24))
                image.blit(price, price.get_rect(midright=(33, 61)))
            else:
                src = self.game.assets.card(spec['card'])
                image = pygame.transform.smoothscale(src, PACKET_SIZE) if src else pygame.Surface(PACKET_SIZE)
            if dim:
                image.fill((83, 81, 77, 255), special_flags=pygame.BLEND_RGBA_MULT)
            ui.skins[key] = image
        return ui.skins[key]

    def _draw_street(self):
        g = self.game
        bg = g.assets.misc(f"street_{g.level['bg']}") or g.assets.background(g.level['bg'])
        if bg:
            g.canvas.blit(bg, (0, 0))
        else:
            g.canvas.fill((70, 110, 42))
        # Keep a small group near the middle of the road on the introductory levels.
        start = (len(STREET_SPOTS) - len(self.preview)) // 2
        for i, (kind, pos) in enumerate(zip(self.preview, STREET_SPOTS[start:])):
            frames = g.assets.zombie(kind)['walk']
            if frames:
                # Different phases keep groups of the same zombie from marching in unison.
                sprite = frames[(int(self.age * 6) + i * 5) % len(frames)]
                rect = sprite.get_rect(midbottom=pos)
                shadow = self.game.ui.skins.get('street_shadow')
                if shadow is None:
                    shadow = pygame.Surface((60, 13), pygame.SRCALPHA)
                    pygame.draw.ellipse(shadow, (30, 23, 33, 64), shadow.get_rect())
                    self.game.ui.skins['street_shadow'] = shadow
                g.canvas.blit(shadow, shadow.get_rect(center=(pos[0], pos[1] - 4)))
                g.canvas.blit(sprite, rect)
        ui = g.ui
        ui.text(f"{g.level['id']}   {g.level['name']}", (632, 544), 20,
                (255, 224, 139), outline=(37, 30, 26), bold=True)
        for i, line in enumerate(g.level.get('brief', ())):
            ui.text(line, (632, 566 + i * 17), 14, (252, 244, 216), outline=(37, 30, 26))

    def _tooltip(self, kind, rect, locked):
        g, ui = self.game, self.game.ui
        spec = C.PLANTS[kind]
        title = PLANT_NAMES[kind] + (' · 尚未解锁' if locked else '')
        lines = (title, f"阳光 {spec['cost']}　冷却 {spec['recharge']:g} 秒", C.PLANT_HELP[kind])
        width = max(ui.font(size, i == 0).size(line)[0]
                    for i, (size, line) in enumerate(zip((16, 13, 13), lines))) + 20
        box = pygame.Rect(rect.x + 6, rect.bottom + 6, width, 69)
        box.clamp_ip(g.canvas.get_rect())
        pygame.draw.rect(g.canvas, (255, 248, 194), box)
        pygame.draw.rect(g.canvas, (62, 44, 29), box, 2)
        for i, line in enumerate(lines):
            ui.text(line, (box.x + 9, box.y + 5 + 20 * i), 16 if i == 0 else 13,
                    (53, 39, 25), center=False, bold=i == 0)

    def draw(self):
        g, ui = self.game, self.game.ui
        canvas, art = g.canvas, g.assets.misc
        self._draw_street()

        cabinet = art('SeedChooser_Background') or art('panel')
        if cabinet:
            canvas.blit(cabinet, (0, 87))
        ui.text('选择你的植物', (232, 104), 22, (255, 211, 95), outline=(71, 38, 14), bold=True)
        required = g.required_seeds()
        bank = art('SeedBank')
        if bank:
            # Stretch only the empty wooden interior, leaving the sun and end cap intact.
            width = max(446, bank_rect(required - 1).right + 12)
            canvas.blit(bank, (0, 0))
            if width > bank.get_width():
                extra = width - bank.get_width()
                canvas.blit(bank, (bank.get_width() - 9, 0), (95, 0, extra, 87))
                canvas.blit(bank, (width - 9, 0), (bank.get_width() - 9, 0, 9, 87))
        ui.draw_sun_value()
        sleeve = art('SeedPacketSilhouette')
        if sleeve:
            for slot in range(40):
                canvas.blit(sleeve, sleeve_rect(slot))
            for i in range(required):
                canvas.blit(sleeve, bank_rect(i))

        hovered = None
        pool = g.available_plants()
        for kind in C.SHOP_ORDER:
            rect = packet_rect(kind)
            if kind in pool:
                canvas.blit(self._packet(kind, kind in g.seeds or kind in self.flights), rect)
            if ui.hover(rect):
                hovered = (kind, rect, kind not in pool)
        for i, kind in enumerate(g.seeds):
            rect = bank_rect(i)
            if kind not in self.flights:
                canvas.blit(self._packet(kind), rect)
            if ui.hover(rect):
                hovered = (kind, rect, False)

        back = art('SeedChooser_Button2')
        if back:
            canvas.blit(back, CHOOSER_BACK_RECT)
        ui.text('返回地图', CHOOSER_BACK_RECT.center, 16, (66, 38, 17), bold=True)
        ready = len(g.seeds) == required
        button = art('SeedChooser_Button' if ready else 'SeedChooser_Button_Disabled')
        if button:
            canvas.blit(button, CHOOSER_START_RECT)
        if ready and ui.hover(CHOOSER_START_RECT) and art('SeedChooser_Button_Glow'):
            canvas.blit(art('SeedChooser_Button_Glow'), CHOOSER_START_RECT)
        ui.text('一起摇滚吧！', CHOOSER_START_RECT.center, 22,
                (255, 220, 135) if ready else (153, 119, 93), outline=(67, 39, 24), bold=True)
        ui.text(f"已选 {len(g.seeds)} / {required}　·　A 快速选满", (232, 521), 14, (222, 182, 128))
        for kind, flight in self.flights.items():
            canvas.blit(self._packet(kind), flight.position(self.age))
        if hovered and not self.flights:
            self._tooltip(*hovered)

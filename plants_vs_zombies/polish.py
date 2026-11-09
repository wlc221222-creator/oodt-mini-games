"""Small visual helpers; no combat timing or hit boxes live here."""
import math
import random
import pygame


def adventure_stone(size, font_loader, glow=0, title="开始冒险", subtitle="守住你的庭院"):
    """Paint at 2x for clean carved edges at the original canvas resolution."""
    w, h = 302, 116
    scale = 2
    s = pygame.Surface((w * scale, h * scale), pygame.SRCALPHA)
    points = [(10, 17), (45, 10), (110, 12), (142, 5), (232, 11),
              (286, 20), (296, 41), (290, 99), (261, 108), (97, 102), (13, 107), (5, 83)]
    pts = lambda p: [(round(x * scale), round(y * scale)) for x, y in p]
    pygame.draw.polygon(s, (25, 31, 26, 165), pts([(x + 2, y + 6) for x, y in points]))
    pygame.draw.polygon(s, (44, 52, 43), pts(points))
    inside = [(x + (3 if x < w / 2 else -3), y + (3 if y < h / 2 else -4)) for x, y in points]
    face = pygame.Surface(s.get_size(), pygame.SRCALPHA)
    for y in range(h * scale):
        t = y / (h * scale)
        c = (round(141 - 49 * t) + glow * 3, round(149 - 45 * t) + glow * 3, round(128 - 42 * t) + glow * 2)
        pygame.draw.line(face, (*c, 255), (0, y), (w * scale, y))
    mask = pygame.Surface(s.get_size(), pygame.SRCALPHA)
    pygame.draw.polygon(mask, (255, 255, 255), pts(inside))
    face.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    s.blit(face, (0, 0))
    rng = random.Random(17)
    grain = pygame.Surface(s.get_size(), pygame.SRCALPHA)
    for _ in range(850):
        x, y = rng.randrange(w * 2), rng.randrange(h * 2)
        shade = (225, 230, 207, 22) if rng.random() < 0.5 else (29, 45, 32, 22)
        pygame.draw.line(grain, shade, (x, y), (x + rng.randrange(1, 5), y), 1)
    grain.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    s.blit(grain, (0, 0))
    pygame.draw.lines(s, (185 + glow * 3, 194 + glow * 3, 163 + glow * 2), False, pts(points[:7]), 4)
    pygame.draw.lines(s, (48, 61, 45), False, pts(points[6:] + points[:1]), 5)
    # Inset chiselled border and a few irregular stone grains.
    pygame.draw.lines(s, (74, 86, 65), False, pts([(20, 34), (18, 89), (105, 87), (270, 93), (278, 36)]), 2)
    for x, y in ((41, 75), (248, 32), (265, 79), (74, 26), (222, 95), (30, 46)):
        pygame.draw.line(s, (128 + glow * 2, 140 + glow * 2, 113), (x * 2, y * 2), ((x + 4) * 2, y * 2), 2)
    pygame.draw.lines(s, (53, 65, 48), False, pts([(270, 21), (260, 29), (264, 35)]), 2)
    # Moss grows around the silhouette; it never runs through the lettering.
    pygame.draw.lines(s, (55, 87, 32), False, pts([(16, 25), (39, 21), (49, 31), (68, 24)]), 4)
    for x, y, angle in ((23, 21, -25), (40, 22, 20), (52, 27, -30), (66, 23, 25), (280, 90, -35), (263, 99, 15)):
        leaf = pygame.Surface((25, 13), pygame.SRCALPHA)
        pygame.draw.ellipse(leaf, (102 + glow * 4, 139 + glow * 3, 52), (1, 1, 23, 11))
        pygame.draw.line(leaf, (61, 100, 35), (3, 6), (21, 6), 2)
        leaf = pygame.transform.rotate(leaf, angle)
        s.blit(leaf, leaf.get_rect(center=(x * 2, y * 2)))
    # Rescale the stone silhouette first; render lettering at its final aspect
    # ratio so smaller menu plaques never squash Chinese glyphs vertically.
    w, h = size
    s = pygame.transform.smoothscale(s, (w * 2, h * 2))
    labels = ((title, 30, round(h * .45), (242, 232, 180)), (subtitle, 13, round(h * .707), (217, 222, 182))) if subtitle else ((title, 24 if h >= 60 else 16, round(h * .5), (232, 231, 196)),)
    for text, size_, y, color in labels:
        font = font_loader(size_ * 2)
        font.set_bold(True)
        shadow = font.render(text, True, (43, 56, 37))
        highlight = font.render(text, True, (165, 178, 133))
        face = font.render(text, True, color)
        rect = face.get_rect(center=(w, y * 2))
        s.blit(highlight, rect.move(-1, -2))
        s.blit(shadow, rect.move(2, 3))
        s.blit(face, rect)
    return pygame.transform.smoothscale(s, size)


class Feedback:
    """Short, self-contained planting and collection responses."""
    def __init__(self, pos, kind='plant', amount=0):
        self.x, self.y = pos
        self.kind = kind
        self.amount = amount
        self.age = 0.0
        self.life = 0.65 if kind == 'sun' else 0.38

    def update(self, dt):
        self.age += dt

    @property
    def alive(self):
        return self.age < self.life

    def draw(self, canvas, font):
        t = min(1, self.age / self.life)
        layer = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
        alpha = round(200 * (1 - t))
        if self.kind == 'sun':
            color = (255, 220, 95)
            for i in range(6):
                a = i * math.tau / 6
                radius = 12 + 26 * t
                x, y = self.x + math.cos(a) * radius, self.y + math.sin(a) * radius - 16 * t
                pygame.draw.circle(layer, (*color, alpha), (round(x), round(y)), max(1, round(3 * (1 - t))))
            label = font.render(f'+{self.amount}', True, color)
            label.set_alpha(round(255 * (1 - t)))
            layer.blit(label, label.get_rect(center=(round(self.x), round(self.y - 18 - 35 * t))))
        else:
            color = (192, 226, 115) if self.kind == 'plant' else (232, 143, 95)
            pygame.draw.ellipse(layer, (*color, alpha), (round(self.x - 18 - 24 * t), round(self.y - 5 - 8 * t),
                                round(36 + 48 * t), round(10 + 16 * t)), 2)
            for i in range(5):
                a = i * math.tau / 5
                x = self.x + math.cos(a) * (14 + 25 * t)
                y = self.y - math.sin(t * math.pi) * 16 + math.sin(a) * 7
                pygame.draw.ellipse(layer, (*color, alpha), (round(x), round(y), 5, 3))
        canvas.blit(layer, (0, 0))

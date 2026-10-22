"""Reusable cartoon panels and scenery, independent of the combat simulation."""
import math
from functools import lru_cache

import pygame

from art import atlas_frame

INK = (49, 81, 52)
PAPER = (255, 249, 222)
MUTED = (108, 124, 84)
GOLD = (223, 173, 62)


def panel(surface, rect, fill=PAPER, border=(164, 156, 101), radius=16, shadow=5):
    rect = pygame.Rect(rect)
    if shadow:
        pygame.draw.rect(surface, (64, 91, 65), rect.move(0, shadow), border_radius=radius)
    pygame.draw.rect(surface, fill, rect, border_radius=radius)
    pygame.draw.rect(surface, border, rect, 2, border_radius=radius)
    if rect.h > 20:
        pygame.draw.line(surface, (255, 255, 235), (rect.x + radius, rect.y + 4),
                         (rect.right - radius, rect.y + 4), 2)


def button(surface, rect, label, font, tone='green', enabled=True):
    """Stable hit areas with hover, bevel and held-mouse feedback."""
    rect = pygame.Rect(rect)
    hover = enabled and rect.collidepoint(pygame.mouse.get_pos())
    pressed = hover and pygame.mouse.get_pressed()[0]
    palettes = {
        'green': ((92, 148, 73), (60, 103, 53), (240, 248, 208)),
        'orange': ((246, 166, 57), (168, 103, 37), (255, 252, 222)),
        'cream': ((244, 235, 195), (153, 151, 94), INK),
    }
    fill, edge, ink = palettes[tone]
    if not enabled:
        fill, edge, ink = (183, 193, 163), (130, 146, 118), (104, 121, 96)
    elif hover:
        fill = tuple(min(255, c + 15) for c in fill)
    face = rect.move(0, 2 if pressed else 0)
    radius = min(13, rect.h // 3)
    pygame.draw.rect(surface, edge, rect.move(0, 4), border_radius=radius)
    pygame.draw.rect(surface, fill, face, border_radius=radius)
    pygame.draw.rect(surface, (255, 230, 143) if hover else edge, face, 2, border_radius=radius)
    pygame.draw.line(surface, (255, 245, 189), (face.x + radius, face.y + 4),
                     (face.right - radius, face.y + 4), 2)
    if rect.h >= 40:
        for x in (face.x + 13, face.right - 14):
            pygame.draw.circle(surface, edge, (x, face.centery), 3)
            pygame.draw.circle(surface, (255, 234, 169), (x, face.centery - 1), 1)
    text = font.render(label, True, ink)
    surface.blit(text, text.get_rect(center=face.center))


def star(surface, center, radius=11, color=(255, 210, 79)):
    points = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        r = radius if i % 2 == 0 else radius * .46
        points.append((center[0] + math.cos(angle) * r, center[1] + math.sin(angle) * r))
    pygame.draw.polygon(surface, color, points)
    pygame.draw.polygon(surface, (174, 136, 51), points, 1)


def lock(surface, center, size=20):
    x, y = center
    pygame.draw.rect(surface, (91, 111, 80), (x - size // 3, y - size // 2, size * 2 // 3, size),
                     max(2, size // 7), border_radius=size // 3)
    pygame.draw.rect(surface, (250, 222, 139), (x - size // 2, y - 1, size, size * 3 // 4),
                     border_radius=max(3, size // 6))
    pygame.draw.circle(surface, (119, 104, 58), (x, y + size // 4), max(2, size // 9))


def leaves(surface, center, size=30):
    x, y = center
    pygame.draw.line(surface, (65, 105, 55), (x - size, y + size // 2), (x + size, y - size // 2), 3)
    for dx, dy, angle in ((-size // 2, 0, 28), (size // 4, -size // 3, -30)):
        leaf = pygame.Surface((size, size // 2 + 4), pygame.SRCALPHA)
        pygame.draw.ellipse(leaf, (128, 172, 67), leaf.get_rect())
        pygame.draw.line(leaf, (190, 209, 105), (3, size // 4), (size - 4, size // 4), 2)
        leaf = pygame.transform.rotate(leaf, angle)
        surface.blit(leaf, leaf.get_rect(center=(x + dx, y + dy)))


def cloud(surface, center, size=100):
    x, y = round(center[0]), round(center[1])
    pygame.draw.ellipse(surface, (202, 229, 229), (x - size // 2, y, size, size // 3))
    pygame.draw.ellipse(surface, (255, 254, 234), (x - size // 2, y - 4, size, size // 3))
    for dx, dy, r in ((-.27, .0, .18), (-.03, -.12, .24), (.24, -.01, .17)):
        pygame.draw.circle(surface, (255, 254, 234), (round(x + size * dx), round(y + size * dy)), round(size * r))


@lru_cache(maxsize=3)
def scene(theme=1):
    """Use the shipped original theme texture under a light, readable UI scene."""
    size = (800, 748)
    image = pygame.Surface(size)
    terrain = atlas_frame(f'Themes/Theme{theme}/BG0/BG1-hd', 'BG1.png')
    image.fill(((134, 206, 218), (155, 186, 83), (235, 197, 130))[theme - 1])
    if terrain is not None:
        image.blit(pygame.transform.smoothscale(terrain, size), (0, 0))
    veil = pygame.Surface(size, pygame.SRCALPHA)
    veil.fill((251, 250, 218, 95))
    image.blit(veil, (0, 0))
    pygame.draw.circle(image, (255, 232, 146), (701, 94), 58)
    pygame.draw.circle(image, (255, 245, 184), (701, 94), 43)
    for x, y, s in ((44, 112, 145), (744, 237, 166), (135, 235, 100)):
        cloud(image, (x, y), s)
    # Curved garden banks frame the interfaces without obscuring their content.
    pygame.draw.ellipse(image, (147, 184, 90), (-180, 628, 810, 290))
    pygame.draw.ellipse(image, (119, 162, 73), (380, 635, 640, 260))
    pygame.draw.ellipse(image, (181, 204, 114), (-220, 676, 1230, 240))
    for x in range(25, 800, 63):
        y = 716 + int(12 * math.sin(x))
        pygame.draw.line(image, (110, 153, 66), (x, y), (x + 2, y - 10), 2)
        pygame.draw.circle(image, (255, 245, 195), (x + 2, y - 12), 4)
        pygame.draw.circle(image, (244, 185, 80), (x + 2, y - 12), 2)
    leaves(image, (24, 31), 46)
    leaves(image, (777, 709), 50)
    return image


def motes(surface, time, top=80, bottom=650):
    """Small UI-only fireflies; no random state or gameplay clock is consumed."""
    for i in range(13):
        x = (i * 79 + 27 + math.sin(time * .45 + i) * 12) % 800
        y = top + (i * 57 - time * (4 + i % 3)) % (bottom - top)
        color = (255, 252, 203) if i % 2 else (226, 241, 160)
        pygame.draw.circle(surface, color, (round(x), round(y)), 2)

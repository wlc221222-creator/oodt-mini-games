"""Original backgrounds and road textures adapted to the gameplay waypoints."""
from functools import lru_cache

import pygame

import config as C
from art import load_image, atlas_frame


def _round_path(surface, color, points, width):
    # A union of axis-aligned strips and round caps is independent of drawing
    # order. No straight tile, border or corner can overwrite another join.
    radius = width // 2
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x0 == x1:
            rect = (x0 - radius, min(y0, y1), width, abs(y1 - y0) + 1)
        else:
            rect = (min(x0, x1), y0 - radius, abs(x1 - x0) + 1, width)
        pygame.draw.rect(surface, color, rect)
    for point in points:
        pygame.draw.circle(surface, color, point, radius)


def _cloud_path(surface, color, points, width, scale):
    """Continuous core with soft cloud lobes, including every corner."""
    _round_path(surface, color, points, max(1, width - 10 * scale))
    spacing = 20 * scale
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        # World-aligned samples give the same outline in either direction.
        start, stop = (sorted((y0, y1)) if x0 == x1 else sorted((x0, x1)))
        for position in range(((start + spacing - 1) // spacing) * spacing, stop + 1, spacing):
            center = (x0, position) if x0 == x1 else (position, y0)
            pygame.draw.circle(surface, color, center, width // 2)
    for point in points:
        pygame.draw.circle(surface, color, point, width // 2)


@lru_cache(maxsize=8)
def road_image(points, theme):
    """One continuous, antialiased road with a shared texture across all joins."""
    scale = 3
    size = (C.FIELD_W * scale, C.FIELD_H * scale)
    scaled = [(x * scale, y * scale) for x, y in points]
    def stroke(surface, color, width):
        if theme == 1:
            _cloud_path(surface, color, scaled, width * scale, scale)
        else:
            _round_path(surface, color, scaled, width * scale)

    layer = pygame.Surface(size, pygame.SRCALPHA)
    palette = (((58, 143, 182), (99, 192, 226), (159, 224, 245), (206, 244, 255)),
               ((73, 122, 18), (126, 172, 20), (172, 208, 39), (153, 128, 13)),
               ((148, 83, 37), (191, 132, 64), (242, 194, 111), (221, 168, 82)))
    for width, color in zip((C.TILE + 9, C.TILE + 7, C.TILE + 3, C.TILE), palette[theme - 1]):
        stroke(layer, color, width)

    texture = pygame.Surface((C.FIELD_W, C.FIELD_H), pygame.SRCALPHA)
    texture.fill((225, 248, 255) if theme == 1 else (189, 140, 0))
    atlas = load_image(f'original/Themes/Theme{theme}/BG1/BG-hd.png')
    if atlas is not None:
        # Take only the road interior; the old tile's grass/cloud borders must
        # never appear as rectangular seams at a turn. Mirrored tiles join at
        # matching edge pixels, with one texture origin for the whole road.
        area = ((180, 260, 80, 36) if theme == 1 else
                (100, 25, 100, 48) if theme == 2 else (108, 84, 42, 42))
        tile = pygame.transform.smoothscale(atlas.subsurface(area), (40, 20))
        variants = {(x, y): pygame.transform.flip(tile, bool(x), bool(y))
                    for x in (0, 1) for y in (0, 1)}
        for y in range(0, C.FIELD_H, tile.get_height()):
            for x in range(0, C.FIELD_W, tile.get_width()):
                texture.blit(variants[(x // 40 % 2, y // 20 % 2)], (x, y))
    texture = pygame.transform.smoothscale(texture, size)
    mask = pygame.Surface(size, pygame.SRCALPHA)
    stroke(mask, (255, 255, 255, 255), C.TILE - 5)
    texture.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    layer.blit(texture, (0, 0))
    return pygame.transform.smoothscale(layer, (C.FIELD_W, C.FIELD_H))


@lru_cache(maxsize=8)
def field_image(index):
    level = C.LEVELS[index]
    image = pygame.Surface((C.FIELD_W, C.FIELD_H))
    theme = level['theme']
    terrain = atlas_frame(f'Themes/Theme{theme}/BG0/BG1-hd', 'BG1.png')
    if terrain is not None:
        image.blit(pygame.transform.smoothscale(terrain, image.get_size()), (0, 0))
    else:
        image.fill(level['grass'][0])
    points = [(col * C.TILE + C.TILE // 2, row * C.TILE + C.TILE // 2)
              for col, row in level['path']]
    road = load_image(f'original/Themes/Theme{theme}/BG1/BG-hd.png')
    if road is not None and theme == 1:
        # Only scenery is copied from the old map; its baked route is never
        # displayed beneath our different, interactive route.
        decorations = ((0, 330, 310, 152), (705, 330, 255, 152))
        for i, area in enumerate(decorations):
            piece = road.subsurface(area)
            piece = pygame.transform.smoothscale(piece, (180, 90))
            image.blit(piece, (0 if i == 0 else C.FIELD_W - 180, C.FIELD_H - 90))
    image.blit(road_image(tuple(points), theme), (0, 0))
    # The endpoint and entrance cues occupy their real path cells.
    x, y = points[0]
    dx, dy = points[1][0] - x, points[1][1] - y
    x, y = max(13, min(C.FIELD_W - 14, x)), max(13, min(C.FIELD_H - 14, y))
    arrow = ([(x - 5, y - 7), (x + 5, y), (x - 5, y + 7)] if dx else
             [(x - 7, y - 5), (x, y + 5), (x + 7, y - 5)])
    pygame.draw.polygon(image, (116, 98, 61), arrow)
    return image

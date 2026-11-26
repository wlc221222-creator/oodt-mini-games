"""Artwork and canvas-space hit regions for the garden selector."""
import pygame

import config as C


# Sloping faces follow the receding right edge of the gravestone.
ADVENTURE = ((516, 104), (552, 111), (572, 105), (603, 107), (624, 118),
             (642, 144), (721, 157), (713, 236), (702, 244), (646, 241),
             (592, 231), (582, 224), (436, 209), (398, 199), (397, 142),
             (406, 133), (461, 130), (481, 111))
LEVELS = ((414, 247), (685, 293), (689, 312), (678, 358), (668, 366),
          (528, 336), (477, 318), (414, 308), (408, 300), (408, 251))
BOOK = ((449, 387), (504, 395), (518, 407), (502, 446), (496, 482),
        (429, 463), (427, 441), (436, 433), (439, 399))
POT = ((548, 496), (562, 473), (589, 458), (613, 458),
       (637, 478), (645, 502), (638, 523), (609, 535), (568, 529), (549, 518))
REGIONS = (ADVENTURE, LEVELS, BOOK, POT)


def _region(points):
    xs, ys = zip(*points)
    rect = pygame.Rect(min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)
    surface = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.polygon(surface, 'white', [(x - rect.x, y - rect.y) for x, y in points])
    return rect, pygame.mask.from_surface(surface)


BOUNDS, MASKS = zip(*(_region(points) for points in REGIONS))
REGION_INDEX = {tuple(rect): i for i, rect in enumerate(BOUNDS)}

FULLSCREEN = pygame.Rect(298, 276, 204, 48)
DONE = pygame.Rect(259, 438, 282, 64)
INTRO_SECONDS = 1.35
HAND_FPS = 30


def control_at(pos):
    for i, rect in enumerate(BOUNDS):
        if rect.collidepoint(pos) and MASKS[i].get_at((int(pos[0]) - rect.x, int(pos[1]) - rect.y)):
            return i
    return None


def _engraving(ui, label, size, angle, color):
    """Cut the letters into the material using a sunlit lower lip and a dark upper edge."""
    key = ('engraving', label, size, angle, color)
    if key not in ui.skins:
        font = ui.font(size * 2, True)
        ink = font.render(label, True, color)
        image = pygame.Surface((ink.get_width() + 8, ink.get_height() + 10), pygame.SRCALPHA)
        lip = font.render(label, True, (175, 175, 166))
        shadow = font.render(label, True, (27, 29, 39))
        image.blit(lip, (4, 6 if size < 25 else 8))
        image.blit(shadow, (3, 2))
        image.blit(ink, (4, 4))
        ui.skins[key] = pygame.transform.rotozoom(image, angle, .5)
    return ui.skins[key]


def _at(canvas, image, center):
    canvas.blit(image, image.get_rect(center=center))


def draw_selector(ui):
    g, canvas = ui.game, ui.canvas
    art = g.assets.misc
    if art('menu'):
        canvas.blit(art('menu'), (0, 0))
    else:
        canvas.fill((91, 100, 82))
    if art('selector_logo'):
        canvas.blit(art('selector_logo'), (19, 32))

    pointer = ui.touch_pos if ui.touch_pos is not None else g._to_canvas(pygame.mouse.get_pos())
    active = control_at(pointer) if g.state == 'menu' else None
    for index, label, center, size in ((0, '开始冒险', (554, 183), 55),
                                       (1, '选择关卡', (547, 302), 38)):
        rim = art(('selector_adventure', 'selector_levels')[index])
        if rim:
            canvas.blit(rim, ((394, 103), (406, 246))[index])
        hover, _ = ui.button_motion(BOUNDS[index])
        pressed = active == index and ui.menu_press == index
        glow = 1 if pressed or (index == 0 and g.state == 'starting') else round(hover * 6) / 6
        color = tuple(pygame.Color(32, 30, 43).lerp((229, 229, 150), glow))[:3]
        pos = (center[0], center[1] + int(pressed))
        _at(canvas, _engraving(ui, label, size, -8, color), pos)
    progress = '已通关' if g.adventure_completed() else f"第 {C.LEVELS[g.unlocked]['id']} 关"
    _at(canvas, _engraving(ui, progress, 16, -7, (215, 213, 175)), (548, 128))

    book = art('selector_almanac')
    if book:
        rect = BOUNDS[2]
        shadow = art('selector_book_shadow')
        if shadow:
            canvas.blit(shadow, (rect.left - 14, rect.bottom - 36))
        book_pos = (422, 385 + int(active == 2 and ui.menu_press == 2))
        canvas.blit(book, book_pos)
        if active == 2:
            key = 'lit_almanac'
            if key not in ui.skins:
                ui.skins[key] = book.copy()
                ui.skins[key].fill((35, 36, 12, 0), special_flags=pygame.BLEND_RGBA_ADD)
            canvas.blit(ui.skins[key], book_pos)
    else:
        _at(canvas, _engraving(ui, '植物图鉴', 18, -7, (70, 57, 37)), BOUNDS[2].center)
    color = (245, 238, 146) if active == 3 else (72, 71, 44)
    _at(canvas, _engraving(ui, '设置', 20, 4, color), (597, 505 + int(active == 3 and ui.menu_press == 3)))

    if g.state == 'starting':
        sheet = art('selector_hand')
        if sheet:
            frame = min(24, int(g.intro_elapsed * HAND_FPS))
            w, h = sheet.get_width() // 5, sheet.get_height() // 5
            canvas.blit(sheet, (185, 276), (frame % 5 * w, frame // 5 * h, w, h))
        if g.intro_elapsed > 1.03:
            ui.shade(round(220 * min(1, (g.intro_elapsed - 1.03) / (INTRO_SECONDS - 1.03))))


def draw_settings(ui):
    ui.shade(145)
    back = ui.game.assets.misc('selector_settings')
    if back:
        _at(ui.canvas, back, (400, 292))
    else:
        ui.panel(pygame.Rect(222, 82, 356, 421), 'stone')
    ui.text('游戏设置', (400, 212), 30, bold=True, outline=(31, 29, 39))
    mark = ui.game.assets.misc('selector_check_on' if ui.game.fullscreen else 'selector_check_off')
    if mark:
        ui.canvas.blit(mark, (FULLSCREEN.x + 14, FULLSCREEN.y + 4))
    ui.text('全屏显示', (424, FULLSCREEN.centery), 23, bold=True,
            color=(244, 230, 155) if ui.hover(FULLSCREEN) else (216, 211, 178))
    ui.text('F 切换显示模式', (400, 356), 15, (192, 191, 173))
    button = ui.game.assets.misc('selector_return')
    if button:
        ui.canvas.blit(ui.scaled(button, DONE.size), DONE)
    ui.text('返回庭院', DONE.center, 23, bold=True, outline=(39, 37, 48),
            color=(255, 240, 157) if ui.hover(DONE) else (220, 218, 193))

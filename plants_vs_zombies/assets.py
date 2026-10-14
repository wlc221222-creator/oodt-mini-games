# -*- coding: utf-8 -*-
"""Sprite layer for the original-art Plants vs Zombies port.

Every picture in the game comes from the original game's extracted art pack
(``assets/graphics``). This module keeps *all* pygame image handling in one
place, so the entity classes can stay focused on behaviour -- which is the
object-oriented talking point of the project.

The loader is written to fail soft: if a frame set cannot be found it returns
an empty list, and the entity falls back to a flat coloured shape instead of
crashing. That keeps the game playable even if the art pack is incomplete.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List

import pygame

ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
GFX_DIR = os.path.join(ASSET_DIR, "graphics")

# The original shows an 800x600 window cut from the top-left of a 1400x600
# background, starting 220 px in. We reproduce that exactly so the art lines
# up with the grid.
BG_CROP_X = 220
MENU_CROP_X = 80


def _frame_index(path: str) -> int:
    stem = os.path.splitext(os.path.basename(path))[0]
    try:
        return int(stem.rsplit("_", 1)[1])
    except (IndexError, ValueError):
        return 0


def _key_out_white(img: pygame.Surface, thresh: int = 240) -> pygame.Surface:
    """Some original frames (Potato Mine, Squash, ...) ship with a solid white
    background and no alpha channel. The original game strips it with a white
    colour key; we do the same, and also drop the near-white fringe so no
    rectangle outline is left behind."""
    import numpy as np

    arr = pygame.surfarray.pixels3d(img).astype(np.int16)
    alpha = pygame.surfarray.pixels_alpha(img)
    white = (arr[:, :, 0] > thresh) & (arr[:, :, 1] > thresh) & (arr[:, :, 2] > thresh)
    alpha[white] = 0
    del arr, alpha
    return img.copy()


def _has_alpha(img: pygame.Surface) -> bool:
    """True when the image already carries a meaningful alpha channel."""
    w, h = img.get_size()
    step = max(1, min(w, h) // 64)
    for y in range(0, h, step):
        for x in range(0, w, step):
            if img.get_at((x, y))[3] < 250:
                return True
    return False


class Anim:
    """A tiny frame animator shared by every entity."""

    def __init__(self, frames: List[pygame.Surface], interval: float = 0.12,
                 loop: bool = True) -> None:
        self.frames = frames or []
        self.interval = interval
        self.loop = loop
        self.t = 0.0
        self.i = 0
        self.done = False

    def set_frames(self, frames: List[pygame.Surface], reset: bool = False) -> None:
        if frames is self.frames and not reset:
            return
        self.frames = frames or []
        if reset:
            self.i = 0
            self.t = 0.0
            self.done = False
        if self.frames:
            self.i %= len(self.frames)

    def update(self, dt: float) -> None:
        if len(self.frames) <= 1:
            self.i = 0
            return
        self.t += dt
        while self.t >= self.interval:
            self.t -= self.interval
            if self.i + 1 >= len(self.frames):
                if self.loop:
                    self.i = 0
                else:
                    self.i = len(self.frames) - 1
                    self.done = True
            else:
                self.i += 1

    def image(self):
        return self.frames[self.i] if self.frames else None


class Assets:
    def __init__(self) -> None:
        self.rects: Dict[str, dict] = {"plant": {}, "zombie": {}}
        self._plant: Dict[str, List[pygame.Surface]] = {}
        self._zombie: Dict[str, Dict[str, List[pygame.Surface]]] = {}
        self._card: Dict[str, pygame.Surface] = {}
        self._bullet: Dict[str, pygame.Surface] = {}
        self._misc: Dict[str, pygame.Surface] = {}
        self.sun_frames: List[pygame.Surface] = []
        self._load_rects()
        self._load_misc()
        self.sun_frames = self._frames(
            self._resolve(os.path.join(GFX_DIR, "Plants", "Sun"), "Sun"), "Sun")

    # ------------------------------------------------------------- internals
    def _load_rects(self) -> None:
        mapping = {"plant": ("plant_rect.json", "plant_image_rect"),
                   "zombie": ("zombie_rect.json", "zombie_image_rect")}
        for key, (fname, root) in mapping.items():
            path = os.path.join(ASSET_DIR, fname)
            if os.path.exists(path):
                with open(path, encoding="utf-8") as fh:
                    self.rects[key] = json.load(fh).get(root, {})

    def _resolve(self, folder: str, base: str) -> str:
        """Find the folder holding ``base_*.png`` frames.

        Art sets sit at varying depths in the original pack (e.g. the cracked
        Wall-nut states live in ``Plants/WallNut/WallNut_cracked1``), so this
        walks the tree and returns the first folder that actually contains
        ``base_N.png`` files.
        """
        if not os.path.isdir(folder):
            return folder

        def has_frames(path: str) -> bool:
            try:
                return any(f.endswith(".png") and f.rsplit("_", 1)[0] == base
                           for f in os.listdir(path))
            except OSError:
                return False

        for root, dirs, _ in os.walk(folder):
            dirs.sort()
            if has_frames(root):
                return root
        return folder

    def _frames(self, folder: str, base: str, crop_x: int = 0,
                crop_w: int | None = None, scale: float = 1.0
                ) -> List[pygame.Surface]:
        # Some art sets live one level deeper (e.g. Zombies/NormalZombie/Zombie).
        nested = os.path.join(folder, base)
        if os.path.isdir(nested):
            folder = nested
        if not os.path.isdir(folder):
            return []
        files = [f for f in os.listdir(folder)
                 if f.endswith(".png") and f.rsplit("_", 1)[0] == base]
        files.sort(key=_frame_index)
        out: List[pygame.Surface] = []
        for f in files:
            img = pygame.image.load(os.path.join(folder, f)).convert_alpha()
            if not _has_alpha(img):
                img = _key_out_white(img)
            w, h = img.get_size()
            cw = crop_w if crop_w is not None else w - crop_x
            if cw <= 0:
                cw = w
                crop_x = 0
            sub = img.subsurface(pygame.Rect(crop_x, 0, cw, h)).copy()
            if scale != 1.0:
                sub = pygame.transform.smoothscale(
                    sub, (max(1, int(cw * scale)), max(1, int(h * scale))))
            out.append(sub)
        return out

    def _load_misc(self) -> None:
        def one(path, crop=None, scale=1.0):
            if not os.path.exists(path):
                return None
            img = pygame.image.load(path).convert_alpha()
            if crop is not None:
                img = img.subsurface(pygame.Rect(*crop)).copy()
            if scale != 1.0:
                w, h = img.get_size()
                img = pygame.transform.smoothscale(
                    img, (int(w * scale), int(h * scale)))
            return img

        for index in (0, 1):
            bg = os.path.join(GFX_DIR, "Items", "Background", f"Background_{index}.jpg")
            if os.path.exists(bg):
                img = pygame.image.load(bg).convert()
                self._misc[f"background_{index}"] = img.subsurface(
                    pygame.Rect(BG_CROP_X, 0, 800, 600)).copy()
        self._misc["background"] = self._misc.get("background_0")

        scr = os.path.join(GFX_DIR, "Screen")
        self._misc["menu"] = one(os.path.join(scr, "MainMenu.png"),
                                 (MENU_CROP_X, 0, 800, 600))
        self._misc["victory"] = one(os.path.join(scr, "GameVictory.png"))
        self._misc["lose"] = one(os.path.join(scr, "GameLoose.png"))
        self._misc["bar"] = one(os.path.join(scr, "ChooserBackground.png"))
        self._misc["panel"] = one(os.path.join(scr, "PanelBackground.png"))
        self._misc["boom"] = one(os.path.join(scr, "Boom.png"))
        self._misc["start_button"] = one(os.path.join(scr, "StartButton.png"))
        self._misc["adventure"] = one(os.path.join(scr, "Adventure_0.png"))
        self._misc["adventure_hover"] = one(os.path.join(scr, "Adventure_1.png"))
        head = one(os.path.join(GFX_DIR, "Zombies", "NormalZombie",
                                "ZombieHead", "ZombieHead_0.png"))
        if head is not None:
            head = _key_out_white(head) if not _has_alpha(head) else head
            head = head.subsurface(head.get_bounding_rect()).copy()
            self._misc["wave_head"] = pygame.transform.smoothscale(head, (34, 36))
        flag = one(os.path.join(GFX_DIR, "Zombies", "FlagZombie",
                                "FlagZombie", "FlagZombie_0.png"), (57, 1, 55, 30))
        if flag is not None:
            self._misc["wave_flag"] = pygame.transform.smoothscale(flag, (27, 16))

        # Bullets are cropped with the original's own rectangles.
        bdir = os.path.join(GFX_DIR, "Bullets")
        for name, sub in (("PeaNormal", "PeaNormal"), ("PeaIce", "PeaIce")):
            r = self.rects["plant"].get(name, {})
            self._bullet[name] = one(
                os.path.join(bdir, sub, f"{sub}_0.png"),
                (r.get("x", 0), 0, r.get("width", 28), r.get("height", 34)))

    # ---------------------------------------------------------------- public
    def plant(self, name: str) -> List[pygame.Surface]:
        if name not in self._plant:
            folder = self._resolve(os.path.join(GFX_DIR, "Plants"), name)
            r = self.rects["plant"].get(name)
            if r:
                self._plant[name] = self._frames(
                    folder, name, r.get("x", 0), r.get("width"))
            else:
                self._plant[name] = self._frames(folder, name)
        return self._plant[name]

    def zombie(self, kind: str) -> Dict[str, List[pygame.Surface]]:
        if kind in self._zombie:
            return self._zombie[kind]
        table = {
            "normal": ("NormalZombie", "Zombie", "ZombieAttack"),
            "cone": ("ConeheadZombie", "ConeheadZombie", "ConeheadZombieAttack"),
            "bucket": ("BucketheadZombie", "BucketheadZombie",
                       "BucketheadZombieAttack"),
        }
        folder, base, attack = table[kind]
        zdir = os.path.join(GFX_DIR, "Zombies", folder)
        ndir = os.path.join(GFX_DIR, "Zombies", "NormalZombie")
        zx = lambda n: self.rects["zombie"].get(n, {}).get("x", 0)
        sets = {
            "walk": self._frames(zdir, base, zx(base)),
            "attack": self._frames(zdir, attack, zx(attack)),
            "body": self._frames(ndir, "Zombie", zx("Zombie")),
            "body_attack": self._frames(ndir, "ZombieAttack", zx("ZombieAttack")),
            "die": self._frames(ndir, "ZombieDie", zx("ZombieDie")),
            "boom": self._frames(ndir, "BoomDie", zx("BoomDie")),
        }
        self._zombie[kind] = sets
        return sets

    def card(self, name: str) -> pygame.Surface | None:
        if name not in self._card:
            path = os.path.join(GFX_DIR, "Cards", f"card_{name}.png")
            self._card[name] = self._one_scaled(path, 0.78)
        return self._card[name]

    def ready_card(self, name: str) -> pygame.Surface | None:
        return self.card(name + "_move") or self.card(name)

    def background(self, index: int = 0) -> pygame.Surface | None:
        return self._misc.get(f"background_{index}") or self._misc.get("background")

    def _one_scaled(self, path: str, scale: float):
        if not os.path.exists(path):
            return None
        img = pygame.image.load(path).convert_alpha()
        w, h = img.get_size()
        return pygame.transform.smoothscale(img, (int(w * scale), int(h * scale)))

    def bullet(self, name: str):
        return self._bullet.get(name)

    def misc(self, name: str):
        return self._misc.get(name)


_ASSETS: Assets | None = None


def get_assets() -> Assets:
    """Lazy singleton -- safe to call before pygame is fully set up."""
    global _ASSETS
    if _ASSETS is None:
        _ASSETS = Assets()
    return _ASSETS

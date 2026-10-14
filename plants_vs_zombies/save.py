# -*- coding: utf-8 -*-
"""Tiny JSON progress store for adventure mode.

Keeps the demo's progression (which levels are unlocked and which plants have
been earned) across runs. Deliberately forgiving: any read/write error is
swallowed so a missing or read-only file never breaks the game.
"""

from __future__ import annotations

import json
import os
import sys

def default_save_path() -> str:
    if getattr(sys, "frozen", False):
        app_data = os.environ.get("LOCALAPPDATA") or os.path.join(
            os.path.expanduser("~"), "AppData", "Local")
        return os.path.join(app_data, "OODTMiniGames", "PlantsVsZombies", "savegame.json")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "savegame.json")


SAVE_PATH = default_save_path()


def load() -> dict:
    try:
        with open(SAVE_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save(data: dict) -> None:
    try:
        os.makedirs(os.path.dirname(os.path.abspath(SAVE_PATH)), exist_ok=True)
        with open(SAVE_PATH, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
    except Exception:
        pass

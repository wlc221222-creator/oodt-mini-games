"""Small validated unlock save, independent of the Plants vs Zombies save."""
import json
import os
from pathlib import Path
import sys

import config as C


def save_path():
    override = os.environ.get('OODT_CARROT_SAVE_PATH')
    if override:
        return Path(override)
    if getattr(sys, 'frozen', False):
        return Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'OODTMiniGames' / 'DefendCarrot' / 'progress.json'
    return Path(__file__).resolve().parent / 'progress.json'


def load():
    default = {'unlocked': 1, 'best': {}}
    try:
        data = json.loads(save_path().read_text(encoding='utf-8'))
        if not isinstance(data, dict):
            return default
        unlocked = data.get('unlocked', 1)
        if type(unlocked) is not int:
            return default
        best = data.get('best', {})
        return {'unlocked': max(1, min(len(C.LEVELS), unlocked)),
                'best': {str(i): value for i in range(len(C.LEVELS))
                         if isinstance(best, dict) and type(value := best.get(str(i))) is int and 1 <= value <= 3}}
    except (OSError, ValueError, TypeError):
        return default


def save(data):
    path = save_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(path)
        return True
    except OSError:
        return False

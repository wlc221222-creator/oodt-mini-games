"""Frozen builds use persistent per-user storage, not onefile extraction."""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import save


def main():
    assert Path(save.default_save_path()).parent == Path(save.__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix="pvz_frozen_save_") as temp:
        with patch.object(sys, "frozen", True, create=True), patch.dict(os.environ, {"LOCALAPPDATA": temp}):
            target = Path(save.default_save_path())
            assert target == Path(temp) / "OODTMiniGames" / "PlantsVsZombies" / "savegame.json"
            with patch.object(save, "SAVE_PATH", str(target)):
                progress = {"unlocked": 2, "plants": ["sunflower", "peashooter", "wallnut", "snowpea"]}
                save.save(progress)
                assert target.is_file() and save.load() == progress
    print("PASS: source save location and persistent packaged save roundtrip")


if __name__ == "__main__":
    main()

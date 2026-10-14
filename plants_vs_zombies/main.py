"""Entry point for the Plants vs Zombies MVP.

Usage:
    python main.py

Controls:
    1-8            select a plant card
    left click     place the selected plant on the lawn, or collect a sun
    right click    cancel the current selection
    Enter          continue the adventure after a win
    R              retry the current level after win or loss
    Esc            return to the menu (quit from the menu)
"""

import sys


def self_test(report_path: str) -> int:
    """Validate the distributed executable without changing player progress."""
    import json
    import os
    import tempfile
    import traceback
    from pathlib import Path

    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    report = {"game": "PlantsVsZombies", "frozen": bool(getattr(sys, "frozen", False))}
    try:
        import pygame
        import config as C
        import save
        from game import Game
        with tempfile.TemporaryDirectory(prefix="pvz_exe_check_") as temp:
            save.SAVE_PATH = str(Path(temp) / "save.json")
            game = Game()
            assert game.unlocked == 0 and game.owned_plants == C.START_PLANTS
            for name in ("menu", "background_0", "background_1", "wave_head", "wave_flag"):
                assert game.assets.misc(name) is not None, name
            for kind, spec in C.PLANTS.items():
                assert game.assets.plant(spec["sprite"]), kind
                assert game.assets.card(spec["card"]) is not None, kind
            for kind in C.ZOMBIES:
                assert game.assets.zombie(kind)["walk"], kind
            game.draw()
            game.start_adventure()
            assert game.level["id"] == "1-1" and game.state == "choosing"
            game.seeds = list(C.START_PLANTS)
            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
            game.draw()
            assert game.state == "playing"
            game.wave_index = len(game.waves)
            game._check_victory()
            game.draw()
            assert save.load()["unlocked"] == 1
            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
            assert game.level["id"] == "1-2" and game.state == "choosing"
            game.draw()
            pygame.quit()
            report.update(ok=True, initial_level="1-1", next_level="1-2", save_roundtrip=True)
    except Exception:
        report.update(ok=False, error=traceback.format_exc())
    Path(report_path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if report["ok"] else 1


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "--self-test":
        sys.exit(self_test(sys.argv[2]))
    from game import Game
    Game().run()


if __name__ == "__main__":
    main()

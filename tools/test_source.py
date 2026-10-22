"""Run real source-game regressions with isolated player saves."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    env = os.environ.copy()
    env["SDL_VIDEODRIVER"] = "dummy"
    env["SDL_AUDIODRIVER"] = "dummy"
    env["PYTHONIOENCODING"] = "utf-8"
    with tempfile.TemporaryDirectory(prefix="oodt_source_tests_") as temp:
        for test in ("test_adventure_flow", "test_ui_flow", "test_almanac", "test_pause", "test_drag_tools", "test_hit_flash", "test_progress", "test_death",
                     "test_plants", "test_packaged_save", "test_gameplay_revision", "test_expansion", "test_level_balance", "test_smoke"):
            code = "import runpy,save;save.SAVE_PATH=" + repr(str(Path(temp) / "save.json"))
            code += ";runpy.run_path(" + repr("tests/" + test + ".py") + ",run_name='__main__')"
            subprocess.run([sys.executable, "-c", code], cwd=ROOT / "plants_vs_zombies", env=env, check=True)
        for test in ("test_rules", "test_ui_flow", "test_presentation", "test_placement", "test_animation",
                     "test_roads", "test_carrot_health", "test_combat", "test_campaign", "test_campaign_balance", "test_smoke"):
            env['OODT_CARROT_SAVE_PATH'] = str(Path(temp) / (test + '_progress.json'))
            subprocess.run([sys.executable, "tests/" + test + ".py"], cwd=ROOT / "defend_carrot", env=env, check=True)
    print("PASS: both source games and all progression/save checks")


if __name__ == "__main__":
    main()

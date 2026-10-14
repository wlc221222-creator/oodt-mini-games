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
        for test in ("test_adventure_flow", "test_ui_flow", "test_progress", "test_death",
                     "test_plants", "test_packaged_save", "test_smoke"):
            code = "import runpy,save;save.SAVE_PATH=" + repr(str(Path(temp) / "save.json"))
            code += ";runpy.run_path(" + repr("tests/" + test + ".py") + ",run_name='__main__')"
            subprocess.run([sys.executable, "-c", code], cwd=ROOT / "plants_vs_zombies", env=env, check=True)
        subprocess.run([sys.executable, "tests/test_smoke.py"], cwd=ROOT / "defend_carrot", env=env, check=True)
    print("PASS: both source games and all progression/save checks")


if __name__ == "__main__":
    main()

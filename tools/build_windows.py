"""Build and validate both independent Windows 64-bit executables."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def main():
    if sys.platform != "win32":
        raise SystemExit("Run this build script using 64-bit Python on Windows.")
    import PyInstaller.__main__

    dist = ROOT / "dist"
    for folder, name in (("plants_vs_zombies", "PlantsVsZombies"), ("defend_carrot", "DefendCarrot")):
        args = ["--noconfirm", "--clean", "--onefile", "--windowed", "--noupx",
                "--name", name, "--paths", str(ROOT / folder),
                "--distpath", str(dist), "--workpath", str(ROOT / "build" / name),
                "--specpath", str(ROOT / "build")]
        if folder == "plants_vs_zombies":
            args += ["--add-data", str(ROOT / folder / "assets") + os.pathsep + "assets"]
        args.append(str(ROOT / folder / "main.py"))
        PyInstaller.__main__.run(args)
        with tempfile.TemporaryDirectory(prefix=name + "_exe_check_") as temp:
            report = Path(temp) / "report.json"
            result = subprocess.run([str(dist / (name + ".exe")), "--self-test", str(report)],
                                    cwd=temp, timeout=90)
            data = json.loads(report.read_text(encoding="utf-8")) if report.is_file() else {}
            assert result.returncode == 0 and data.get("ok") and data.get("frozen"), data
            print("Executable check passed:", name, data, flush=True)
    print("Build complete:", dist, flush=True)


if __name__ == "__main__":
    main()

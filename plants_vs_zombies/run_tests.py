"""Run the Plants vs Zombies regressions with an isolated save."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    root = Path(__file__).resolve().parent
    env = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', PYTHONIOENCODING='utf-8')
    with tempfile.TemporaryDirectory(prefix='pvz_regressions_') as temp:
        for test in sorted((root / 'tests').glob('test_*.py')):
            code = 'import runpy,save;save.SAVE_PATH=' + repr(str(Path(temp) / 'save.json'))
            code += ';runpy.run_path(' + repr(str(test)) + ',run_name="__main__")'
            subprocess.run([sys.executable, '-B', '-c', code], cwd=root, env=env, check=True)
    print('PASS: Plants vs Zombies regressions, including menu, touch and motion')


if __name__ == '__main__':
    main()

import sys
from pathlib import Path

# Добавляем src в PYTHONPATH при прямом запуске python main.py
src_dir = Path(__file__).resolve().parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from maxgoida.app import run

if __name__ == "__main__":
    run()

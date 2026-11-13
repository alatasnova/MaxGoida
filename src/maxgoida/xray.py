import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def get_xray_binary_path() -> str:
    """Определяет путь к исполняемому файлу xray.exe относительно корня проекта."""
    # Поиск xray.exe в стандартных местах
    current = Path(__file__).resolve().parent
    # current = src/maxgoida, root = src/maxgoida/../.. = project root
    project_root = current.parent.parent
    potential_paths = [
        project_root / "xray" / "xray.exe",
        project_root / "xray" / "xray",
        Path("xray/xray.exe"),
        Path("xray/xray"),
    ]
    for p in potential_paths:
        if p.exists():
            return str(p)
    return "xray"


class Tunnel:
    def __init__(self, config: dict, local_port: int, verbose: bool = False):
        self.local_port = local_port
        self.config = config
        self.verbose = verbose
        self.process = None
        self.tmp_cfg_file = None
        self.xray_path = get_xray_binary_path()

    def __enter__(self):
        # Создаём временный файл с конфигурацией
        self.tmp_cfg_file = tempfile.NamedTemporaryFile(
            mode="w+",
            suffix=".json",
            delete=False,
            prefix="shared_"
        )
        self.tmp_cfg_file.write(json.dumps(self.config))
        self.tmp_cfg_file.flush()

        self.process = subprocess.Popen(
            [self.xray_path, "run", "-c", self.tmp_cfg_file.name],
            stdin=subprocess.DEVNULL,
            stdout=sys.stdout if self.verbose else subprocess.DEVNULL,
            stderr=sys.stderr if self.verbose else subprocess.DEVNULL,
            text=self.verbose,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.process is not None:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            except OSError as e:
                if self.verbose:
                    print(f"Warning: could not terminate process: {e}")

        if self.tmp_cfg_file is not None:
            try:
                self.tmp_cfg_file.close()
                if os.path.exists(self.tmp_cfg_file.name):
                    os.unlink(self.tmp_cfg_file.name)
            except OSError as e:
                if self.verbose:
                    print(f"Warning: could not remove temp file: {e}")

import json
import os
import subprocess
import sys
import tempfile

class Tunnel:
    def __init__(self, config: dict, local_port: int, verbose=True):
        self.local_port = local_port
        self.config = config
        self.verbose = verbose
        self.process = None
        self.tmp_cfg_file = None

    def __enter__(self):
        # Создаём временный файл с конфигурацией
        self.tmp_cfg_file = tempfile.NamedTemporaryFile(
            mode="w+",
            suffix=".json",
            delete=False,
            prefix='shared_'
        )
        self.tmp_cfg_file.write(json.dumps(self.config))
        self.tmp_cfg_file.flush()

        self.process = subprocess.Popen(
            ["xray/xray", "run", "-c", self.tmp_cfg_file.name],
            stdin=subprocess.DEVNULL,
            stdout=sys.stdout if self.verbose else subprocess.DEVNULL,
            stderr=sys.stderr,
            text=self.verbose,
        )

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 1. Завершаем процесс
        if self.process is not None:
            try:
                self.process.terminate()
                # Даём время на завершение (опционально)
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Если не завершился, принудительно убиваем
                self.process.kill()
                self.process.wait()
            except OSError as e:
                # На Windows может быть OSError, если процесс уже завершился
                print(f"Warning: could not terminate process: {e}")

        # 2. Закрываем и удаляем временный файл
        if self.tmp_cfg_file is not None:
            try:
                self.tmp_cfg_file.close()
                os.unlink(self.tmp_cfg_file.name)
            except OSError as e:
                print(f"Warning: could not remove temp file: {e}")
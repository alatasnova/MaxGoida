import json
import os
import subprocess
import sys
import tempfile

# TODO: currently supports VLESS only

class Tunnel:
    def __init__(self, config: dict, local_port: int):
        self.local_port = local_port
        self.config = config

        self.tmp_cfg_file = tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False, prefix='shared_')

        self.tmp_cfg_file.write(json.dumps(self.config))
        self.tmp_cfg_file.flush()

        self.process = subprocess.Popen(
            ["xray/xray", "run", "-c", self.tmp_cfg_file.name],
            stdout=sys.stdout, # TODO: it's for debug. We should use better logging.
            stderr=sys.stderr,
            text=True,
        )

    def __del__(self):
        self.process.terminate()
        self.tmp_cfg_file.close()
        os.unlink(self.tmp_cfg_file.name)
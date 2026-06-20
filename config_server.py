import base64
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, FileResponse

from pinger import PingResult


def encode_64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")


class ConfigServer:
    def __init__(self):
        self.title = "MaxGoida"
        self.update_interval: int = 1  # in hours
        self.configs = []
        self.timestamp = datetime.now()
        self.app = FastAPI()

        @self.app.get('/')
        def handle_fetch():
            return PlainTextResponse(self.generate_response())

        @self.app.get('/alt')
        def handle_fetch_alt():
            return FileResponse('static/configs.txt')

    def generate_response(self) -> str:
        resp = [
            f"# profile-title: {self.title}",
            f"# profile-update-interval: {self.update_interval}",
            f"# last-updated: {self.timestamp.strftime('%d/%m/%Y, %H:%M:%S')}"
            '',
            *[config.link for config in self.configs]
        ]

        return '\n'.join(resp)

    def update_configs(self, configs: list[PingResult]):
        self.configs = configs
        self.timestamp = datetime.now()

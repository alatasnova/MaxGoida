import base64
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, FileResponse


def encode_64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")


class ConfigServer:
    def __init__(self):
        self.title = "MaxGoida"
        self.update_interval: int = 1  # in hours
        self.configs: list[str] = []
        self.timestamp = datetime.now()
        self.app = FastAPI()

        @self.app.get("/")
        def handle_fetch():
            return PlainTextResponse(self.generate_response())

        @self.app.get("/alt")
        def handle_fetch_alt():
            return FileResponse("static/configs.txt")

    def generate_response(self) -> str:
        resp = [
            f"# profile-title: {self.title}",
            f"# profile-update-interval: {self.update_interval}",
            f"# last-updated: {self.timestamp.strftime('%d/%m/%Y, %H:%M:%S')}",
            "",
            *self.configs
        ]
        return "\n".join(resp)

    def update_configs(self, configs: list[str]):
        """Обновляет итоговый список рабочих ссылок подписки."""
        self.configs = configs
        self.timestamp = datetime.now()

    def add_working_config(self, config_link: str):
        """Добавляет рабочий конфиг в список (или обновляет его), если его там еще нет."""
        base = config_link.split("#")[0]
        # Если конфиг уже был с другим именем, заменяем его
        for idx, existing in enumerate(self.configs):
            if existing.split("#")[0] == base:
                self.configs[idx] = config_link
                self.timestamp = datetime.now()
                return

        self.configs.append(config_link)
        self.timestamp = datetime.now()

    def remove_config(self, raw_link: str):
        """Удаляет конфиг из активной подписки, если он перестал работать."""
        base = raw_link.split("#")[0]
        self.configs = [c for c in self.configs if c.split("#")[0] != base]

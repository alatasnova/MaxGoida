import asyncio
import httpx


class Fetcher:
    def __init__(self, url_list: list[str]):
        self.urls = url_list

    async def _fetch_url(self, client: httpx.AsyncClient, url: str) -> tuple[str, set[str]]:
        """Загружает конфиги по ссылке и возвращает кортеж (url, configs)."""
        print(f"[Fetcher] Загрузка {url}...")
        try:
            response = await client.get(url, follow_redirects=True, timeout=15.0)
            if response.is_success:
                configs = {
                    line.strip()
                    for line in response.text.split("\n")
                    if line.strip() and not line.strip().startswith("#")
                }
                print(f"[Fetcher] Успешно получено {len(configs)} конфигов из {url}")
                return url, configs
            else:
                print(f"[Fetcher] Предупреждение: {url} ответил {response.status_code}. Пропускаем.")
                return url, set()
        except Exception as e:
            print(f"[Fetcher] Ошибка загрузки {url}: {e}. Пропускаем источник.")
            return url, set()

    async def fetch_by_sources(self) -> dict[str, set[str]]:
        """
        Возвращает словарь {url_источника: set_конфигов}.
        Позволяет отслеживать принадлежность конфига к конкретному списку.
        """
        async with httpx.AsyncClient() as client:
            tasks = [self._fetch_url(client, url) for url in self.urls]
            results = await asyncio.gather(*tasks)
            return {url: configs for url, configs in results if configs}

    async def fetch_all(self) -> set[str]:
        """Возвращает общий набор всех уникальных конфигураций."""
        by_sources = await self.fetch_by_sources()
        all_configs = {cfg for configs in by_sources.values() for cfg in configs}
        print(f"[Fetcher] Всего уникальных конфигов со всех источников: {len(all_configs)}")
        return all_configs

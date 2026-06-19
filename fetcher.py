import asyncio
import httpx

class Fetcher:
    def __init__(self, url_list: list[str]):
        self.urls = url_list
        self.client = httpx.AsyncClient()

    async def _fetch_url(self, url: str):
        print("Fetching", url)
        response = await self.client.get(url, follow_redirects=True)
        if response.is_success:
            return {config.strip() for config in response.text.split('\n') if config and not config.startswith('#')}
        else:
            print(response.status_code)

    async def fetch_all(self):
        results = await asyncio.gather(*[self._fetch_url(url) for url in self.urls])
        return {item for items in results for item in items}

URLS = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/BLACK_VLESS_RUS.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/23.txt"
]

async def main():
    fetcher = Fetcher(URLS)
    configs = await fetcher.fetch_all()
    print(configs)

if __name__ == '__main__':
    asyncio.run(main())
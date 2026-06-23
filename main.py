import asyncio

import httpx
import uvicorn

from config_server import ConfigServer
from fetcher import Fetcher
from pinger import ConfigPinger, PingResult


URLS = [
    # "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/BLACK_VLESS_RUS.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/23.txt",
    # "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/6.txt"
]
START_PORT = 8089
MAX_CONCURRENT = 20

async def main():
    config_server = ConfigServer()
    config = uvicorn.Config(config_server.app, host='0.0.0.0', port=5000, log_level="info")
    server = uvicorn.Server(config)

    asyncio.create_task(server.serve())

    await loop(config_server)

def filter_success_results(ping_results: list[PingResult]) -> list[PingResult]:
    return [r for r in ping_results if r.success]

async def loop(server: ConfigServer):
    fetcher = Fetcher(URLS)
    pinger = ConfigPinger(START_PORT, max_concurrent=MAX_CONCURRENT)

    while True:
        try:
            print("Fetching configs..")
            raw_configs = await fetcher.fetch_all()
        except httpx.ConnectTimeout:
            print("Can't fetch configs (Timeout)! Retrying...")
            continue
        except httpx.ConnectError:
            print("Can't fetch configs (Connect Error)! Retrying...")
            continue

        print(f"Pinging {len(raw_configs)} configs...")
        pre_results = filter_success_results(await pinger.ping_links(raw_configs, verbose=False))

        # 2 step check
        success_rate = len(pre_results) / len(raw_configs)
        print(f"Got {len(pre_results)} working of {len(raw_configs)} ({success_rate * 100}%)! Quick 2 step checking...")
        final_results = await pinger.ping_links([i.link for i in pre_results])

        print(f"Tier 1 sorted configs (got {len(final_results)}):")
        for i in final_results:
            print(i.link)

        # desik will make the rest
        # (selenuim)
        # oh no fuck
        ...

        server.update_configs(final_results)


if __name__ == '__main__':
    asyncio.run(main())
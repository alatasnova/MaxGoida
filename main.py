import asyncio
import random

import httpx
import uvicorn

from config_server import ConfigServer
from fetcher import Fetcher
from pinger import ConfigPinger, PingResult


URLS = [
    # "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/BLACK_VLESS_RUS.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/23.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/6.txt"
]

START_PORT = 8089
MAX_CONCURRENT = 5


configs_reputation: dict[str, int] = {}
MAX_CONFIG_REPUTATION = 1
MIN_CONFIG_REPUTATION = -3

async def main():
    config_server = ConfigServer()
    config = uvicorn.Config(config_server.app, host='0.0.0.0', port=5000, log_level="info")
    server = uvicorn.Server(config)

    asyncio.create_task(server.serve())

    await loop(config_server)

def filter_success_results(ping_results: list[PingResult]) -> list[PingResult]:
    return [r for r in ping_results if r.success]

def calc_check_probability(config_reputation: int) -> float:
    if config_reputation >= 0:
        return 1.0
    if config_reputation == MIN_CONFIG_REPUTATION:
        return 0.05
    return 1 / (abs(config_reputation) + 0.5)

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

        to_ping = []
        for config in raw_configs:
            current_config_reputation = configs_reputation.setdefault(config, 0)
            if random.random() < calc_check_probability(current_config_reputation):
                to_ping.append(config)

        print(f"Pinging {len(to_ping)} configs (filtered from {len(raw_configs)})...")
        ping_results = await pinger.ping_links(to_ping, verbose=False)
        pre_results = []
        for result in ping_results:
            current_config_reputation = configs_reputation.setdefault(result.link, 0)
            if result.success:
                pre_results.append(result)
                current_config_reputation += 1
            else:
                current_config_reputation -= 1
            current_config_reputation = min(MAX_CONFIG_REPUTATION, max(MIN_CONFIG_REPUTATION, current_config_reputation))
            configs_reputation[result.link] = current_config_reputation


        # 2 step check
        success_rate = len(pre_results) / len(to_ping)
        print(f"Got {len(pre_results)} working of {len(to_ping)} ({success_rate * 100}%)! Quick 2 step checking...")
        final_results = await pinger.ping_links([i.link for i in pre_results])

        print(f"Tier 1 sorted configs (got {len(final_results)}):")
        for i in final_results:
            print(i.link)

        # desik will make the rest
        # (selenuim)
        # oh no fuck
        ...

        server.update_configs(list(final_results))


if __name__ == '__main__':
    asyncio.run(main())
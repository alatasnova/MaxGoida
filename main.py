import asyncio

import sub_server
from fetcher import Fetcher
from pinger import ConfigPinger, PingResult


URLS = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/BLACK_VLESS_RUS.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/23.txt"
]
BATCH_SIZE = 20

async def main():
    fetcher = Fetcher(URLS)
    pinger = ConfigPinger()

    while True:
        # Fetch all configs
        raw_configs = await fetcher.fetch_all()

        # Ping them first
        start_port = 8089

        ping_results = await asyncio.gather(*[
            pinger.ping_url(link, local_tunnel_port=start_port + i)
            for i, link in enumerate(raw_configs)]
        )

        configs_filtered = filter(lambda x: x.success, ping_results)
        print("Tier 1 sorted configs:")
        for i in configs_filtered:
            print(i.link)

        # desik will make the rest
        ...




if __name__ == '__main__':
    asyncio.run(main())
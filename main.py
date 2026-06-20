import asyncio
import uvicorn

from config_server import ConfigServer
from fetcher import Fetcher
from pinger import ConfigPinger, PingResult


URLS = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/BLACK_VLESS_RUS.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/23.txt"
]
START_PORT = 8089
MAX_CONCURRENT = 20

async def main():
    config_server = ConfigServer()
    config = uvicorn.Config(config_server.app, host='0.0.0.0', port=5000, log_level="info")
    server = uvicorn.Server(config)

    asyncio.create_task(server.serve())

    await loop(config_server)

async def loop(server: ConfigServer):
    fetcher = Fetcher(URLS)
    pinger = ConfigPinger()

    while True:
        print("Fetching configs..")
        raw_configs = await fetcher.fetch_all()

        port_pull = asyncio.Queue()

        for port in range(START_PORT, START_PORT + MAX_CONCURRENT):
            await port_pull.put(port)

        async def ping_config(link: str):
            port = await port_pull.get()
            try:
                print(f"(port {port}) Pinging {link}")
                return await pinger.ping_link(
                    link, tunnel_port=port
                )
            finally:
                await port_pull.put(port)

        ping_results = await asyncio.gather(
            *(ping_config(link) for link in raw_configs)
        )

        configs_success = [r for r in ping_results if r.success]
        print("Tier 1 sorted configs:")
        for i in configs_success:
            print(i.link)

        # desik will make the rest
        # (selenuim)
        ...

        server.update_configs(configs_success)


if __name__ == '__main__':
    asyncio.run(main())
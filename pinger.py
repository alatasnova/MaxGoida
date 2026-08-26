import xray
import asyncio
import httpx
from datetime import timedelta
from dataclasses import dataclass
from parser import link_to_config

@dataclass
class PingResult:
    link: str
    ms: int
    success: bool
    reason: str


class ConfigPinger:
    def __init__(self, start_port: int, max_concurrent: int = 20, ping_url="http://cp.cloudflare.com/", timeout: float = 1.5):
        self.ping_url = ping_url
        self.timeout: float = timeout
        self.free_port_pull = asyncio.Queue()

        for port in range(start_port, start_port + max_concurrent):
            self.free_port_pull.put_nowait(port)


    async def ping_links(self, links: list[str], verbose=False) -> tuple[PingResult]:
        return await asyncio.gather(
            *(self.ping_link(link, verbose=verbose) for link in links)
        )

    async def ping_link(self, link: str, verbose=False) -> PingResult:
        tunnel_port = await self.free_port_pull.get()
        if verbose:
            print(f"(port {tunnel_port}) Pinging {link}")
        try:
            try:
                config = link_to_config.link_to_config(link, tunnel_port)
            except NotImplementedError:
                return PingResult(link, 0, False, "unsupported")
            except ValueError:
                return PingResult(link, 0, False, "unsupported")

            with xray.Tunnel(config, tunnel_port, verbose=False):
                async with httpx.AsyncClient(proxy=f'socks5h://127.0.0.1:{tunnel_port}') as client:
                    try:
                        response = await client.head(self.ping_url, timeout=self.timeout)
                        if not response.is_error:
                            # Success
                            latency = response.elapsed / timedelta(milliseconds=1)
                            return PingResult(link, round(latency / 2), True, "success")
                        else:
                            # Status code error
                            return PingResult(link, 0, False, str(response.status_code))
                    except httpx.HTTPError as e:
                        # Unreachable
                        return PingResult(link, 0, False, f"unreachable: {str(e)}")
        finally:
            await self.free_port_pull.put(tunnel_port)
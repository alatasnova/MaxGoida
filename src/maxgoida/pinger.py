import asyncio
from dataclasses import dataclass
from datetime import timedelta
import httpx

from maxgoida.parser import link_to_config
from maxgoida.xray import Tunnel


@dataclass
class PingResult:
    link: str
    ms: int
    success: bool
    reason: str


class ConfigPinger:
    def __init__(
        self,
        start_port: int,
        max_concurrent: int = 20,
        ping_url: str = "http://cp.cloudflare.com/",
        timeout: float = 1.5,
    ):
        self.ping_url = ping_url
        self.timeout: float = timeout
        self.free_port_pool = asyncio.Queue()

        for port in range(start_port, start_port + max_concurrent):
            self.free_port_pool.put_nowait(port)

    async def ping_links(self, links: list[str], verbose: bool = False) -> list[PingResult]:
        tasks = [self.ping_link(link, verbose=verbose) for link in links]
        results = await asyncio.gather(*tasks)
        return list(results)

    async def ping_link(self, link: str, verbose: bool = False) -> PingResult:
        tunnel_port = await self.free_port_pool.get()
        if verbose:
            print(f"(port {tunnel_port}) Pinging {link[:40]}...")
        try:
            try:
                config = link_to_config.link_to_config(link, tunnel_port)
            except NotImplementedError:
                return PingResult(link, 0, False, "unsupported_protocol")
            except ValueError:
                return PingResult(link, 0, False, "invalid_config")
            except Exception as e:
                return PingResult(link, 0, False, f"parse_error: {e}")

            with Tunnel(config, tunnel_port, verbose=False):
                async with httpx.AsyncClient(proxy=f"socks5h://127.0.0.1:{tunnel_port}") as client:
                    try:
                        response = await client.head(self.ping_url, timeout=self.timeout)
                        if not response.is_error:
                            latency = response.elapsed / timedelta(milliseconds=1)
                            return PingResult(link, round(latency / 2), True, "success")
                        else:
                            return PingResult(link, 0, False, str(response.status_code))
                    except httpx.HTTPError as e:
                        return PingResult(link, 0, False, f"unreachable: {e}")
                    except Exception as e:
                        return PingResult(link, 0, False, f"error: {e}")
        finally:
            await self.free_port_pool.put(tunnel_port)

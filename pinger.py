import requests, httpx
from datetime import timedelta
from dataclasses import dataclass

import xray
from parser import link_to_config


@dataclass
class PingResult:
    link: str
    ms: int
    success: bool
    reason: str


class ConfigPinger:
    def __init__(self, ping_url="http://cp.cloudflare.com/", timeout: float = 1.5):
        self.ping_url = ping_url
        self.timeout: float = timeout

    async def ping_link(self, link: str, tunnel_port=8089) -> PingResult:
        try:
            config = link_to_config.link_to_config(link, tunnel_port)
        except NotImplementedError:
            return PingResult(link, 0, False, "unsupported")

        client = httpx.AsyncClient(proxy=f'socks5h://127.0.0.1:{tunnel_port}')

        with xray.Tunnel(config, tunnel_port, verbose=False):
            try:
                response = await client.head(self.ping_url, timeout=self.timeout)
                if not response.is_error:
                    # Success
                    latency = response.elapsed / timedelta(milliseconds=1)
                    return PingResult(link, round(latency / 2), True, "success")
                else:
                    # Status code error
                    return PingResult(link, 0, False, str(response.status_code))
            except requests.exceptions.RequestException as e:
                # Unreachable
                return PingResult(link, 0, False, f"unreachable: {str(e)}")

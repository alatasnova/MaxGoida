import requests
import xray

from dataclasses import dataclass
from parser import link_parser, link_to_config

@dataclass
class PingResult:
    link: str
    ms: int
    success: bool
    reason: str


DEFAULT_PING_URL = "http://cp.cloudflare.com/"

def try_ping_link(link: str, ping_url=DEFAULT_PING_URL, local_tunnel_port=8089, timeout=2) -> PingResult:
    try:
        parsed_link = link_parser.parse_any(link)
    except NotImplementedError:
        return PingResult(link, 0, False, "unsupported")

    try:
        config = link_to_config.link_to_config(link, local_tunnel_port)
    except NotImplementedError:
        return PingResult(link, 0, False, "unsupported")

    proxies = {
        'http': f'socks5h://127.0.0.1:{local_tunnel_port}',
        'https': f'socks5h://127.0.0.1:{local_tunnel_port}'
    }


    with tunnel.Tunnel(config, local_tunnel_port, verbose=False):
        try:
            response = requests.head(ping_url, proxies=proxies, timeout=timeout)
            if response.status_code == 200 or response.status_code == 302 or response.status_code == 204:
                return PingResult(link, round(response.elapsed.seconds / 1000 / 2), True, "success")
            else:
                return PingResult(link, 0, False, str(response.status_code))
        except requests.exceptions.RequestException:
            return PingResult(link, 0, False, "unreachable")

unique_port = 8089
def get_unique_port() -> int:
    global unique_port
    unique_port += 1
    return unique_port

# testing configs
links = """vless://ff19693c-11f3-4df9-8713-79a85a5ca090@109.236.57.143:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=sellflow.org&fp=firefox&pbk=SbVKOEMjK0sIlbwg4akyBg5mL5KZwwB-ed4eEE7YnRc&sid&packetEncoding=xudp#%F0%9F%87%B7%F0%9F%87%BA%20Russia,%20Moscow%20%7C%20[BL]
vless://ff19693c-11f3-4df9-8713-79a85a5ca090@109.236.57.68:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=sellflow.org&fp=firefox&pbk=SbVKOEMjK0sIlbwg4akyBg5mL5KZwwB-ed4eEE7YnRc&sid&packetEncoding=xudp#%F0%9F%87%B7%F0%9F%87%BA%20Russia,%20Moscow%20%7C%20[BL]
vless://ff19693c-11f3-4df9-8713-79a85a5ca090@109.236.57.141:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=sellflow.org&fp=firefox&pbk=SbVKOEMjK0sIlbwg4akyBg5mL5KZwwB-ed4eEE7YnRc&sid&packetEncoding=xudp#%F0%9F%87%B7%F0%9F%87%BA%20Russia,%20Moscow%20%7C%20[BL]
vless://ff19693c-11f3-4df9-8713-79a85a5ca090@109.236.57.69:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=sellflow.org&fp=firefox&pbk=SbVKOEMjK0sIlbwg4akyBg5mL5KZwwB-ed4eEE7YnRc&sid&packetEncoding=xudp#%F0%9F%87%B7%F0%9F%87%BA%20Russia,%20Moscow%20%7C%20[BL]
vless://ff19693c-11f3-4df9-8713-79a85a5ca090@109.236.57.63:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=sellflow.org&fp=firefox&pbk=SbVKOEMjK0sIlbwg4akyBg5mL5KZwwB-ed4eEE7YnRc&sid&packetEncoding=xudp#%F0%9F%87%B7%F0%9F%87%BA%20Russia,%20Moscow%20%7C%20[BL]
vless://ff19693c-11f3-4df9-8713-79a85a5ca090@109.236.57.64:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=sellflow.org&fp=firefox&pbk=SbVKOEMjK0sIlbwg4akyBg5mL5KZwwB-ed4eEE7YnRc&sid&packetEncoding=xudp#%F0%9F%87%B7%F0%9F%87%BA%20Russia,%20Moscow%20%7C%20[BL]
vless://d39664df-5bc0-4f49-9894-8f03b4150082@fan.soft26.ir:8443?encryption=none&type=xhttp&security=reality&sni=www.yahoo.com&fp=chrome&pbk=QLamtir13xwzyWVlPRN3C7lw_fhSBU7X4H3A8zAl5Fg&sid=6f3192&path=/&mode=auto#%F0%9F%87%A8%F0%9F%87%AD%20Switzerland,%20Geneva%20%7C%20%F0%9F%8C%90%20%7C%20[BL]
vless://90f87df6-920d-47dd-9a89-13b92523e7f1@free08.tunnely.ru:8080?encryption=none&type=ws&path=/ws/&packetEncoding=xudp#%F0%9F%87%BA%F0%9F%87%B8%20United%20States,%20Atlanta%20%7C%20[BL]
vless://42e0d02c-b75c-4b9d-bc15-773aa3cbe6bc@14.102.228.201:2052?encryption=none&type=xhttp&security=none&host=u2.pabloping.cloud&path=/pabloping&mode=auto#%F0%9F%87%AB%F0%9F%87%B7%20France,%20Paris%20%7C%20[BL]
vless://db721061-c044-4c21-8c88-14be627343a7@fin83.alexanderoff.ru:11604?encryption=none&packetEncoding=xudp#%F0%9F%87%AB%F0%9F%87%AE%20Finland,%20Helsinki%20%7C%20[BL]
vless://db721061-c044-4c21-8c88-14be627343a7@fin83.alexanderoff.ru:11604?encryption=none&packetEncoding=xudp#%F0%9F%87%AB%F0%9F%87%AE%20Finland,%20Helsinki%20%7C%20[BL]"""

ping_results: list[PingResult] = []
for link in links.split("\n"):
    ping = try_ping_link(
        link,
        local_tunnel_port=get_unique_port(),
    )
    ping_results.append(ping)
    print(f"| {link}")
    print("|", f"* {ping.ms} ms" if ping.success else f"- {ping.reason}")
    print("")

configs_filtered = filter(lambda x: x.success, ping_results)
print("Tier 1 sorted configs:")
for i in configs_filtered:
    print(i.link)
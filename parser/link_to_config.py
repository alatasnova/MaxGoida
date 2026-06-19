# 1. Parse
# 2. Simple AST Tree
# 3. Build

import json
from . import link_parser
from .config_constructor import *


def link_to_config(link: str, inbound_port: int) -> dict:
    if link.startswith("vless://"):
        return vless_to_config(link, inbound_port)
    elif link.startswith("ss://"):
        return shadowsocks_to_config(link, inbound_port)
    raise NotImplementedError(f"Encountered unsupported protocol")

def wrap_config(outbound: dict, inbound_port: int) -> dict:
    result = {
        "inbounds": [{
            "port": inbound_port,
            "listen": "127.0.0.1",
            "protocol": "socks",
            "settings": {
                "auth": "noauth",
                "udp": True,
            },
            "sniffing": {
                "enabled": True,
                "destOverride": ["http", "tls"]
            }
        }],
        "outbounds": [outbound]
    }

    return result

def shadowsocks_to_config(link: str, inbound_port: int) -> dict:
    url = link_parser.parse_shadowsocks(link)
    shadowsocks_outbound = ShadowSocksOutbound(
        ShadowSocksSettings(
            url.address,
            url.port,
            url.method,
            url.password # TODO: UoT params?
        )
    )

    return wrap_config(shadowsocks_outbound(), inbound_port)

def vless_to_config(link: str, inbound_port: int) -> dict:
    url = link_parser.parse_vless(link)

    if url.security not in ["none", "reality"]:
        raise NotImplementedError(f"{url.security} secure protocol is not supported.") # And don't need to, it doesn't work in most cases

    vless_outbound = VLessOutbound(
        VLessSettings(
            url.address,
            url.port,
            url.id,
            url.flow
        ),
        StreamSettings(
            url.type,
            url.security,
        )
    )

    if url.security == "reality":
        vless_outbound.stream_settings.reality_settings = RealitySettings(
            url.fp,
            url.sni,
            url.pbk,
            url.sid
        )

    return wrap_config(vless_outbound(), inbound_port)

# Test
if __name__ == "__main__":
    print("Parsing VLess")
    config = link_to_config(
        "vless://7177f5c4-f26a-4ab5-820f-62cb6ba649f7@31.170.22.193:47997?encryption=none&flow=xtls-rprx-vision&security=reality&sni=apple.com&fp=chrome&pbk=cFora2YYa3aZdpWW8vMD9iX97qRKtyLzXv4pWgXoh20&sid=ead461&type=tcp&headerType=none#%5B%F0%9F%87%B1%F0%9F%87%BB%5D%20%5Bvl-re-ra%5D%20%5B260225-173317.470%5D",
        inbound_port=10212
    )
    print(json.dumps(config, indent=2))

    print("Parsing Shadowsocks")
    config = link_to_config(
        "ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTprMWRCT21PQjRvcWk3VW1wMzdhMWJR@82.38.31.218:8080?#%40Rayan_Config-82.38.31.218-%40beepassvpn_bot",
        inbound_port=10213
    )
    print(json.dumps(config, indent=2))
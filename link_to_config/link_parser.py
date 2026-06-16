import json
import base64
from urllib.parse import urlparse, parse_qs, unquote, ParseResult
from dataclasses import dataclass

@dataclass
class BaseLink:
    protocol: str
    address: str
    port: int
    username: str
    query_params: dict
    raw: ParseResult

@dataclass
class VLessLink:
    address: str
    port: int
    id: str
    flow: str
    type: str
    security: str
    fp: str
    sni: str
    pbk: str
    sid: str

@dataclass
class ShadowSocksLink:
    address: str
    port: int
    method: str
    password: str

def parse_base(link: str) -> BaseLink:
    parsed = urlparse(link)
    query_params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
    return BaseLink(
        protocol=parsed.scheme,
        address=parsed.hostname,
        port=parsed.port,
        username=parsed.username,
        query_params=query_params,
        raw=parsed
    )

def parse_vless(link: str) -> VLessLink:
    # Разбираем URL на части
    base_link = parse_base(link)

    if base_link.protocol != 'vless':
        raise ValueError("Got not VLess protocol")

    return VLessLink(base_link.address, base_link.port, base_link.username,
                     base_link.query_params.get("flow"), base_link.query_params.get("type"), base_link.query_params.get("security"),
                     base_link.query_params.get("fp"), base_link.query_params.get("sni"), base_link.query_params.get("pbk"), base_link.query_params.get("sid"))

def parse_shadowsocks(link: str) -> ShadowSocksLink:
    base_link = parse_base(link)

    if base_link.protocol != 'ss':
        raise ValueError("Got not ShadowSocks protocol")

    try:
        method_and_password = base64.b64decode(base_link.username).decode("utf-8")
    except:
        method_and_password = base_link.username

    method, password = method_and_password.split(":")

    return ShadowSocksLink(base_link.address, base_link.port, method, password)

if __name__ == "__main__":
    print(parse_shadowsocks("ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpoYkdycGZ2TnJKc1VtS21QYlIzaVky@tinkered-pennies-puppies.freesocks.work:443#🇺🇸[openproxylist.com] ss-US"))
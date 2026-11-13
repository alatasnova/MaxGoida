from dataclasses import dataclass
from typing import Literal

@dataclass
class RealitySettings:
    fingerprint: str
    server_name: str
    public_key: str
    short_id: str
    spider_x: str = ""
    show: bool = False

    def __call__(self, *args, **kwargs):
        return {
            "show": self.show,
            "fingerprint": self.fingerprint,
            "serverName": self.server_name,
            "publicKey": self.public_key,
            "shortId": self.short_id,
            "spiderX": self.spider_x,
        }

@dataclass
class TLSSettings:
    def __call__(self, *args, **kwargs):
        raise NotImplemented()

@dataclass
class StreamSettings:
    network: Literal["raw", "xhttp", "kcp", "grpc", "ws", "httpupgrade", "hysteria", "tcp"]
    security: Literal["reality", "none"]
    reality_settings: RealitySettings = None
    tls_settings: TLSSettings = None

    def __call__(self, *args, **kwargs):
        result = {
            "network": self.network,
            "security": self.security,
        }

        if self.security == "tls":
            if self.tls_settings is None:
                raise ValueError("TLS settings not specified for TLS network")
            result["tlsSettings"] = self.tls_settings()
        elif self.security == "reality":
            if self.reality_settings is None:
                raise ValueError("Reality settings not specified for Reality network")
            result["realitySettings"] = self.reality_settings() # че за шиз ебаный

        return result

@dataclass
class VLessSettings:
    address: str
    port: int
    id: str # UUID-like
    flow: str
    level: int = 0
    encryption: str = "none"

    def __call__(self, *args, **kwargs):
        return {
            "vnext": [{
                "address": self.address,
                "port": self.port,
                "users": [{
                    "id": self.id,
                    "encryption": self.encryption,
                    "flow": self.flow,
                    "level": self.level
                }]
            }]
        }

@dataclass
class VLessOutbound:
    vless_settings: VLessSettings
    stream_settings: StreamSettings

    def __call__(self, *args, **kwargs):
        return {
            "protocol": "vless",
            "settings": self.vless_settings(),
            "streamSettings": self.stream_settings()
        }

@dataclass
class ShadowSocksSettings:
    address: str
    port: int
    method: str
    password: str
    uot: bool = True
    uot_version: int = 2
    level: int = 0
    email: str = None

    def __call__(self, *args, **kwargs):
        return {
            "servers": [{
                "address": self.address,
                "port": self.port,
                "method": self.method,
                "password": self.password,
                "email": self.email,
                "UoTVersion": self.uot_version,
                "level": self.level
            }]
        }

@dataclass
class ShadowSocksOutbound:
    shadowsocks_settings: ShadowSocksSettings
    def __call__(self, *args, **kwargs):
        return {
            "protocol": "shadowsocks",
            "settings": self.shadowsocks_settings(),
        }
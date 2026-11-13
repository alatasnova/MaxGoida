"""
MaxGoida Package
Пакет для агрегации, тестирования и раздачи VPN/прокси конфигураций.
"""

from maxgoida.fetcher import Fetcher
from maxgoida.pinger import ConfigPinger, PingResult
from maxgoida.reputation import ReputationManager
from maxgoida.server import ConfigServer
from maxgoida.service_checker import BrowserServiceChecker
from maxgoida.xray import Tunnel

__all__ = [
    "Fetcher",
    "ConfigPinger",
    "PingResult",
    "ReputationManager",
    "ConfigServer",
    "BrowserServiceChecker",
    "Tunnel",
]

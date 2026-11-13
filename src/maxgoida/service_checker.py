import asyncio
import re
from dataclasses import dataclass
from urllib.parse import unquote

from playwright.async_api import Playwright, async_playwright

from maxgoida.parser import link_to_config
from maxgoida.xray import Tunnel


@dataclass
class ServiceCheckResult:
    available_services: list[str]  # e.g. ["YT", "GH", "GM", "AG", "DS", "TG"]
    details: dict[str, bool]


def update_link_tag(link: str, services: list[str]) -> str:
    """
    Добавляет или обновляет тег сервисов в названии (хэш-фрагменте) ссылки.
    НЕ кодирует скобки и пробелы через quote, чтобы клиенты (v2rayN, Nekoray)
    отображали имя прямо в интерфейсе.
    
    Пример:
      Было: ss://...@ip:port#%F0%9F%87%AC%F0%9F%87%A7[openproxylist.com]%20ss-GB
      Стало: ss://...@ip:port#[YT GH AG DS] 🇬🇧[openproxylist.com] ss-GB
    """
    if not services:
        return link

    tag = f"[{' '.join(services)}]"

    if '#' not in link:
        return f"{link}#{tag}"

    base_part, fragment = link.split('#', 1)
    unquoted_fragment = unquote(fragment).strip()

    # Очищаем старый тег, если он уже был
    cleaned_fragment = re.sub(r'^\[(?:YT|GH|GM|AG|DS|TG|\s)+\]\s*', '', unquoted_fragment).strip()

    if cleaned_fragment:
        new_name = f"{tag} {cleaned_fragment}"
    else:
        new_name = tag

    return f"{base_part}#{new_name}"


class BrowserServiceChecker:
    """
    Второй уровень отбора конфигураций с использованием headless Playwright.
    Поднимает локальный туннель xray и проверяет доступность ключевых сервисов.
    """

    def __init__(
        self,
        start_port: int = 15000,
        max_concurrent: int = 2,
        page_timeout_ms: int = 8000,
    ):
        self.page_timeout_ms = page_timeout_ms
        self.port_pool = asyncio.Queue()
        for p in range(start_port, start_port + max_concurrent):
            self.port_pool.put_nowait(p)

    async def check_youtube(self, page) -> bool:
        """Проверка доступности YouTube."""
        try:
            response = await page.goto(
                "https://www.youtube.com",
                wait_until="commit",
                timeout=self.page_timeout_ms,
            )
            if response and response.status < 400:
                return True
            title = await page.title()
            if "YouTube" in title:
                return True
        except Exception:
            pass
        return False

    async def check_github(self, page) -> bool:
        """Проверка доступности GitHub."""
        try:
            response = await page.goto(
                "https://github.com",
                wait_until="commit",
                timeout=self.page_timeout_ms,
            )
            if response and response.status < 400:
                return True
            title = await page.title()
            if "GitHub" in title:
                return True
        except Exception:
            pass
        return False

    async def check_gemini(self, page) -> bool:
        """Проверка доступности Gemini (Google AI) с учетом региональных заглушек."""
        try:
            response = await page.goto(
                "https://gemini.google.com",
                wait_until="domcontentloaded",
                timeout=self.page_timeout_ms,
            )
            title = await page.title()
            content = await page.content()
            content_lower = content.lower()
            is_blocked = (
                "isn't currently supported in your country" in content_lower
                or "isn’t currently supported in your country" in content_lower
                or "is not supported in your country" in content_lower
                or "не поддерживается в вашей стране" in content_lower
            )
            if not is_blocked and (response and response.status < 400 or "Gemini" in title):
                return True
        except Exception:
            pass
        return False

    async def check_antigravity(self, page) -> bool:
        """Проверка доступности API-бэкенда Google Antigravity."""
        try:
            response = await page.goto(
                "https://daily-cloudcode-pa.googleapis.com/generate_204",
                wait_until="commit",
                timeout=self.page_timeout_ms,
            )
            if response is not None:
                return True
        except Exception:
            try:
                alt_response = await page.goto(
                    "https://antigravity.google",
                    wait_until="commit",
                    timeout=self.page_timeout_ms,
                )
                if alt_response and alt_response.status < 400:
                    return True
            except Exception:
                pass
        return False

    async def check_discord(self, page) -> bool:
        """Проверка доступности Discord."""
        try:
            response = await page.goto(
                "https://discord.com",
                wait_until="commit",
                timeout=self.page_timeout_ms,
            )
            if response and response.status < 400:
                return True
            title = await page.title()
            if "Discord" in title:
                return True
        except Exception:
            pass
        return False

    async def check_telegram(self, page) -> bool:
        """Проверка доступности инфраструктуры Telegram."""
        try:
            response = await page.goto(
                "https://web.telegram.org",
                wait_until="commit",
                timeout=self.page_timeout_ms,
            )
            if response and response.status < 400:
                return True
            title = await page.title()
            if "Telegram" in title:
                return True
        except Exception:
            pass
        return False

    async def test_all_services(self, page) -> ServiceCheckResult:
        details = {}
        available = []

        checks = [
            ("YT", self.check_youtube),
            ("GH", self.check_github),
            ("GM", self.check_gemini),
            ("AG", self.check_antigravity),
            ("DS", self.check_discord),
            ("TG", self.check_telegram),
        ]

        for code, check_fn in checks:
            try:
                is_ok = await check_fn(page)
            except Exception:
                is_ok = False
            details[code] = is_ok
            if is_ok:
                available.append(code)

        return ServiceCheckResult(available_services=available, details=details)

    async def test_link(self, playwright: Playwright, link: str) -> tuple[str, ServiceCheckResult]:
        tunnel_port = await self.port_pool.get()
        try:
            try:
                config = link_to_config.link_to_config(link, tunnel_port)
            except Exception as e:
                print(f"[BrowserChecker] Ошибка создания конфига для {link[:30]}: {e}")
                return link, ServiceCheckResult([], {})

            with Tunnel(config, tunnel_port, verbose=False):
                await asyncio.sleep(0.8)

                browser = await playwright.chromium.launch(
                    headless=True,
                    proxy={"server": f"socks5://127.0.0.1:{tunnel_port}"},
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        f"--proxy-server=socks5://127.0.0.1:{tunnel_port}",
                    ],
                )
                try:
                    context = await browser.new_context(
                        ignore_https_errors=True,
                    )
                    page = await context.new_page()
                    result = await self.test_all_services(page)
                    await context.close()
                finally:
                    await browser.close()

                updated_link = update_link_tag(link, result.available_services)
                print(f"[BrowserChecker] {link[:45]}... -> {result.available_services} (детали: {result.details})")
                return updated_link, result
        except Exception as e:
            print(f"[BrowserChecker] Исключение при тестировании: {e}")
            return link, ServiceCheckResult([], {})
        finally:
            await self.port_pool.put(tunnel_port)

    async def test_batch(self, playwright: Playwright, links: list[str]) -> list[tuple[str, ServiceCheckResult]]:
        if not links:
            return []
        tasks = [self.test_link(playwright, link) for link in links]
        return await asyncio.gather(*tasks)

    async def test_all(self, links: list[str], max_to_test: int = 5) -> list[tuple[str, ServiceCheckResult]]:
        to_test = links[:max_to_test]
        if not to_test:
            return []

        async with async_playwright() as playwright:
            return await self.test_batch(playwright, to_test)

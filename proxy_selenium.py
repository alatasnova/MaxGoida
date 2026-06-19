import asyncio
from parser import link_to_config
from playwright.async_api import Playwright, async_playwright

from xray import Tunnel


class BrowserProxy:
    def __init__(self, p: Playwright, proxy_url: str, inbound_port: int):
        self.p = p
        self.inbound_port = inbound_port
        self.proxy_config = link_to_config.link_to_config(proxy_url, inbound_port)

    async def start(self):
        self.tunnel = Tunnel(self.proxy_config, self.inbound_port)

        self.browser = await self.p.chromium.launch(headless=True)
        self.context = await self.browser.new_context(proxy={
            "server": f"socks://127.0.0.1:{self.inbound_port}"
        })

# vless://7177f5c4-f26a-4ab5-820f-62cb6ba649f7@31.170.22.193:47997?encryption=none&flow=xtls-rprx-vision&security=reality&sni=apple.com&fp=chrome&pbk=cFora2YYa3aZdpWW8vMD9iX97qRKtyLzXv4pWgXoh20&sid=ead461&type=tcp&headerType=none#%5B%F0%9F%87%B1%F0%9F%87%BB%5D%20%5Bvl-re-ra%5D%20%5B260225-173317.470%5D


async def main():
    async with async_playwright() as p:
        bp1 = BrowserProxy(p,
       "ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTprMWRCT21PQjRvcWk3VW1wMzdhMWJR@82.38.31.218:8080?#%40Rayan_Config-82.38.31.218-%40beepassvpn_bot",
       14482
        )
        bp2 = BrowserProxy(p,
        "vless://38707963-acf6-4e72-8db6-94faba4b5844@72.56.108.252:443?encryption=none&security=reality&sni=yahoo.com&fp=chrome&pbk=FV_Zfr_YpvUVYmLpggwOwoJdiYVsmAqgXqDIGAILP3A&sid=3f8a&spx=%2F&type=tcp&headerType=none#%5B%F0%9F%87%A9%F0%9F%87%AA%5D%20%5Bvl-re-ra%5D%20%5B260225-173008.536%5D",
        14483
        )
        await bp1.start()
        await bp2.start()

        page1 = await bp1.context.new_page()
        page2 = await bp2.context.new_page()
        await page1.goto("https://2ip.ru")
        await page2.goto("https://ident.me")
        await asyncio.sleep(4)
        print(await page1.inner_text("body"))
        print(await page2.inner_text("body"))

if __name__ == "__main__":
    asyncio.run(main())
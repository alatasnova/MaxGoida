import asyncio
import os
import random
import sys
from pathlib import Path
from urllib.parse import urlparse
import uvicorn
from playwright.async_api import async_playwright

from maxgoida.fetcher import Fetcher
from maxgoida.pinger import ConfigPinger, PingResult
from maxgoida.reputation import ReputationManager
from maxgoida.server import ConfigServer
from maxgoida.service_checker import BrowserServiceChecker


DEFAULT_SOURCES = [
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/V2RAY_RAW.txt",
    "https://gitlab.com/avencores/goida-vpn-configs/-/raw/main/githubmirror/26.txt"
]

SOURCES_FILE = "sources.txt"

START_PORT = 8089
BATCH_SIZE = 200               # Размер параллельного батча
MAX_CONCURRENT_PINGS = 20     # Конкурентность Xray-туннелей
REFETCH_EVERY_N_BATCHES = 5   # Перезагрузка источников каждые N батчей


def format_source_display(url: str, max_length: int = 50) -> str:
    """
    Форматирует URL источника для читаемого отображения в консоли,
    сохраняя значащие последние сегменты (путь/имя файла).
    """
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    if not path:
        return url[-max_length:] if len(url) > max_length else url

    parts = path.split("/")
    display = parts[-1]
    for part in reversed(parts[:-1]):
        candidate = f"{part}/{display}"
        if len(candidate) + 4 <= max_length:
            display = candidate
        else:
            break

    if len(display) < len(url):
        return f".../{display}"
    return display


def load_sources_from_file(file_path: str = SOURCES_FILE) -> list[str]:
    """
    Загружает список URL источников из файла sources.txt.
    Игнорирует пустые строки и комментарии (#).
    Если файл отсутствует, создает его с дефолтными значениями.
    """
    path = Path(file_path)
    if not path.exists():
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("# Список источников публичных подписок / конфигов (по одной ссылке на строку)\n")
                for s in DEFAULT_SOURCES:
                    f.write(f"{s}\n")
        except Exception:
            pass
        return list(DEFAULT_SOURCES)

    urls = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    urls.append(line)
    except Exception as e:
        print(f"[Sources] Ошибка чтения {file_path}: {e}. Используем дефолтные источники.")
        return list(DEFAULT_SOURCES)

    return urls if urls else list(DEFAULT_SOURCES)


def sample_balanced_batch(
    source_pools: dict[str, list[str]],
    rep_manager: ReputationManager,
    batch_size: int
) -> list[tuple[str, str]]:
    """
    Двухэтапная сбалансированная выборка батча:
    1. Источник выбирается пропорционально его относительной репутации (баллам за сервисы).
    2. Внутри выбранного источника конфиг выбирается пропорционально его качеству.
    """
    batch: list[tuple[str, str]] = []
    selected_configs_set = set()

    max_attempts = batch_size * 10
    attempts = 0

    while len(batch) < batch_size and attempts < max_attempts:
        attempts += 1

        active_sources = [
            src for src, pool in source_pools.items() if pool
        ]
        if not active_sources:
            break

        source_weights = [
            rep_manager.get_relative_source_weight(src)
            for src in active_sources
        ]

        chosen_source = random.choices(active_sources, weights=source_weights, k=1)[0]
        src_pool = source_pools[chosen_source]

        config_weights = [
            rep_manager.get_config_base_weight(cfg)
            for cfg in src_pool
        ]
        chosen_config = random.choices(src_pool, weights=config_weights, k=1)[0]

        src_pool.remove(chosen_config)

        if chosen_config not in selected_configs_set:
            selected_configs_set.add(chosen_config)
            batch.append((chosen_config, chosen_source))

    return batch


async def browser_checker_worker(
    queue: asyncio.Queue,
    browser_checker: BrowserServiceChecker,
    server: ConfigServer,
    rep_manager: ReputationManager,
    config_source_map: dict[str, str],
):
    """
    Фоновый рабочий процесс Playwright.
    Берёт живые ссылки из очереди, выполняет глубокую проверку доступности сервисов,
    начисляет баллы качественной репутации конфигу и его источнику,
    и обновляет теги в подписке на сервере без задержки основного потока.
    """
    async with async_playwright() as playwright:
        while True:
            link = await queue.get()
            try:
                # Если ссылка была удалена из активных на сервере пока ждала очередь — пропускаем
                base_link = link.split("#")[0]
                is_still_active = any(c.split("#")[0] == base_link for c in server.configs)
                if not is_still_active:
                    queue.task_done()
                    continue

                updated_link, check_res = await browser_checker.test_link(playwright, link)
                # Обновляем имя конфига на сервере с добавлением найденных тегов [YT GH GM AG DS TG]
                server.add_working_config(updated_link)

                # Начисляем качественные баллы в репутацию конфига и источника
                services_count = len(check_res.available_services)
                src_url = config_source_map.get(link)
                rep_manager.record_service_points(link, src_url, services_count)

                services_str = " ".join(check_res.available_services) if check_res.available_services else "None"
                print(f"[BrowserWorker] ✓ Проверено: {updated_link[:65]}... [{services_str}] (+{services_count * 2} баллов, в очереди: {queue.qsize()})")
            except Exception as e:
                print(f"[BrowserWorker] Ошибка тестирования {link[:40]}: {e}")
            finally:
                queue.task_done()


async def loop(server: ConfigServer, rep_manager: ReputationManager):
    current_sources = load_sources_from_file()
    print(f"[Sources] Загружено источников из {SOURCES_FILE}: {len(current_sources)}")
    fetcher = Fetcher(current_sources)
    pinger = ConfigPinger(START_PORT, max_concurrent=MAX_CONCURRENT_PINGS)

    # Выделяем изолированные порты под фоновые туннели браузера
    browser_checker = BrowserServiceChecker(
        start_port=START_PORT + MAX_CONCURRENT_PINGS + 1,
        max_concurrent=2,
    )

    # Асинхронная очередь для фоновой браузерной проверки
    browser_queue = asyncio.Queue()
    queued_links_history = set()

    # Пулы конфигов, сгруппированные по источникам: {source_url: [configs]}
    source_pools: dict[str, list[str]] = {}
    config_source_map: dict[str, str] = {}
    batch_counter = 0

    # Запускаем браузерного воркера в фоновой задаче
    asyncio.create_task(
        browser_checker_worker(browser_queue, browser_checker, server, rep_manager, config_source_map)
    )

    while True:
        # Проверяем, есть ли хотя бы в одном источнике еще не протестированные конфиги
        total_remaining = sum(len(pool) for pool in source_pools.values())

        # 1. Периодический фетч или начальное наполнение пулов
        if total_remaining == 0 or batch_counter % REFETCH_EVERY_N_BATCHES == 0:
            print("\n" + "=" * 65)
            print(f"[Loop] Обновление источников списков (Батч #{batch_counter})...")
            
            # Перечитываем sources.txt на каждом обновлении, чтобы изменения подхватывались на лету
            current_sources = load_sources_from_file()
            fetcher.urls = current_sources

            try:
                sources_data = await fetcher.fetch_by_sources()
                all_seen_configs = set()
                new_source_pools: dict[str, list[str]] = {}

                for src_url, configs in sources_data.items():
                    all_seen_configs.update(configs)
                    new_source_pools[src_url] = list(configs)
                    for cfg in configs:
                        config_source_map[cfg] = src_url

                if all_seen_configs:
                    source_pools = new_source_pools
                    rep_manager.age_and_clean_configs(all_seen_configs)
                    total_available = sum(len(p) for p in source_pools.values())
                    print(f"[Loop] Загружено {len(source_pools)} источников, суммарно {total_available} конфигов.")

                    print("[Loop] Текущая качественная репутация источников (по баллам сервисов):")
                    for src in current_sources:
                        rel_w = rep_manager.get_relative_source_weight(src)
                        stat = rep_manager.sources.get(src)
                        tested = stat.total_tested if stat else 0
                        pings = stat.total_ping_success if stat else 0
                        service_pts = stat.total_service_points if stat else 0
                        pool_size = len(source_pools.get(src, []))
                        src_name = format_source_display(src, max_length=42)
                        print(f"  • {src_name:<42} -> вес: {rel_w:.2f} | баллов за сервисы: {service_pts} | пинг: {pings}/{tested} (в пуле: {pool_size})")
                else:
                    print("[Loop] Внимание: ни один источник не отдал конфигов. Продолжаем работу.")
            except Exception as e:
                print(f"[Loop] Ошибка при обновлении источников: {e}. Пропускаем обновление.")

            rep_manager.save()

        total_remaining = sum(len(pool) for pool in source_pools.values())
        if total_remaining == 0:
            print("[Loop] Все пулы пусты. Ожидание 10 секунд перед повторным фетчем...")
            await asyncio.sleep(10)
            continue

        # 2. Сбалансированный рандомный батчинг
        batch_items = sample_balanced_batch(
            source_pools,
            rep_manager,
            BATCH_SIZE
        )
        if not batch_items:
            await asyncio.sleep(1)
            continue

        batch_configs = [item[0] for item in batch_items]
        for cfg, src_url in batch_items:
            config_source_map[cfg] = src_url

        batch_counter += 1
        total_remaining = sum(len(pool) for pool in source_pools.values())

        sources_summary = {}
        for _, s_url in batch_items:
            short_name = format_source_display(s_url, max_length=25)
            sources_summary[short_name] = sources_summary.get(short_name, 0) + 1
        summary_str = ", ".join(f"{k}: {v}" for k, v in sources_summary.items())

        print(f"\n--- [Батч #{batch_counter}] Выборка: {len(batch_configs)} шт. [{summary_str}] (осталось в пулах: {total_remaining}) ---")

        # 3. Первый уровень: быстрый параллельный пинг батча через Xray
        ping_results = await pinger.ping_links(batch_configs, verbose=False)
        working_ping_results: list[PingResult] = []

        for res in ping_results:
            src_url = config_source_map.get(res.link)
            rep_manager.record_ping_result(res.link, src_url, success=res.success)
            if res.success:
                working_ping_results.append(res)
                # Конфиг рабочий! Мгновенно отдаем его в подписку
                server.add_working_config(res.link)

                # И сразу ставим в фоновую очередь на браузерное определение сервисов
                base_cfg = res.link.split("#")[0]
                if base_cfg not in queued_links_history:
                    queued_links_history.add(base_cfg)
                    browser_queue.put_nowait(res.link)
            else:
                # Если перестал работать — сразу убираем
                server.remove_config(res.link)

        print(f"[Батч #{batch_counter}] Пинг прошли: {len(working_ping_results)} из {len(batch_configs)} | Активно на сервере: {len(server.configs)} нод (в очереди на браузер: {browser_queue.qsize()})")

        rep_manager.save()
        await asyncio.sleep(0.1)


def run():
    rep_manager = ReputationManager()
    rep_manager.load()

    server = ConfigServer()
    config = uvicorn.Config(server.app, host="0.0.0.0", port=5000, log_level="warning")
    uv_server = uvicorn.Server(config)

    async def main_async():
        asyncio.create_task(uv_server.serve())
        print("[Server] Подписка доступна на http://0.0.0.0:5000/")
        await loop(server, rep_manager)

    asyncio.run(main_async())


if __name__ == "__main__":
    run()

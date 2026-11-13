# MaxGoida 🌐🛡️

Инструмент для автоматического сбора, глубокого и качественного тестирования публичных VPN/прокси-подписок (VLESS, VMess, Trojan, Shadowsocks) и раздачи только гарантированно рабочих конфигураций для обхода блокировок.

---

## 📌 Архитектура и принципы работы

В открытом доступе находится множество подписок и списков прокси, но большая часть из них не работает, блокируется ТСПУ по SNI/протоколам или имеет ограничения по гео-доступу к сервисам (Gemini, Antigravity, Discord и др.).

### 1. Относительная динамическая репутация списков (источников)
Каждый источник (`URL`) тестируется непрерывно:
- Никаких жестких отсечений по порогу ("<2% значит не тестируем").
- Списки оцениваются **относительно друг друга**:
  $$\text{weight}(\text{source}) = \frac{\text{success\_rate}(\text{source})}{\max(\text{success\_rate})}$$
- Если в Списке А работает **1.0%** конфигов, а в Списке Б — **0.5%**, то конфиги из Списка Б будут выбираться на проверку **ровно в 2 раза реже**, чем из Списка А.
- Для надежности используется сглаживание Лапласа $\frac{\text{success} + 1}{\text{total} + 2}$, что позволяет новым источникам быстро получить шанс проявить себя.

### 2. Рандомный взвешенный батчинг (Weighted Random Sampling)
- Конфиги выбираются не по порядку из файлов, а случайно.
- Вероятность попадания конфига в следующий батч пропорциональна:
  $$P(\text{config}) \propto \text{config\_reputation\_weight} \times \text{relative\_source\_weight}$$
- Проверка проходит параллельными батчами по 10 штук (`BATCH_SIZE = 10`), ноды сразу же по готовности добавляются в подписку.
- Каждые 10 батчей происходит мягкое обновление источников.

### 3. Двухэтапная фильтрация
1. **Быстрый пинг Xray (`pinger.py`)**:
   - Поднятие легковесных локальных туннелей `xray-core` на индивидуальных socks5-портах.
   - Сетевой замер HTTP HEAD к Cloudflare с тайм-аутом 1.5 сек.
2. **Headless-браузер (`service_checker.py`)**:
   - Только живые ноды тестируются в Playwright на доступность сервисов:
     - **`[YT]` — YouTube**: проверка структуры и плеера `youtube.com`.
     - **`[GH]` — GitHub**: проверка доступности `github.com`.
     - **`[GM]` — Gemini**: проверка доступности AI от Google с детекцией гео-заглушек (*"isn't currently supported in your country"* / *"не поддерживается в вашей стране"*).
     - **`[AG]` — Antigravity**: проверка доступности API-бэкенда Google Antigravity (`daily-cloudcode-pa.googleapis.com` / `antigravity.google`).
     - **`[DS]` — Discord**: проверка доступности `discord.com`.
     - **`[TG]` — Telegram**: проверка веб-клиента `web.telegram.org`.

### 🏷️ Динамические теги в названии конфига
Каждый рабочий конфиг получает префикс в имени с теми сервисами, которые реально открылись через него:
- `vless://...@ip:port#[YT GH GM AG DS TG] Server-Name` — работают все сервисы.
- `vless://...@ip:port#[YT GH AG DS] Server-Name` — работают YouTube, GitHub, Antigravity и Discord.

---

## 🚀 Быстрый старт с uv

Проект использует современный менеджер пакетов [uv](https://docs.astral.sh/uv/).

### 1. Установка uv (если ещё не установлен)

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Синхронизация зависимостей и браузеров

`uv` создаст виртуальное окружение и установит зависимости:
```bash
uv sync
```

Если Playwright запускается впервые, установите браузер Chromium:
```bash
uv run playwright install chromium
```

### 3. Запуск проекта

**Через uv:**
```bash
uv run python main.py
```

**Или с помощью готового bat-скрипта (Windows):**
```cmd
run-max-goida.bat
```

Сервер раздачи подписки доступен по адресу:
- `http://localhost:5000/` — динамическая подписка с проверенными и протегированными конфигами.
- `http://localhost:5000/alt` — альтернативный статический список (`static/configs.txt`).

---

## 📁 Чистая модульная структура (`src/maxgoida`)

```text
MaxGoida/
├── src/
│   └── maxgoida/
│       ├── parser/                 # Парсер ссылок в структуры Xray
│       │   ├── config_constructor.py
│       │   ├── link_parser.py
│       │   ├── link_to_config.py
│       │   └── __init__.py
│       ├── app.py                 # Главный цикл приложения и рандомный батчинг
│       ├── fetcher.py             # Загрузка и отслеживание источников
│       ├── pinger.py              # Быстрый socks5-пингер через Xray
│       ├── reputation.py          # Динамическая репутация конфигов и списков
│       ├── server.py              # FastAPI сервер раздачи подписок
│       ├── service_checker.py     # Headless-проверка сервисов (YT, GM, AG, DS, TG)
│       ├── xray.py                # Контекстный менеджер процесса Xray-core
│       ├── __init__.py
│       └── __main__.py
├── static/                        # Статические списки
│   └── configs.txt
├── xray/                          # Бинарники Xray-core
│   ├── xray.exe
│   └── wintun.dll
├── main.py                        # Точка входа в корне
├── run-max-goida.bat              # Запуск для Windows
├── pyproject.toml                 # PEP 621 конфигурация uv
├── requirements.txt
└── .gitignore
```

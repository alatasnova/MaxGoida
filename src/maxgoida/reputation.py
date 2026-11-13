import json
import os
from dataclasses import dataclass, field


@dataclass
class ConfigReputation:
    score: int = 0
    cycles_not_seen: float = 0
    service_count: int = 0  # Количество подтвержденных сервисов (YT, GH, GM, AG, DS, TG)


@dataclass
class SourceReputation:
    """
    Качественная статистика источника (списка/зеркала).
    total_tested: сколько всего конфигов было проверено из этого источника.
    total_ping_success: сколько из них хотя бы ответило на базовый пинг.
    total_service_points: сумма набранных баллов за работающие сервисы (YT, GH, GM, AG, DS, TG).
    """
    total_tested: int = 0
    total_ping_success: int = 0
    total_service_points: int = 0


class ReputationManager:
    """
    Управляет качественной репутацией конфигов и источников на основе баллов за сервисы.
    
    Принцип подсчета качества (Quality Score):
    - Базовый пинг: если конфиг пингуется, он дает +1 базовый балл (жив).
    - Каждый работающий сервис (YouTube, GitHub, Gemini, Antigravity, Discord, Telegram):
      дает еще +2 качественных балла.
      То есть нода со всеми сервисами приносит 1 + (6 * 2) = 13 баллов!
      А «нода-пустышка», которая просто пингуется, но ничего не открывает — всего 1 балл.
    - Мертвая нода: 0 баллов.
    
    Репутация источника:
    - quality_rate = (total_service_points + total_ping_success + 1.0) / (total_tested + 1.0)
    - relative_source_weight = quality_rate(source) / max(quality_rate)
    Таким образом, списки, из которых ноды реально открывают сайты, получают В РАЗЫ более
    высокий приоритет тестирования, чем списки с мусором, который только пингуется или вообще лежит.
    """

    def __init__(
        self,
        filepath: str = "configs_rep.json",
        max_reputation: int = 20,
        min_reputation: int = -5,
        cycles_threshold: int = 15,
    ):
        self.filepath = filepath
        self.max_reputation = max_reputation
        self.min_reputation = min_reputation
        self.cycles_threshold = cycles_threshold

        self.configs: dict[str, ConfigReputation] = {}
        self.sources: dict[str, SourceReputation] = {}

    def get_source_quality_rate(self, source_url: str) -> float:
        """
        Возвращает средний балл качества на один протестированный конфиг источника
        со сглаживанием Лапласа для новых источников.
        """
        stat = self.sources.get(source_url)
        if not stat or stat.total_tested == 0:
            return 0.5  # Стартовый априорный рейтинг для нового списка

        # total_service_points + total_ping_success отражает реальную полезность
        points = stat.total_service_points + stat.total_ping_success
        return (points + 1.0) / (stat.total_tested + 1.0)

    def get_relative_source_weight(self, source_url: str) -> float:
        """
        Относительный вес списка по отношению к самому качественному источнику.
        Никаких жестких отсечений — вес масштабируется пропорционально среднему баллу.
        """
        all_rates = [
            self.get_source_quality_rate(src)
            for src in self.sources.keys()
        ]
        if not all_rates:
            return 1.0

        max_rate = max(all_rates)
        if max_rate <= 0:
            return 1.0

        current_rate = self.get_source_quality_rate(source_url)
        return max(0.05, current_rate / max_rate)

    def get_config_base_weight(self, config: str) -> float:
        """
        Базовый вес конфига для вероятностного выбора:
        Конфиги с высоким score (много работающих сервисов) имеют приоритет.
        """
        rep = self.configs.setdefault(config, ConfigReputation(0))
        if rep.score > 0:
            # Чем больше сервисов тянет конфиг, тем выше вес (до 2.5x)
            return 1.0 + min(1.5, rep.score * 0.1)
        elif rep.score == 0:
            return 1.0
        elif rep.score == -1:
            return 0.3
        elif rep.score == -2:
            return 0.1
        return 0.02

    def record_ping_result(self, config: str, source_url: str | None, success: bool):
        """Регистрирует базовый результат сетевого пинга."""
        rep = self.configs.setdefault(config, ConfigReputation(0))
        if success:
            rep.score = min(self.max_reputation, rep.score + 1)
        else:
            rep.score = max(self.min_reputation, rep.score - 1)

        if source_url:
            src_stat = self.sources.setdefault(source_url, SourceReputation())
            src_stat.total_tested += 1
            if success:
                src_stat.total_ping_success += 1

    def record_service_points(self, config: str, source_url: str | None, services_count: int):
        """
        Начисляет качественные баллы за подтвержденные в браузере сервисы (YT, GH, GM, AG, DS, TG).
        """
        rep = self.configs.setdefault(config, ConfigReputation(0))
        rep.service_count = services_count
        # За каждый рабочий сервис добавляем +2 к скору конфига
        rep.score = min(self.max_reputation, rep.score + (services_count * 2))

        if source_url:
            src_stat = self.sources.setdefault(source_url, SourceReputation())
            src_stat.total_service_points += (services_count * 2)

    def age_and_clean_configs(self, seen_configs: set[str]):
        """Увеличивает счетчик неактивности и удаляет давно исчезнувшие конфиги."""
        for cfg in seen_configs:
            if cfg in self.configs:
                self.configs[cfg].cycles_not_seen = 0

        for cfg in list(self.configs.keys()):
            if cfg not in seen_configs:
                self.configs[cfg].cycles_not_seen += 1
                if self.configs[cfg].cycles_not_seen > self.cycles_threshold:
                    self.configs.pop(cfg, None)

    def save(self):
        """Сохраняет базу репутаций и списков на диск."""
        data = {
            "configs": {k: v.__dict__ for k, v in self.configs.items()},
            "sources": {k: v.__dict__ for k, v in self.sources.items()}
        }
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            print(f"[Reputation] Ошибка сохранения: {e}")

    def load(self):
        """Загружает базу репутаций из файла."""
        if not os.path.exists(self.filepath):
            print("[Reputation] Файл репутаций не найден. Старт с чистой базой.")
            return

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                raw = json.load(f)

            if "configs" in raw and "sources" in raw:
                self.configs = {
                    k: ConfigReputation(**v) for k, v in raw["configs"].items()
                }
                self.sources = {
                    k: SourceReputation(**v) for k, v in raw["sources"].items()
                }
            else:
                self.configs = {
                    k: ConfigReputation(**v) for k, v in raw.items()
                }

            print(f"[Reputation] Загружено {len(self.configs)} конфигов, {len(self.sources)} источников.")
        except Exception as e:
            print(f"[Reputation] Ошибка загрузки базы: {e}. Начинаем с нуля.")

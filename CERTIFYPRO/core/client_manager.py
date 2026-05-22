"""
ClientManager - управління глобальним контекстом клієнта.

Забезпечує:
- Завантаження профілів з YAML
- Вибір активного клієнта
- Доступ до налаштувань клієнта
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class CompanyConfig:
    """Налаштування компанії."""

    name: str
    code: str
    director: str


@dataclass
class FeaturesConfig:
    """Налаштування функцій."""

    import_product: bool = False
    ugoda_templates: int = 1


@dataclass
class ClientProfile:
    """Профіль клієнта."""

    client_id: str
    name: str
    display_name: str
    template_suffix: str
    launcher_mapping: str  # Як названий у лаунчері (applicants.db papka_proektu)
    company: CompanyConfig
    features: FeaturesConfig
    data_dir: str
    description: str


@dataclass
class GlobalConfig:
    """Глобальні налаштування."""

    version: str = "3.0.0"
    app_name: str = "CertifyPro"
    appearance_mode: str = "dark"
    color_theme: str = "blue"
    date_format: str = "%d.%m.%Y"
    file_date_format: str = "%Y-%m-%d"
    datetime_format: str = "%d.%m.%Y %H:%M"
    font_family: str = "Times New Roman"
    font_size: int = 10
    language: str = "uk"
    max_parties_per_app: int = 100
    min_app_number: int = 1
    max_app_number: int = 999
    reg_number_prefix: str = "114"


class ClientManager:
    """
    Менеджер клієнтів - єдине джерело інформації про поточний клієнт.

    Використання:
        # Ініціалізація
        manager = ClientManager()
        manager.load_profiles(Path("resources/profiles.yaml"))

        # Вибір клієнта
        manager.select_client("afina")

        # Доступ до налаштувань
        current = manager.current_client
        print(current.template_suffix)  # "_А"
    """

    def __init__(self):
        self._profiles: Dict[str, ClientProfile] = {}
        self._global: GlobalConfig = GlobalConfig()
        self._current_client: Optional[ClientProfile] = None
        self._profiles_path: Optional[Path] = None

    def load_profiles(self, profiles_path: Path) -> None:
        """Завантажити профілі з YAML файлу."""
        self._profiles_path = profiles_path

        if not profiles_path.exists():
            raise FileNotFoundError(f"Файл профілів не знайдено: {profiles_path}")

        with open(profiles_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Завантажити глобальні налаштування
        if "global" in data:
            self._global = GlobalConfig(**data["global"])

        # Завантажити клієнтів
        if "clients" not in data:
            raise ValueError("YAML має містити секцію 'clients'")

        for client_id, client_data in data["clients"].items():
            company = CompanyConfig(**client_data["company"])
            features = FeaturesConfig(**client_data["features"])

            profile = ClientProfile(
                client_id=client_id,
                name=client_data["name"],
                display_name=client_data["display_name"],
                template_suffix=client_data["template_suffix"],
                launcher_mapping=client_data.get(
                    "launcher_mapping", client_data["name"]
                ),
                company=company,
                features=features,
                data_dir=client_data["data_dir"],
                description=client_data.get("description", ""),
            )

            self._profiles[client_id] = profile

        logger.info(f"Завантажено {len(self._profiles)} профілів клієнтів")

    def select_client(self, client_id: str) -> ClientProfile:
        """Вибрати активного клієнта."""
        if client_id not in self._profiles:
            available = ", ".join(self._profiles.keys())
            raise ValueError(f"Невідомий client_id: {client_id}. Доступні: {available}")

        self._current_client = self._profiles[client_id]
        logger.info(f"Вибрано клієнта: {self._current_client.display_name}")
        return self._current_client

    @property
    def current_client(self) -> ClientProfile:
        """Повернути поточний клієнт."""
        if self._current_client is None:
            raise RuntimeError("Клієнта не вибрано. Викличте select_client() спочатку.")
        return self._current_client

    @property
    def global_config(self) -> GlobalConfig:
        """Повернути глобальні налаштування."""
        return self._global

    def get_client_ids(self) -> list[str]:
        """Повернути список доступних client_id."""
        return list(self._profiles.keys())

    def get_all_profiles(self) -> Dict[str, ClientProfile]:
        """Повернути всі профілі."""
        return self._profiles.copy()

    def get_launcher_to_client_mapping(self) -> Dict[str, str]:
        """Повернути маппінг papka_proektu → client_id для лаунчера.

        Returns:
            {"АФІНА": "afina", "ДЖОНСОН": "johnson"}
        """
        return {
            profile.launcher_mapping: client_id
            for client_id, profile in self._profiles.items()
        }

    def get_template_suffix(self) -> str:
        """Повернути суффікс шаблонів поточного клієнта."""
        return self.current_client.template_suffix

    def has_feature(self, feature_name: str) -> bool:
        """Перевірити чи увімкнено функцію для поточного клієнта."""
        return getattr(self.current_client.features, feature_name, False)

    def get_ugoda_template_count(self) -> int:
        """Повернути кількість шаблонів угоди."""
        return self.current_client.features.ugoda_templates


# Глобальний екземпляр (синглтон)
_client_manager: Optional[ClientManager] = None


def get_client_manager() -> ClientManager:
    """Повернути глобальний ClientManager (створює якщо немає)."""
    global _client_manager
    if _client_manager is None:
        _client_manager = ClientManager()
    return _client_manager


def get_current_client() -> ClientProfile:
    """Зручний доступ до поточного клієнта."""
    return get_client_manager().current_client


def get_global_config() -> GlobalConfig:
    """Зручний доступ до глобальних налаштувань."""
    return get_client_manager().global_config

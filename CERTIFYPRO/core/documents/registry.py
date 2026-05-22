"""
Registry-паттерн для генераторів документів.

Дозволяє реєструвати генератори за іменем та створювати їх через фабрику.
Це робить пайплайни конфігурованими даними, а не кодом.

Приклад використання:
    registry = GeneratorRegistry()
    registry.register("zayavka", ZayavkaGenerator)
    generator = registry.create("zayavka", template_dir, output_dir, context_builder)
"""

import logging
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)


# Тип функції-фабрики: повертає екземпляр генератора
GeneratorFactory = Callable[..., Any]


class GeneratorRegistry:
    """
    Реєстр генераторів документів.

    Зберігає мапу імен → фабрики генераторів.
    Дозволяє створювати генератори динамічно за іменем.
    """

    def __init__(self):
        self._factories: Dict[str, GeneratorFactory] = {}

    def register(self, name: str, factory: GeneratorFactory) -> None:
        """
        Зареєструвати фабрику генератора.

        Args:
            name: Унікальне ім'я генератора
            factory: Функція-фабрика, що повертає екземпляр генератора
        """
        if name in self._factories:
            logger.warning(f"Генератор '{name}' вже зареєстровано, замінюємо")
        self._factories[name] = factory
        logger.debug(f"Зареєстровано генератор: {name}")

    def unregister(self, name: str) -> None:
        """Видалити генератор з реєстру."""
        self._factories.pop(name, None)
        logger.debug(f"Видалено генератор: {name}")

    def create(self, name: str, *args, **kwargs) -> Any:
        """
        Створити генератор за іменем.

        Args:
            name: Ім'я зареєстрованого генератора
            *args, **kwargs: Аргументи для фабрики

        Returns:
            Екземпляр генератора

        Raises:
            KeyError: Якщо генератор з таким іменем не зареєстровано
        """
        if name not in self._factories:
            raise KeyError(
                f"Генератор '{name}' не зареєстровано. Доступні: {list(self._factories.keys())}"
            )
        return self._factories[name](*args, **kwargs)

    def has(self, name: str) -> bool:
        """Перевірити чи генератор зареєстровано."""
        return name in self._factories

    def list_names(self) -> list:
        """Повернути список зареєстрованих імен."""
        return list(self._factories.keys())

    def count(self) -> int:
        """Кількість зареєстрованих генераторів."""
        return len(self._factories)


def create_default_registry(
    template_dir, output_dir, context_builder=None
) -> GeneratorRegistry:
    """
    Створити реєстр зі всіма стандартними генераторами.

    Args:
        template_dir: Шлях до шаблонів
        output_dir: Шлях до виводу
        context_builder: DocumentDataService (для ZayavkaGenerator)

    Returns:
        Заповнений GeneratorRegistry
    """
    from documents.generators.akt_ident_generator import AktIdentGenerator
    from documents.generators.akt_vidbir_generator import AktVidbirGenerator
    from documents.generators.deklaraciya_generator import DeklaraciyaGenerator
    from documents.generators.perelik_generator import PerelikGenerator
    from documents.generators.protocol_rozgl_generator import (
        ProtocolRozglGenerator,
    )
    from documents.generators.protokol_analiz_generator import (
        ProtokolAnalizGenerator,
    )
    from documents.generators.reshenya_generator import ReshenyaGenerator
    from documents.generators.reshenya_vidachu_generator import (
        ReshenyaVidachuGenerator,
    )
    from documents.generators.sertifikat_generator import SertifikatGenerator
    from documents.generators.ugoda_generator import UgodaGenerator
    from documents.generators.vysnovok_generator import VysnovokGenerator
    from documents.generators.zayavka_generator import ZayavkaGenerator

    registry = GeneratorRegistry()

    # ВЦ генератори
    registry.register(
        "zayavka",
        lambda: ZayavkaGenerator(template_dir, output_dir, context_builder),
    )
    registry.register(
        "protocol_rozgl",
        lambda: ProtocolRozglGenerator(template_dir, output_dir),
    )
    registry.register(
        "perelik",
        lambda: PerelikGenerator(template_dir, output_dir),
    )
    registry.register(
        "reshenya",
        lambda: ReshenyaGenerator(template_dir, output_dir),
    )
    registry.register(
        "akt_vidbir",
        lambda: AktVidbirGenerator(template_dir, output_dir),
    )
    registry.register(
        "akt_ident",
        lambda: AktIdentGenerator(template_dir, output_dir),
    )

    # Фінальні генератори
    registry.register(
        "sertifikat",
        lambda: SertifikatGenerator(template_dir, output_dir),
    )
    registry.register(
        "deklaraciya",
        lambda: DeklaraciyaGenerator(template_dir, output_dir),
    )
    registry.register(
        "ugoda",
        lambda: UgodaGenerator(template_dir, output_dir),
    )
    registry.register(
        "reshenya_vidachu",
        lambda: ReshenyaVidachuGenerator(template_dir, output_dir),
    )
    registry.register(
        "protokol_analiz",
        lambda: ProtokolAnalizGenerator(template_dir, output_dir),
    )
    registry.register(
        "vysnovok",
        lambda: VysnovokGenerator(template_dir, output_dir),
    )

    return registry

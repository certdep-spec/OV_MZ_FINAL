"""
Пайплайн генерації ВЦ документів (до випробувань).

Послідовність:
1. Заявка + Реєстрація + Додатки
2. Протокол розгляду
3. Для кожної партії: Перелік, Рішення, Акт відбору, Акт ідентифікації
"""

import logging
from pathlib import Path
from typing import Any, Dict, List

from documents.pipelines.base_pipeline import BasePipeline
from documents.registry import create_default_registry

logger = logging.getLogger(__name__)

# Послідовність генерації ВЦ документів
_VC_SEQUENCE = [
    "zayavka",  # Заявка + Реєстрація + Додатки
    "protocol_rozgl",  # Протокол розгляду
]

# Послідовність для кожної партії
_VC_PARTY_SEQUENCE = [
    "perelik",  # Перелік
    "reshenya",  # Рішення
    "akt_vidbir",  # Акт відбору
    "akt_ident",  # Акт ідентифікації
]


class VCPipeline(BasePipeline):
    """
    Пайплайн генерації документів ДЛЯ ВЦ (до випробувань).

    Використовує Registry для створення генераторів.
    """

    def __init__(
        self,
        template_dir: Path,
        output_dir: Path,
        context_builder,
    ):
        """
        Ініціалізація ВЦ пайплайну.

        Args:
            template_dir: Шлях до шаблонів
            output_dir: Шлях до виводу документів
            context_builder: DocumentDataService для збору даних
        """
        super().__init__(name="ВЦ документи")
        self.context_builder = context_builder

        # Створюємо Registry та зберігаємо генератори
        registry = create_default_registry(template_dir, output_dir, context_builder)
        self._generators: Dict[str, Any] = {}
        for name in registry.list_names():
            self._generators[name] = registry.create(name)

    # ===== Властивості для зворотної сумісності =====
    @property
    def zayavka_gen(self):
        return self._generators["zayavka"]

    @property
    def protocol_rozgl_gen(self):
        return self._generators["protocol_rozgl"]

    @property
    def perelik_gen(self):
        return self._generators["perelik"]

    @property
    def reshenya_gen(self):
        return self._generators["reshenya"]

    @property
    def akt_vidbir_gen(self):
        return self._generators["akt_vidbir"]

    @property
    def akt_ident_gen(self):
        return self._generators["akt_ident"]

    def execute(
        self,
        app_data: Dict,
        parties: List[Dict],
        folder: Path,
        file_date: str = None,
        **kwargs,
    ) -> Dict[str, int]:
        """
        Генерація всіх ВЦ документів.

        Args:
            app_data: Дані заявки
            parties: Список партій
            folder: Шлях до папки для документів
            file_date: Дата для імені файлу (за замовчуванням — сьогодні)

        Returns:
            Словник з кількістю згенерованих документів по типу
        """
        if file_date is None:
            file_date = self._get_file_date()

        results = {
            "zayavka": 0,
            "dodatok": 0,
            "perelik": 0,
            "protocol": 0,
            "reshennya": 0,
            "akt_vidbir": 0,
            "akt_ident": 0,
        }

        try:
            logger.info(f"\n📁 Папка для документів: {folder}")

            # Збираємо всі стандарти
            all_standards_text = self.context_builder.collect_all_standards(parties)

            # ===== 1. ЗАЯВКА + РЕЄСТРАЦІЯ + ДОДАТКИ =====
            zayavka_results = self._generators["zayavka"].generate(
                app_data,
                parties=parties,
                folder=folder,
                file_date=file_date,
                standards_text=all_standards_text,
            )
            results.update(zayavka_results)

            # ===== 2. ПРОТОКОЛ РОЗГЛЯДУ =====
            protocol_results = self._generators["protocol_rozgl"].generate(
                app_data,
                folder=folder,
                file_date=file_date,
                standards_text=all_standards_text,
            )
            results.update(protocol_results)

            # ===== ДЛЯ КОЖНОЇ ПАРТІЇ =====
            for party_idx, party in enumerate(parties, 1):
                try:
                    logger.info(f"\n📦 Обробка партії {party_idx}/{len(parties)}...")

                    party_standards_text = self.context_builder.collect_party_standards(
                        party
                    )

                    # Перелік
                    perelik_results = self._generators["perelik"].generate(
                        app_data,
                        party,
                        party_idx,
                        folder,
                        file_date,
                        party_standards_text,
                    )
                    results["perelik"] += perelik_results.get("perelik", 0)

                    # Рішення
                    reshenya_results = self._generators["reshenya"].generate(
                        app_data,
                        party,
                        party_idx,
                        folder,
                        file_date,
                        party_standards_text,
                    )
                    results["reshennya"] += reshenya_results.get("reshennya", 0)

                    # Акт відбору
                    akt_vidbir_results = self._generators["akt_vidbir"].generate(
                        app_data,
                        party,
                        party_idx,
                        folder,
                        file_date,
                        party_standards_text,
                    )
                    results["akt_vidbir"] += akt_vidbir_results.get("akt_vidbir", 0)

                    # Акт ідентифікації
                    akt_ident_results = self._generators["akt_ident"].generate(
                        app_data,
                        party,
                        party_idx,
                        folder,
                        file_date,
                        party_standards_text,
                    )
                    results["akt_ident"] += akt_ident_results.get("akt_ident", 0)

                except Exception as e:
                    logger.error(
                        f"❌ Помилка обробки партії {party_idx}: {e}",
                        exc_info=True,
                    )

            # ===== ЗВІТ =====
            self._print_report(results, folder)

        except Exception as e:
            logger.error(f"❌ Помилка генерації ВЦ документів: {e}", exc_info=True)

        return results

    def _print_report(self, results: Dict, folder: Path = None):
        """Специфічний звіт для ВЦ документів"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 ЗВІТ ПРО ГЕНЕРАЦІЮ ВЦ ДОКУМЕНТІВ")
        logger.info("=" * 60)
        if folder:
            logger.info(f"📁 Папка: {folder}")
        logger.info(f"✅ Заявка (зареєстрована + Додатки): {results['zayavka']}")
        logger.info(f"✅ Протокол розгляду: {results['protocol']}")
        logger.info(f"✅ Перелік: {results['perelik']}")
        logger.info(f"✅ Рішення: {results['reshennya']}")
        logger.info(f"✅ Акт відбору: {results['akt_vidbir']}")
        logger.info(f"✅ Акт ідентифікації: {results['akt_ident']}")
        logger.info("=" * 60)

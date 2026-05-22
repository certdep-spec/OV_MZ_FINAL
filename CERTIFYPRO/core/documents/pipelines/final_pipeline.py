"""
Пайплайн генерації фінальних документів.

Послідовність для кожної партії:
1. Сертифікат
2. Декларація
3. Угода
4. Рішення на видачу
5. Протокол аналізування
6. Висновок
"""

import logging
from pathlib import Path
from typing import Any, Dict

from documents.pipelines.base_pipeline import BasePipeline
from documents.registry import create_default_registry

logger = logging.getLogger(__name__)


class FinalPipeline(BasePipeline):
    """
    Пайплайн генерації фінальних документів для однієї партії.

    Використовує Registry для створення генераторів.
    """

    def __init__(
        self,
        template_dir: Path,
        output_dir: Path,
        context_builder,
    ):
        """
        Ініціалізація фінального пайплайну.

        Args:
            template_dir: Шлях до шаблонів
            output_dir: Шлях до виводу документів
            context_builder: DocumentDataService для збору даних
        """
        super().__init__(name="Фінальні документи")
        self.context_builder = context_builder

        # Створюємо Registry та зберігаємо генератори
        registry = create_default_registry(template_dir, output_dir, context_builder)
        self._generators: Dict[str, Any] = {}
        for name in registry.list_names():
            self._generators[name] = registry.create(name)

    # ===== Властивості для зворотної сумісності =====
    @property
    def sertifikat_gen(self):
        return self._generators["sertifikat"]

    @property
    def deklaraciya_gen(self):
        return self._generators["deklaraciya"]

    @property
    def ugoda_gen(self):
        return self._generators["ugoda"]

    @property
    def reshenya_vidachu_gen(self):
        return self._generators["reshenya_vidachu"]

    @property
    def protokol_analiz_gen(self):
        return self._generators["protokol_analiz"]

    @property
    def vysnovok_gen(self):
        return self._generators["vysnovok"]

    def execute(
        self,
        app_data: Dict,
        party_data: Dict,
        party_id: int,
        folder: Path,
        file_date: str = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Генерація фінальних документів для однієї партії.

        Args:
            app_data: Дані заявки
            party_data: Дані партії
            party_id: ID партії в БД
            folder: Шлях до папки для документів
            file_date: Дата для імені файлу (за замовчуванням — сьогодні)

        Returns:
            Словник з результатами генерації
        """
        if file_date is None:
            file_date = self._get_file_date()

        results = {
            "sertifikat": 0,
            "deklaracija": 0,
            "ugoda": 0,
            "rishennya_vidachu": 0,
            "protokol_analiz": 0,
            "vysnovok": 0,
            "folder": "",
        }

        try:
            results["folder"] = str(folder)

            product_name = party_data.get("product_name", "")
            version = party_data.get("version", "")
            party_code = party_data.get("party_code", "01E")

            # Отримуємо сертифікати ПАР
            par_certificates = self.context_builder.get_par_certificates(
                product_name, version or ""
            )
            logger.info("Партія ID=%s: продукт='%s', код='%s'", party_id, product_name, party_code)

            # ===== 1. СЕРТИФІКАТ =====
            sert_results = self._generators["sertifikat"].generate(
                app_data,
                party_data,
                party_id,
                folder,
                file_date,
                par_certificates,
            )
            results.update(sert_results)

            # ===== 2. ДЕКЛАРАЦІЯ =====
            dekl_results = self._generators["deklaraciya"].generate(
                app_data,
                party_data,
                party_id,
                folder,
                file_date,
                par_certificates,
            )
            results.update(dekl_results)

            # ===== 3. УГОДА =====
            ugoda_results = self._generators["ugoda"].generate(
                app_data,
                party_data,
                party_id,
                folder,
                file_date,
                par_certificates,
            )
            results.update(ugoda_results)

            # ===== 4. РІШЕННЯ НА ВИДАЧУ =====
            rish_results = self._generators["reshenya_vidachu"].generate(
                app_data,
                party_data,
                party_id,
                folder,
                file_date,
                par_certificates,
            )
            results.update(rish_results)

            # ===== 5. ПРОТОКОЛ АНАЛІЗУВАННЯ =====
            prot_results = self._generators["protokol_analiz"].generate(
                app_data,
                party_data,
                party_id,
                folder,
                file_date,
                par_certificates,
            )
            results.update(prot_results)

            # ===== 6. ВИСНОВОК =====
            vysn_results = self._generators["vysnovok"].generate(
                app_data,
                party_data,
                party_id,
                folder,
                file_date,
                par_certificates,
            )
            results.update(vysn_results)

            # ===== ЗВІТ =====
            self._print_report(results, product_name, party_code)

        except Exception as e:
            logger.error(
                f"❌ Помилка генерації фінальних документів: {e}",
                exc_info=True,
            )

        return results

    def _print_report(
        self, results: Dict, product_name: str = None, party_code: str = None
    ):
        """Специфічний звіт для фінальних документів"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 ЗВІТ ПРО ГЕНЕРАЦІЮ ФІНАЛЬНИХ ДОКУМЕНТІВ")
        logger.info("=" * 60)
        if product_name:
            logger.info("Продукт: %s", product_name)
        if party_code:
            logger.info("Код партії: %s", party_code)
        logger.info("Сертифікат: %s", results["sertifikat"])
        logger.info("Декларація: %s", results["deklaracija"])
        logger.info("Угода: %s", results["ugoda"])
        logger.info("Рішення: %s", results["rishennya_vidachu"])
        logger.info("Протокол: %s", results["protokol_analiz"])
        logger.info("Висновок: %s", results["vysnovok"])

        total = sum(
            v for k, v in results.items() if k != "folder" and isinstance(v, int)
        )
        logger.info("Всього згенеровано: %d з 6 документів", total)
        logger.info("=" * 60 + "\n")

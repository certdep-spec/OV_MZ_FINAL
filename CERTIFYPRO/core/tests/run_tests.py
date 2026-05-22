"""
Запуск тестів для CertifyPro
"""

import logging
import sys
import unittest
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Додаємо корінь проекту до шляху
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    # Створення тестового набору
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Додавання тестів
    logger.info("🔍 Завантаження тестів...")

    # DTO тести
    suite.addTests(loader.loadTestsFromName("tests.test_dto"))
    logger.info("  ✅ DTO тести")

    # Сервіси тести
    suite.addTests(loader.loadTestsFromName("tests.test_services"))
    logger.info("  ✅ Сервіси тести")

    # Запуск тестів
    logger.info("\n🚀 Запуск тестів...\n")

    runner = unittest.TextTestRunner(verbosity=2, failfast=False, buffer=True)

    result = runner.run(suite)

    # Статистика
    logger.info("\n" + "=" * 70)
    logger.info(f"📊 РЕЗУЛЬТАТИ: {result.testsRun} тестів")
    logger.info(
        f"   ✅ Успішно: {result.testsRun - len(result.failures) - len(result.errors)}"
    )
    logger.info(f"   ❌ Помилок: {len(result.errors)}")
    logger.info(f"   ⚠️  Провалів: {len(result.failures)}")
    logger.info("=" * 70)

    # Вихідний код
    sys.exit(0 if result.wasSuccessful() else 1)

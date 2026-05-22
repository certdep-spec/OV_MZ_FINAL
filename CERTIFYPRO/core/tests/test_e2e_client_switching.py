"""
E2E-тест мультиклиентского переключения контекста.

Проверяет:
1. Инициализация ClientManager
2. Переключение afina → johnson
3. Проверка что состояние НЕ "протекает" между клиентами
   - template_suffix корректный
   - DEFAULT_COMPANY корректный
   - DB_PATH указывает на правильную БД
   - has_feature() возвращает правильные значения
"""

import sys
from pathlib import Path

# Добавляем core в PYTHONPATH
CORE_DIR = Path(__file__).parent.parent
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))


def test_client_switching_no_leak():
    """Тест: переключение клиентов не вызывает 'протекания' состояния"""
    import config
    from client_manager import ClientManager

    print("=" * 60)
    print("E2E: ТЕСТ ПЕРЕКЛЮЧЕНИЯ КОНТЕКСТА")
    print("=" * 60)

    # Инициализируем
    manager = ClientManager()
    profiles_path = CORE_DIR.parent / "resources" / "profiles.yaml"
    manager.load_profiles(profiles_path)

    # ===== Тест 1: АФІНА =====
    print("\n📋 1. Инициализация АФІНА")
    manager.select_client("afina")

    assert manager.get_template_suffix() == "_А", (
        f"Ожидался '_А', получен '{manager.get_template_suffix()}'"
    )
    assert not manager.has_feature("import_product"), "АФІНА не должен поддерживать импорт"
    assert manager.get_ugoda_template_count() == 1, (
        f"АФІНА: 1 шаблон угоды, получено {manager.get_ugoda_template_count()}"
    )
    assert "АФІНА" in manager.current_client.company.name, (
        f"Компания: {manager.current_client.company.name}"
    )
    print(f"   ✅ template_suffix = {manager.get_template_suffix()}")
    print(f"   ✅ import_product = {manager.has_feature('import_product')}")
    print(f"   ✅ company = {manager.current_client.company.name}")

    # ===== Тест 2: Переключение на ДЖОНСОН =====
    print("\n📋 2. Переключение на ДЖОНСОН")
    manager.select_client("johnson")

    assert manager.get_template_suffix() == "_Д", (
        f"Ожидался '_Д', получен '{manager.get_template_suffix()}'"
    )
    assert manager.has_feature("import_product"), "ДЖОНСОН должен поддерживать импорт"
    assert manager.get_ugoda_template_count() == 2, (
        f"ДЖОНСОН: 2 шаблона угоды, получено {manager.get_ugoda_template_count()}"
    )
    assert "ДЖОНСОН" in manager.current_client.company.name, (
        f"Компания: {manager.current_client.company.name}"
    )
    print(f"   ✅ template_suffix = {manager.get_template_suffix()}")
    print(f"   ✅ import_product = {manager.has_feature('import_product')}")
    print(f"   ✅ ugoda_templates = {manager.get_ugoda_template_count()}")
    print(f"   ✅ company = {manager.current_client.company.name}")

    # ===== Тест 3: Переключение обратно на АФІНА =====
    print("\n📋 3. Переключение обратно на АФІНА")
    manager.select_client("afina")

    assert manager.get_template_suffix() == "_А", (
        f"После переключения обратно: '_А', получен '{manager.get_template_suffix()}'"
    )
    assert not manager.has_feature("import_product"), (
        "После переключения: АФІНА не поддерживает импорт"
    )
    print(f"   ✅ template_suffix = {manager.get_template_suffix()}")
    print(f"   ✅ import_product = {manager.has_feature('import_product')}")

    # ===== Тест 4: config.init_client_config =====
    print("\n📋 4. Тест config.init_client_config")

    # Сброс состояния
    import client_manager as cm

    cm._client_manager = None
    config._client_initialized = False

    # Инициализация АФІНА через config
    config.init_client_config("afina")
    assert config.DEFAULT_COMPANY == "ТОВ «АФІНА-ГРУП»", (
        f"DEFAULT_COMPANY: {config.DEFAULT_COMPANY}"
    )
    assert "АФІНА" in str(config.DB_PATH), f"DB_PATH: {config.DB_PATH}"
    print(f"   ✅ DEFAULT_COMPANY = {config.DEFAULT_COMPANY}")
    print(f"   ✅ DB_PATH = {config.DB_PATH}")

    # Сброс и инициализация ДЖОНСОН
    cm._client_manager = None
    config._client_initialized = False

    config.init_client_config("johnson")
    assert "ДЖОНСОН" in config.DEFAULT_COMPANY, f"DEFAULT_COMPANY: {config.DEFAULT_COMPANY}"
    assert "ДЖОНСОН" in str(config.DB_PATH), f"DB_PATH: {config.DB_PATH}"
    print(f"   ✅ DEFAULT_COMPANY = {config.DEFAULT_COMPANY}")
    print(f"   ✅ DB_PATH = {config.DB_PATH}")

    # ===== Тест 5: launcher_mapping =====
    print("\n📋 5. Тест launcher_mapping")
    cm._client_manager = None
    manager2 = ClientManager()
    manager2.load_profiles(profiles_path)

    mapping = manager2.get_launcher_to_client_mapping()
    assert mapping == {
        "АФІНА": "afina",
        "ДЖОНСОН": "johnson",
        "PROCTER": "procter",
    }, f"Маппинг: {mapping}"
    print(f"   ✅ mapping = {mapping}")

    print("\n" + "=" * 60)
    print("✅ ВСЕ E2E ТЕСТЫ ПРОЙДЕНЫ — НУЛЕВОЕ 'ПРОТЕКАНИЕ'!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_client_switching_no_leak()
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

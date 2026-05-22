# Журнал изменений (Changelog)

Все значимые изменения проекта CertifyPro.

Формат ведётся согласно [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/),
версионирование — согласно [Semantic Versioning](https://semver.org/lang/ru/).

---

## [3.1.0] — 2026-04-13

### 🆕 Додано
- **Авто-створення інфраструктури нових клієнтів** — при додаванні через GUI лаунчера автоматично створюються: папка проекту, пуста БД `certify.db` (6 таблиць), реєстрація в `profiles.yaml`
- **`client_provisioner.py`** — модуль у `client_launcher/` для повної ініціалізації клієнта (папки + БД + YAML + відкат при помилці)
- **`db_schema.sql`** — єдиний файл SQL-схеми БД (`CERTIFYPRO/core/database/`), замість дублювання між `di.py` та `db_manager.py`
- **Fallback для динамічних клієнтів** у `config.py` — якщо клієнт запущений напряму і відсутній у `profiles.yaml`, мінімальна інфраструктура створюється автоматично
- **Покращені UI-повідомлення** при додаванні нового клієнта — показується результат створення папок, БД, YAML

### 📝 Оновлено документацію
- `docs/ARCHITECTURE.md` — додано секцію "Автоматична ініціалізація клієнтів"
- `docs/ADMIN_GUIDE.md` — автоматичний спосіб як основний, ручний — для просунутих
- `README.md` — оновлено інструкцію з додавання клієнта

### 🔧 Змінено
- `applicants_db.add_applicant()` тепер приймає `auto_provision=True` за замовчуванням
- `init_client_config()` викликає `_ensure_dynamic_client_infrastructure()` для клієнтів поза `profiles.yaml`

---

## [3.0.0] — 2026-04-12

### 🎉 Добавлено
- **Мультиклієнтська архітектура** — підтримка декількох клієнтів (АФІНА, ДЖОНСОН) через `profiles.yaml`
- **`ClientManager`** — singleton-менеджер профілів клієнтів з завантаженням з YAML
- **`ClientConfig`** dataclass — інкапсульована конфігурація клієнта (замість глобальних змінних)
- **Динамічний вибір шаблонів** — суфікси `_А` / `_Д` на основі профілю
- **`launcher_mapping`** — маппінг заявника на client_id з YAML (новий клієнт без правки коду)
- **Бейдж клієнта** — відображення поточного клієнта у куті кожного вікна
- **Теги-константи** (`documents/tags.py`) — єдиний реєстр тегів шаблонів
- **`BasePartyDocumentGenerator`** — базовий клас для 4 генераторів ВЦ документів
- **`ApplicationRegistrar`** — окремий модуль реєстрації заявок
- **`AppendixBuilder`** — окремий модуль побудови додатків
- **`geometry_manager.py`** — єдиний модуль збереження геометрії вікон
- **E2E-тест** переключення контексту (`test_e2e_client_switching.py`)
- **Портативний .exe** — автоматичне розгортання БД при першому запуску

### 🔧 Змінено
- `DocumentContextBuilder` → `DocumentDataService` — усунено плутанину імен
- `_build_final_replacements` перенесено в `DocumentBase` — усунено створення тимчасових об'єктів
- 4 генератори (`perelik`, `reshenya`, `akt_vidbir`, `akt_ident`) рефакторизовані через `BasePartyDocumentGenerator`
- `ZayavkaGenerator` розділено: 429 → 129 строк + 2 окремі модулі
- `profiles.yaml` — відносні шляхи `data_dir` для portable-режиму
- `config.py` — шляхи відносно папки .exe у frozen-режимі

### 🗑️ Видалено
- `ProtocolGenerator` — мертвий код (не використовується, не зареєстрований)
- Дублювання `save/restore_window_geometry` з 3 файлів — замінено на `geometry_manager.py`
- Створення тимчасових `SertifikatGenerator` у 6 генераторах
- Хардкод маппінгу `papka_proektu → client_id` в лаунчері
- Мертві іморти `SertifikatGenerator` з 3 файлів

### 🐛 Виправлено
- Пошук ID заявника за назвою замість справжнього database ID (баг редагування/видалення)
- Відсутність UNIQUE constraint на `kod_edrpou` — можливі дублікати
- Відсутність обробки помилок `subprocess.run` — падіння CertifyPro залишалося непоміченим
- `template_resolver` fallback на `_Д` без попередження

---

## [2.0.0] — 2026-03-24

### 🎉 Додано
- DI-контейнер (`core/di.py`)
- Пайплайни генерації документів (`VCPipeline`, `FinalPipeline`)
- Registry-паттерн для генераторів (`GeneratorRegistry`)
- Імпорт з Excel (openpyxl)
- Вікно довідників (продукція, стандарти, потужності, склад)
- Збереження геометрії всіх вікон
- PyInstaller-збірка (`.exe`)
- 23 unit-тести

### 🔧 Змінено
- Архітектура: `gui/`, `services/`, `documents/`, `models/`, `database/`
- Перехід від моноліту до модульної структури
- DTO-моделі для всіх сутностей

---

## [1.0.0] — 2026-01-15

### 🎉 Додано
- Базова GUI (CustomTkinter)
- Генерація документів через `docxtpl` + `copy+replace`
- SQLite база даних
- Шаблони `.docx` для АФІНА
- Реєстр заявок
- Формування заявок з партіями

[3.0.0]: https://github.com/example/certifypro/releases/tag/v3.0.0
[2.0.0]: https://github.com/example/certifypro/releases/tag/v2.0.0
[1.0.0]: https://github.com/example/certifypro/releases/tag/v1.0.0

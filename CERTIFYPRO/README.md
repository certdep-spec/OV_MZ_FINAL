# CertifyPro v3.0 — Система автоматизації документації сертифікації

## Огляд

**CertifyPro** — десктопне GUI-застосунок для автоматизації створення документів сертифікації продукції. Система генерує повний пакет документів (заявка, протоколи, акти, сертифікати, угоди тощо) на основі шаблонів `.docx` та даних з бази SQLite.

**Версія:** 3.0.0 (Мультиклієнтська)  
**Технології:** Python, CustomTkinter, SQLite, python-docx, docxtpl, PyYAML

---

## Можливості

### 📝 Заявки

- Створення нових заявок з вибором продукції та стандартів
- Імпорт даних з Excel (.xlsx, .xlsm)
- Відкриття та редагування існуючих заявок
- Додавання партій продукції з деталями (код, дата, кількість, одиниці)

### 📄 Генерація документів (13 типів)

- Заявка + Реєстрація + Додатки
- Протокол розгляду
- Перелік вихідної декларації
- Рішення за заявкою
- Акт відбору зразків
- Акт ідентифікації
- Сертифікат відповідності
- Декларація про відповідність
- Угода (підтримка вітчизняної та імпортної продукції)
- Рішення на видачу
- Протокол аналізування
- Висновок

### 📚 Довідники

- Продукція (назва, код ТУ, термін зберігання)
- Стандарти НД
- Виробничі потужності
- Склад продукції (ПАР) з версіонуванням

### 🏢 Мультиклієнтська архітектура

- Підтримка декількох клієнтів через `profiles.yaml`
- Кожен клієнт має свою БД, шаблони та налаштування
- Динамічний вибір шаблонів на основі профілю (`_А` / `_Д`)

---

## Встановлення та запуск

### З .exe (рекомендовано)

1. Запустіть `launcher.exe` для вибору клієнта
2. Оберіть підприємство зі списку
3. Натисніть "🚀 Запустити проект"

Або запустіть `CertifyPro.exe` напряму з аргументом:

```text
CertifyPro.exe afina    # Клієнт АФІНА
CertifyPro.exe johnson  # Клієнт ДЖОНСОН
```

### З вихідного коду

```bash
# Встановлення залежностей
pip install -r requirements.txt

# Запуск через лаунчер
cd C:\FINAL
python -m client_launcher.launcher

# Або напряму (з кореня CERTIFYPRO)
cd C:\FINAL\CERTIFYPRO
python core\main.py afina
```

---

## Структура проекту

```text
C:\FINAL/
├── client_launcher/          # Лаунчер вибору клієнта
│   ├── launcher.py           # Точка входу лаунчера
│   ├── launcher_dialog.py    # GUI вибору заявника
│   ├── applicants_db.py      # БД заявників
│   ├── registry_dialog.py    # Реєстр заявок
│   ├── geometry_manager.py   # Збереження геометрії вікон
│   └── requirements.txt
│
├── CERTIFYPRO/               # Основний проект v3.0
│   ├── resources/
│   │   ├── profiles.yaml     # Профілі клієнтів
│   │   └── templates/        # 25 шаблонів (_А + _Д)
│   │
│   ├── core/                 # Ядро системи
│   │   ├── main.py           # Точка входу (вибір клієнта + GUI)
│   │   ├── config.py         # Конфігурація (ClientConfig)
│   │   ├── client_manager.py # Менеджер клієнтів
│   │   │
│   │   ├── gui/              # Графічний інтерфейс
│   │   │   ├── main_window.py
│   │   │   ├── app_form.py
│   │   │   ├── app_selector.py
│   │   │   ├── dictionaries_window.py
│   │   │   ├── client_badge.py     # Бейдж клієнта
│   │   │   └── widgets/
│   │   │
│   │   ├── documents/        # Генерація документів
│   │   │   ├── document_base.py
│   │   │   ├── vc_generator.py
│   │   │   ├── tags.py           # Константи тегів
│   │   │   ├── app_registration.py
│   │   │   ├── appendix_builder.py
│   │   │   ├── generators/       # 12 генераторів
│   │   │   │   ├── base_party_generator.py
│   │   │   │   ├── zayavka_generator.py
│   │   │   │   └── ...
│   │   │   └── pipelines/        # ВЦ + Фінальні
│   │   │
│   │   ├── services/         # Бізнес-логіка
│   │   ├── database/         # Робота з БД
│   │   ├── models/           # DTO
│   │   ├── core/             # DI-контейнер
│   │   ├── utils/            # Утиліти
│   │   └── tests/            # 28+ тестів
│   │
│   └── dist/                 # Збірка PyInstaller
│
├── АФІНА/                    # Клієнт АФІНА (дані)
│   ├── data/certify.db       # БД заявника
│   └── data/Documents/       # Згенеровані документи
│
└── ДЖОНСОН/                  # Клієнт ДЖОНСОН (дані)
    ├── data/certify.db       # БД заявника
    └── data/Documents/       # Згенеровані документи
```

---

### ➕ Автоматическое добавление нового клиента (v3.1+)

Начиная с версии 3.1.0, новый клиент добавляется автоматически через GUI лаунчера:

1. Запустите `launcher.exe` (или `python -m client_launcher.launcher`)
2. Нажмите **"⚙️ Керувати заявниками"** → **"➕ Додати"**
3. Заполните форму (Назва, Адреса, ЄДРПОУ, Керівник, Папка проекту)
4. Нажмите **"✅ Зберегти"**

Система автоматически создаст:

- 📁 Папку проекта: `<PROJECT_ROOT>/<papka_proektu>/data/`
- 📁 Подпапку `Documents/` для документов
- 💾 Пустую БД `certify.db` с полной схемой (6 таблиц)
- 📝 Запись в `profiles.yaml`

**Никакого ручного редактирования файлов!**

> Примечание: имя папки на кириллице транслитерируется для `client_id` в profiles.yaml.
> Например, "НОВИЙ_КЛІЄНТ" → `novyj_klient`.

---

## Додавання нового клієнта

### Ручной способ (v3.0 и ранее)

### Без правки коду

1. **Додайте профіль** в `resources/profiles.yaml`:

```yaml
clients:
  newclient:
    name: "NEWCLIENT"
    display_name: "ТОВ «НОВИЙ КЛІЄНТ»"
    template_suffix: "_Н"
    launcher_mapping: "НОВИЙ"
    company:
      name: "ТОВ «НОВИЙ КЛІЄНТ»"
      code: "12345678"
      director: "І. І. Петренко"
    features:
      import_product: false
      ugoda_templates: 1
    data_dir: "C:/FINAL/NEWCLIENT/data"
    description: "Новий клієнт"
```

1. **Створіть папку** `C:\FINAL\NEWCLIENT\data\` з порожньою `certify.db`

1. **Створіть шаблони** `resources/templates/*_Н.docx`

1. **Додайте заявника** через лаунчер → "⚙️ Керувати заявниками" з `papka_proektu = "НОВИЙ"`

---

## Архітектура

### Мультиклієнтська модель

```text
Лаунчер → profiles.yaml → ClientManager → init_client_config(client_id)
                                                        ↓
                                            ClientConfig (dataclass)
                                                        ↓
                                  ┌─────────────────────┼─────────────────────┐
                                  ↓                     ↓                     ↓
                            БД (SQLite)          Шаблони (.docx)       GUI (CustomTkinter)
                        C:/FINAL/КЛІЄНТ/      resources/templates/  core/gui/main_window.py
                          data/certify.db         *_К.docx
```

### Генерація документів

```text
GUI → VCDocumentGenerator (Facade)
         ↓
    VCPipeline / FinalPipeline
         ↓
    GeneratorRegistry (фабрика)
         ↓
    12 генераторів (наслідування DocumentBase)
         ↓
    docxtpl / copy+replace → .docx файли
```

---

## Тестування

```bash
cd C:\FINAL\CERTIFYPRO\core

# Unit-тести
python tests\run_tests.py

# E2E-тест переключення контексту
python tests\test_e2e_client_switching.py

# Тест мультиклієнтської конфігурації
python test_multi_client.py
```

---

## Збірка .exe

```bash
cd C:\FINAL\CERTIFYPRO\core
pyinstaller CertifyPro.spec
```

Зібраний файл: `dist/CertifyPro.exe` (≈70 MB)  
Архів для розповсюдження: `CertifyPro_v3.0.zip`

### Запуск .exe

```text
CertifyPro.exe afina    # Клієнт АФІНА
CertifyPro.exe johnson  # Клієнт ДЖОНСОН
CertifyPro.exe          # Без аргументу — GUI вибору клієнта
```

### Вміст дистрибутиву

| Файл | Розмір | Призначення |
| --- | --- | --- |
| `CertifyPro.exe` | ~70 MB | Виконуваний файл (все включено) |
| `README_CertifyPro.txt` | ~10 KB | Документація |

**Базы данных включены в .exe** — при первом запуске они извлекаются во временную директорию.

---

## Залежності

| Пакет | Призначення |
| --- | --- |
| customtkinter | GUI фреймворк |
| python-docx | Робота з .docx |
| docxtpl | Шаблонізація документів |
| openpyxl | Імпорт з Excel |
| PyYAML | Читання profiles.yaml |
| python-dotenv | Завантаження .env |
| PyInstaller | Збірка .exe |

---

## Версії

| Версія | Опис |
| --- | --- |
| v1.0 | Моноклієнтська версія (АФІНА) |
| v2.0 | Оптимізована архітектура, DI-контейнер, пайплайни |
| v3.0 | Мультиклієнтська, profiles.yaml, ClientConfig, бейдж клієнта |

---

## Ліцензія

Внутрішній проект для автоматизації документообігу сертифікації.

---

## Правила кодировки

Проект полностью работает в UTF-8. Подробную информацию и требования к кодировке читайте в [docs/encoding.md](docs/encoding.md).

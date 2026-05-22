# CertifyPro v2.0

Система автоматизації документації сертифікації.

## 📋 Огляд

CertifyPro — це десктопний застосунок для автоматизації створення документів сертифікації продукції.
Система генерує:
- Заявки на сертифікацію
- Протоколи розгляду
- Переліки продукції
- Рішення
- Акти відбору та ідентифікації
- Сертифікати
- Декларації відповідності
- Угоди

## 🚀 Швидкий старт

### Вимоги
- Python 3.10+
- Windows/Linux/macOS

### Встановлення

```bash
# Клонувати репозиторій
git clone <repository-url>
cd CertifyPro2

# Створити віртуальне оточення
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

# Встановити залежності
pip install -r requirements.txt
```

### Запуск

```bash
python main.py
```

## 🏗 Архітектура

### Багаторівнева архітектура

```
┌─────────────────────────────────────────────────────────────┐
│                      GUI Layer (gui/)                       │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ app_form.py │  │main_window.py│  │widgets/           │  │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer (services/)                 │
│  ┌──────────────────┐  ┌────────────────┐  ┌────────────┐  │
│  │ApplicationService│  │DictionaryService│ │DocumentSvc │  │
│  └──────────────────┘  └────────────────┘  └────────────┘  │
│  ┌──────────────────┐                                       │
│  │ ImportService    │                                       │
│  └──────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Data Access Layer (database/)               │
│  ┌────────────────────────────────────────────────────┐     │
│  │              DatabaseManager (db_manager.py)        │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Models (models/)                       │
│  ┌────────────────────────────────────────────────────┐     │
│  │              DTO (Data Transfer Objects)            │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Структура проекту

```
CertifyPro2/
├── main.py                      # Точка входу
├── config.py                    # Конфігурація
├── exceptions.py                # Кастомні виключення
├── requirements.txt             # Залежності
│
├── gui/                         # GUI компоненти
│   ├── main_window.py           # Головне вікно
│   ├── app_form.py              # Форма заявки
│   ├── app_selector.py          # Діалог вибору заявки
│   ├── dictionaries_window.py   # Вікно довідників
│   └── widgets/                 # Віджети
│       ├── product_selection_dialog.py
│       ├── standards_selection_dialog.py
│       └── party_details_dialog.py
│
├── services/                    # Бізнес-логіка
│   ├── base_service.py          # Базовий клас сервісу
│   ├── application_service.py   # Заявки
│   ├── dictionary_service.py    # Довідники
│   ├── document_service.py      # Документи
│   └── import_service.py        # Імпорт з Excel
│
├── models/                      # DTO моделі
│   └── dto.py
│
├── database/                    # Доступ до БД
│   └── db_manager.py            # DatabaseManager
│
├── documents/                   # Генерація документів
│   ├── vc_generator.py          # Головний фасад
│   ├── document_base.py         # Базовий клас
│   ├── document_utils.py        # Утиліти форматування
│   ├── table_utils.py           # Утиліти таблиць
│   ├── context_builder.py       # Builder контексту
│   └── generators/              # Конкретні генератори
│       ├── zayavka_generator.py
│       ├── protocol_rozgl_generator.py
│       ├── perelik_generator.py
│       ├── reshenya_generator.py
│       ├── akt_vidbir_generator.py
│       ├── akt_ident_generator.py
│       ├── sertifikat_generator.py
│       ├── deklaraciya_generator.py
│       ├── ugoda_generator.py
│       └── ...
│
├── utils/                       # Утиліти
│   └── path_utils.py
│
├── templates/                   # Шаблони .docx
├── tests/                       # Unit/Інтеграційні тести
├── logs/                        # Логи
└── data/                        # Дані (БД)
```

## 🧪 Тестування

### Запуск тестів

```bash
# Всі тести
python -m pytest tests/ -v

# З покриттям
python -m pytest tests/ -v --cov=services --cov=documents --cov=gui

# Конкретний тест
python -m pytest tests/test_services.py -v
```

### Статистика тестів

- **Всього тестів:** 194
- **Покриття (без GUI):** 58%
- **Статус:** ✅ Всі проходять

## 📖 Використання

### Створення заявки через сервіси

```python
from services.application_service import ApplicationService
from models.dto import ApplicationDTO, PartyDTO

# Ініціалізація
app_service = ApplicationService("data/certify.db")

# Створення заявки
app = ApplicationDTO(
    app_number="001",
    app_date="05.04.2026",
    company_name="ТОВ Тест",
    company_code="12345678",
)
app_id = app_service.save_application(app)

# Додавання партій
parties = [
    PartyDTO(
        product_name="Продукт А",
        party_code="01E",
        quantity=1000,
        standards=[1, 2],
    ),
]
app_service.save_parties(app_id, parties)
```

### Імпорт з Excel

```python
from services.import_service import ImportService

import_service = ImportService("data/certify.db")
stats = import_service.import_from_excel("data.xlsx")

print(f"Продуктів: {stats['products']}")
print(f"Стандартів: {stats['standards']}")
```

### Генерація документів

```python
from documents.vc_generator import VCDocumentGenerator
from services.document_service import DocumentService

doc_service = DocumentService(
    "data/certify.db",
    "templates/",
    "data/Documents/"
)

vc_gen = VCDocumentGenerator(
    "templates/",
    "data/Documents/",
    document_service=doc_service
)

app_data = {
    "app_number": "001",
    "app_date": "05.04.2026",
    "company_name": "ТОВ Тест",
}

results = vc_gen.generate_vc_documents(app_data, parties)
```

## ⚙️ Конфігурація

Основні налаштування в `config.py`:

```python
# Шляхи
DB_PATH = "data/certify.db"
TEMPLATES_DIR = "templates/"
DOCUMENTS_DIR = "data/Documents/"

# За замовчуванням
DEFAULT_COMPANY = "ТОВ «АФІНА-ГРУП»"
DEFAULT_COMPANY_CODE = "33324489"
DEFAULT_DIRECTOR = "А. О. Жовтан"
```

## 📝 Примітки

- **DatabaseManager** — legacy, використовується тільки для ініціалізації БД
- **Сервіси** — основний спосіб роботи з даними
- **DTO** — типізовані об'єкти для передачі даних

## 🤝 Внесок

1. Fork репозиторій
2. Створіть feature гілку (`git checkout -b feature/amazing-feature`)
3. Commit зміни (`git commit -m 'Add amazing feature'`)
4. Push до гілки (`git push origin feature/amazing-feature`)
5. Відкрийте Pull Request

## 📄 Ліцензія

Proprietary

---

**Версія:** 2.0  
**Дата:** 2026-04-05

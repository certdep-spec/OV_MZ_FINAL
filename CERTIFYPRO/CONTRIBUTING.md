# Посібник контриб'ютора

Дякуємо за інтерес до розвитку CertifyPro! Цей документ описує процес участі в розробці.

---

## Початок роботи

### 1. Форк та клонування

```bash
git clone <url-репозиторію>
cd C:\FINAL\CERTIFYPRO
```

### 2. Налаштування середовища

```bash
# Віртуальне середовище
python -m venv venv
venv\Scripts\activate

# Залежності
pip install -r requirements.txt
pip install -r requirements-dev.txt  # інструменти розробки
```

### 3. Запуск тестів

```bash
cd core
python tests\run_tests.py
```

---

## Структура проекту

```
CERTIFYPRO/
├── core/                    # Ядро системи
│   ├── main.py              # Точка входу
│   ├── config.py            # Конфігурація
│   ├── client_manager.py    # Менеджер клієнтів
│   │
│   ├── gui/                 # Графічний інтерфейс
│   │   ├── main_window.py   # Головне вікно
│   │   ├── app_form.py      # Форма заявки
│   │   └── widgets/         # Віджети
│   │
│   ├── documents/           # Генерація документів
│   │   ├── document_base.py # Базовий клас
│   │   ├── tags.py          # Константи тегів
│   │   ├── generators/      # 12 генераторів
│   │   └── pipelines/       # ВЦ + Фінальні
│   │
│   ├── services/            # Бізнес-логіка
│   ├── database/            # Робота з БД
│   ├── models/              # DTO
│   ├── core/di.py           # DI-контейнер
│   ├── utils/               # Утиліти
│   └── tests/               # Тести
│
├── resources/
│   ├── profiles.yaml        # Профілі клієнтів
│   └── templates/           # 25 шаблонів .docx
│
└── dist/                    # Збірка PyInstaller
```

---

## Як додати новий генератор документів

### Крок 1: Створіть файл

```python
# documents/generators/moi_novyi_generator.py
from documents.document_base import DocumentBase
from documents.template_resolver import build_template_name

class MoiNovyiGenerator(DocumentBase):
    def get_template_name(self) -> str:
        return build_template_name("Мій_Новий_Шаблон")

    def generate(self, app_data, party_data=None, party_id=0, **kwargs):
        # Ваша логіка
        return {"moi_novyi": 1}
```

### Крок 2: Зареєструйте в Registry

```python
# documents/registry.py
from documents.generators.moi_novyi_generator import MoiNovyiGenerator

# У create_default_registry():
registry.register(
    "moi_novyi",
    lambda: MoiNovyiGenerator(template_dir, output_dir),
)
```

### Крок 3: Додайте шаблон

```
resources/templates/Мій_Новий_Шаблон_А.docx  # для АФІНА
resources/templates/Мій_Новий_Шаблон_Д.docx  # для ДЖОНСОН
```

### Крок 4: Додайте тест

```python
# tests/test_moi_novyi_generator.py
def test_moi_novyi_generator():
    from documents.generators.moi_novyi_generator import MoiNovyiGenerator
    # ...
```

---

## Як додати нового клієнта

### Без правки коду

1. **`profiles.yaml`** — додайте профіль:
```yaml
clients:
  newclient:
    name: "NEWCLIENT"
    display_name: "ТОВ «НОВИЙ»"
    template_suffix: "_Н"
    launcher_mapping: "НОВИЙ"
    company:
      name: "ТОВ «НОВИЙ»"
      code: "12345678"
      director: "І. І. Петренко"
    features:
      import_product: false
      ugoda_templates: 1
    data_dir: "data/НОВИЙ"
    description: "Новий клієнт"
```

2. **Створіть БД:** `data/НОВИЙ/certify.db` (скопіюйте структуру з АФІНА)

3. **Створіть шаблони:** `resources/templates/*_Н.docx`

4. **Додайте заявника** через лаунчер → "⚙️ Керувати заявниками"

---

## Як додати новий тег шаблону

### Крок 1: Додайте константу

```python
# documents/tags.py
MOI_NOVYI_TAG = "[МН1]"
```

### Крок 2: Використовуйте в генераторі

```python
from documents import tags as T

context = {
    T.strip_brackets(T.MOI_NOVYI_TAG): "значення",
}
```

### Крок 3: Додайте тег у шаблон `.docx`

Вставте `[МН1]` у відповідне місце шаблону.

---

## Правила кодування

### Стиль
- **Мова коду:** Ukrainian (коментарі, логи, змінні)
- **Форматування:** 4 пробіли, без табів
- **Макс. довжина рядка:** 100 символів
- **Іменування:** `snake_case` для змінних, `PascalCase` для класів

### Типізація
- Використовуйте type hints для всіх функцій
```python
def get_client_config() -> ClientConfig:
    ...
```

### Документація
- Docstring для кожного публічного класу та функції
- Коментарі пояснюють «чому», а не «що»

### Тести
- Кожен новий модуль — мінімум 1 тест
- Покриття: `python -m pytest --cov=core tests/`

---

## Git-потік

```bash
# Створіть гілку для нової функції
git checkout -b feature/nazva-funktsiyi

# Комітьте часто
git add .
git commit -m "✨ додано новий генератор"

# Пуш та PR
git push origin feature/nazva-funktsiyi
```

### Назви комітів (Conventional Commits)

| Префікс | Значення |
|---|---|
| `feat:` | Нова функціональність |
| `fix:` | Виправлення багу |
| `docs:` | Документація |
| `refactor:` | Рефакторинг |
| `test:` | Додано/оновлено тести |
| `chore:` | Збірка, залежності |
| `🔥` | Видалення коду |

---

## Перевірка перед PR

```bash
# 1. Тести
cd core && python tests\run_tests.py

# 2. Лінтер
flake8 . --max-line-length=100

# 3. Імпорти
isort .

# 4. Збірка .exe
pyinstaller --clean CertifyPro.spec

# 5. Тест .exe
dist\CertifyPro.exe afina
```

---

## Архітектурні принципи

1. **DRY** — жодного дублювання коду
2. **SRP** — один клас = одна відповідальність
3. **DI** — залежності через DI-контейнер
4. **Конфігурація окремо** — `profiles.yaml`, не код
5. **Тести обов'язкові** — без тестів = немає функції

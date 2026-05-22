# Збірка та розгортання (Deployment)

## Швидка збірка .exe

```bash
cd C:\FINAL\CERTIFYPRO\core
pyinstaller CertifyPro.spec
```

Результат: `dist/CertifyPro.exe` (~70 MB)

---

## Повний цикл розгортання

### Крок 1: Підготовка середовища

```bash
# Створіть віртуальне середовище (опціонально)
python -m venv venv
venv\Scripts\activate

# Встановіть залежності
pip install -r C:\FINAL\CERTIFYPRO\requirements.txt
pip install pyinstaller
```

### Крок 2: Запуск тестів

```bash
cd C:\FINAL\CERTIFYPRO\core

# Unit-тести
python tests\run_tests.py

# E2E-тест
python tests\test_e2e_client_switching.py

# Тест мультиклієнтської конфігурації
python test_multi_client.py
```

**Очікуваний результат:** 28/28 тестів ✅

### Крок 3: Оновлення версії

Оновіть версію у трьох місцях:

1. `config.py`:
```python
VERSION = "3.0.0"
```

2. `pyproject.toml`:
```toml
version = "3.0.0"
```

3. `CHANGELOG.md` — додайте запис про нову версію

### Крок 4: Збірка .exe

```bash
cd C:\FINAL\CERTIFYPRO\core

# Очищення кешу
rmdir /s /q build dist 2>nul

# Збірка
pyinstaller --clean CertifyPro.spec
```

### Крок 5: Перевірка .exe

```bash
# Перевірка що .exe існує
dir dist\CertifyPro.exe

# Тест запуску (АФІНА)
dist\CertifyPro.exe afina

# Тест запуску (ДЖОНСОН)
dist\CertifyPro.exe johnson

# Тест GUI вибору клієнта
dist\CertifyPro.exe
```

### Крок 6: Створення архіву

```bash
cd C:\FINAL\CERTIFYPRO\core
python -c "import shutil; shutil.make_archive('CertifyPro_v3.0', 'zip', root_dir='dist', base_dir='.')"
```

Результат: `CertifyPro_v3.0.zip`

### Крок 7: Git-тег

```bash
git add .
git commit -m "🚀 Реліз v3.0.0"
git tag -a v3.0.0 -m "Реліз v3.0.0 — Мультиклієнтська архітектура"
git push origin main --tags
```

---

## Spec-файл: що включає

| Компонент | Джерело | Куди в .exe |
|---|---|---|
| Python-модулі | `core/*.py`, `gui/`, `services/`, `documents/`, `models/` | Вбудовано в .exe |
| `profiles.yaml` | `resources/profiles.yaml` | `_MEIPASS/resources/` |
| Шаблони `.docx` | `resources/templates/*.docx` | `_MEIPASS/resources/templates/` |
| БД АФІНА | `C:\FINAL\АФІНА\data\certify.db` | `_MEIPASS/data/АФІНА/` |
| БД ДЖОНСОН | `C:\FINAL\ДЖОНСОН\data\certify.db` | `_MEIPASS/data/ДЖОНСОН/` |

---

## Як працює розгортання БД

При першому запуску `.exe`:

1. PyInstaller розпаковує вміст у тимчасову папку `_MEIPASS`
2. `config.py` викликає `_deploy_databases()`
3. Для кожного клієнта (`АФІНА`, `ДЖОНСОН`):
   - Перевіряє чи існує `data/КЛІЄНТ/certify.db` поруч з `.exe`
   - Якщо не існує — копіює з `_MEIPASS/data/КЛІЄНТ/certify.db`
   - Створює папку `data/КЛІЄНТ/Documents/`
4. При наступних запусках БД **не перезаписується**

---

## Розгортання на сервері / мережевому диску

### Варіант A: Один .exe на кожному ПК

Скопіюйте `CertifyPro.exe` на кожен ПК. Кожен ПК має свою копію БД.

### Варіант B: Спільна БД на мережевому диску

1. Розмістіть `data/` на мережевому диску:
```
\\server\CertifyPro\data\
├── АФІНА\certify.db
└── ДЖОНСОН\certify.db
```

2. Оновіть `profiles.yaml`:
```yaml
clients:
  afina:
    data_dir: "\\\\server\\CertifyPro\\data\\АФІНА"
```

⚠️ **Обмеження:** SQLite не підтримує одночасний доступ з кількох ПК. Можливі блокування.

---

## CI/CD (автоматизація)

### Приклад GitHub Actions

```yaml
name: Build CertifyPro

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - run: pip install -r requirements.txt
      - run: cd core && python tests\run_tests.py
      - run: cd core && pyinstaller --clean CertifyPro.spec
      - uses: actions/upload-artifact@v4
        with:
          name: CertifyPro
          path: core/dist/CertifyPro.exe
```

---

## Моніторинг після розгортання

| Що перевіряти | Як |
|---|---|
| Логи | `logs/certifypro.log` — шукайте `ERROR`, `WARNING` |
| Розмір БД | `data/КЛІЄНТ/certify.db` — має зростати з використанням |
| Вільне місце | `data/КЛІЄНТ/Documents/` — може займати багато місця |
| Версія | Запустіть `.exe` — версія відображається у заголовку |

---

## Відкат на попередню версію

1. Зупиніть `.exe`
2. Зробіть бекап `data/`
3. Замініть `CertifyPro.exe` на попередню версію
4. Запустіть — БД підхопиться

# Інструкція з встановлення

## Системні вимоги

| Параметр | Мінімальні | Рекомендовані |
|---|---|---|
| ОС | Windows 10 | Windows 11 |
| RAM | 256 MB | 512 MB |
| Диск | 200 MB | 500 MB |
| Python | 3.13+ (для запуску з коду) | — |

---

## Варіант 1: Portable .exe (рекомендовано)

### Швидкий старт

1. Скопіюйте `CertifyPro.exe` у будь-яку папку
2. Запустіть подвійним кліком
3. При першому запуску програма автоматично створить:
   - `data/АФІНА/certify.db` — база даних АФІНА
   - `data/ДЖОНСОН/certify.db` — база даних ДЖОНСОН
   - `data/.../Documents/` — папки для документів
   - `logs/certifypro.log` — журнал

### Запуск

| Команда | Дія |
|---|---|
| `CertifyPro.exe` | GUI вибору клієнта |
| `CertifyPro.exe afina` | Відразу клієнт АФІНА |
| `CertifyPro.exe johnson` | Відразу клієнт ДЖОНСОН |

### Перенос на інший ПК

Просто скопіюйте `CertifyPro.exe` — все інше створиться автоматично.

Для збереження існуючих даних скопіюйте також папку `data/`.

---

## Варіант 2: Запуск з вихідного коду

### Крок 1: Встановлення Python

```bash
# Перевірте версію
python --version  # Потрібен Python 3.13+
```

Якщо Python не встановлено: https://www.python.org/downloads/

### Крок 2: Клонування / копіювання проекту

```bash
# Якщо є git-репозиторій
git clone <url> C:\FINAL\CERTIFYPRO

# Або скопіюйте папку C:\FINAL\CERTIFYPRO вручну
```

### Крок 3: Встановлення залежностей

```bash
# Основні залежності
pip install -r C:\FINAL\CERTIFYPRO\requirements.txt

# Залежності лаунчера
pip install -r C:\FINAL\client_launcher\requirements.txt
```

### Крок 4: Запуск

```bash
# Через лаунчер (вибір клієнта)
cd C:\FINAL
python -m client_launcher.launcher

# Або напряму
cd C:\FINAL\CERTIFYPRO
python core\main.py afina     # Клієнт АФІНА
python core\main.py johnson   # Клієнт ДЖОНСОН
```

---

## Варіант 3: Збірка .exe з коду

### Крок 1: Встановлення залежностей

```bash
pip install -r C:\FINAL\CERTIFYPRO\requirements.txt
pip install pyinstaller
```

### Крок 2: Збірка

```bash
cd C:\FINAL\CERTIFYPRO\core
pyinstaller CertifyPro.spec
```

### Крок 3: Результат

```
dist/CertifyPro.exe    ← 69.8 MB, готовий до розповсюдження
```

---

## Структура після встановлення

### .exe-версія

```
C:\Будь-яка_папка\
├── CertifyPro.exe          ← Програма (69.8 MB)
├── data\                   ← Створюється автоматично
│   ├── АФІНА\
│   │   ├── certify.db      ← База даних
│   │   └── Documents\      ← Згенеровані документи
│   └── ДЖОНСОН\
│       ├── certify.db
│       └── Documents\
└── logs\
    └── certifypro.log      ← Журнал роботи
```

### Версія з коду

```
C:\FINAL\
├── client_launcher\        ← Лаунчер вибору клієнта
│   ├── launcher.py
│   ├── applicants_db.py
│   └── ...
├── CERTIFYPRO\
│   ├── core\               ← Ядро системи
│   │   ├── main.py         ← Точка входу
│   │   ├── config.py       ← Конфігурація
│   │   ├── gui\            ← Інтерфейс
│   │   ├── documents\      ← Генерація документів
│   │   ├── services\       ← Бізнес-логіка
│   │   └── tests\          ← Тести
│   ├── resources\
│   │   ├── profiles.yaml   ← Профілі клієнтів
│   │   └── templates\      ← 25 шаблонів .docx
│   └── dist\
│       └── CertifyPro.exe  ← Зібраний .exe
├── АФІНА\data\certify.db   ← БД АФІНА
└── ДЖОНСОН\data\certify.db ← БД ДЖОНСОН
```

---

## Вирішення проблем

| Проблема | Рішення |
|---|---|
| `.exe` не запускається | Перевірте наявність антивіруса — може блокувати `.exe` без підпису |
| `ModuleNotFoundError` | Запустіть `pip install -r requirements.txt` |
| БД порожня | Видаліть `data/КЛІЄНТ/certify.db` і перезапустіть .exe — створиться заново |
| Шаблон не знайдено | Перевірте наявність файлів `resources/templates/*.docx` |
| Помилка кодування | Запустіть з консолі: `chcp 65001 && CertifyPro.exe` |

---

## Оновлення

### З v2.x на v3.0

1. Зробіть бекап `data/КЛІЄНТ/certify.db`
2. Замініть `CertifyPro.exe` на нову версію
3. Запустіть — БД підхопиться автоматично
4. Шаблони мають суфікси `_А` / `_Д` — переконайтесь що вони є

### З v1.x на v3.0

Повна заміна. Зробіть експорт даних зі старої версії перед оновленням.

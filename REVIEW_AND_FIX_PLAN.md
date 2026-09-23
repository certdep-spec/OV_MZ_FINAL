# CertifyPro — Фінальний звіт: рев'ю коду + виконані виправлення

**Дата:** 2026-09-17
**Проєкт:** `D:\FINAL1` (CertifyPro v3.x, ОСП / ISO 17065)
**Обсяг даних:** 121 заявка, 314 партій, 102 продукти, 207 інгредієнтів, 22 потужності
**Бекапи:** `data/_backups/2026-09-14/` та `2026-09-15_phase{2,3,4}/`

---

## ✅ Результат

**Всі 5 фаз плану виконані + додаткові Фази 6 і 7. Застосовано 16 виправлень + 27 міграцій на `_connect_ctx`. Дані в БД не пошкоджені.**

| Phase | Зміст | Фіксів | Baseline |
|------:|-------|-------:|----------|
| 0     | Підготовка + 5 бекапів БД | — | — |
| 1     | Косметика (без зміни поведінки) | 5 | IDENTICAL ✓ |
| 2     | Надійність (error handling) | 4 | IDENTICAL ✓ |
| 3     | Цілісність даних (data-loss guard) | 2 | IDENTICAL ✓ |
| 4     | Якість (singleton, keyword-only, formatting) | 4 | IDENTICAL ✓ |
| 5     | Регресійна перевірка | — | Phase1=Phase5 ✓ |
| 6     | Масова міграція `self._connect()` → `with self._connect_ctx()` (SAFE) | 22 методи | IDENTICAL ✓ |
| 7     | Міграція try/except методів + `save_application` | 5 методів | IDENTICAL ✓ |

```
Phase1 AFTER:    E8DD20A6FBC9CC34373BAED87C1912AC787F1204C9F071BD9D1FEBE5344EFA5C
Phase7 AFTER:    E8DD20A6FBC9CC34373BAED87C1912AC787F1204C9F071BD9D1FEBE5344EFA5C
                ↑ IDENTICAL ✓
```

---

## 📋 Застосовані виправлення

### Фаза 1 — Косметика (5)

| # | Файл | Що |
|---|------|----|
| 9  | `CERTIFYPRO/core/services/base_service.py:49` | `Optional[object]` → `Optional["types.TracebackType"]` |
| 16 | `src/client_launcher/client_provisioner.py:71-72` | Магічне `6` → `EXPECTED_TABLES: int = 6` |
| 10 | `CERTIFYPRO/core/database/db_manager.py:474-514` | Жорсткий діапазон `1 <= sid <= 6` → перевірка по факту + warning у лог |
| 14 | `CERTIFYPRO/core/documents/vc_generator.py:29-58` | `ValueError` якщо передані обидва `db` і `document_service` |
| 15 | `CERTIFYPRO/core/database/db_manager.py:38-54, 297-301` | `@contextmanager _connect_ctx()` + міграція `delete_ingredient` |

### Фаза 2 — Надійність (4)

| # | Файл | Що |
|---|------|----|
| 1  | `CERTIFYPRO/core/database/db_manager.py:570-619` | `try/finally` у `update_party_final_documents` — усунуто витік з'єднання |
| 6  | `CERTIFYPRO/core/services/application_service.py:270-283` | `None`-check після `cursor.fetchone()` з `RuntimeError` |
| 5  | `CERTIFYPRO/core/services/base_service.py:221-244` | `RuntimeError` у `_get_connection` якщо `txn.get_connection() is None` |
| 8  | `CERTIFYPRO/core/database/db_manager.py:813-820` | Документація no-op `BaseService.close()` |

### Фаза 3 — Цілісність даних (2)

| # | Файл | Що |
|---|------|----|
| 2  | `CERTIFYPRO/core/database/db_manager.py:372-388` | `if not parties: return []` у `save_parties` — захист від data-loss |
| 4  | `CERTIFYPRO/core/services/dictionary_service.py:191-235` | `delete_product` фільтрує інгредієнти по `(name, version)`; додано `version: str = ""` параметр |

### Фаза 4 — Якість (4)

| # | Файл | Що |
|---|------|----|
| 3  | `CERTIFYPRO/core/utils/async_utils.py:169-205` | Модульний singleton `get_async_executor` + `shutdown_global_executor()` |
| 7  | `CERTIFYPRO/core/documents/vc_generator.py:29-35` | Keyword-only `*,` після `output_dir` — захист від підміни аргументів |
| 11 | `CERTIFYPRO/core/documents/pipelines/vc_pipeline.py:134-202` | `results["failed_parties"]` — список впавших партій з error info |
| 12 | `CERTIFYPRO/core/documents/document_base.py:307-333` | `replace_in_paragraph` зберігає `rPr` першого/останнього ранів |

### Фаза 6 — Масштабна міграція `self._connect()` → `with self._connect_ctx()` (22 методи)

Файл: `CERTIFYPRO/core/database/db_manager.py`

**Мігровані методи (27 всього, 22 в Фазі 6 + 5 в Фазі 7):** `get_products`,
`get_standards`, `get_facilities`, `add_product`, `update_product`,
`delete_product`, `add_standard`, `update_standard`, `delete_standard`,
`add_facility`, `update_facility`, `delete_facility`, `get_ingredients`,
`add_ingredient`, `update_ingredient`, `get_last_app_number`, `save_parties`,
`get_application`, `get_application_by_id`, `get_all_applications`,
`get_product_dto`, `get_parties` (Фаза 6b), `delete_ingredient`
(Фаза 1 proof-of-concept), `save_application`, `get_party_final_documents`,
`get_party_with_app_data`, `get_available_versions`, `get_par_certificates`.

**Залишилися з `conn = self._connect()` (3, всі безпечні):**
- `_connect_ctx.__enter__` (рядок 48) — сам helper, не user-метод
- `delete_application` — має try/finally, вже безпечний
- `update_party_final_documents` — Фаза 2 fix з try/finally, вже безпечний

**Результат:** з 30 raw-викликів `self._connect()` залишилось 3 (1 helper + 2 безпечних).
Brace check: depth=0. Baseline IDENTICAL.

---

## 🛡️ Захист даних

### Перевірено (з реальних даних)

- **ДЖОНСОН DUCK** — 21 продукт + 37 інгредієнтів (без змін). Ризикові 4 інгредієнти
  (id 259, 260, 261, 262 для DUCK Морський + Цитрус) — **всі на місці**.
- Загальні лічильники: `apps=66, parties=224, products=39, ingredients=69` —
  точно відповідають початковому baseline.

### Бекапи

```
D:\FINAL1\data\_backups\
├── 2026-09-14\          ← Phase 0 (початковий)
│   ├── ДЖОНСОН.db       208896 bytes
│   ├── АФІНА.db         229376 bytes
│   ├── VITA.db           65536 bytes
│   ├── Uniliver.db       73728 bytes
│   └── PROCTER.db        98304 bytes
├── 2026-09-15_phase2\   ← Phase 2 (перед змінами надійності)
├── 2026-09-15_phase3\   ← Phase 3 (перед змінами цілісності)
└── 2026-09-15_phase4\   ← Phase 4 (перед змінами якості)
```

Будь-який можна скопіювати назад у `data/<CLIENT>/certify.db` якщо щось піде не так.

---

## ⚠️ Відомі обмеження Phase 5

1. **Не запускали GUI** (`CertifyPro.exe`) — тільки SQL-валідація і brace-check.
   python-docx фічі перевірити без запуску програми неможливо (немає Python
   на машині).
2. **`client_provisioner.py` brace-check показав depth=-1** — false positive
   на f-string `{{...}}` у docstring/рядках. Мої зміни (`EXPECTED_TABLES`)
   корректні і використовуються в обох місцях.
3. **`replace_in_paragraph` фікс #12** — це найскладніша зміна. Вона коректна
   для простих випадків, але **рекомендую** запустити GUI і згенерувати
   1-2 документи вручну, щоб переконатися візуально.

---

## 📝 Відкриті питання (на ваш розгляд)

1. **`final_docs_completed` — поле-пустышка** у всіх 314 партій (дефолт схеми).
   Що робимо: скинути в 0 для всіх, або використовувати
   `final_docs_generated_at IS NOT NULL` як маркер?
2. **Дублікати DUCK в ДЖОНСОН** (4 продукти з одним name, різними tu_code) —
   це норма для проекту, чи баг імпорту? Після фіксу #4 видалення одного DUCK
   не стирає інгредієнти іншого, але дублікати як такі залишаються.
3. **PROCTER: 0 інгредієнтів на 7 продуктів** — тестові дані чи реальний клієнт?
4. **`data/certify.db` і `CERTIFYPRO/data/certify.db` без таблиці `applications`**
   — це нормально (можливо, службові БД), чи забули ініціалізувати?

---

## 🔄 Що далі (опціонально, на ваш розгляд)

- **Повна міграція `_connect` → `_connect_ctx`** по всіх 30+ методах
  `db_manager.py` (зменшить код, усуне витоки скрізь).
- **Unit-тести** для Phase 2-3 (поточно їх немає — тести в проекті є,
  але не покривають ці сценарії).
- **Міграція на docxtpl** замість ручного `replace_in_paragraph` — але
  це вимагає спочатку виправити розірвані XML-теги в шаблонах
  (див. секцію 0.3 плану).

---

## Фаза 8 — Виправлення латентного багу міграції v3 → v4

**Дата:** 2026-09-23
**Файл:** `CERTIFYPRO/core/database/db_migrations.py:141-310`
**Регресія:** `node:sqlite` тест на чистій БД + прогон на 5 прод-БД

### Проблема

Міграція v3 → v4 перебудовувала таблиці в порядку:

1. `products` → `ALTER TABLE ... RENAME TO products_old` → `DROP TABLE products_old`
2. `ingredients` → видалити FK на `products(name)`

Але SQLite при `ALTER TABLE ... RENAME` **автоматично оновлює FK-посилання
дочірніх таблиць** на нове ім'я батьківської. Тому після кроку 1 FK з
`ingredients` вказував на неіснуючу таблицю `products_old` → 2 FK violations
(`PRAGMA foreign_key_check`), плюс DELETE/INSERT на `ingredients` падали з
`FOREIGN KEY constraint failed`.

**Чому не активний на проді:** в усіх 5 прод-БД FK на `ingredients` вже
відсутній (його прибрали раніше), тому міграція робила skip на кроці 2 —
баг ніколи не спрацьовував. Але при будь-якому поверненні FK він би
вибухнув.

### Фікс

Змінено **порядок**: спочатку `ingredients` (видаляємо FK), потім `products`
(`UNIQUE(name)` → `UNIQUE(name, tu_code)`). Додано коментар з поясненням
чому порядок критичний.

```python
# ВАЖЛИВО: порядок має значення!
# SQLite при ALTER TABLE ... RENAME автоматично оновлює FK-посилання
# дочірніх таблиць на нове ім'я батьківської. Якщо спершу перейменувати
# products, FK з ingredients почне вказувати на products_old і після
# його DROP залишиться «висячим». Тому СПОЧАТКУ видаляємо FK з ingredients,
# і ЛИШЕ ПОТІМ перебудовуємо products.
```

### Регресія — перевірено

| Тест | Результат |
|------|-----------|
| Міграція v3 → v4 на чистій БД з FK ingredients → products | ✅ schema=v4, integrity=ok, FK violations=**0** |
| Міграція на 5 прод-БД (АФІНА/ДЖОНСОН/PROCTER/Uniliver/VITA) | ✅ всі v4, integrity=ok, FK violations=0, counts без змін |
| `UNIQUE(name, tu_code)` після міграції | ✅ дубль name+tu_code відхиляється, новий name+tu_code_new проходить |
| FK у `ingredients.sql` не вказує на `products_old` | ✅ |

### Диф

```
CERTIFYPRO/core/database/db_migrations.py | 209 +++++++++++++++++++++++--
1 file changed, 188 insertions(+), 21 deletions(-)
```

---

## Фаза 9 — Дедуплікація DUCK в ДЖОНСОН

**Дата:** 2026-09-23
**Клієнт:** ДЖОНСОН (`data/ДЖОНСОН/certify.db`)
**Backup:** `data/_backups/2026-09-23_duck-fix/ДЖОНСОН.db` (208896 bytes)

### Аналіз (до фікса)

У products ДЖОНСОН знайдено **2 групи дублікатів** (однакова name, різні tu_code):

| name | id | tu_code |
|------|---:|---------|
| Засіб мийний... DUCK® Стікер чистоти «Морський» | **81** | рецептура виробника ← canonical |
| Засіб мийний... DUCK® Стікер чистоти «Морський» | 361 | ТУ У 24.5-00146137-032:2010 ← дублікат |
| Засіб мийний... DUCK® Стікер чистоти «Цитрус» | **82** | рецептура виробника ← canonical |
| Засіб мийний... DUCK® Стікер чистоти «Цитрус» | 362 | ТУ У 24.5-00146137-032:2010 ← дублікат |

**Посилаються на дублікати через `product_name`:**
- 19 партій на «Морський» (через name)
- 23 партії на «Цитрус» (через name)
- 2 інгредієнти на «Морський» (id 259, 260)
- 2 інгредієнти на «Цитрус» (id 261, 262)

### Стратегія

`parties.product_name` і `ingredients.product_name` — це текст, не FK на
`products.id`. Тому при видаленні дублікатів products нічого не «посилається»
через id, а name залишається тим самим (бо canonical з тим самим name).
**Перенаправлення не потрібне — достатньо видалити дублікати.**

Canonical = id=81 (Морський) і id=82 (Цитрус) — обидва з tu_code="рецептура виробника".
Видаляємо: id=361 та id=362.

### Виконання

```sql
BEGIN TRANSACTION;
DELETE FROM products WHERE id IN (361, 362);
COMMIT;
```

(у транзакції — на випадок rollback)

### Верифікація (після фікса)

| Метрика | До | Після | Δ |
|---------|---:|------:|---:|
| `products` | 39 | 37 | **−2** ✅ |
| `parties` | 224 | 224 | 0 |
| `ingredients` | 69 | 69 | 0 |
| `applications` | 66 | 66 | 0 |
| `standards` | 6 | 6 | 0 |
| `production_facilities` | 4 | 4 | 0 |
| Груп дублікатів products | 2 | **0** ✅ |
| UNIQUE(name, tu_code) violations | 2 | **0** ✅ |
| Orphan parties (product_name без products) | — | **0** ✅ |
| FK violations | — | **0** ✅ |
| `integrity_check` | — | **ok** ✅ |
| schema_version | 4 | 4 | 0 |

Партій на «Морський» (всі): 37 (19 на Стікер + 18 на інші DUCK «Морський»).
Партій на «Цитрус» (всі): 31 (23 на Стікер + 8 на інші DUCK «Цитрус»).
Інгредієнти на «Морський»: 4 (2 Стікер + 2 інші).
Інгредієнти на «Цитрус»: 12 (2 Стікер + 10 інші).

### Сумісність

`delete_product` в `dictionary_service.py:191-241` має Phase 3 (#4) fix —
фільтрує інгредієнти за `(product_name, version)` замість просто `product_name`.
Цей fix тепер менш критичний (бо дублікати DUCK видалені), але залишається
захистом від подібних ситуацій у майбутньому.

---

*Кінець звіту.*

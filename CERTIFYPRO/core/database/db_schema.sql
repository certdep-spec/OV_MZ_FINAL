-- ============================================================================
-- CertifyPro — Схема базы данных SQLite
-- Версия: 3.0.0
-- Назначение: Единый источник истины для инициализации БД клиентов
-- ============================================================================
-- Использование:
--   1. Программно: прочитать файл и выполнить через sqlite3.execute()
--   2. Вручную: sqlite3 certify.db < db_schema.sql
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. products — Довідник продукції
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    tu_code TEXT,
    shelf_life_months INTEGER DEFAULT 36,
    dkpp_code TEXT DEFAULT '20.41.32-50.00',
    uktzed_code TEXT DEFAULT '3402',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 2. standards — Довідник стандартів (НД)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS standards (
    id INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    active INTEGER DEFAULT 1
);

-- ----------------------------------------------------------------------------
-- 3. applications — Заявки
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_number TEXT NOT NULL UNIQUE,
    app_date TEXT NOT NULL,
    company_name TEXT,
    company_code TEXT,
    company_address TEXT,
    director_name TEXT,
    tu_code TEXT,
    production_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 4. parties — Партії (связана с applications)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS parties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    party_number INTEGER,
    product_name TEXT NOT NULL,
    party_code TEXT,
    party_date TEXT,
    mfg_date TEXT,
    quantity REAL,
    unit TEXT DEFAULT 'шт',
    protocol_number TEXT,
    protocol_date TEXT,
    cert_number TEXT,
    cert_date TEXT,
    shelf_life_months INTEGER,
    standards_data TEXT,
    final_docs_completed INTEGER DEFAULT 0,
    final_docs_generated_at TIMESTAMP,
    version TEXT,
    is_import INTEGER DEFAULT 0,
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 5. ingredients — Склад продукції
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    version TEXT,
    chemical_name TEXT,
    trade_mark TEXT,
    cas_number TEXT,
    certificate TEXT,
    FOREIGN KEY (product_name) REFERENCES products(name),
    UNIQUE(product_name, version, chemical_name)
);

-- ----------------------------------------------------------------------------
-- 6. production_facilities — Виробничі потужності
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS production_facilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    address TEXT UNIQUE NOT NULL,
    company_name TEXT
);

-- ----------------------------------------------------------------------------
-- Индексы (опционально, для производительности)
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_parties_application_id ON parties(application_id);
CREATE INDEX IF NOT EXISTS idx_ingredients_product_name ON ingredients(product_name);
CREATE INDEX IF NOT EXISTS idx_applications_app_number ON applications(app_number);

-- ----------------------------------------------------------------------------
-- 7. schema_version — Версия схемы БД (миграции)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

-- Если таблица пуста, устанавливаем базовую версию 3
INSERT INTO schema_version (version) 
SELECT 3 WHERE NOT EXISTS (SELECT 1 FROM schema_version);


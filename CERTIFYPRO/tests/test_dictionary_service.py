import unittest
import sqlite3
import os
import sys

# Додаємо шлях до core, щоб імпорти працювали
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))

from services.dictionary_service import DictionaryService
from models.dto import IngredientDTO

class TestDictionaryService(unittest.TestCase):
    def setUp(self):
        # БД в пам'яті
        self.db_path = ":memory:"
        self.service = DictionaryService(self.db_path)
        
        # Нам потрібно створити таблиці в ТІЙ ЖЕ БД, яку відкриває сервіс.
        # Оскільки :memory: у кожного підключення свій, ми підмінимо метод _get_connection
        self.test_conn = sqlite3.connect(':memory:')
        self.test_conn.row_factory = sqlite3.Row
        
        # Патчимо сервіс, щоб він використовував наше з'єднання
        from contextlib import contextmanager
        @contextmanager
        def mock_get_conn():
            yield self.test_conn
            
        self.service._get_connection = mock_get_conn
        
        # Створюємо необхідні таблиці з коректними іменами колонок з BaseService
        self.test_conn.execute(f"""
            CREATE TABLE {self.service.Tables.PRODUCTS} (
                {self.service.ProductColumns.ID} INTEGER PRIMARY KEY,
                {self.service.ProductColumns.NAME} TEXT NOT NULL
            )
        """)
        self.test_conn.execute(f"""
            CREATE TABLE {self.service.Tables.INGREDIENTS} (
                {self.service.IngredientColumns.ID} INTEGER PRIMARY KEY,
                {self.service.IngredientColumns.PRODUCT_NAME} TEXT,
                {self.service.IngredientColumns.VERSION} TEXT,
                {self.service.IngredientColumns.CERTIFICATE} TEXT
            )
        """)

    def tearDown(self):
        self.test_conn.close()

    def test_version_normalization(self):
        p_name = 'Test Product'
        self.test_conn.execute(f"INSERT INTO {self.service.Tables.PRODUCTS} ({self.service.ProductColumns.NAME}) VALUES (?)", (p_name,))
        self.test_conn.execute(f"INSERT INTO {self.service.Tables.INGREDIENTS} ({self.service.IngredientColumns.PRODUCT_NAME}, {self.service.IngredientColumns.VERSION}, {self.service.IngredientColumns.CERTIFICATE}) VALUES (?, ?, ?)",
                         (p_name, 'A', 'CERT_A'))
        
        # Латинська A
        res = self.service.get_par_certificates(p_name, 'A')
        self.assertEqual(res, 'CERT_A')
        
        # Кириллична А
        res = self.service.get_par_certificates(p_name, 'А')
        self.assertEqual(res, 'CERT_A')

    def test_filtering_by_version(self):
        p_name = 'Liquid Soap'
        self.test_conn.execute(f"INSERT INTO {self.service.Tables.PRODUCTS} ({self.service.ProductColumns.NAME}) VALUES (?)", (p_name,))
        self.test_conn.execute(f"INSERT INTO {self.service.Tables.INGREDIENTS} ({self.service.IngredientColumns.PRODUCT_NAME}, {self.service.IngredientColumns.VERSION}, {self.service.IngredientColumns.CERTIFICATE}) VALUES (?, ?, ?)",
                         (p_name, 'A', 'CERT_1'))
        self.test_conn.execute(f"INSERT INTO {self.service.Tables.INGREDIENTS} ({self.service.IngredientColumns.PRODUCT_NAME}, {self.service.IngredientColumns.VERSION}, {self.service.IngredientColumns.CERTIFICATE}) VALUES (?, ?, ?)",
                         (p_name, 'A', 'CERT_2'))
        self.test_conn.execute(f"INSERT INTO {self.service.Tables.INGREDIENTS} ({self.service.IngredientColumns.PRODUCT_NAME}, {self.service.IngredientColumns.VERSION}, {self.service.IngredientColumns.CERTIFICATE}) VALUES (?, ?, ?)",
                         (p_name, 'B', 'CERT_3'))

        # Перевірка версії A
        res_a = self.service.get_par_certificates(p_name, 'A')
        self.assertIn('CERT_1', res_a)
        self.assertIn('CERT_2', res_a)
        self.assertNotIn('CERT_3', res_a)

    def test_empty_version_returns_nothing(self):
        p_name = 'Product'
        self.test_conn.execute(f"INSERT INTO {self.service.Tables.PRODUCTS} ({self.service.ProductColumns.NAME}) VALUES (?)", (p_name,))
        self.test_conn.execute(f"INSERT INTO {self.service.Tables.INGREDIENTS} ({self.service.IngredientColumns.PRODUCT_NAME}, {self.service.IngredientColumns.VERSION}, {self.service.IngredientColumns.CERTIFICATE}) VALUES (?, ?, ?)",
                         (p_name, 'A', 'CERT_A'))
        
        # Якщо версія не вказана, має повернути порожній рядок
        res = self.service.get_par_certificates(p_name, '')
        self.assertEqual(res, '')

    def test_robust_product_matching(self):
        # Перевірка ігнорування регістру та пробілів у назві продукту
        p_name_db = '  My Product  '
        self.test_conn.execute(f"INSERT INTO {self.service.Tables.PRODUCTS} ({self.service.ProductColumns.NAME}) VALUES (?)", (p_name_db,))
        self.test_conn.execute(f"INSERT INTO {self.service.Tables.INGREDIENTS} ({self.service.IngredientColumns.PRODUCT_NAME}, {self.service.IngredientColumns.VERSION}, {self.service.IngredientColumns.CERTIFICATE}) VALUES (?, ?, ?)",
                         (p_name_db, 'A', 'CERT_OK'))
        
        # Шукаємо без пробілів та в іншому регістрі
        res = self.service.get_par_certificates('my product', 'A')
        self.assertEqual(res, 'CERT_OK')

if __name__ == '__main__':
    unittest.main()

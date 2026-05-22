"""
Модуль власних виключень для CertifyPro v2.

Ієрархія виключень:
- CertifyProError (базове)
  - ValidationError (помилки валідації даних)
  - DatabaseError (помилки роботи з БД)
  - TemplateNotFoundError (шаблон не знайдено)
  - DocumentGenerationError (помилки генерації документів)
  - ConfigurationError (помилки конфігурації)
  - ImportError (помилки імпорту/експорту даних)
"""


class CertifyProError(Exception):
    """Базовий клас виключень для CertifyPro."""


class ValidationError(CertifyProError):
    """Виключення при помилках валідації даних."""


class DatabaseError(CertifyProError):
    """Виключення при помилках роботи з базою даних."""


class TemplateNotFoundError(CertifyProError):
    """Виключення коли шаблон документу не знайдено."""


class DocumentGenerationError(CertifyProError):
    """Виключення при помилках генерації документів."""


class ConfigurationError(CertifyProError):
    """Виключення при помилках конфігурації."""


class DataImportError(CertifyProError):
    """Виключення при помилках імпорту/експорту даних."""

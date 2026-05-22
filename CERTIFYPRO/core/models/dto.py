"""
DTO моделі для CertifyPro
Data Transfer Objects - об'єкти для передачі даних між шарами
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from exceptions import ValidationError


def _validate_required_str(value: str, field_name: str) -> None:
    """Перевірити що рядок не порожній"""
    if not value or not value.strip():
        raise ValidationError(f"Поле '{field_name}' не може бути порожнім")


def _validate_positive_int(value: int, field_name: str) -> None:
    """Перевірити що ціле число позитивне"""
    if value <= 0:
        raise ValidationError(f"Поле '{field_name}' повинно бути позитивним числом")


@dataclass
class ProductDTO:
    """Модель продукції"""

    name: str
    tu_code: str = ""
    shelf_life_months: int = 36
    dkpp_code: str = "20.41.32-50.00"
    uktzed_code: str = "3402"
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Валідація при створенні об'єкта"""
        if not self.name or not self.name.strip():
            raise ValidationError("Назва продукції не може бути порожньою")
        if self.shelf_life_months <= 0:
            raise ValidationError("Термін зберігання повинен бути позитивним")


@dataclass
class StandardDTO:
    """Модель стандарту НД"""

    id: int
    description: str
    active: bool = True

    def __post_init__(self):
        """Валідація при створенні об'єкта"""
        if self.id <= 0:
            raise ValidationError("ID стандарту повинен бути позитивним числом")
        if not self.description or not self.description.strip():
            raise ValidationError("Опис стандарту не може бути порожнім")


@dataclass
class ProductionFacilityDTO:
    """Модель виробничої потужності"""

    address: str
    company_name: str = ""
    id: Optional[int] = None

    def __post_init__(self):
        """Валідація при створенні об'єкта"""
        if not self.address or not self.address.strip():
            raise ValidationError("Адреса виробництва не може бути порожньою")


@dataclass
class IngredientDTO:
    """Модель інгредієнту (склад продукції)"""

    product_name: str
    chemical_name: str = ""
    trade_mark: str = ""
    cas_number: str = ""
    certificate: str = ""
    version: str = ""
    id: Optional[int] = None

    def __post_init__(self):
        """Валідація при створенні об'єкта"""
        if not self.product_name or not self.product_name.strip():
            raise ValidationError(
                "Назва продукту для інгредієнта не може бути порожньою"
            )
        if self.chemical_name and not self.chemical_name.strip():
            raise ValidationError("Хімічна назва не може бути порожньою, якщо вказана")


@dataclass
class PartyDTO:
    """Модель партії продукції"""

    product_name: str
    party_code: str = ""
    party_date: str = ""
    mfg_date: str = ""
    quantity: float = 0.0
    unit: str = "шт"
    shelf_life_months: int = 36
    standards: List[int] = field(default_factory=list)
    protocol_number: str = ""
    protocol_date: str = ""
    cert_number: str = ""
    cert_date: str = ""
    party_number: int = 0
    version: str = ""
    is_import: bool = False
    id: Optional[int] = None
    app_id: Optional[int] = None
    final_docs_completed: bool = False
    final_docs_generated_at: Optional[datetime] = None

    def __post_init__(self):
        """Валідація при створенні об'єкта"""
        if not self.product_name or not self.product_name.strip():
            raise ValidationError("Назва продукції партії не може бути порожньою")
        if self.shelf_life_months <= 0:
            raise ValidationError("Термін зберігання повинен бути позитивним")
        # Перевірка та приведення standards до списку int
        if self.standards:
            try:
                self.standards = [int(s) for s in self.standards]
            except (ValueError, TypeError):
                raise ValidationError(
                    "Список стандартів повинен містити тільки цілі числа"
                )


@dataclass
class ApplicationDTO:
    """Модель заявки"""

    app_number: str
    app_date: str
    company_name: str = ""
    company_code: str = ""
    company_address: str = ""
    director_name: str = ""
    tu_code: str = ""
    production_address: str = ""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    parties: List[PartyDTO] = field(default_factory=list)

    def __post_init__(self):
        """Валідація при створенні об'єкта"""
        _validate_required_str(self.app_number, "номер заявки")
        _validate_required_str(self.app_date, "дата заявки")
        # Простий перевірка формату дати DD.MM.YYYY
        try:
            datetime.strptime(self.app_date, "%d.%m.%Y")
        except ValueError:
            raise ValidationError(
                "Неправильний формат дати заявки. Використовуйте DD.MM.YYYY"
            )


@dataclass
class ImportStatsDTO:
    """Статистика імпорту з Excel"""

    products: int = 0
    standards: int = 0
    facilities: int = 0
    ingredients: int = 0
    applications: int = 0
    parties: int = 0
    errors: int = 0


@dataclass
class FinalDocumentsDTO:
    """Модель фінальних документів партії"""

    protocol_number: str = ""
    protocol_date: str = ""
    cert_number: str = ""
    cert_date: str = ""
    completed: bool = False
    generated_at: Optional[datetime] = None


@dataclass
class DocumentContextDTO:
    """Контекст для генерації документів"""

    application: ApplicationDTO
    parties: List[PartyDTO]
    products: Dict[str, List[IngredientDTO]] = field(default_factory=dict)
    standards_text: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """Валідація контексту"""
        if not isinstance(self.application, ApplicationDTO):
            raise ValidationError("application має бути ApplicationDTO")
        if not isinstance(self.parties, list):
            raise ValidationError("parties має бути списком")

    def get_ingredients_for_product(
        self, product_name: str, version: Optional[str] = None
    ) -> List[IngredientDTO]:
        """Отримати інгредієнти для продукту з фільтрацією за версією"""
        ingredients = self.products.get(product_name, [])
        if version:
            from utils.version_normalizer import normalize_version
            normalized_filter = normalize_version(version)
            ingredients = [
                ing for ing in ingredients 
                if normalize_version(ing.version) == normalized_filter
            ]
        return ingredients

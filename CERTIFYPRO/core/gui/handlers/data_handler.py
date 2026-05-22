import logging
from typing import Dict, List

from models.dto import ApplicationDTO, PartyDTO

logger = logging.getLogger(__name__)


class DataPersistenceHandler:
    """Хендлер для перетворення даних та взаємодії з сервісами БД."""

    def __init__(self, window):
        self.window = window
        self.app_service = window.app_service

    def save_all(self, app_data: Dict, parties: List[Dict]) -> Dict:
        """Атомарне збереження заявки та партій"""
        party_dtos = [self._dict_to_party_dto(p, i + 1) for i, p in enumerate(parties)]

        app_dto = ApplicationDTO(
            id=app_data.get("id"),
            app_number=str(app_data["app_number"]),
            app_date=app_data["app_date"],
            company_name=app_data.get("company_name", ""),
            company_code=app_data.get("company_code", ""),
            company_address=app_data.get("company_address", ""),
            director_name=app_data.get("director_name", ""),
            tu_code=app_data.get("tu_code", ""),
            production_address=app_data.get("production_address", ""),
        )

        app_id, party_ids = self.app_service.save_application_with_parties(
            app_dto, party_dtos
        )

        # Оновлюємо ID в пам'яті, щоб наступні операції бачили актуальні ID
        for party, db_id in zip(parties, party_ids):
            party["id"] = db_id
            


        return {"app_id": app_id, "party_ids": party_ids}

    def _dict_to_party_dto(self, party_dict: Dict, number: int) -> PartyDTO:
        """Конвертація словника UI у DTO"""
        # Логіка вилучення ID стандартів
        standards_ids = []
        if "standards" in party_dict:
            for s in party_dict["standards"]:
                if isinstance(s, dict) and "id" in s:
                    standards_ids.append(s["id"])
                elif isinstance(s, (int, str)):
                    standards_ids.append(int(s))

        return PartyDTO(
            id=party_dict.get("id"),
            app_id=party_dict.get("app_id"),
            party_number=number,
            product_name=party_dict.get("product_name", ""),
            party_code=party_dict.get("party_code", party_dict.get("code", "")),
            party_date=party_dict.get("party_date", ""),
            mfg_date=party_dict.get("mfg_date", ""),
            quantity=float(party_dict.get("quantity", 0) or 0),
            unit=party_dict.get("unit", "шт"),
            shelf_life_months=party_dict.get("shelf_life_months", 36),
            standards=standards_ids,
            protocol_number=party_dict.get("protocol_number", ""),
            protocol_date=party_dict.get("protocol_date", ""),
            cert_number=party_dict.get("cert_number", ""),
            cert_date=party_dict.get("cert_date", ""),
            version=party_dict.get("version", ""),
        )

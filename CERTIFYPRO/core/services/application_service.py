"""
Сервіс управління заявками
"""

import json
import logging
from typing import Any, List, Optional

from models.dto import ApplicationDTO, FinalDocumentsDTO, PartyDTO

from .base_service import BaseService

logger = logging.getLogger(__name__)


class ApplicationService(BaseService):
    """Сервіс для роботи з заявками та партіями"""

    # ===== ЗАЯВКИ =====

    def get_last_app_number(self) -> str:
        """Отримати останній номер заявки"""
        row = self._execute_query(
            f"SELECT {self.AppColumns.APP_NUMBER} FROM {self.Tables.APPLICATIONS} WHERE {self.AppColumns.ID} = (SELECT MAX({self.AppColumns.ID}) FROM {self.Tables.APPLICATIONS})"
        )
        return row[0][self.AppColumns.APP_NUMBER] if row else "001"

    def get_application_by_number(self, app_number: str) -> Optional[ApplicationDTO]:
        """Отримати заявку за номером"""
        rows = self._execute_query(
            f"SELECT * FROM {self.Tables.APPLICATIONS} WHERE {self.AppColumns.APP_NUMBER} = ?",
            (app_number,),
        )
        if not rows:
            return None
        row = rows[0]
        return self._row_to_application(row)

    def get_application_by_id(self, app_id: int) -> Optional[ApplicationDTO]:
        """Отримати заявку за ID"""
        rows = self._execute_query(
            f"SELECT * FROM {self.Tables.APPLICATIONS} WHERE {self.AppColumns.ID} = ?",
            (app_id,),
        )
        if not rows:
            return None
        row = rows[0]
        app = self._row_to_application(row)
        # Завантажити партії
        app.parties = self.get_parties_for_application(app_id)
        return app

    def get_all_applications(self) -> List[ApplicationDTO]:
        """Отримати всі заявки"""
        rows = self._execute_query(
            f"SELECT * FROM {self.Tables.APPLICATIONS} ORDER BY {self.AppColumns.CREATED_AT} DESC"
        )
        return [self._row_to_application(row) for row in rows]

    def save_application(self, application: ApplicationDTO) -> int:
        """Зберегти заявку (upsert з поверненням ID)"""
        if application.id:
            self._execute_command(
                f"""UPDATE {self.Tables.APPLICATIONS} SET
                    {self.AppColumns.APP_NUMBER}           = ?,
                    {self.AppColumns.APP_DATE}             = ?,
                    {self.AppColumns.COMPANY_NAME}         = ?,
                    {self.AppColumns.COMPANY_CODE}         = ?,
                    {self.AppColumns.COMPANY_ADDRESS}      = ?,
                    {self.AppColumns.DIRECTOR_NAME}        = ?,
                    {self.AppColumns.TU_CODE}              = ?,
                    {self.AppColumns.PRODUCTION_ADDRESS}   = ?,
                    {self.AppColumns.UPDATED_AT}           = CURRENT_TIMESTAMP
                WHERE {self.AppColumns.ID} = ?""",
                (
                    application.app_number,
                    application.app_date,
                    application.company_name,
                    application.company_code,
                    application.company_address,
                    application.director_name,
                    application.tu_code,
                    application.production_address,
                    application.id,
                ),
            )
            return application.id

        rows = self._execute_query(
            f"""INSERT INTO {self.Tables.APPLICATIONS}
            ({self.AppColumns.APP_NUMBER}, {self.AppColumns.APP_DATE}, {self.AppColumns.COMPANY_NAME}, {self.AppColumns.COMPANY_CODE}, {self.AppColumns.COMPANY_ADDRESS},
             {self.AppColumns.DIRECTOR_NAME}, {self.AppColumns.TU_CODE}, {self.AppColumns.PRODUCTION_ADDRESS})
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT({self.AppColumns.APP_NUMBER}) DO UPDATE SET
                {self.AppColumns.APP_DATE}             = excluded.{self.AppColumns.APP_DATE},
                {self.AppColumns.COMPANY_NAME}         = excluded.{self.AppColumns.COMPANY_NAME},
                {self.AppColumns.COMPANY_CODE}         = excluded.{self.AppColumns.COMPANY_CODE},
                {self.AppColumns.COMPANY_ADDRESS}      = excluded.{self.AppColumns.COMPANY_ADDRESS},
                {self.AppColumns.DIRECTOR_NAME}        = excluded.{self.AppColumns.DIRECTOR_NAME},
                {self.AppColumns.TU_CODE}              = excluded.{self.AppColumns.TU_CODE},
                {self.AppColumns.PRODUCTION_ADDRESS}   = excluded.{self.AppColumns.PRODUCTION_ADDRESS},
                {self.AppColumns.UPDATED_AT}           = CURRENT_TIMESTAMP
            RETURNING {self.AppColumns.ID}""",
            (
                application.app_number,
                application.app_date,
                application.company_name,
                application.company_code,
                application.company_address,
                application.director_name,
                application.tu_code,
                application.production_address,
            ),
        )
        app_id = rows[0][self.AppColumns.ID] if rows else 0
        logger.info(
            f"Заявку {application.app_number} збережено/оновлено (RETURNING), ID={app_id}"
        )
        return app_id

    def delete_application(self, app_id: int) -> bool:
        """Видалити заявку та всі її партії (Cascade через foreign keys)"""
        self._execute_command(
            f"DELETE FROM {self.Tables.APPLICATIONS} WHERE {self.AppColumns.ID} = ?",
            (app_id,),
        )
        logger.info(f"Заявку ID={app_id} видалено")
        return True

    def _row_to_application(self, row: Any) -> ApplicationDTO:
        """Конвертувати рядок БД в ApplicationDTO"""
        return ApplicationDTO(
            id=self._get_value(row, self.AppColumns.ID),
            app_number=self._get_value(row, self.AppColumns.APP_NUMBER),
            app_date=self._get_value(row, self.AppColumns.APP_DATE),
            company_name=self._get_value(row, self.AppColumns.COMPANY_NAME, ""),
            company_code=self._get_value(row, self.AppColumns.COMPANY_CODE, ""),
            company_address=self._get_value(row, self.AppColumns.COMPANY_ADDRESS, ""),
            director_name=self._get_value(row, self.AppColumns.DIRECTOR_NAME, ""),
            tu_code=self._get_value(row, self.AppColumns.TU_CODE, ""),
            production_address=self._get_value(
                row, self.AppColumns.PRODUCTION_ADDRESS, ""
            ),
            created_at=self._get_value(row, self.AppColumns.CREATED_AT),
            updated_at=self._get_value(row, self.AppColumns.UPDATED_AT),
            parties=[],
        )

    # ===== ПАРТІЇ =====

    def get_parties_for_application(self, app_id: int) -> List[PartyDTO]:
        """Отримати всі партії для заявки"""
        rows = self._execute_query(
            f"SELECT * FROM {self.Tables.PARTIES} WHERE {self.PartyColumns.APPLICATION_ID} = ? ORDER BY {self.PartyColumns.PARTY_NUMBER}",
            (app_id,),
        )
        return [self._row_to_party(row) for row in rows]

    def save_parties(self, app_id: int, parties: List[PartyDTO]) -> List[int]:
        """Зберегти партії для заявки"""
        party_ids: List[int] = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Видалити старі партії
            cursor.execute(
                f"DELETE FROM {self.Tables.PARTIES} WHERE {self.PartyColumns.APPLICATION_ID} = ?",
                (app_id,),
            )

            for party in parties:
                # Серіалізуємо стандарти у JSON
                standards_json = json.dumps(party.standards, ensure_ascii=False)

                cursor.execute(
                    f"""INSERT INTO {self.Tables.PARTIES}
                    ({self.PartyColumns.APPLICATION_ID}, {self.PartyColumns.PARTY_NUMBER}, {self.PartyColumns.PRODUCT_NAME}, {self.PartyColumns.PARTY_CODE}, {self.PartyColumns.PARTY_DATE},
                     {self.PartyColumns.MFG_DATE}, {self.PartyColumns.QUANTITY}, {self.PartyColumns.UNIT}, {self.PartyColumns.PROTOCOL_NUMBER}, {self.PartyColumns.PROTOCOL_DATE}, {self.PartyColumns.CERT_NUMBER}, {self.PartyColumns.CERT_DATE},
                     {self.PartyColumns.SHELF_LIFE_MONTHS}, {self.PartyColumns.STANDARDS_DATA}, {self.PartyColumns.VERSION}, {self.PartyColumns.IS_IMPORT})
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        app_id,
                        party.party_number,
                        party.product_name,
                        party.party_code,
                        party.party_date,
                        party.mfg_date,
                        party.quantity,
                        party.unit,
                        party.protocol_number,
                        party.protocol_date,
                        party.cert_number,
                        party.cert_date,
                        party.shelf_life_months,
                        standards_json,
                        party.version,
                        1 if party.is_import else 0,
                    ),
                )
                party_ids.append(cursor.lastrowid or 0)

            logger.info(f"Збережено {len(parties)} партій для заявки ID={app_id}")

        return party_ids

    def save_application_with_parties(
        self, application: ApplicationDTO, parties: List[PartyDTO]
    ) -> tuple[int, List[int]]:
        """Атомарне збереження заявки та всіх її партій в одній транзакції."""
        party_ids: List[int] = []
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Збереження заявки
            if application.id:
                cursor.execute(
                    f"""UPDATE {self.Tables.APPLICATIONS} SET
                        {self.AppColumns.APP_NUMBER}=?,
                        {self.AppColumns.APP_DATE}=?,
                        {self.AppColumns.COMPANY_NAME}=?,
                        {self.AppColumns.COMPANY_CODE}=?,
                        {self.AppColumns.COMPANY_ADDRESS}=?,
                        {self.AppColumns.DIRECTOR_NAME}=?,
                        {self.AppColumns.TU_CODE}=?,
                        {self.AppColumns.PRODUCTION_ADDRESS}=?,
                        {self.AppColumns.UPDATED_AT}=CURRENT_TIMESTAMP
                    WHERE {self.AppColumns.ID}=?""",
                    (
                        application.app_number,
                        application.app_date,
                        application.company_name,
                        application.company_code,
                        application.company_address,
                        application.director_name,
                        application.tu_code,
                        application.production_address,
                        application.id,
                    ),
                )
                app_id = application.id
            else:
                cursor.execute(
                    f"""INSERT INTO {self.Tables.APPLICATIONS}
                    ({self.AppColumns.APP_NUMBER}, {self.AppColumns.APP_DATE}, {self.AppColumns.COMPANY_NAME}, {self.AppColumns.COMPANY_CODE},
                     {self.AppColumns.COMPANY_ADDRESS}, {self.AppColumns.DIRECTOR_NAME}, {self.AppColumns.TU_CODE}, {self.AppColumns.PRODUCTION_ADDRESS}, {self.AppColumns.UPDATED_AT})
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT({self.AppColumns.APP_NUMBER}) DO UPDATE SET
                    {self.AppColumns.APP_DATE}=excluded.{self.AppColumns.APP_DATE},
                    {self.AppColumns.COMPANY_NAME}=excluded.{self.AppColumns.COMPANY_NAME},
                    {self.AppColumns.COMPANY_CODE}=excluded.{self.AppColumns.COMPANY_CODE},
                    {self.AppColumns.COMPANY_ADDRESS}=excluded.{self.AppColumns.COMPANY_ADDRESS},
                    {self.AppColumns.DIRECTOR_NAME}=excluded.{self.AppColumns.DIRECTOR_NAME},
                    {self.AppColumns.TU_CODE}=excluded.{self.AppColumns.TU_CODE},
                    {self.AppColumns.PRODUCTION_ADDRESS}=excluded.{self.AppColumns.PRODUCTION_ADDRESS},
                    {self.AppColumns.UPDATED_AT}=CURRENT_TIMESTAMP""",
                    (
                        application.app_number,
                        application.app_date,
                        application.company_name,
                        application.company_code,
                        application.company_address,
                        application.director_name,
                        application.tu_code,
                        application.production_address,
                    ),
                )

                cursor.execute(
                    f"SELECT {self.AppColumns.ID} FROM {self.Tables.APPLICATIONS} WHERE {self.AppColumns.APP_NUMBER} = ?",
                    (application.app_number,),
                )
                app_id = cursor.fetchone()[0]

            # 2. Видалення старих партій
            cursor.execute(
                f"DELETE FROM {self.Tables.PARTIES} WHERE {self.PartyColumns.APPLICATION_ID} = ?",
                (app_id,),
            )

            # 3. Збереження нових партій
            for party in parties:
                standards_json = json.dumps(party.standards, ensure_ascii=False)
                cursor.execute(
                    f"""INSERT INTO {self.Tables.PARTIES}
                    ({self.PartyColumns.APPLICATION_ID}, {self.PartyColumns.PARTY_NUMBER}, {self.PartyColumns.PRODUCT_NAME}, {self.PartyColumns.PARTY_CODE}, {self.PartyColumns.PARTY_DATE},
                     {self.PartyColumns.MFG_DATE}, {self.PartyColumns.QUANTITY}, {self.PartyColumns.UNIT}, {self.PartyColumns.PROTOCOL_NUMBER}, {self.PartyColumns.PROTOCOL_DATE}, {self.PartyColumns.CERT_NUMBER}, {self.PartyColumns.CERT_DATE},
                     {self.PartyColumns.SHELF_LIFE_MONTHS}, {self.PartyColumns.STANDARDS_DATA}, {self.PartyColumns.VERSION}, {self.PartyColumns.IS_IMPORT})
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        app_id,
                        party.party_number,
                        party.product_name,
                        party.party_code,
                        party.party_date,
                        party.mfg_date,
                        party.quantity,
                        party.unit,
                        party.protocol_number,
                        party.protocol_date,
                        party.cert_number,
                        party.cert_date,
                        party.shelf_life_months,
                        standards_json,
                        party.version,
                        1 if party.is_import else 0,
                    ),
                )
                party_ids.append(cursor.lastrowid or 0)

            logger.info(
                f"Атомарно збережено заявку {application.app_number} (ID={app_id}) та {len(parties)} партій"
            )
            return app_id, party_ids

    def _row_to_party(self, row: Any) -> PartyDTO:
        """Конвертувати рядок БД в PartyDTO"""
        # Розпаковуємо стандарти з JSON
        standards = []
        standards_data = self._get_value(row, self.PartyColumns.STANDARDS_DATA)
        if standards_data:
            try:
                standards = json.loads(standards_data)
                # Переконуємось, що всі ID - цілі числа (в БД могли потрапити рядки)
                if isinstance(standards, list):
                    standards = [int(s) for s in standards if str(s).isdigit()]
                else:
                    standards = []
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                logger.warning(
                    f"Помилка декодування або приведення JSON в standards_data для партії ID={self._get_value(row, self.PartyColumns.ID)}: {e}"
                )
                standards = []

        return PartyDTO(
            id=self._get_value(row, self.PartyColumns.ID),
            app_id=self._get_value(row, self.PartyColumns.APPLICATION_ID),
            party_number=self._get_value(row, self.PartyColumns.PARTY_NUMBER, 0),
            product_name=self._get_value(row, self.PartyColumns.PRODUCT_NAME),
            party_code=self._get_value(row, self.PartyColumns.PARTY_CODE, ""),
            party_date=self._get_value(row, self.PartyColumns.PARTY_DATE, ""),
            mfg_date=self._get_value(row, self.PartyColumns.MFG_DATE, ""),
            quantity=self._get_value(row, self.PartyColumns.QUANTITY, 0.0),
            unit=self._get_value(row, self.PartyColumns.UNIT, "шт"),
            shelf_life_months=self._get_value(
                row, self.PartyColumns.SHELF_LIFE_MONTHS, 36
            ),
            standards=standards,
            protocol_number=self._get_value(row, self.PartyColumns.PROTOCOL_NUMBER, ""),
            protocol_date=self._get_value(row, self.PartyColumns.PROTOCOL_DATE, ""),
            cert_number=self._get_value(row, self.PartyColumns.CERT_NUMBER, ""),
            cert_date=self._get_value(row, self.PartyColumns.CERT_DATE, ""),
            version=self._get_value(row, self.PartyColumns.VERSION, ""),
            final_docs_completed=bool(
                self._get_value(row, self.PartyColumns.FINAL_DOCS_COMPLETED, False)
            ),
            final_docs_generated_at=self._get_value(
                row, self.PartyColumns.FINAL_DOCS_GENERATED_AT
            ),
        )

    # ===== ФІНАЛЬНІ ДОКУМЕНТИ =====

    def update_party_final_documents(
        self, party_id: int, final_data: FinalDocumentsDTO
    ) -> bool:
        """Зберегти дані фінальних документів для партії"""
        self._execute_command(
            f"""UPDATE {self.Tables.PARTIES} SET
                {self.PartyColumns.PROTOCOL_NUMBER} = ?, {self.PartyColumns.PROTOCOL_DATE} = ?,
                {self.PartyColumns.CERT_NUMBER} = ?, {self.PartyColumns.CERT_DATE} = ?,
                {self.PartyColumns.FINAL_DOCS_COMPLETED} = 1,
                {self.PartyColumns.FINAL_DOCS_GENERATED_AT} = CURRENT_TIMESTAMP
            WHERE {self.PartyColumns.ID} = ?""",
            (
                final_data.protocol_number,
                final_data.protocol_date,
                final_data.cert_number,
                final_data.cert_date,
                party_id,
            ),
        )
        logger.info(f"✅ Фінальні документи для партії ID={party_id} збережено")
        return True

    def get_party_final_documents(self, party_id: int) -> Optional[FinalDocumentsDTO]:
        """Отримати дані фінальних документів для партії"""
        rows = self._execute_query(
            f"""SELECT {self.PartyColumns.PROTOCOL_NUMBER}, {self.PartyColumns.PROTOCOL_DATE}, {self.PartyColumns.CERT_NUMBER}, {self.PartyColumns.CERT_DATE},
                      {self.PartyColumns.FINAL_DOCS_COMPLETED}, {self.PartyColumns.FINAL_DOCS_GENERATED_AT}
               FROM {self.Tables.PARTIES} WHERE {self.PartyColumns.ID} = ?""",
            (party_id,),
        )
        if not rows:
            return None

        row = rows[0]
        return FinalDocumentsDTO(
            protocol_number=self._get_value(row, self.PartyColumns.PROTOCOL_NUMBER, ""),
            protocol_date=self._get_value(row, self.PartyColumns.PROTOCOL_DATE, ""),
            cert_number=self._get_value(row, self.PartyColumns.CERT_NUMBER, ""),
            cert_date=self._get_value(row, self.PartyColumns.CERT_DATE, ""),
            completed=bool(
                self._get_value(row, self.PartyColumns.FINAL_DOCS_COMPLETED, False)
            ),
            generated_at=self._get_value(
                row, self.PartyColumns.FINAL_DOCS_GENERATED_AT
            ),
        )

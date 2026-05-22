"""
Генератор Переліку вихідної декларації
"""

from documents.generators.base_party_generator import (
    BasePartyDocumentGenerator,
)


class PerelikGenerator(BasePartyDocumentGenerator):
    """Генерує Перелік вихідної декларації для партії"""

    def get_template_name(self) -> str:
        from documents.template_resolver import build_template_name

        return build_template_name("2_ПЕРЕЛІК_ДАНИХ_бланк")

    @property
    def filename_prefix(self) -> str:
        return "Перелік"

    @property
    def result_key(self) -> str:
        return "perelik"

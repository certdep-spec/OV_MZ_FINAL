"""
Генератор Рішення
"""

from documents.generators.base_party_generator import (
    BasePartyDocumentGenerator,
)


class ReshenyaGenerator(BasePartyDocumentGenerator):
    """Генерує Рішення для партії"""

    def get_template_name(self) -> str:
        from documents.template_resolver import build_template_name

        return build_template_name("4_Рішення_за_Заявкою_бланк")

    @property
    def filename_prefix(self) -> str:
        return "Рішення"

    @property
    def result_key(self) -> str:
        return "reshennya"

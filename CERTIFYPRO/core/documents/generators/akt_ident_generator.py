"""
Генератор Акту ідентифікації
"""

from documents.generators.base_party_generator import (
    BasePartyDocumentGenerator,
)


class AktIdentGenerator(BasePartyDocumentGenerator):
    """Генерує Акт ідентифікації для партії"""

    def get_template_name(self) -> str:
        from documents.template_resolver import build_template_name

        return build_template_name("6_Акт_ідент_бланк")

    @property
    def filename_prefix(self) -> str:
        return "Акт_ідентифікації"

    @property
    def result_key(self) -> str:
        return "akt_ident"

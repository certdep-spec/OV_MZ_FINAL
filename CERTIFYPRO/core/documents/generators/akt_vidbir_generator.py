"""
Генератор Акту відбору зразків
"""

from documents.generators.base_party_generator import (
    BasePartyDocumentGenerator,
)


class AktVidbirGenerator(BasePartyDocumentGenerator):
    """Генерує Акт відбору зразків для партії"""

    def get_template_name(self) -> str:
        from documents.template_resolver import build_template_name

        return build_template_name("5_Акт_відбору_бланк")

    @property
    def filename_prefix(self) -> str:
        return "Акт_відбору"

    @property
    def result_key(self) -> str:
        return "akt_vidbir"

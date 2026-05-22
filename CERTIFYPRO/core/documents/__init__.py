"""
Генератори документів
"""

from documents.context.document_context import DocumentDataService
from documents.document_base import DocumentBase
from documents.generators.akt_ident_generator import AktIdentGenerator
from documents.generators.akt_vidbir_generator import AktVidbirGenerator
from documents.generators.deklaraciya_generator import DeklaraciyaGenerator
from documents.generators.perelik_generator import PerelikGenerator
from documents.generators.protocol_rozgl_generator import (
    ProtocolRozglGenerator,
)
from documents.generators.protokol_analiz_generator import (
    ProtokolAnalizGenerator,
)
from documents.generators.reshenya_generator import ReshenyaGenerator
from documents.generators.reshenya_vidachu_generator import (
    ReshenyaVidachuGenerator,
)
from documents.generators.sertifikat_generator import SertifikatGenerator
from documents.generators.ugoda_generator import UgodaGenerator
from documents.generators.zayavka_generator import ZayavkaGenerator
from documents.vc_generator import VCDocumentGenerator

__all__ = [
    "DocumentBase",
    "DocumentDataService",
    "ZayavkaGenerator",
    "ProtocolRozglGenerator",
    "PerelikGenerator",
    "ReshenyaGenerator",
    "AktVidbirGenerator",
    "AktIdentGenerator",
    "SertifikatGenerator",
    "DeklaraciyaGenerator",
    "UgodaGenerator",
    "ReshenyaVidachuGenerator",
    "ProtokolAnalizGenerator",
    "VCDocumentGenerator",
]

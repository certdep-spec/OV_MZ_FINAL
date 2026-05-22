"""
Pipeline-модулі для оркестрації генерації документів.

Pipeline інкапсулює послідовність генерації документів,
що дозволяє легко додавати нові типи документів
та тестувати кожен пайплайн окремо.
"""

from documents.pipelines.base_pipeline import BasePipeline
from documents.pipelines.final_pipeline import FinalPipeline
from documents.pipelines.vc_pipeline import VCPipeline

__all__ = ["BasePipeline", "VCPipeline", "FinalPipeline"]

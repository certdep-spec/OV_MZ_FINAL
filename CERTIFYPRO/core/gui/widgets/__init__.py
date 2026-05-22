"""
GUI Widgets package for CertifyPro
Компоненти багаторазового використання
"""

from .final_documents_dialog import FinalDocumentsDialog
from .party_details_dialog import (
    FinalDocumentsPerPartyDialog,
    PartyDetailsDialog,
)
from .product_selection_dialog import ProductSelectionDialog
from .product_selector import ProductSelectorWidget
from .standards_selection_dialog import StandardsSelectionDialog
from .standards_selector import StandardsSelectorWidget

__all__ = [
    "ProductSelectorWidget",
    "StandardsSelectorWidget",
    "ProductSelectionDialog",
    "StandardsSelectionDialog",
    "PartyDetailsDialog",
    "FinalDocumentsPerPartyDialog",
    "FinalDocumentsDialog",
]

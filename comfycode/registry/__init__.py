"""Registry package for asset management with Pydantic models.

Provides typed models, validation, and documentation generation for registry entries
including characters, clothing, models, LoRAs, and datasets.
"""

from .models import (
    BlobRef,
    Character,
    Clothing,
    Dataset,
    LoRA,
    Model,
    NsfwRating,
    Provenance,
    BatchManifest,
    VariantResult,
    SelectionOutput,
    JournalEntry,
    RunJournal,
)
from .loader import (
    RegistryLoader,
    RegistryError,
    RegistryEntryNotFound,
    ValidationError,
)
from .generator import InventoryGenerator
from .validation import validate_entry

__all__ = [
    # Models
    "BlobRef",
    "Character",
    "Clothing",
    "Dataset",
    "LoRA",
    "Model",
    "NsfwRating",
    "Provenance",
    "BatchManifest",
    "VariantResult",
    "SelectionOutput",
    "JournalEntry",
    "RunJournal",
    # Loader
    "RegistryLoader",
    "RegistryError",
    "RegistryEntryNotFound",
    "ValidationError",
    # Generator
    "InventoryGenerator",
    # Validation
    "validate_entry",
]

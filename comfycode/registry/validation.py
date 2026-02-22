"""Validation utilities for registry entries."""

from __future__ import annotations

from typing import Any, Dict, Literal, Type

from pydantic import BaseModel, ValidationError as PydanticValidationError

from .models import Character, Clothing, Dataset, LoRA, Model
from .loader import ValidationError


EntryType = Literal["character", "clothing", "model", "lora", "dataset"]

# Mapping of entry types to model classes
ENTRY_TYPE_MAP: Dict[str, Type[BaseModel]] = {
    "character": Character,
    "clothing": Clothing,
    "model": Model,
    "lora": LoRA,
    "dataset": Dataset,
}


def validate_entry(data: Dict[str, Any], entry_type: EntryType) -> bool:
    """Validate a registry entry against its Pydantic model.
    
    Args:
        data: Entry data to validate.
        entry_type: Type of registry entry.
        
    Returns:
        True if valid.
        
    Raises:
        ValidationError: If validation fails.
        ValueError: If entry_type is unknown.
    """
    model_class = ENTRY_TYPE_MAP.get(entry_type)
    if not model_class:
        raise ValueError(f"Unknown entry type: {entry_type}")
    
    try:
        model_class.model_validate(data)
        return True
    except PydanticValidationError as e:
        raise ValidationError(f"Validation failed: {e}") from e

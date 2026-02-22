"""Registry loader for reading and validating registry entries."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Type, TypeVar, Union

from pydantic import BaseModel, ValidationError as PydanticValidationError

from .models import Character, Clothing, Dataset, LoRA, Model

logger = logging.getLogger(__name__)


class RegistryError(Exception):
    """Base exception for registry operations."""
    pass


class RegistryEntryNotFound(RegistryError):
    """Raised when a registry entry is not found."""
    pass


class ValidationError(RegistryError):
    """Raised when a registry entry fails validation."""
    pass


# Type variable for generic model loading
T = TypeVar("T", bound=BaseModel)

# Mapping of entry types to model classes
ENTRY_TYPE_MAP: Dict[str, Type[BaseModel]] = {
    "characters": Character,
    "clothing": Clothing,
    "models": Model,
    "loras": LoRA,
    "datasets": Dataset,
}


class RegistryLoader:
    """Loads and validates registry entries from the filesystem."""
    
    def __init__(self, registry_path: Union[str, Path]):
        """Initialize the registry loader.
        
        Args:
            registry_path: Path to the registry root directory.
        """
        self.registry_path = Path(registry_path)
    
    def _get_entry_path(self, entry_type: str, entry_id: str) -> Path:
        """Get the path to an entry file."""
        return self.registry_path / entry_type / f"{entry_id}.json"
    
    def _load_json(self, path: Path) -> Dict[str, Any]:
        """Load and parse a JSON file."""
        if not path.exists():
            raise RegistryEntryNotFound(f"Entry not found: {path}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in %s: %s", path, e)
            raise RegistryError(f"Invalid JSON in {path}: {e}") from e
        except OSError as e:
            logger.error("Failed to read %s: %s", path, e)
            raise RegistryError(f"Failed to read {path}: {e}") from e
    
    def _load_typed(self, entry_type: str, entry_id: str, model_class: Type[T]) -> T:
        """Load an entry and validate it against a Pydantic model."""
        path = self._get_entry_path(entry_type, entry_id)
        logger.debug("Loading %s entry: %s", entry_type, entry_id)
        data = self._load_json(path)
        
        try:
            return model_class.model_validate(data)
        except PydanticValidationError as e:
            logger.warning("Validation failed for %s/%s: %s", entry_type, entry_id, e)
            raise ValidationError(f"Validation failed for {entry_id}: {e}") from e
    
    def load_character(self, char_id: str) -> Character:
        """Load a character entry.
        
        Args:
            char_id: Character identifier.
            
        Returns:
            Validated Character model.
        """
        return self._load_typed("characters", char_id, Character)
    
    def load_clothing(self, clothing_id: str) -> Clothing:
        """Load a clothing entry.
        
        Args:
            clothing_id: Clothing identifier.
            
        Returns:
            Validated Clothing model.
        """
        return self._load_typed("clothing", clothing_id, Clothing)
    
    def load_model(self, model_id: str) -> Model:
        """Load a model entry.
        
        Args:
            model_id: Model identifier.
            
        Returns:
            Validated Model model.
        """
        return self._load_typed("models", model_id, Model)
    
    def load_lora(self, lora_id: str) -> LoRA:
        """Load a LoRA entry.
        
        Args:
            lora_id: LoRA identifier.
            
        Returns:
            Validated LoRA model.
        """
        return self._load_typed("loras", lora_id, LoRA)
    
    def load_dataset(self, dataset_id: str) -> Dataset:
        """Load a dataset entry.
        
        Args:
            dataset_id: Dataset identifier.
            
        Returns:
            Validated Dataset model.
        """
        return self._load_typed("datasets", dataset_id, Dataset)
    
    def load_raw(self, entry_type: str, entry_id: str) -> Dict[str, Any]:
        """Load an entry as raw JSON without Pydantic validation.
        
        Args:
            entry_type: Type directory (e.g., 'characters', 'models').
            entry_id: Entry identifier.
            
        Returns:
            Raw entry data as dict.
        """
        path = self._get_entry_path(entry_type, entry_id)
        return self._load_json(path)
    
    def load_all(self, entry_type: str) -> List[Dict[str, Any]]:
        """Load all entries of a given type as raw JSON.
        
        Args:
            entry_type: Type directory (e.g., 'characters', 'models').
            
        Returns:
            List of entry data, sorted by ID for determinism.
        """
        type_dir = self.registry_path / entry_type
        if not type_dir.exists():
            return []
        
        entries = []
        for entry_file in sorted(type_dir.glob("*.json")):
            try:
                with open(entry_file, "r", encoding="utf-8") as f:
                    entries.append(json.load(f))
            except (json.JSONDecodeError, OSError) as e:
                logger.error("Failed to load %s: %s", entry_file, e)
                raise RegistryError(f"Failed to load {entry_file}: {e}") from e
        
        logger.debug("Loaded %d entries from %s", len(entries), entry_type)
        # Sort by ID for determinism
        return sorted(entries, key=lambda e: e.get("id", ""))
    
    def load_all_typed(self, entry_type: str) -> List[BaseModel]:
        """Load all entries of a given type as Pydantic models.
        
        Args:
            entry_type: Type directory (e.g., 'characters', 'models').
            
        Returns:
            List of validated Pydantic models, sorted by ID.
        """
        model_class = ENTRY_TYPE_MAP.get(entry_type)
        if not model_class:
            raise ValueError(f"Unknown entry type: {entry_type}")
        
        type_dir = self.registry_path / entry_type
        if not type_dir.exists():
            return []
        
        entries = []
        for entry_file in sorted(type_dir.glob("*.json")):
            try:
                with open(entry_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.error("Failed to load %s: %s", entry_file, e)
                raise RegistryError(f"Failed to load {entry_file}: {e}") from e
            try:
                entries.append(model_class.model_validate(data))
            except PydanticValidationError as e:
                logger.warning("Validation failed for %s: %s", entry_file.stem, e)
                raise ValidationError(
                    f"Validation failed for {entry_file.stem}: {e}"
                ) from e
        
        logger.debug("Loaded %d typed entries from %s", len(entries), entry_type)
        return sorted(entries, key=lambda e: e.id)

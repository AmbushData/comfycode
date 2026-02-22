"""Pydantic models for registry entries.

All registry schemas are defined as Pydantic models, providing:
- Type hints and IDE autocomplete
- Runtime validation with clear error messages
- JSON serialization/deserialization
- Automatic JSON Schema export for external tooling
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class NsfwRating(str, Enum):
    """NSFW content rating levels."""
    SFW = "sfw"
    NSFW_MILD = "nsfw-mild"
    NSFW_EXPLICIT = "nsfw-explicit"


class ModelType(str, Enum):
    """Base model architecture types."""
    SD15 = "sd15"
    SD21 = "sd21"
    SDXL = "sdxl"
    SDXL_TURBO = "sdxl-turbo"
    FLUX = "flux"
    OTHER = "other"


class LoRAType(str, Enum):
    """LoRA adapter types."""
    CHARACTER = "character"
    STYLE = "style"
    CONCEPT = "concept"
    POSE = "pose"
    CLOTHING = "clothing"
    OTHER = "other"


class ClothingCategory(str, Enum):
    """Clothing item categories."""
    TOP = "top"
    BOTTOM = "bottom"
    DRESS = "dress"
    OUTERWEAR = "outerwear"
    SWIMWEAR = "swimwear"
    LINGERIE = "lingerie"
    ACCESSORIES = "accessories"
    FOOTWEAR = "footwear"
    OTHER = "other"


class DatasetPurpose(str, Enum):
    """Dataset purpose types."""
    LORA_TRAINING = "lora-training"
    EVALUATION = "evaluation"
    FINE_TUNING = "fine-tuning"
    TESTING = "testing"


# ============================================================================
# Common Models
# ============================================================================

class BlobRef(BaseModel):
    """Reference to a blob storage object."""
    container: str = Field(..., description="Blob container name")
    path: str = Field(..., description="Path within container")
    sha256: Optional[str] = Field(
        None, 
        description="SHA-256 hash for integrity verification",
        pattern=r"^[a-f0-9]{64}$"
    )
    size_bytes: Optional[int] = Field(None, ge=0, description="File size in bytes")

    def get_url(self, storage_account: str) -> str:
        """Get the full URL for this blob."""
        return f"https://{storage_account}.blob.core.windows.net/{self.container}/{self.path}"


class Provenance(BaseModel):
    """Source and attribution information."""
    source: Optional[str] = Field(None, description="Original source (URL, name, etc.)")
    author: Optional[str] = Field(None, description="Original author/creator")
    license: Optional[str] = Field(None, description="License type")
    url: Optional[str] = Field(None, description="Source URL")
    notes: Optional[str] = Field(None, description="Additional provenance notes")


# ============================================================================
# Registry Entry Models
# ============================================================================

class Character(BaseModel):
    """AI influencer character registry entry."""
    id: str = Field(..., pattern=r"^[a-z0-9-]+$", description="Unique character identifier")
    name: str = Field(..., min_length=1, description="Character display name")
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$", description="Semantic version")
    description: Optional[str] = Field(None, description="Character description")
    
    # Identity
    identity: Dict[str, Any] = Field(
        default_factory=dict,
        description="Persona and personality traits"
    )
    
    # Appearance
    appearance: Dict[str, Any] = Field(
        default_factory=dict,
        description="Physical appearance traits for prompt consistency"
    )
    
    # References
    reference_images: List[BlobRef] = Field(
        default_factory=list,
        description="Reference images for visual consistency"
    )
    associated_loras: List[str] = Field(
        default_factory=list,
        description="LoRA IDs trained for this character"
    )
    
    # Metadata
    nsfw: NsfwRating = Field(NsfwRating.SFW, description="NSFW rating")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "aria-v1",
                "name": "Aria",
                "version": "1.0.0",
                "description": "Primary AI influencer character",
                "identity": {"persona": "Friendly tech enthusiast"},
                "appearance": {"hair_color": "brown", "eye_color": "blue"},
                "nsfw": "sfw",
                "created_at": "2025-01-01T00:00:00Z"
            }
        }
    )


class Clothing(BaseModel):
    """Clothing item registry entry."""
    id: str = Field(..., pattern=r"^[a-z0-9-]+$")
    name: str = Field(..., min_length=1)
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    description: Optional[str] = None
    
    category: ClothingCategory = Field(..., description="Clothing category")
    style_tags: List[str] = Field(default_factory=list, description="Style descriptors")
    prompt_tags: List[str] = Field(default_factory=list, description="Prompt trigger words")
    colors: List[str] = Field(default_factory=list, description="Available colors")
    
    reference_images: List[BlobRef] = Field(default_factory=list)
    nsfw: NsfwRating = Field(NsfwRating.SFW)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(...)
    updated_at: Optional[datetime] = None


class Model(BaseModel):
    """Base model (checkpoint) registry entry."""
    id: str = Field(..., pattern=r"^[a-z0-9-]+$")
    name: str = Field(..., min_length=1)
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    description: Optional[str] = None
    
    model_type: ModelType = Field(..., description="Base model architecture")
    blob_ref: BlobRef = Field(..., description="Reference to model file")
    vae_ref: Optional[BlobRef] = Field(None, description="Optional VAE file reference")
    
    recommended_settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Recommended generation settings"
    )
    capabilities: List[str] = Field(
        default_factory=list,
        description="Model capabilities (inpainting, img2img, etc.)"
    )
    
    provenance: Optional[Provenance] = None
    nsfw: NsfwRating = Field(NsfwRating.SFW)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(...)
    updated_at: Optional[datetime] = None


class LoRA(BaseModel):
    """LoRA adapter registry entry."""
    id: str = Field(..., pattern=r"^[a-z0-9-]+$")
    name: str = Field(..., min_length=1)
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    description: Optional[str] = None
    
    base_model: ModelType = Field(..., description="Compatible base model type")
    lora_type: LoRAType = Field(..., description="LoRA adapter type")
    blob_ref: BlobRef = Field(..., description="Reference to LoRA file")
    
    trigger_words: List[str] = Field(
        default_factory=list,
        description="Trigger words for activation"
    )
    recommended_weight: float = Field(
        1.0,
        ge=0.0,
        le=2.0,
        description="Recommended LoRA weight"
    )
    
    associated_character: Optional[str] = Field(
        None,
        description="Character ID if this is a character LoRA"
    )
    training_info: Dict[str, Any] = Field(
        default_factory=dict,
        description="Training configuration details"
    )
    
    provenance: Optional[Provenance] = None
    nsfw: NsfwRating = Field(NsfwRating.SFW)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(...)
    updated_at: Optional[datetime] = None


class Dataset(BaseModel):
    """Training dataset registry entry."""
    id: str = Field(..., pattern=r"^[a-z0-9-]+$")
    name: str = Field(..., min_length=1)
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    description: Optional[str] = None
    
    purpose: DatasetPurpose = Field(..., description="Dataset purpose")
    image_count: int = Field(..., ge=0, description="Number of images")
    format: str = Field("zip", description="Archive format")
    
    blob_ref: BlobRef = Field(..., description="Reference to dataset archive")
    captions: bool = Field(True, description="Whether dataset includes captions")
    
    associated_character: Optional[str] = Field(
        None,
        description="Character ID if this is a character dataset"
    )
    curation_info: Dict[str, Any] = Field(
        default_factory=dict,
        description="Dataset curation details"
    )
    
    provenance: Optional[Provenance] = None
    nsfw: NsfwRating = Field(NsfwRating.SFW)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(...)
    updated_at: Optional[datetime] = None


# ============================================================================
# Batch Processing Models
# ============================================================================

class WorkflowRef(BaseModel):
    """Reference to a workflow."""
    id: str = Field(..., description="Workflow identifier")
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    path: Optional[str] = Field(None, description="Relative path to workflow file")


class BatchManifest(BaseModel):
    """Batch generation run manifest."""
    id: str = Field(..., pattern=r"^batch-[a-z0-9-]+$")
    name: Optional[str] = None
    description: Optional[str] = None
    
    workflow_ref: WorkflowRef = Field(..., description="Workflow used for generation")
    character_ref: Optional[str] = Field(None, description="Character registry ID")
    
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Generation parameters (fixed and grid)"
    )
    generation_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Execution settings"
    )
    output_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Output storage configuration"
    )
    scoring_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Scoring configuration"
    )
    
    status: Literal["pending", "running", "completed", "failed", "cancelled"] = "pending"
    variants_total: int = Field(0, ge=0)
    variants_completed: int = Field(0, ge=0)
    variants_failed: int = Field(0, ge=0)
    
    created_at: datetime = Field(...)
    created_by: Optional[str] = None
    completed_at: Optional[datetime] = None


class VariantScores(BaseModel):
    """Scores for a generated variant."""
    aesthetic: Optional[float] = Field(None, ge=0, le=1)
    nsfw_score: Optional[float] = Field(None, ge=0, le=1)
    nsfw_rating: Optional[NsfwRating] = None
    face_quality: Optional[float] = Field(None, ge=0, le=1)
    similarity: Optional[float] = Field(None, ge=0, le=1)
    composition: Optional[float] = Field(None, ge=0, le=1)
    overall: Optional[float] = Field(None, ge=0, le=1)


class VariantResult(BaseModel):
    """Individual variant generation result."""
    id: str = Field(..., pattern=r"^variant-[a-z0-9-]+$")
    batch_id: str = Field(..., description="Parent batch run ID")
    index: int = Field(..., ge=0, description="Variant index in batch")
    
    workflow_ref: Optional[WorkflowRef] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    artifacts: Dict[str, BlobRef] = Field(
        default_factory=dict,
        description="Generated artifacts (image, thumbnail, etc.)"
    )
    scores: Optional[VariantScores] = None
    
    status: Literal["pending", "generating", "completed", "failed", "skipped"] = "pending"
    error: Optional[Dict[str, Any]] = None
    timing: Optional[Dict[str, int]] = None
    
    created_at: datetime = Field(...)
    completed_at: Optional[datetime] = None


class SelectionEntry(BaseModel):
    """A selected variant with rationale."""
    rank: int = Field(..., ge=1)
    variant_id: str
    scores: VariantScores
    nsfw_rating: Optional[NsfwRating] = None
    rationale: str = Field(..., description="Selection rationale")
    artifacts: Dict[str, BlobRef] = Field(default_factory=dict)
    parameters_summary: Dict[str, Any] = Field(default_factory=dict)


class SelectionOutput(BaseModel):
    """Top-K variant selection results."""
    id: str = Field(..., pattern=r"^selection-[a-z0-9-]+$")
    batch_id: str
    
    selection_criteria: Dict[str, Any] = Field(
        default_factory=dict,
        description="Criteria used for selection"
    )
    total_candidates: int = Field(0, ge=0)
    filtered_count: int = Field(0, ge=0)
    
    selections: List[SelectionEntry] = Field(default_factory=list)
    rejected_summary: Dict[str, int] = Field(default_factory=dict)
    
    created_at: datetime = Field(...)
    created_by: Optional[str] = None
    notes: Optional[str] = None


# ============================================================================
# Agent Memory Models (Run Journal)
# ============================================================================

class JournalEntryType(str, Enum):
    """Types of journal entries."""
    OBSERVATION = "observation"
    DECISION = "decision"
    LEARNING = "learning"
    PREFERENCE = "preference"
    CONSTRAINT = "constraint"
    EXPERIMENT_RESULT = "experiment_result"
    ERROR_REPORT = "error_report"
    MILESTONE = "milestone"


class JournalEntry(BaseModel):
    """A single journal entry."""
    entry_id: str = Field(..., pattern=r"^entry-[a-z0-9-]+$")
    timestamp: datetime
    type: JournalEntryType
    
    source: Dict[str, str] = Field(
        default_factory=dict,
        description="Source info (agent, session_id, batch_id)"
    )
    content: Dict[str, Any] = Field(
        ...,
        description="Entry content based on type"
    )
    
    tags: List[str] = Field(default_factory=list)
    references: List[Dict[str, str]] = Field(default_factory=list)


class RunJournal(BaseModel):
    """Agent run journal - append-only memory substrate."""
    journal_id: str = Field(..., pattern=r"^journal-[a-z0-9-]+$")
    
    subject: Dict[str, str] = Field(
        default_factory=dict,
        description="Subject of journal (type, id, name)"
    )
    
    created_at: datetime
    last_entry_at: Optional[datetime] = None
    entry_count: int = Field(0, ge=0)
    
    entries: List[JournalEntry] = Field(default_factory=list)

    def append_entry(self, entry: JournalEntry) -> None:
        """Append an entry to the journal (in-memory only).
        
        Note: This mutates the model instance in memory. The caller is 
        responsible for persisting the journal to disk after modifications.
        """
        self.entries.append(entry)
        self.entry_count = len(self.entries)
        self.last_entry_at = entry.timestamp

# Blob Storage Conventions

**Version**: 1.0.0
**Last Updated**: 2026-02-22

## Overview

Large binary assets are stored in Azure Blob Storage. This document defines path conventions for reproducibility and organization.

---

## Storage Account Structure

```
<storage-account>/
├── models/                 # Base model checkpoints
├── loras/                  # LoRA adapters
├── datasets/               # Training datasets
├── references/             # Reference images
│   ├── characters/
│   └── clothing/
├── outputs/                # Generated outputs
│   ├── images/
│   └── videos/
└── staging/                # Temporary/work-in-progress
```

---

## Container Configuration

| Container | Purpose | Access | Retention |
|-----------|---------|--------|-----------|
| `assets` | Production assets (models, LoRAs, datasets) | Private | Permanent |
| `references` | Reference images | Private | Permanent |
| `outputs` | Generated content | Private | Configurable |
| `staging` | Temporary uploads | Private | 7 days |

---

## Path Naming Conventions

### General Format

```
{asset_type}/{id}/{filename}
```

### Models

```
models/{model-id}/{model-id}-{version}.safetensors
```

**Example:**
```
models/sd-xl-base/sd-xl-base-1.0.0.safetensors
models/sd-xl-base/sd-xl-base-1.0.0.sha256
```

### LoRAs

```
loras/{lora-id}/{lora-id}-{version}.safetensors
```

**Example:**
```
loras/aria-face-v1/aria-face-v1-1.0.0.safetensors
```

### Datasets

```
datasets/{dataset-id}/{dataset-id}-{version}.{format}
```

**Example:**
```
datasets/aria-training-v1/aria-training-v1-1.0.0.zip
```

### Reference Images

```
references/{type}/{id}/{filename}
```

**Example:**
```
references/characters/aria-v1/reference-001.png
references/characters/aria-v1/reference-002.png
references/clothing/summer-dress-v1/front.png
```

### Generated Outputs

```
outputs/{format}/{run-id}/{variant-id}.{ext}
```

**Example:**
```
outputs/images/run-2026-02-22-001/variant-001.png
outputs/images/run-2026-02-22-001/variant-002.png
outputs/videos/run-2026-02-22-002/clip-001.mp4
```

---

## Hash Files

Every large binary SHOULD have an accompanying `.sha256` file containing the SHA-256 hash:

```
models/sd-xl-base/sd-xl-base-1.0.0.safetensors
models/sd-xl-base/sd-xl-base-1.0.0.sha256
```

**Hash file format:**
```
abc123def456...  sd-xl-base-1.0.0.safetensors
```

---

## Blob Reference Format

Registry entries reference blobs using this format:

```json
{
  "blob_ref": {
    "container": "assets",
    "path": "models/sd-xl-base/sd-xl-base-1.0.0.safetensors",
    "sha256": "abc123def456...",
    "size_bytes": 6938078296
  }
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `container` | Yes | Blob container name |
| `path` | Yes | Full path within container |
| `sha256` | Recommended | SHA-256 hash for integrity verification |
| `size_bytes` | Optional | File size for capacity planning |

---

## Naming Rules

1. **Lowercase only**: All paths use lowercase letters
2. **Hyphen-separated**: Use hyphens, not underscores (e.g., `aria-face-v1`)
3. **Version suffix**: Include version in filename (e.g., `model-1.0.0.safetensors`)
4. **No spaces**: Replace spaces with hyphens
5. **ASCII only**: Avoid special characters and Unicode

**Valid examples:**
- `models/realistic-vision-v5/realistic-vision-v5-1.0.0.safetensors`
- `loras/aria-face-v1/aria-face-v1-2.1.0.safetensors`
- `references/characters/aria-v1/ref-001.png`

**Invalid examples:**
- `models/Realistic Vision/model.safetensors` (spaces, uppercase)
- `loras/aria_face_v1/model.safetensors` (underscores)

---

## NSFW Content Routing

NSFW content is stored separately for routing:

```
outputs/images/{run-id}/sfw/variant-001.png
outputs/images/{run-id}/nsfw-mild/variant-002.png
outputs/images/{run-id}/nsfw-explicit/variant-003.png
```

**Note**: NSFW content is labeled and routed, not blocked. Storage paths reflect the rating for access control.

---

## Reproducibility

To ensure reproducibility:

1. **Immutable assets**: Once uploaded, model/LoRA/dataset files are immutable
2. **Version in path**: Version number is part of the path
3. **Hash verification**: SHA-256 hashes enable integrity checks
4. **No overwrites**: New versions get new paths

To update an asset, create a new version:
```
loras/aria-face-v1/aria-face-v1-1.0.0.safetensors  # Original
loras/aria-face-v1/aria-face-v1-1.1.0.safetensors  # Updated
```

---

## Environment Configuration

Blob storage connection is configured via environment variables:

| Variable | Description |
|----------|-------------|
| `COMFYCODE_BLOB_ACCOUNT` | Azure Storage account name |
| `COMFYCODE_BLOB_CONTAINER` | Default container name |
| `COMFYCODE_BLOB_SAS_TOKEN` | SAS token for authentication (optional) |
| `AZURE_STORAGE_CONNECTION_STRING` | Full connection string (alternative) |

---

## Usage in Code

```python
from comfycode.registry import BlobRef

# Create a blob reference
ref = BlobRef(
    container="assets",
    path="models/sd-xl-base/sd-xl-base-1.0.0.safetensors",
    sha256="abc123...",
    size_bytes=6938078296
)

# Get full URL (requires configured storage account)
url = ref.get_url()

# Verify integrity after download
ref.verify_hash("/local/path/to/file.safetensors")
```

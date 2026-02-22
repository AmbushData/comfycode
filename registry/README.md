# Asset Registry

**Version**: 1.0.0
**Last Updated**: 2026-02-22

## Overview

The `registry/` directory contains metadata for all assets used in AI influencer generation. Large binary files are stored in Azure Blob Storage; this registry holds the metadata and references.

---

## Directory Structure

```
registry/
├── README.md               # This file
├── characters/             # Character definitions (identity, appearance)
├── clothing/               # Clothing items and accessories
├── models/                 # Base models (checkpoints)
├── loras/                  # LoRA adapters
└── datasets/               # Training datasets
```

---

## Asset Types

| Type | Path | Description |
|------|------|-------------|
| **Characters** | `registry/characters/` | AI influencer personas with identity traits |
| **Clothing** | `registry/clothing/` | Wearable items, accessories, styles |
| **Models** | `registry/models/` | Base model checkpoints (SD, SDXL, etc.) |
| **LoRAs** | `registry/loras/` | Fine-tuned LoRA adapters |
| **Datasets** | `registry/datasets/` | Training/evaluation image datasets |

---

## Blob Storage References

All large binary assets are stored in Azure Blob Storage. Registry entries reference them via:

```json
{
  "blob_ref": {
    "container": "assets",
    "path": "models/sd_xl_base_1.0.safetensors",
    "sha256": "abc123...",
    "size_bytes": 6938078296
  }
}
```

See [BLOB_CONVENTIONS.md](../docs/BLOB_CONVENTIONS.md) for full path naming rules.

---

## File Naming

- **Folder names**: Match the asset `id` (lowercase, hyphenated)
- **Metadata file**: `{id}.json` or `index.json` in the folder
- **Example**: `registry/characters/aria-v1/index.json`

---

## Schema Validation

All registry entries are validated against JSON schemas in `comfycode/schemas/`.

Run validation:
```bash
python -m comfycode.registry validate
```

---

## NSFW Handling

Assets can be tagged with NSFW labels for routing purposes:

```json
{
  "nsfw": {
    "rating": "sfw",
    "labels": []
  }
}
```

| Rating | Description |
|--------|-------------|
| `sfw` | Safe for work |
| `nsfw-mild` | Suggestive but not explicit |
| `nsfw-explicit` | Explicit content |

**NSFW content is labeled and routed, not blocked.**

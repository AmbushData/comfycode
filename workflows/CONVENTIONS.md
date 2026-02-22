# Workflow Library Conventions

**Version**: 1.0.0
**Last Updated**: 2026-02-22

## Overview

The `workflows/` directory contains ComfyUI workflow definitions organized by intent. Each workflow must include metadata for reproducibility, provenance tracking, and automation.

---

## Directory Structure

```
workflows/
├── CONVENTIONS.md          # This file
├── photo/                  # Instagram-style photo generation
│   ├── portrait-v1/
│   │   ├── workflow.json   # ComfyUI prompt/UI JSON
│   │   └── workflow.meta.json
│   └── ...
├── lora/                   # LoRA training, dataset prep, evaluation
│   ├── training-sdxl/
│   │   ├── workflow.json
│   │   └── workflow.meta.json
│   └── ...
└── video/                  # Short video generation
    ├── talking-head-v1/
    │   ├── workflow.json
    │   └── workflow.meta.json
    └── ...
```

---

## Workflow Categories

| Category | Path | Purpose |
|----------|------|---------|
| **Photo** | `workflows/photo/` | Instagram-style photos, portraits, product shots |
| **LoRA** | `workflows/lora/` | Dataset preparation, LoRA training, model evaluation |
| **Video** | `workflows/video/` | Short video clips, talking heads, animations |

---

## Workflow Metadata Schema

Every workflow folder MUST contain a `workflow.meta.json` file with the following structure:

```json
{
  "$schema": "../schemas/workflow-meta.schema.json",
  "id": "portrait-v1",
  "name": "Portrait Generator v1",
  "version": "1.0.0",
  "category": "photo",
  "type": "baseline",
  "description": "Generates high-quality portrait photos with consistent lighting.",
  
  "inputs": {
    "required": [
      {"name": "prompt", "type": "string", "description": "Positive prompt"},
      {"name": "character_id", "type": "string", "description": "Character registry ID"}
    ],
    "optional": [
      {"name": "seed", "type": "integer", "description": "Random seed", "default": -1},
      {"name": "negative_prompt", "type": "string", "description": "Negative prompt"}
    ]
  },
  
  "outputs": [
    {"name": "image", "type": "image/png", "description": "Generated portrait"}
  ],
  
  "compatibility": {
    "comfyui_version": ">=0.2.0",
    "required_nodes": ["KSampler", "VAEDecode", "CLIPTextEncode"],
    "required_models": ["sd_xl_base_1.0.safetensors"]
  },
  
  "provenance": null,
  
  "created_at": "2026-02-22T00:00:00Z",
  "updated_at": "2026-02-22T00:00:00Z"
}
```

---

## Baseline vs Derived Workflows

### Baseline Workflows

Baseline workflows are **immutable golden references**. They are either:
- Created internally as stable starting points
- Sourced externally (from community, vendors, etc.)

**Rules for baseline workflows:**
- `type` field MUST be `"baseline"`
- MUST NOT be modified after initial commit (create a derived workflow instead)
- If externally sourced, `provenance` field is REQUIRED

### Derived Workflows

Derived workflows are **modifications of baseline workflows**.

**Rules for derived workflows:**
- `type` field MUST be `"derived"`
- `parent` field is REQUIRED, referencing the baseline workflow ID
- `changes` field documents what was modified

**Derived workflow metadata example:**
```json
{
  "id": "portrait-v1-anime",
  "type": "derived",
  "parent": {
    "id": "portrait-v1",
    "version": "1.0.0"
  },
  "changes": [
    "Added anime-style LoRA",
    "Adjusted CFG scale for stylization"
  ]
}
```

---

## Provenance (Externally Sourced Workflows)

Any workflow sourced from external parties MUST include provenance metadata:

```json
{
  "provenance": {
    "source": "civitai",
    "source_url": "https://civitai.com/models/12345",
    "author": "original_author_name",
    "license": "CreativeML Open RAIL-M",
    "retrieved_at": "2026-02-20T14:30:00Z",
    "original_name": "Amazing Portrait Workflow",
    "notes": "Retrieved from CivitAI, adapted for SDXL"
  }
}
```

**Required provenance fields:**
| Field | Required | Description |
|-------|----------|-------------|
| `source` | Yes | Source identifier (e.g., "civitai", "github", "vendor") |
| `source_url` | Yes | URL where workflow was obtained |
| `author` | Yes | Original author name/handle |
| `license` | Yes | License under which workflow is distributed |
| `retrieved_at` | Yes | ISO 8601 timestamp when workflow was downloaded |
| `original_name` | No | Original name if renamed |
| `notes` | No | Additional context |

---

## Validation

Workflow metadata is validated against JSON schemas in `comfycode/schemas/`.

Run validation locally:
```bash
python -m comfycode.registry validate-workflows
```

---

## Naming Conventions

- **Folder names**: lowercase, hyphenated (e.g., `portrait-v1`, `training-sdxl`)
- **Version suffix**: Use `-vN` suffix for major versions (e.g., `portrait-v1`, `portrait-v2`)
- **File names**: 
  - `workflow.json` — the ComfyUI workflow definition
  - `workflow.meta.json` — metadata file
  - `README.md` — optional human-readable documentation

---

## Example: Complete Workflow Folder

```
workflows/photo/portrait-v1/
├── workflow.json           # ComfyUI prompt JSON
├── workflow.meta.json      # Metadata (required)
└── README.md              # Optional documentation
```

---
ID: 004
Origin: 004
UUID: 4f9b1c2e
Status: QA Complete
---

# Plan 004 — AI Influencer Asset Registry + Workflow Library (MVP)

**Target Release:** v0.3.0
**Semver Rationale:** Minor version bump — introduces new capability surface (asset registry + workflow library taxonomy) without breaking existing APIs.
**Epic Alignment:** Epic 1.0 — AI Influencer Asset Registry + Workflow Library
**Created:** 2026-02-22

## Change Log

| Date | Agent | Change | Notes |
|------|-------|--------|-------|
| 2026-02-22 | Planner | Created plan | Architectural concerns integrated: hybrid git+Blob storage, workflow taxonomy, provenance, NSFW labeling/routing, auto-updating docs |
| 2026-02-22 | Critic | Addressed critique findings | Added Dependencies section, semver rationale, CI scope clarification; resolved blocking open question |
| 2026-02-22 | QA | QA Complete | Full test suite pass (183 tests); docs generator smoke validated; noted doc/version follow-ups |

---

## Value Statement and Business Objective

As a **team creating hyper-realistic AI influencers**, I want **a structured workflow library plus a low-cost, file-based registry for characters/clothing/LoRAs/models and batch variant scoring**, so that **we can scale content generation with consistent identity, repeatable runs, and clear provenance while keeping infrastructure costs minimal**.

## Objective

Deliver the MVP foundations for the AI Influencer vertical:
1. **Workflow library taxonomy** with sections for photo, LoRA, and short video workflows.
2. **Hybrid persistence**:
   - small metadata in the git repo (JSON/YAML)
   - large binaries/images in Azure Blob Storage
   - optional Azure Tables as a thin lookup mirror
3. **Batch variant manifests** with scoring fields (including NSFW labeling) and selection outputs.
4. **Agent memory substrate** via durable run journaling (file-based records that agents can read to stay consistent across iterations).
5. **Auto-updating documentation** generated deterministically from the repo inventory and registry manifests.

## Architecture Alignment

Aligned to:
- `agent-output/architecture/system-architecture.md` (AI Influencer target architecture: registry, workflow taxonomy, agents, NSFW labeling)
- `agent-output/architecture/system-architecture-diagram.mmd`

## Scope

**In scope**
- Define the workflow library structure (photo / LoRA / video), including baseline vs derived workflow conventions.
- Define minimal registry schemas and file locations for:
  - characters
  - clothing items
  - models
  - LoRAs
  - datasets
- Define the blob layout conventions for binaries and reference images.
- Implement a deterministic documentation generator that produces inventory summaries.
- Add batch result manifests that record parameters + scores + artifact references.
- Add a durable, file-based **run journal** format intended to serve as an agent memory substrate (summaries, selections, and pointers to artifacts).

**Out of scope (MVP)**
- Building or running a full LoRA training stack inside ComfyCode (training orchestration is planned later).
- Automated aesthetic/face-consistency scoring models (can start with placeholder/manual scores + schema; later add model-based scoring).
- UI JSON → IR import.
- A full search service (Cognitive Search, etc.).

## Constraints (Non-Negotiable)

- **Cost-minimized**: no always-on DB required.
- **Hybrid persistence**: store small text metadata in git; store large binaries/images in Blob.
- **NSFW handling**: NSFW must be labeled and routed; it must not be globally blocked.
- **Provenance required**: externally sourced workflows must track source/license/date and be treated as immutable baselines.
## Dependencies

- **Epic 0.7 (UI Interop)**: Not required. Plan 004 can proceed independently. UI interop is optional tooling for debugging/visualization but is not a prerequisite for registry or workflow library functionality.
- **Azure Blob Storage**: Available (assumed provisioned).
## Assumptions

- Workflow “copying” is acceptable for initial iteration if provenance is tracked.
- Azure Blob Storage is available for large assets.
- Teams can accept a minimal schema now, with backward-compatible evolution.

## OPEN QUESTION [RESOLVED]

- Do we treat the **git registry JSON** as the canonical index, or do we mirror canonical metadata into Blob sidecars as well?
  - **RESOLVED (2026-02-22)**: Git registry is the sole canonical source for metadata. No Blob sidecars required—access is only from our package, so portability to external consumers is not needed.

---

## Plan

### 1) Workflow Library Taxonomy + Conventions

**Owner:** Implementer

**Tasks**
1. Create workflow sections:
   - `workflows/photo/` (Instagram-style photos)
   - `workflows/lora/` (dataset prep / training / eval)
   - `workflows/video/` (short video)
2. Define a standard workflow metadata file for each workflow (inputs/outputs/notes/compatibility).
3. Define baseline vs derived conventions:
   - baseline workflows are immutable (sourced or “golden”) 
   - derived workflows record a parent reference and change notes
4. Add required provenance fields for externally sourced workflows.

**Acceptance criteria**
- Repo includes clear workflow sections and a documented convention for baseline vs derived.
- Every workflow has metadata including provenance when sourced externally.

### 2) Registry Schemas (Characters / Clothing / Models / LoRAs / Datasets)

**Owner:** Implementer

**Tasks**
1. Define minimal schemas for each registry entry type.
2. Store registry entries as files in the repo under `registry/`.
3. Define required blob reference fields for binaries/images (URI/prefix + hash where applicable).

**Acceptance criteria**
- Minimal schemas exist and are validated consistently.
- Entries can reference Blob assets without requiring an always-on database.

### 3) Blob Storage Conventions (Binaries + Reference Images)

**Owner:** Implementer

**Tasks**
1. Define Blob path conventions for:
   - models
   - LoRAs
   - datasets
   - character reference images
   - clothing reference images
2. Define naming conventions to support reproducibility (include IDs + hashes).

**Acceptance criteria**
- A single, documented convention exists and is used by registry entries.

### 4) Batch Variant Manifests + Scoring Fields

**Owner:** Implementer

**Tasks**
1. Define a “batch run” manifest format (params grid + workflow reference + outputs).
2. Define a “variant result” record format that includes:
   - prompt/workflow reference
   - parameters (seed/prompt/controls)
   - artifact references (output paths)
   - scores (including NSFW label/routing fields)
3. Define selection output format (top-K selection + rationale).

**Acceptance criteria**
- Batch runs can record variants and selections deterministically.
- NSFW fields are present and used for routing/selection, not hard-blocking.

### 5) Agent Memory Substrate (Run Journaling + Retrieval-Friendly Indexing)

**Owner:** Implementer

**Tasks**
1. Define a durable “run journal” record format intended for agent consumption (decisions, selections, rationale, pointers).
2. Define a minimal indexing strategy that enables deterministic lookup (file-based), with an option to mirror a thin index to Azure Tables.
3. Ensure memory records avoid secrets/credentials and are safe to commit when appropriate.

**Acceptance criteria**
- Every batch run can emit a journal entry that can be used as memory in later runs.
- Journals are file-based by default and link to Blob artifacts; optional thin mirror to Azure Tables is documented.
- NSFW remains a label for routing and is persisted in journals.

### 6) Auto-Updating Documentation

**Owner:** Implementer

**Tasks**
1. Implement a deterministic docs generator that reads:
   - workflow library inventory
   - registry entries
2. Output a generated inventory doc (e.g., `docs/generated/inventory.md`) suitable for commit.
3. Ensure generator can run locally and in CI.

**Acceptance criteria**
- Running the generator produces up-to-date inventory docs with no manual editing.

**Scope note**: CI pipeline integration for automatic doc generation is deferred to a follow-up task. This task delivers the generator itself, runnable locally.

### 7) Version and Release Artifacts

**Owner:** DevOps

**Tasks**
1. Update version metadata for the target release group.
2. Update changelog/release notes as used by the repo.

**Acceptance criteria**
- Version artifacts reflect inclusion of the AI influencer MVP foundations.

---

## Validation

- Unit tests for schema validation, inventory generation determinism, and manifest serialization.
- Smoke tests for reading workflow metadata + registry entries.

## Risks

- Schema churn if requirements are underspecified; mitigate by keeping schemas minimal and versioned.
- Provenance discipline may be skipped; mitigate with validation that enforces provenance fields for sourced workflows.
- Storage path/hashing conventions must be correct early; changing later is expensive.

## Rollback

- All changes are additive (new folders + new generated docs); rollback is removing registry/docs generator and reverting workflow taxonomy.

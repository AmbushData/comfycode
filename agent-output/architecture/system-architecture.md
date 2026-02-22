# System Architecture — ComfyCode

**Last Updated**: 2026-02-22
**Owner**: Architect
**Status**: Current

## Changelog

| Date | Change | Rationale | Related |
|------|--------|-----------|---------|
| 2026-02-22 | Initial architecture doc created | Establish source-of-truth; capture implemented docs/tooling work and upcoming bidirectional conversion design | Plans 001–002; UX request (JSON↔Python↔UI) |
| 2026-02-22 | Reconciled interop implementation + scoped AI Influencer platform | Keep doc aligned to current codebase; define next epic architecture (file-based Azure storage, LoRA/asset registry, workflow taxonomy, tuning agents) | Plan 003 implemented; AI Influencer epic requirements |
| 2026-02-22 | Added D008: Pydantic as default validation standard | Standardize on Pydantic v2 models for runtime validation + typed contracts; JSON Schema may be generated for tooling | Plan 004 implementation |
| 2026-02-22 | Added Workflow Expert agent role | Define specialized agent for ComfyUI workflow creation/improvement/validation with deep domain knowledge | User request for workflow expertise agent |
| 2026-02-22 | Added D009: RunPod as production GPU runtime | Confirm RunPod over Google Colab for stable, scriptable GPU compute with persistent storage and direct ingress | User decision on production runtime platform |
| 2026-02-22 | Portability + IaC + CI/CD assessment | Define required package boundaries, Pulumi-based infra, and CI/CD baseline before production planning | Findings 004 portability/IaC/CI/CD |

---

## Purpose

ComfyCode is the workflow engine and automation substrate for a single product vertical: **hyper-realistic AI influencers**.

It provides:
- A Python-first way to build and run ComfyUI workflows (images today; video workflows as a target).
- Batch-oriented execution for generating multiple variants per prompt/character.
- Workflow interop tooling so teams can still use the ComfyUI UI when helpful (debugging, exploration) while keeping production logic in code.

Primary non-functional constraints for the AI Influencer platform:
- **Cost-minimized**: avoid always-on infrastructure; prefer file-based persistence.
- **Azure-first**: storage and simple lookup services should use Azure primitives.
- **Reproducible**: workflows, LoRA artifacts, and datasets must be versionable and traceable.

---

## High-Level Architecture

### Runtime Components (Current)

- **`converter`**: Converts a ComfyUI *prompt dict* JSON (API format) into Python code using the `Workflow` builder API.
- **`workflow`**: Provides a `Workflow` model that can:
  - Build workflows programmatically (`add_node`)
  - Load/modify template workflows (`from_file`, setters like `set_seed`) and then `build()` into prompt dict JSON
- **`comfyui_client`**: Submits prompt dicts to a ComfyUI server and streams events.
- **`runpod_client`**: Provisioning/lifecycle for RunPod pods.
- **`batch` / `pipeline`**: Orchestration, parameter injection, and repeat execution.

### Interop & Conversion (Current)

The following interop components exist in the codebase as of Plan 003 implementation:
- **`formats`**: explicit format contracts + validation for prompt JSON vs UI JSON.
- **`ir`**: internal workflow IR (nodes/edges) with prompt JSON ↔ IR conversion.
- **`export`**: execution-based Python module export contract (`create_workflow()` → prompt JSON).
- **`layout`**: deterministic layered DAG layout for UI readability.
- **`ui_export`**: IR/prompt → UI workflow JSON for ComfyUI UI import.

### Interop Model (Current)

To support UI interop, ComfyCode needs to represent workflows at **two different JSON layers**:

1) **Prompt JSON** (API prompt format):
- Data shape: `{ node_id: { class_type, inputs } }`
- Used by: ComfyUI HTTP API
- Currently supported by: `Workflow.build()`, `converter.convert()` (JSON→Python)

2) **UI Workflow JSON** (ComfyUI UI export/import format):
- Includes: node positions, sizes, UI metadata (exact schema varies by ComfyUI version)
- Used by: ComfyUI web UI
- Supported as an **export target** for UI visualization; it is not used for runtime execution.

---

## Conversions via an Intermediate Representation (IR)

### Why an IR

Direct conversion between every pair (Python↔prompt JSON↔UI JSON) tends to be brittle and lossy.

A stable **Workflow IR** keeps the system flexible and makes layout generation a first-class concern without leaking UI details into runtime submission.

### Workflow IR (Conceptual)

A minimal IR should capture:
- `nodes`: `id`, `class_type`, `inputs`
- `edges`: derived from link inputs (node_id + slot references)
- `metadata` (optional): human-friendly names, grouping/stages, layout hints

### Conversion Matrix

- **Prompt JSON → IR**: parse nodes/inputs; infer edges.
- **IR → Python**: generate `workflow.add_node(...)` calls; preserve wiring.
- **Python → IR**: prefer *execution-based export* (run code to produce prompt dict; then parse prompt dict → IR).
  - Avoid static Python AST parsing initially; it is fragile and hard to support.
- **IR → Prompt JSON**: straightforward serialization.
- **IR → UI Workflow JSON**: generate UI nodes + links + **layout**.
- **UI Workflow JSON → IR**: parse UI export; map to nodes/links; preserve positions in metadata.

Status notes:
- Prompt JSON ↔ IR, IR → UI JSON, and Python export via `create_workflow()` are implemented.
- UI JSON → IR import is deferred.

### Execution-Based “Code → JSON” (Recommended v1)

When a user says “convert code into json workflows”, the most robust path is:
- Import or execute the Python workflow module in a controlled entrypoint
- Obtain a prompt dict (the same one used for API submission)
- Serialize to prompt JSON (and optionally also emit UI JSON)

This keeps conversion aligned with real runtime behavior and avoids trying to interpret arbitrary Python.

---

## Layout: Visually Pleasing Node Alignment (Deterministic)

### Requirements

- **Deterministic**: same workflow yields same layout every time.
- **Readable**: limited wire crossings, left-to-right flow.
- **Stable under small edits**: adding a node should not completely reshuffle unrelated regions.
- **Configurable**: allow tuning spacing but keep sensible defaults.

### Approach (MVP)

1) Build a DAG from IR edges.
2) Assign **layers** using topological depth:
   - sources (no incoming edges) at layer 0
   - downstream nodes at increasing layers
3) Within each layer, order nodes by:
   - (a) class_type grouping heuristic, then
   - (b) node id or stable hash
4) Compute positions:
   - `x = layer * X_STEP`
   - `y = index_in_layer * Y_STEP`

Defaults (conceptual): `X_STEP≈300`, `Y_STEP≈120`.

### Preservation Rules

- If importing from UI JSON and positions exist, **preserve** them by default.
- If exporting to UI JSON from code/prompt JSON, **generate** layout.
- Allow an option to “reflow” an existing UI layout (opt-in).

### “Pleasant” Heuristics (Future)

- Reduce crossings: barycentric ordering per layer.
- Pin known stages (e.g., loaders left, samplers middle, decoders/savers right).
- Align common node types across variations for batch workflows.

---

## Interfaces (Public Surface Area)

To keep UX flexible without bloating core runtime APIs:

- **CLI**
  - `comfycode <prompt.json>` remains JSON→Python.
  - Supported subcommands include `convert` and `export`.
  - `export` supports exporting prompt JSON and UI JSON (UI export is opt-in).

- **Python API**
  - Keep `Workflow.build()` returning prompt dict.
  - Add exports later (proposal):
    - `workflow.to_prompt_dict()` (alias of build)
    - `workflow.to_ui_json(layout="auto"|"preserve"|"none")`

---

## Data Boundaries

- **Prompt JSON** is the canonical runtime submission format.
- **UI JSON** is an interchange format for occasional UI usage.
- **IR** is internal; used to avoid loss and enable layout.

AI Influencer platform persistence boundaries:
- **Git repo** holds *small, human-auditable text* assets: workflow definitions, manifests, character/clothing descriptions, and registry indexes.
- **Azure Storage account (Blob)** holds *large/binary* assets: model checkpoints, LoRA weights, training datasets, reference images, and generated outputs.
- **Azure Table Storage** (optional) is a thin lookup accelerator; it MUST not become the sole source of truth.

---

## Quality Attributes

- **Maintainability**: IR isolates UI schema churn from core workflow submission.
- **Correctness**: execution-based export ensures “code→JSON” matches runtime behavior.
- **Reproducibility**: deterministic layout + `uv.lock` support stable environments.
- **UX Flexibility**: Python-first workflow remains primary; UI is optional tooling.

Portability / production readiness attributes (required as the codebase grows):
- **Portability**: reproducible environments, minimal implicit system dependencies, and clear install/run paths.
- **Modularity**: package boundaries that match domains (interop vs runtime vs clients vs registry).
- **Deployability**: infra is codified and repeatable; CI/CD is the default path for changes.

---

## Problem Areas / Design Debt

- Current `converter.convert()` supports only the prompt dict API JSON, not UI export JSON.
- There is no explicit format contract module describing prompt JSON vs UI JSON.
- Layout metadata is not modeled; UI import/export is currently unsupported.

AI Influencer platform (next epic) design gaps:
- No artifact registry for LoRAs/models/datasets (file-based index + lookup required).
- No character/clothing asset repository conventions.
- No quality gates or scoring to select “best” variants from large batches.
- No workflow taxonomy and packaging structure for photo vs LoRA vs video workflows.
- No automated documentation generation for workflow/library inventory.

Portability / production readiness gaps:
- Current Python modules are mostly flat under `comfycode/`, which will not scale as features expand.
- Infrastructure definitions (Azure Storage) are not codified as IaC in-repo.
- CI/CD is not defined for testing/building/deploying infra/runtime changes.
- Build artifacts (e.g., `*.egg-info/`) risk being mistaken for source; must be treated as generated output only.

---

## Decisions

### D001 — Introduce Workflow IR for conversions

- **Context**: Need bidirectional conversions and UI layout generation.
- **Choice**: Use an internal IR to mediate conversions.
- **Alternatives**: Pairwise converters; static Python AST parsing.
- **Consequences**:
  - + isolates UI schema changes
  - + enables deterministic layout
  - − requires new module and careful versioning

### D002 — Prefer execution-based export for Python→JSON

- **Context**: Python is too flexible to parse reliably.
- **Choice**: Execute/import and export the realized prompt dict.
- **Alternatives**: Static AST parsing; restrict DSL.
- **Consequences**:
  - + accurate by construction
  - + simpler implementation
  - − requires guardrails against side effects

### D003 — Prefer file-based artifacts + Azure Tables for lookup (AI Influencer)

- **Context**: Cost must stay low; infra should scale-to-zero. The product needs to store LoRAs, models, datasets, and character/clothing assets with searchable metadata.
- **Choice**: Use a **hybrid file-based registry**:
  - Store **metadata/registries/manifests** as JSON/YAML in the **git repo**.
  - Store **large binaries and images** in **Azure Blob Storage**, referenced by URI + content hash from the repo metadata.
  - Use **Azure Table Storage** only as an optional, thin lookup index (mirrors repo metadata keys → blob prefixes).
- **Alternatives**: Cosmos DB; SQL; full search service.
- **Consequences**:
  - + very low baseline cost
  - + simple mental model (repo metadata + blob files are source of truth)
  - − querying is limited (requires careful key design)
  - − eventual consistency / manual reindexing considerations

### D004 — Workflow taxonomy by intent (AI Influencer)

- **Context**: The product needs multiple workflow families: LoRA training, photo generation (Instagram style), and short video.
- **Choice**: Treat workflows as a **typed library** with clear categories and standardized inputs/outputs.
- **Alternatives**: One flat workflows folder; ad-hoc naming.
- **Consequences**:
  - + makes automation and documentation generation straightforward
  - + reduces operational mistakes (wrong workflow in pipeline)

### D005 — Agent-oriented optimization loop (AI Influencer)

- **Context**: Generating “hyper-realistic influencer” output requires iterative tuning (prompts, seeds, negative prompts, ControlNet, LoRA selection) and quality filtering.
- **Choice**: Introduce internal “agents” as deterministic services (not autonomous black boxes) that propose parameter changes and record decisions.
- **Alternatives**: Manual iteration only.
- **Consequences**:
  - + scalable tuning for batch generation
  - + auditable improvements over time
  - − requires clear guardrails + telemetry to avoid runaway costs

### D006 — NSFW is a required label, not a hard blocker

- **Context**: The influencer use case may intentionally produce NSFW content; the system still needs classification for routing, policy, and downstream handling.
- **Choice**: Quality scoring MUST include NSFW classification, but the default QualityGate MUST NOT globally reject NSFW outputs. Instead, it should:
  - label outputs with an `nsfw_score`/`nsfw_class`
  - route outputs to the appropriate storage path/catalog
  - optionally enforce user-configured constraints (e.g., "only NSFW" / "only SFW" / "mixed")
- **Alternatives**: Always block NSFW.
- **Consequences**:
  - + supports the core use case while keeping metadata explicit
  - − requires careful defaults to avoid accidental mixing in downstream pipelines

### D007 — External workflow provenance is mandatory

- **Context**: Initial workflows may be sourced from third parties (“copying” examples). The system must remain maintainable and legally safe.
- **Choice**: Any externally sourced workflow MUST include provenance metadata (source URL/author, license/permission, date acquired) and be stored as an immutable baseline, with derived variants tracked.
- **Alternatives**: Ad-hoc copying.
- **Consequences**:
  - + enables reproducibility and responsible reuse
  - − requires lightweight metadata discipline
### D008 — Pydantic as default validation standard

- **Context**: ComfyCode needs consistent, developer-friendly validation for structured inputs/outputs (registry entries, manifests, configuration-like payloads, and any typed data exchanged between modules). JSON Schema is language-agnostic but adds drift risk and requires manual marshaling in Python.
- **Choice**: Use **Pydantic v2 models** as the **default** mechanism for runtime validation and typed data contracts in the Python codebase.
  - Pydantic models are the **source of truth** for validation rules and serialization.
  - JSON Schema may be **generated** from Pydantic for tooling and documentation, but is not the canonical contract.
- **Alternatives**: JSON Schema files with `jsonschema` validation; ad-hoc validation; dataclasses + manual checks.
- **Consequences**:
  - + Native Python type hints + IDE autocomplete
  - + Runtime validation with clearer error messages
  - + Automatic serialization/deserialization
  - + Models become single source of truth (no schema drift)
  - + Validators, computed fields, model inheritance supported
  - − Pydantic becomes a core dependency
  - − Minor version constraints (Pydantic v2+ required)

**Usage guidance**:
- Prefer Pydantic for any new “schema-like” validation (request/response payloads, manifests, registry entries, config objects).
- Use lightweight checks (simple `if`/`raise`) only for tiny invariants where introducing a model would be overkill.
- If external consumers need a language-agnostic contract, export JSON Schema from Pydantic rather than maintaining parallel schema files.
### D009 — RunPod as production GPU runtime

- **Context**: Need stable, controllable GPU compute for ComfyUI workloads with UI access for debugging and API-based production execution. Evaluated RunPod vs Google Colab.
- **Choice**: Use **RunPod** as the production GPU runtime platform.
  - Persistent pods with fixed GPU allocation and stable networking
  - Public port exposure without ngrok (ComfyUI UI on 8188, optional Jupyter on 8888)
  - Scriptable provisioning via API/CLI for CI/CD integration
  - Persistent volume support for models/outputs/datasets
  - Deterministic GPU selection (A10/A100/4090) with pay-per-use billing
- **Alternatives**: Google Colab (interactive, ephemeral, requires tunneling, limited automation); on-premise GPU infrastructure.
- **Consequences**:
  - + Stable service lifecycle for production workflows
  - + Reproducible GPU environment across runs
  - + Direct ingress without tunneling complexity
  - + API-driven provisioning supports CI/CD
  - + Persistent storage eliminates session loss
  - − Infrastructure cost (pay for uptime vs flat Colab subscription)
  - − Requires explicit security (access control, IP allowlisting, tokens)

**Deployment pattern**:
- ComfyUI server exposed on public port with token/basic auth
- Optional Jupyter Lab for interactive notebook exploration
- Mounted volume for models/LoRAs/datasets + Azure Blob for large artifact sync
- `comfycode.runpod_client` manages pod lifecycle

### D010 — Package-by-domain module structure

- **Context**: Project portability and maintainability require clear, stable module boundaries as the codebase grows beyond a small number of files.
- **Choice**: Organize Python code as **package-by-domain** submodules under `comfycode/` (incremental refactor, test-protected).
  - Target domains (illustrative): `cli/`, `clients/`, `workflows/`, `interop/`, `pipeline/`, `registry/`, `config/`.
  - Keep public surface area stable; if breaking changes are unavoidable, version explicitly.
- **Alternatives**: Keep a flat module layout; split by technical layer only.
- **Consequences**:
  - + Easier navigation and clearer ownership boundaries
  - + Improved testability (narrow dependencies)
  - − Refactor cost; requires staged migration and careful imports

### D011 — Pulumi as IaC for Azure persistence

- **Context**: Storage account + containers (and optional Tables) must be reproducible across environments.
- **Choice**: Use **Pulumi** (Python) as Infrastructure-as-Code for Azure persistence primitives.
  - IaC lives in-repo under a dedicated boundary (e.g., `infra/`).
  - Secrets must be managed via Pulumi config/secret providers and CI secrets, not committed.
- **Alternatives**: Manual provisioning; ARM/Bicep/Terraform.
- **Consequences**:
  - + Repeatable environments and safer changes via preview/apply
  - + Fits Python-first engineering stack
  - − Adds tooling surface and CI credentials management requirements

### D012 — CI/CD as the default change path

- **Context**: Production readiness requires automated quality gates and repeatable deployment.
- **Choice**: Establish CI/CD (e.g., GitHub Actions) for:
  - test/lint/build on PR
  - Pulumi preview on PR (optional but recommended)
  - Pulumi apply on main/tag with approval gates
  - artifact strategy for RunPod runtime (container image or template sync) explicitly defined
- **Alternatives**: Run everything manually from developer machines.
- **Consequences**:
  - + Safer, repeatable deployments
  - + Clear audit trail of infra/runtime changes
  - − Requires initial setup effort and secret management
---

## Roadmap Readiness

Interop capability has been implemented (Plan 003).

Next epic readiness (AI Influencer platform):
- Architecture has an agreed persistence strategy (file-based + Azure Blob + Azure Tables).
- Planning MUST define concrete folder conventions, index keys, and batch quality gates for the first vertical slice.

---

## AI Influencer Platform — Target Architecture (Pre-Planning Assessment)

This section scopes the AI Influencer epic(s). It is an architectural assessment and is not a claim that the components are already implemented.

### Workflow Taxonomy (Required)

Workflows MUST be organized by intent and have standardized contracts:

1) **LoRA workflows**
- Dataset curation/prep workflows (captioning, bucketing, face crop validation)
- Training workflows (external trainer integration; ComfyUI-based training if used)
- Evaluation workflows (fixed prompt suite → scored outputs)

2) **Instagram-style photo workflows**
- Portrait and lifestyle presets
- Outfit/application support (clothing references)
- Consistency controls (LoRA + reference images / adapters)

3) **Short video workflows**
- Image→video / video→video templates
- Identity lock (consistent face/body)
- Output slicing + thumbnail selection

### File-Based Artifact Registry (Required)

Artifacts are stored as files with JSON metadata.

Source of truth split:
- **Repo (git)**: small metadata and indexes (text files)
- **Blob**: large binaries and images
- **Tables (optional)**: thin lookup mirror for faster access

Repo layout (workspace-relative conceptual):
- `registry/models/{model_id}.json`
- `registry/loras/{lora_id}.json`
- `registry/datasets/{dataset_id}.json`
- `registry/characters/{character_id}.json`
- `registry/clothing/{item_id}.json`
- `workflows/photo/...`
- `workflows/lora/...`
- `workflows/video/...`

All registry entries MUST reference blob assets by `blob_uri` (or prefix) and include a content hash (e.g., sha256) when applicable.

Canonical storage (Blob) layout (conceptual):
- `artifacts/models/{model_id}/model.safetensors`
- `artifacts/models/{model_id}/metadata.json`
- `artifacts/loras/{lora_id}/lora.safetensors`
- `artifacts/loras/{lora_id}/metadata.json`
- `artifacts/datasets/{dataset_id}/manifest.json`
- `artifacts/datasets/{dataset_id}/images/...`
- `characters/{character_id}/profile.json`
- `characters/{character_id}/reference_images/...`
- `clothing/{item_id}/images/...`
- `clothing/{item_id}/metadata.json`

Azure Tables (lookup) entities (minimum viable):
- **Characters**: `PartitionKey="character"`, `RowKey=character_id`, `blob_prefix`, `status`, `updated_at`
- **LoRAs**: `PartitionKey="lora"`, `RowKey=lora_id`, `blob_prefix`, `character_id`, `base_model_id`, `updated_at`
- **Clothing**: `PartitionKey="clothing"`, `RowKey=item_id`, `blob_prefix`, `tags`

### Batch Generation + Variant Management (Required)

Batch generation is a first-class workflow:
- Generate N variants (seeds / prompts / control params)
- Score outputs (aesthetic, face consistency, NSFW classification, artifact detection)
- Select top-K and record provenance (workflow version + parameters + artifact IDs)

NSFW handling requirements:
- NSFW MUST be scored/labeled.
- Output selection MAY filter by NSFW class depending on the run goal, but NSFW content is not globally blocked.

### Agent Roles (Required)

Agents are scoped services that produce proposals + records:
- **Workflow Expert**: ComfyUI workflow specialist with deep knowledge of nodes, models, parameters, and best practices. Creates, improves, and validates workflows. Knows model compatibility (SD1.5/SDXL/Flux), LoRA application, sampling parameters, and node selection. Ensures workflows follow taxonomy (photo/lora/video) and provenance requirements. Handoff to Implementer for ComfyCode Python translation.
- **WorkflowTuner**: suggests prompt/control parameter changes for better realism/consistency.
- **VariantPlanner**: generates parameter grids for batch runs (seeds/outfits/poses).
- **QualityGate**: scores and filters outputs; outputs structured reasons; includes NSFW labeling + routing.
- **LoRATrainer**: orchestrates training job execution and registers resulting LoRA artifact.
- **DatasetCurator**: manages clothing/character reference sets and dataset manifests.

### Workflow Sourcing & Baselines (Required)

Initial workflow development may be based on third-party examples.

Requirements:
- Store sourced workflows under the workflow taxonomy with an explicit provenance block (source/author/license/date).
- Treat the sourced workflow as an immutable baseline; track modifications as derived variants.
- Do not embed or redistribute proprietary assets without permission.

### Auto-Updating Documentation (Required)

Documentation MUST be generated from the source-of-truth inventories:
- Workflow library inventory (by taxonomy)
- Artifact registry summaries (models/loras/datasets)
- Character/clothing catalog summaries

The generator should run in CI (or a local command) and update docs deterministically from repo + blob manifests.


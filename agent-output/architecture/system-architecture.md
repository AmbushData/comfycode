# System Architecture — ComfyCode

**Last Updated**: 2026-02-22
**Owner**: Architect
**Status**: Current

## Changelog

| Date | Change | Rationale | Related |
|------|--------|-----------|---------|
| 2026-02-22 | Initial architecture doc created | Establish source-of-truth; capture implemented docs/tooling work and upcoming bidirectional conversion design | Plans 001–002; UX request (JSON↔Python↔UI) |

---

## Purpose

ComfyCode is a developer-focused Python framework for building and executing ComfyUI workflows programmatically, with optional infrastructure management (RunPod) and a CLI that converts ComfyUI prompt JSON into Python code.

A key product requirement emerging from QA + user feedback is a **flexible user experience**:
- Stay Python-first (avoid relying on the ComfyUI UI for day-to-day work)
- Still allow occasional UI usage for exploration/debugging
- Preserve or generate **visually pleasing node layouts** when exporting workflows for the UI
- Support **bidirectional conversion** (JSON→code and code→JSON)

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

### Interop Goals (New)

To support UI interop, ComfyCode needs to represent workflows at **two different JSON layers**:

1) **Prompt JSON** (API prompt format):
- Data shape: `{ node_id: { class_type, inputs } }`
- Used by: ComfyUI HTTP API
- Currently supported by: `Workflow.build()`, `converter.convert()` (JSON→Python)

2) **UI Workflow JSON** (ComfyUI UI export/import format):
- Includes: node positions, sizes, UI metadata (exact schema varies by ComfyUI version)
- Used by: ComfyUI web UI
- Not currently supported

---

## Proposed Design: Bidirectional Conversion via an Intermediate Representation (IR)

### Why an IR

Direct conversion between every pair (Python↔prompt JSON↔UI JSON) tends to be brittle and lossy.

A stable **Workflow IR** keeps the system flexible and makes layout generation a first-class concern without leaking UI details into runtime submission.

### Workflow IR (Conceptual)

A minimal IR should capture:
- `nodes`: `id`, `class_type`, `inputs`
- `edges`: derived from link inputs (node_id + slot references)
- `metadata` (optional): human-friendly names, grouping/stages, layout hints

### Conversion Matrix (Target)

- **Prompt JSON → IR**: parse nodes/inputs; infer edges.
- **IR → Python**: generate `workflow.add_node(...)` calls; preserve wiring.
- **Python → IR**: prefer *execution-based export* (run code to produce prompt dict; then parse prompt dict → IR).
  - Avoid static Python AST parsing initially; it is fragile and hard to support.
- **IR → Prompt JSON**: straightforward serialization.
- **IR → UI Workflow JSON**: generate UI nodes + links + **layout**.
- **UI Workflow JSON → IR**: parse UI export; map to nodes/links; preserve positions in metadata.

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
  - Add new subcommands later (proposal):
    - `comfycode export <python_file> --prompt-json out.json`
    - `comfycode export <python_file> --ui-json out_ui.json --layout auto`
    - `comfycode convert-ui <ui.json> --python out.py`

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

---

## Quality Attributes

- **Maintainability**: IR isolates UI schema churn from core workflow submission.
- **Correctness**: execution-based export ensures “code→JSON” matches runtime behavior.
- **Reproducibility**: deterministic layout + `uv.lock` support stable environments.
- **UX Flexibility**: Python-first workflow remains primary; UI is optional tooling.

---

## Problem Areas / Design Debt

- Current `converter.convert()` supports only the prompt dict API JSON, not UI export JSON.
- There is no explicit format contract module describing prompt JSON vs UI JSON.
- Layout metadata is not modeled; UI import/export is currently unsupported.

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

---

## Roadmap Readiness

This capability should be tracked as a dedicated future epic (post-Epic 0.1 docs), since it introduces new user-facing functionality and format contracts.

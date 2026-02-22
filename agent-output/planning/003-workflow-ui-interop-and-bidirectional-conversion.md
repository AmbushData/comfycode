---
ID: 003
Origin: 003
UUID: 8a4c2d1f
Status: QA Complete
---

# Plan 003 — Workflow UI Interop & Bidirectional Conversion (Epic 0.7)

**Target Release:** v0.2.0
**Epic Alignment:** Epic 0.7 — Workflow UI Interop & Bidirectional Conversion
**Created:** 2026-02-22

## Change Log

| Date | Agent | Change | Notes |
|------|-------|--------|-------|
| 2026-02-22 | Planner | Created plan | Initial plan to deliver flexible UX via bidirectional conversion + deterministic layout |
| 2026-02-22 | Planner | Resolved blocking question | Target current stable ComfyUI; ready for Critic |
| 2026-02-22 | User | Confirmed design | Prompt JSON canonical; UI JSON opt-in for viewing |
| 2026-02-22 | Critic | Approved | 4 findings (1 MEDIUM, 3 LOW); addressed before implementer handoff |
| 2026-02-22 | Planner | Addressed critique findings | Added dependencies, resolved open questions, clarified export guardrails + IR versioning |
| 2026-02-22 | Implementer | Started implementation | Milestones 1-6 in progress |
| 2026-02-22 | Implementer | Completed Milestones 1-6 | Ready for QA |
| 2026-02-22 | QA | QA Complete | Full test suite passing; manual ComfyUI import deferred to UAT |

---

## Value Statement and Business Objective

As a **developer building ComfyCode workflows in Python**, I want **to convert workflows both ways (Python ↔ ComfyUI JSON) and optionally open them in the ComfyUI UI with readable layout**, so that **I can iterate programmatically most of the time while still using the UI when it’s helpful**.

## Objective

Deliver the minimum set of APIs/CLI that enable:
- **JSON → Python** (keep existing capability stable)
- **Python → prompt JSON** export (ComfyUI API prompt format)
- **prompt JSON → UI workflow JSON** export with deterministic, non-overlapping, visually pleasant node placement

## Architecture Alignment

Aligned to the proposed design in:
- `agent-output/architecture/system-architecture.md` (IR + deterministic layout + execution-based export)
- `agent-output/architecture/system-architecture-diagram.mmd`

## Dependencies

- **Plan 001 / Plan 002 completion**: This plan assumes developer tooling + docs baseline from Epic 0.1 is already implemented and validated.
- **Release sequencing**: v0.1.1 work (Epic 0.1) should be released/merged before starting v0.2.0 implementation to avoid rebasing churn and doc/tooling mismatches.

## Scope

**In scope**
- Introduce an internal **Workflow IR** representation for conversion and layout
- Add conversion utilities for:
  - prompt JSON ↔ IR
  - IR → Python source generation (re-using or refactoring the existing converter)
  - IR → UI workflow JSON export (first supported schema/version documented)
- Add an **execution-based** Python→prompt JSON export entrypoint with guardrails
- Add deterministic layout generation for UI export (layered DAG layout; no overlap by default)
- Update README/docs to explain the new workflows and the limitations

**Out of scope**
- Static Python AST parsing of arbitrary Python workflow code
- Building a GUI, web UI, or any new interactive editor
- Implementing advanced layout optimization (crossing minimization beyond MVP)
- Full support for every ComfyUI UI export schema/version
- UI workflow JSON → IR (UI JSON import) in v0.2.0 (explicitly deferred)

## Assumptions

- The repo will treat **prompt JSON** (ComfyUI API prompt dict) as canonical for execution.
- **UI workflow JSON** is an optional "view" format for debugging/exploration in the ComfyUI web interface — not a runtime format.
- UI workflow JSON schema differences exist; we will support **one documented target schema/version** initially.
- "Code → JSON" export is limited to workflows built via ComfyCode's APIs or a documented entrypoint contract.
- **IR is internal-only** in v0.2.0 (used as a conversion/layout implementation detail), and is not persisted as a stable, user-facing file format.

## Design Decision

**Prompt JSON is canonical; UI JSON is opt-in for viewing.**

| Format | Role | When used |
|--------|------|-----------|
| Prompt JSON | Runtime execution format | Always — `Workflow.build()` produces this |
| UI JSON | Visual debugging format | Only when exporting for ComfyUI web UI |

This keeps daily workflow simple (Python → prompt JSON → API) and avoids coupling to UI schema churn.

## OPEN QUESTION [RESOLVED]

- Which ComfyUI UI workflow JSON schema/version should be the initial target for import/export?
  - **Resolution**: Target the current stable ComfyUI release's UI export format at time of implementation. Document the supported schema in code. Note any known incompatibilities with older/newer versions in docs.

## OPEN QUESTION [RESOLVED]

- Do we want UI JSON import in v0.2.0, or only export (Python/prompt JSON → UI JSON) initially?
  - **Resolution**: **Export-only in v0.2.0.** UI JSON import is deferred to a future release.

## OPEN QUESTION [RESOLVED]

- What guardrails are acceptable for execution-based export?
  - **Resolution**: Require a **single explicit entrypoint function** (e.g., `create_workflow()`) that returns a ComfyCode `Workflow` instance (or a prompt dict). The export tool will only call that entrypoint and will document that other side effects in module import/entrypoint execution are the user's responsibility.

---

## Plan

### 1) Define Format Contracts (Prompt vs UI)

**Owner:** Implementer

**Tasks**
1. Document and codify the supported **prompt JSON** structure (current).
2. Document and codify the supported **UI workflow JSON** structure (initial target).
3. Define explicit “lossiness” expectations (what metadata is preserved vs dropped).

**Acceptance criteria**
- A single source-of-truth module/doc identifies:
  - prompt JSON schema used for execution
  - UI JSON schema used for UI interop
  - supported/unsupported fields

### 2) Introduce Workflow IR

**Owner:** Implementer

**Tasks**
1. Create IR model capturing nodes/edges/metadata (including optional layout hints).
2. Implement prompt JSON → IR and IR → prompt JSON.

**Acceptance criteria**
- Round-trip: prompt JSON → IR → prompt JSON yields equivalent execution graph
- IR is treated as an internal implementation detail (no requirement to persist IR to disk)

### 3) JSON → Python (Preserve and Stabilize)

**Owner:** Implementer

**Tasks**
1. Refactor existing JSON→Python converter to operate via IR (or document why not).
2. Ensure deterministic output ordering and readable formatting remain.

**Acceptance criteria**
- Existing CLI flow (`python -m comfycode <prompt.json>`) continues to work

### 4) Python → prompt JSON Export (Execution-Based)

**Owner:** Implementer

**Tasks**
1. Define a supported entrypoint contract for export: **a single explicit function** (e.g., `create_workflow()`) returning a `Workflow` (or prompt dict).
2. Add a CLI/API path that executes the entrypoint and serializes **prompt JSON**.
3. Add guardrails and clear failure modes (documentation + safe defaults) aligned to the contract (only call the entrypoint; do not attempt to execute arbitrary symbols).

**Acceptance criteria**
- A user can take a supported ComfyCode workflow module and export a prompt JSON file that ComfyUI API accepts

### 5) prompt JSON → UI JSON Export with Deterministic Layout

**Owner:** Implementer

**Tasks**
1. Implement deterministic layout generation (layered DAG layout; stable ordering; spacing parameters).
2. Implement IR → UI JSON export including positions.
3. Ensure layout avoids node overlap by default.

**Acceptance criteria**
- Exported UI JSON imports into ComfyUI UI
- Nodes are placed deterministically and are readable (no overlap; left-to-right flow)

### 6) Documentation Updates

**Owner:** Implementer

**Tasks**
1. Document conversion flows and when to use each (Python-first vs UI-assisted).
2. Document limitations (supported schema/version, export contract, what metadata is preserved).

**Acceptance criteria**
- README includes a “UI Interop” section with working commands/examples

### 7) Update Version and Release Artifacts

**Owner:** DevOps

**Tasks**
1. Update version to match the target release grouping.
2. Update release notes/changelog artifacts if used.

**Acceptance criteria**
- Version metadata and release artifacts reflect the new conversion capability

---

## Validation

- Unit tests for IR round-trips and deterministic layout.
- Integration validation:
  - Convert `workflows/*.json` → Python and confirm output runs/builds prompt JSON
  - Export Python → prompt JSON and validate it matches expected schema
  - Export prompt JSON → UI JSON and validate it can be loaded in ComfyUI UI

## Testing Strategy (High Level)

- **Unit**: IR parsing/serialization, layout determinism and non-overlap guarantees.
- **Integration**: CLI conversion and export commands operating on sample workflows.

## Risks / Notes

- ComfyUI UI JSON schema churn: mitigate by supporting one documented schema first and isolating it behind format-contract modules.
- Execution-based export safety: mitigate with a narrow entrypoint contract and explicit documentation.
- Layout “pleasantness” is subjective: mitigate by deterministic, readable baseline and allowing spacing configuration.

## Handoff

Plan is Critic-approved and ready for implementer handoff.

**Next:** Implementer executes milestones 1–6; DevOps executes milestone 7.

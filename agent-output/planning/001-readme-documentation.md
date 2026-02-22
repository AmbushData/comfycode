---
ID: 001
Origin: 001
UUID: 9c7a1f2b
Status: In Progress
---

# Plan 001 — README Developer Onboarding (Epic 0.1)

**Target Release: v0.1.1**
**Epic Alignment:** Epic 0.1 — Comprehensive Developer Documentation
**Created:** 2026-02-22

## Change Log
| Date | Agent | Change | Notes |
|------|-------|--------|-------|
| 2026-02-22 | Planner | Created plan | Initial plan for Epic 0.1 (README onboarding) |
| 2026-02-22 | Implementer | Started implementation | Critic approved; addressing F001 during impl |

---

## Value Statement and Business Objective

As a **developer evaluating ComfyCode**, I want **clear, complete documentation with quick-start examples**, so that **I can understand the value proposition, install the package, and run my first workflow without external help**.

## Objective
Deliver a single-file README that enables a new developer to:
- Understand what ComfyCode is and where it fits (ComfyUI + RunPod)
- Install it correctly
- Successfully run at least one “first success” command locally (converter flow)
- Understand how to configure and use the Python API for real workflow execution
- Contribute and run tests

## Scope

**In scope**
- Update `README.md` to satisfy Epic 0.1 acceptance criteria (single file)
- Ensure documentation is consistent with current public APIs and defaults
- Ensure examples reference real commands and shipped example workflows

**Out of scope**
- New features, refactors, new modules, or behavior changes in runtime code
- New documentation website or multiple doc pages for v0.1.x
- Expanding CLI surface area beyond documenting what already exists

## Context (Repository Facts to Stay Accurate)
- CLI exists via `python -m comfycode <workflow.json>` and console script `comfycode <workflow.json>` (JSON → Python converter)
- Configuration is via environment variables and `Config` attributes
- Current env vars used by `Config`:
  - `RUNPOD_API_KEY`, `RUNPOD_TEMPLATE_ID`, `RUNPOD_GPU_TYPE`
  - `COMFYUI_HOST`, `COMFYUI_PORT`, `COMFYUI_TIMEOUT`
  - `OUTPUT_DIR`
- Example workflows exist in `workflows/` (e.g., `txt2img.json`, `img2img.json`)

## Assumptions
- “First workflow” success for onboarding can be satisfied by running the converter against `workflows/txt2img.json` (no external services required)
- The README will also describe the *optional* execution path (requires a running ComfyUI server and optionally RunPod)
- README length target: ~200–400 lines (concise but complete)

## OPEN QUESTION [CLOSED]
- None identified for this epic at this time.

---

## Plan

### 1) Requirements & Accuracy Pass
**Owner:** Implementer

**Tasks**
1. Inventory current public entry points and defaults (CLI, `Config`, key classes)
2. Identify minimum “first success” path that is runnable without external services
3. Confirm README claims match code/module structure (config → runpod → comfyui → workflow → batch → pipeline)

**Acceptance criteria**
- README outline is defined and maps 1:1 to Epic 0.1 acceptance criteria
- No README section depends on undocumented, non-existent APIs

### 2) Rewrite `README.md` (Single File)
**Owner:** Implementer

**Tasks**
1. Add a crisp overview section (what/why)
2. Add “Key Features” section (workflow builder, JSON→Python converter, ComfyUI execution, RunPod provisioning, batching/pipeline)
3. Add “Installation” section
   - Include Python requirement
   - Include `pip install -e .` (dev) and `pip install .` (local install)
4. Add “Quick Start (CLI)” section
   - Demonstrate converting `workflows/txt2img.json` to Python
   - Document `-o/--output` behavior
5. Add “Quick Start (Python)” section
   - Show a minimal example building a workflow programmatically and how it would be executed via the client/pipeline
   - Clearly separate: (a) building a workflow dict vs (b) executing against a running ComfyUI server
6. Add “Configuration” section
   - Document env vars listed in `Config`
   - Document defaults (e.g., host `127.0.0.1`, port `8188`, output dir `./output`)
7. Add “Architecture” section
   - One-paragraph explanation of each layer/module and how they compose
8. Add “API Summary” section
   - Brief descriptions for: `Config`, `RunPodClient`, `ComfyUIClient`, `Workflow`, `BatchProcessor`, `Pipeline`
9. Add “Development” section
   - How to run unit tests
   - Style expectations only if already established (avoid inventing new conventions)
10. Add “License” section referencing MIT

**Acceptance criteria (Epic 0.1 mapping)**
- README includes installation instructions (pip install)
- README demonstrates CLI usage with a concrete example
- README shows a Python API usage example
- README documents required env vars / configuration
- README explains architectural layers (6 modules)
- README includes API reference summary for key classes
- README provides development setup and test-running instructions

### 3) Validation (Non-QA)
**Owner:** Implementer

**Tasks**
1. Run converter quick-start command locally using the repo’s `workflows/*.json`
2. Run existing unit tests
3. Spot-check README for broken commands, missing prerequisites, and clarity

**Acceptance criteria**
- Converter quick-start command completes successfully (generates Python to stdout or output file)
- `pytest` passes

### 4) Version Management & Release Artifacts
**Owner:** DevOps (with Implementer support)

**Goal**: Ensure artifacts align to Target Release v0.1.1.

**Tasks**
1. Bump version `0.1.0` → `0.1.1` in packaging metadata
2. Ensure Python version constraints are consistent across packaging files
3. Update changelog/release notes *if a changelog exists* (do not create new docs unless requested)

**Acceptance criteria**
- Packaging metadata reports v0.1.1 consistently
- Python requirement is consistent and matches intended support policy

---

## Testing Strategy (High-Level)
- Unit tests: run existing `pytest` suite (no new QA test cases defined here)
- Smoke checks: run the documented CLI converter example(s)

## Risks & Mitigations
- **Risk:** README becomes too long / unfocused → keep a strict outline and prioritize “first success”
- **Risk:** Docs drift from code → verify against `Config` env vars and CLI behavior during validation
- **Risk:** External-service steps (RunPod/ComfyUI) confuse new users → clearly mark prerequisites and keep optional path separate

## Rollback
- If the README changes are unclear or inaccurate, revert `README.md` edits and re-apply with a tighter outline
- If version/artifact updates cause packaging inconsistencies, revert version bump and re-attempt with a single source of truth

## Handoff Notes
- Next step is Critic review of this plan for scope discipline and measurability.
- After Critic approval, Implementer executes README updates; DevOps handles version/artifact alignment for v0.1.1.

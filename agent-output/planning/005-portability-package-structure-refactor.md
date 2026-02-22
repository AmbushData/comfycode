---
ID: 005
Origin: 005
UUID: 9e3a7c1d
Status: Active
---

# Plan 005 — Portability: Package-by-Domain Structure Refactor

**Target Release:** v0.3.0
**Semver Rationale:** Patch/minor within the v0.3.0 release group; primarily internal re-organization for portability/maintainability (confirm with roadmap).
**Epic Alignment:** Production readiness foundation (supports AI Influencer MVP evolution)
**Created:** 2026-02-22

## Change Log

| Date | Agent | Change | Notes |
|------|-------|--------|-------|
| 2026-02-22 | Planner | Created plan | Implements D010 package-by-domain boundaries; portability requirements from Findings 004 |

---

## Value Statement and Business Objective

As a **team moving ComfyCode toward production**, I want a **portable, maintainable Python package structure with logical submodules**, so that **contributors can navigate, test, and ship changes safely as the codebase grows**.

## Objective

1. Establish clear Python module boundaries under `comfycode/` aligned to product domains.
2. Reduce ambiguity between source vs generated artifacts (e.g., `*.egg-info`).
3. Preserve public API expectations while enabling scalable growth.

## Architecture Alignment (Non‑Negotiable)

- D010 — Package-by-domain module structure
- D008 — Pydantic as default validation standard
- Findings 004 — Portability/IaC/CI/CD requirements

## Scope

**In scope**
- Define a target module map (package-by-domain) and migrate existing modules incrementally.
- Ensure imports and public entrypoints remain stable (or are versioned deliberately).
- Update internal references and tests to match new locations.
- Establish build-artifact hygiene: treat `*.egg-info/` as generated output (not source-of-truth).

**Out of scope**
- Feature development unrelated to portability.
- Large behavior changes to runtime logic beyond what is required to preserve behavior during refactor.

## Constraints (Non‑Negotiable)

- Refactor MUST be incremental and test-protected; no “big bang” churn.
- Pydantic remains the default for structured validation.
- Generated artifacts (e.g., `*.egg-info`) MUST NOT be committed or treated as canonical source.

## Assumptions

- Existing test suite provides sufficient safety net for incremental module moves.

## OPEN QUESTION [CLOSED]

- Release grouping: **CLOSED**. This refactor is required for portability/maintainability and can be executed without changing external behavior when done with compatibility shims/re-exports. It can ship as part of the v0.3.0 release group unless the roadmap explicitly splits it out.

---

## Plan

### 1) Define Target Package Map

**Owner:** Implementer

**Tasks**
1. Propose target subpackages under `comfycode/` (per D010) and map current modules into them.
2. Identify public entrypoints that MUST remain stable (CLI, core imports).

**Acceptance criteria**
- Target package map is documented in the implementation doc and reviewed against architecture.

### 2) Incremental Module Migration

**Owner:** Implementer

**Tasks**
1. Move modules into the new subpackages in small batches.
2. Keep import compatibility where reasonable (re-export symbols in `__init__.py` or provide compatibility shims).
3. Update tests and any CLI entrypoints to import from the new locations.

**Acceptance criteria**
- All tests pass after each migration batch.
- Public CLI entrypoints remain functional.

### 3) Build Artifact Hygiene

**Owner:** Implementer

**Tasks**
1. Ensure `*.egg-info/` is treated as generated output (gitignore/cleanup guidance).
2. Document the uv-based developer workflow to avoid committing build outputs.

**Acceptance criteria**
- Repo no longer treats `comfycode.egg-info/` as a source directory.

### 4) Documentation Update

**Owner:** Implementer

**Tasks**
1. Update README/dev docs to reflect the new module layout.
2. Update any architecture references if module names/paths change.

**Acceptance criteria**
- Documentation points to the correct modules/subpackages.

### 5) Version and Release Artifacts

**Owner:** DevOps

**Tasks**
1. Confirm whether this plan changes external API surface.
2. Apply versioning and changelog updates consistent with the target release group.

**Acceptance criteria**
- Version artifacts and release notes accurately reflect the refactor and compatibility posture.

---

## Validation

- Full unit test suite passes.
- Smoke test CLI commands (`convert`, `export`) after refactor.

## Risks

- Import path churn breaking downstream usage; mitigate via re-exports/compat shims and clear release notes.
- Hidden coupling between modules; mitigate by moving in small batches and keeping tests green.

## Rollback

- Revert module moves and compatibility shims; keep changes small and batchable.

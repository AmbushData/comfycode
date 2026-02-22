---
ID: 002
Origin: 002
UUID: 6f2b0c9e
Status: Implemented
---

# Plan 002 — uv sync + Dev Dependencies + README Corrections

**Target Release:** v0.1.1
**Epic Alignment:** Epic 0.1 — Comprehensive Developer Documentation
**Created:** 2026-02-22

## Change Log

| Date | Agent | Change | Notes |
|------|-------|--------|-------|
| 2026-02-22 | Planner | Created plan | Follow-up based on QA findings from Plan 001 |
| 2026-02-22 | Planner | Handoff to Critic | User approved handoff; ready for critique |
| 2026-02-22 | Critic | Approved | 4 findings (1 MEDIUM, 3 LOW); see critique |
| 2026-02-22 | Implementer | Milestones 1–4 complete | See implementation doc |

---

## Context (Why This Plan Exists)

QA execution for Plan 001 validated core onboarding flows (tests + CLI converter), but flagged documentation correctness issues and a desire to standardize setup using `uv`.

Key QA findings (from `agent-output/qa/001-readme-documentation-qa.md`):
- README links to `LICENSE`, but no `LICENSE` file exists
- README suggests `pytest --cov...`, but `pytest-cov` is not installed/declared
- README suggests `pip install -e ".[dev]"`, but no `dev` extra exists
- README clone URL uses a placeholder (`your-org`)

---

## Value Statement and Business Objective

As a **developer evaluating or contributing to ComfyCode**, I want **a reproducible setup workflow (`uv sync`) and accurate development documentation**, so that **I can run tests and documentation commands reliably without debugging dependency/tooling mismatches**.

## Objective

Make developer setup reproducible and documentation accurate by:
- Supporting a lockfile-based workflow via `uv sync`
- Declaring runtime + dev dependencies in `pyproject.toml`
- Ensuring README development commands work as written

## Assumptions

- `uv` is an approved dependency management tool for this repo going forward.
- It is acceptable to treat `pyproject.toml` as the dependency source of truth.
- Adding a lockfile (`uv.lock`) is acceptable to commit to the repository.

## OPEN QUESTION (Non-blocking)

- What is the canonical repository URL to use in README clone instructions?
- Should `requirements.txt` remain supported (kept in sync) or be deprecated in favor of `pyproject.toml` + `uv.lock`?

## Scope

**In scope**
- Add runtime dependencies to `pyproject.toml` (remove duplication / clarify relationship with `requirements.txt`)
- Add dev extras (pytest, pytest-cov, etc.)
- Add `uv.lock` and `uv`-based setup instructions
- Fix README inaccuracies: clone URL, dev install command, coverage command, license link

**Out of scope**
- Changing runtime behavior of `comfycode`
- Adding CI pipelines (unless already present and minimal update is required)
- Refactoring modules or adding features

## Plan

### 1) Define Dependencies in `pyproject.toml`

**Owner:** Implementer

**Tasks**
- Add `[project].dependencies` mirroring runtime deps currently in `requirements.txt`:
  - `requests>=2.31.0`
  - `websocket-client>=1.7.0`
  - `Pillow>=10.0.0`
- Add `[project.optional-dependencies]` with at least:
  - `dev = ["pytest", "pytest-cov"]`

**Acceptance criteria**
- `pip install -e ".[dev]"` installs without warnings about missing extras

### 2) Adopt `uv sync` (Lockfile-Driven)

**Owner:** Implementer

**Tasks**
- Generate and commit a lockfile:
  - `uv lock`
- Ensure `uv sync` brings up a working environment:
  - `uv sync --all-extras`
- Optionally document `uv run pytest` as the canonical test invocation

**Acceptance criteria**
- On a fresh checkout: `uv sync --all-extras` then `uv run pytest -q` passes

### 3) Correct README “Development” Section

**Owner:** Implementer

**Tasks**
- Update clone URL to the real repository URL (or remove the URL and keep it generic without placeholders)
- Update dev install instructions to one of:
  - `uv sync --all-extras` (preferred), or
  - `pip install -e ".[dev]"`
- Update coverage instructions to either:
  - `uv run pytest --cov=comfycode --cov-report=term-missing`, or
  - explicitly mention installing `pytest-cov`

**Acceptance criteria**
- Every README command in “Development” runs successfully in a clean environment

### 4) License Link Correctness

**Owner:** Implementer

**Tasks**
- Either add a root `LICENSE` file (MIT), or adjust README to reference the correct location.

**Acceptance criteria**
- README license link is not broken

### 5) Update Version and Release Artifacts

**Owner:** DevOps

**Tasks**
- Ensure the release version matches the roadmap target release (`v0.1.1`) across packaging artifacts.
- Add or update release notes/changelog artifacts if the project uses them.

**Acceptance criteria**
- Version is consistent across the repo’s packaging metadata.
- Release artifacts accurately reflect the dependency/tooling changes.

## Validation

Run in a clean environment:

```bash
uv sync --all-extras
uv run python -m comfycode workflows/txt2img.json
uv run pytest -q
uv run pytest --cov=comfycode --cov-report=term-missing
```

## Testing Strategy (High Level)

- **Unit**: existing pytest suite must pass.
- **Documentation validation**: README commands must run successfully in a clean environment created via `uv sync`.
- **Packaging**: editable install should work with and without dev extras.

## Risks / Notes

- If `requirements.txt` is still desired for downstream consumers, document the source-of-truth (prefer `pyproject.toml`) and keep `requirements.txt` in sync.
- Avoid introducing new “style rules” in README unless the formatter/linter is actually configured in-repo.

## Handoff

- **Next:** Critic review of this plan (scope/measurability/risk).
- **After Critic approval:** Implementer executes tasks 1–4; DevOps executes milestone 5.

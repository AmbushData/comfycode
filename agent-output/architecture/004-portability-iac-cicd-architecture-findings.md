---
ID: 004
Origin: 004
UUID: 4f9b1c2e
Status: Active
---

# Architecture Findings 004 — Portability, Packaging, IaC (Pulumi), CI/CD, and RunPod Runtime

**Date**: 2026-02-22
**Trigger**: User request to prioritize project portability and production readiness (clear package structure, IaC, CI/CD, and GPU runtime strategy).

## Context

The project is moving from “developer tool + experimentation” toward **production** workloads for ComfyUI-based pipelines (AI influencer vertical). This requires:
- A portable, maintainable Python package layout
- A reproducible build/story under `uv`
- Infrastructure-as-code for Azure Storage (and related dependencies)
- CI/CD for test/build/deploy
- A clear GPU runtime model (chosen: RunPod) including optional UI + notebook exploration

Constraints already established:
- Azure-first persistence primitives
- Pydantic is the default validation standard (D008)
- RunPod is the production GPU runtime (D009)

## Current Observations (Repo State)

- Python package is functional, but most modules are flat under `comfycode/`.
- Registry is already cleanly grouped as `comfycode/registry/`.
- There is no IaC directory or Pulumi project in-repo.
- CI/CD is not defined in `agent-output/devops/` nor as GitHub Actions workflows.
- Build artifacts like `comfycode.egg-info/` can exist locally; they should not be treated as source.

## Architectural Requirements (Before Planning)

### R1 — Portable Python package boundaries

The codebase MUST evolve to a “package-by-domain” structure so it remains navigable and testable as features expand.

Minimum target grouping (illustrative):
- `comfycode/cli/` — CLI entrypoints and subcommands
- `comfycode/clients/` — RunPod/ComfyUI clients and transport concerns
- `comfycode/workflows/` — workflow builder and workflow composition (Python-first)
- `comfycode/interop/` — prompt JSON, UI JSON, IR, layout, export/convert tooling
- `comfycode/pipeline/` — batch + pipeline orchestration
- `comfycode/registry/` — registry models/loader/generator (already exists)
- `comfycode/config/` — configuration and settings models (Pydantic)

Non-goals:
- A “massive refactor” without tests. Migration must be incremental and test-protected.

### R2 — Build artifact hygiene under uv

- `*.egg-info/` is a build/install artifact and MUST NOT be a source-of-truth directory.
- The repo should treat it as generated output (ignored/cleaned), regardless of whether `uv` or `pip` is used.

### R3 — IaC for Azure Storage via Pulumi

We need reproducible provisioning for:
- Storage account
- Blob container(s) for artifacts/images/outputs
- (Optional) Table storage resources

Pulumi standards:
- IaC should be part of the repo under a dedicated boundary (e.g., `infra/`)
- Use Pulumi config for secrets; do not commit credentials

### R4 — Single settings schema (App + IaC)

A single Pydantic “settings schema” SHOULD define non-secret settings used by both:
- the application (ComfyCode runtime)
- the Pulumi stack (resource naming, containers, regions, tags)

This avoids drift between “what the app expects” and “what infra provides”.

### R5 — CI/CD baseline

Minimum CI/CD must support:
- Unit tests + packaging checks on PR
- Optional: Pulumi preview on PR
- Deploy: Pulumi up on main/tag, gated by approvals
- Artifact publishing strategy for RunPod (container image or template sync) must be explicitly chosen

### R6 — RunPod runtime model (UI + API + notebooks)

RunPod is not “only serverless scripts”. We must support two operational modes:
1) **Exploration**: run ComfyUI UI (8188) + optional Jupyter (8888) on a persistent pod, secured
2) **Production**: run batch scripts / pipeline execution on ephemeral or long-lived pods, with persistent volumes and Azure Blob sync

## Alternatives Considered

- Google Colab + ngrok tunnels: viable for ad-hoc exploration but brittle for production, limited automation, and unstable runtime lifecycle.
- Always-on managed DB for registry/search: violates cost-minimized constraints for MVP; keep file + Blob strategy.

## Risks / Architecture Debt

- Large package refactors can cause churn; must be staged and validated.
- IaC + app settings drift if multiple config formats proliferate.
- Exposing ComfyUI/Jupyter over public ports introduces security risks; must define a security baseline (token + IP allowlist + no secrets in notebooks).

## Integration Requirements (What planners/implementers MUST include)

- A migration plan for module grouping that preserves public APIs or explicitly versions changes.
- A Pulumi project skeleton with:
  - settings inputs
  - outputs (storage account name, container URLs)
  - secure secret handling
- A CI/CD definition that gates deploy and keeps credentials out of git.
- A documented RunPod operational runbook for:
  - starting a pod
  - exposing UI + notebook ports
  - persisting volumes
  - syncing artifacts with Azure Blob

## Verdict

**APPROVED_WITH_CHANGES** for moving forward to planning.

Planning MUST first incorporate the above requirements, especially: package boundaries (R1), Pulumi IaC + settings contract (R3–R4), and CI/CD baseline (R5).

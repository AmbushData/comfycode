---
ID: 006
Origin: 006
UUID: 3b4f8a20
Status: Active
---

# Plan 006 — Pulumi IaC: Azure Storage Account + Containers (AI Influencer)

**Target Release:** v0.3.0
**Semver Rationale:** Operational capability; may not require a package version bump but must be tracked in the v0.3.0 release group (confirm with roadmap).
**Epic Alignment:** Epic 1.0 / 1.1 enablement (Azure persistence primitives)
**Created:** 2026-02-22

## Change Log

| Date | Agent | Change | Notes |
|------|-------|--------|-------|
| 2026-02-22 | Planner | Created plan | Implements D011 Pulumi IaC and Findings 004 infra requirements |

---

## Value Statement and Business Objective

As a **team operating ComfyCode on Azure + RunPod**, I want **repeatable infrastructure provisioning for storage**, so that **environments are reproducible, secure, and easy to deploy without manual steps**.

## Objective

1. Provision Azure Storage account and required containers deterministically via Pulumi.
2. Standardize environment configuration via **Pulumi stack Config** (code-first), using Pulumi secrets for sensitive values.
3. Produce outputs required by the application and future automation (container names, endpoints).

## Architecture Alignment (Non‑Negotiable)

- D011 — Pulumi as IaC for Azure persistence
- D008 — Pydantic as default validation standard (useful for validating non-secret config shapes)
- Findings 004 — Secure secret handling

## Scope

**In scope**
- Add an `infra/` boundary containing a Pulumi project (Python) to provision:
  - Azure Storage Account
  - Blob containers for artifacts/images/outputs (as required by conventions)
  - Optional Table storage resources (if used as thin lookup mirror)
- Define required Pulumi Config keys (naming, region, resource group, tags, container names) and use **Pulumi secrets** for sensitive values.
- Optionally validate the non-secret config shape in code (Pydantic model inside `infra/`) to reduce drift.

**Out of scope**
- Implementing app-side Azure Blob client code.
- Migrating existing assets.

## Constraints (Non‑Negotiable)

- No credentials committed to git.
- Pulumi secrets must be used for sensitive configuration.
- IaC must be environment-aware (dev/staging/prod) via Pulumi stacks.

## Assumptions

- An Azure subscription/tenant is available and the team can create a service principal for CI.

## OPEN QUESTION [RESOLVED]

- Pulumi backend: **RESOLVED → Pulumi Cloud** (default). If you later require self-managed state, we can migrate state to Azure Blob; keep the code unchanged.

---

## Plan

### 1) Define Pulumi Config Contract

**Owner:** Implementer

**Tasks**
1. Define required Pulumi Config keys (naming, region, resource group, tags, container names).
2. Define how the application will discover outputs (env vars, config file, or generated outputs).
3. (Optional) Add code-level validation of non-secret config shapes to fail fast on misconfiguration.

**Acceptance criteria**
- Config keys are documented and validated (code-first; optional Pydantic validation for non-secret config).

### 2) Implement Pulumi Project

**Owner:** Implementer

**Tasks**
1. Create Pulumi project under `infra/`.
2. Implement storage provisioning (account + containers + optional tables).
3. Export stack outputs needed by runtime.

**Acceptance criteria**
- `pulumi preview` shows intended changes.
- `pulumi up` creates resources idempotently.
- Outputs are available for downstream use.

### 3) Documentation + Runbook

**Owner:** Implementer

**Tasks**
1. Document local setup (install Pulumi, login to backend, set config, run preview/apply).
2. Document secrets and how CI supplies them.

**Acceptance criteria**
- A developer can provision a dev environment from scratch using docs.

### 4) Version and Release Artifacts

**Owner:** DevOps

**Tasks**
1. Decide whether IaC introduction warrants a release-note entry only or also a version bump.
2. Ensure release artifacts reflect availability of IaC.

**Acceptance criteria**
- Release notes reflect the new provisioning path.

---

## Validation

- Pulumi preview/apply works in a clean environment.
- Resources match naming conventions and required containers.

## Risks

- Misconfigured secrets in CI causing failed deploys; mitigate with clear env var contracts and dry-run preview.
- Drift between app expectations and infra outputs; mitigate via a shared settings contract.

## Rollback

- Pulumi stack destroy for dev/staging; production rollback requires explicit review and data retention plan.

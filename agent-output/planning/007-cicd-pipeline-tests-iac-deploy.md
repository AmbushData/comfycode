---
ID: 007
Origin: 007
UUID: b0a12f67
Status: Active
---

# Plan 007 — CI/CD: Tests, Packaging, and Pulumi Deploy

**Target Release:** v0.3.0
**Semver Rationale:** Operational capability; typically tracked via release notes rather than code version bump alone (confirm with roadmap).
**Epic Alignment:** Production readiness foundation (enables repeatable deploy and quality gates)
**Created:** 2026-02-22

## Change Log

| Date | Agent | Change | Notes |
|------|-------|--------|-------|
| 2026-02-22 | Planner | Created plan | Implements D012 CI/CD baseline and Findings 004 requirements |

---

## Value Statement and Business Objective

As a **team shipping ComfyCode toward production**, I want **automated CI/CD for tests and infrastructure deployment**, so that **changes are validated consistently and deployments are repeatable with an audit trail**.

## Objective

1. CI pipeline validates code quality (tests, packaging checks) on every PR.
2. CD pipeline supports Pulumi preview on PR and Pulumi apply on main/tag with approvals.
3. Establish a standard artifact strategy for RunPod runtime (explicit choice required).

## Architecture Alignment (Non‑Negotiable)

- D012 — CI/CD as the default change path
- D011 — Pulumi IaC for Azure persistence (integration)
- Findings 004 — Secret management, deploy gating, and reproducible runtime

## Scope

**In scope**
- Add CI workflows to run:
  - unit tests
  - packaging sanity checks
  - optional lint/type checks if already used in repo
- Add CD workflows for Pulumi:
  - preview on PR
  - apply on main/tag with environment approvals
- Define secret handling approach (GitHub Actions secrets + Pulumi secrets).

**Out of scope**
- Full production observability/telemetry (separate epic).

## Constraints (Non‑Negotiable)

- No secrets committed to git.
- Deploy actions must be gated (environment approvals) for production.
- CI must be fast and deterministic.

## OPEN QUESTION [RESOLVED]

- RunPod artifact strategy: **RESOLVED → use container image**. Rationale: best portability and reproducibility; aligns with CI/CD image build/publish and avoids template drift. Template sync can be added later if needed for speed, but container image is the primary path.

---

## Plan

### 1) CI: Test and Build Gates

**Owner:** DevOps

**Tasks**
1. Define GitHub Actions workflow to run unit tests in a clean environment.
2. Add packaging sanity checks (build/install smoke).
3. Publish test results as workflow artifacts/logs.

**Acceptance criteria**
- PR checks run automatically.
- Main branch is protected by passing CI.

### 2) CD: Pulumi Preview and Apply

**Owner:** DevOps

**Tasks**
1. Add Pulumi preview workflow triggered on PR.
2. Add Pulumi apply workflow gated on main/tag with approvals.
3. Configure secrets and identity (OIDC or service principal) per org standards.

**Acceptance criteria**
- Preview runs without leaking secrets.
- Apply requires explicit approval for production.

### 3) Runtime Delivery (RunPod)

**Owner:** DevOps

**Tasks**
1. Choose runtime artifact strategy:
   - container image build/publish, or
   - RunPod template provisioning updates
2. Document how CI/CD publishes and how runtime consumes artifacts.

**Acceptance criteria**
- There is a documented, repeatable path from commit → runnable RunPod environment.

### 4) Version and Release Artifacts

**Owner:** DevOps

**Tasks**
1. Ensure release notes reflect CI/CD availability.
2. Align any version bump policy with the target release group.

**Acceptance criteria**
- Release artifacts accurately reflect CI/CD changes.

---

## Validation

- CI passes on a clean runner.
- Pulumi preview/apply works end-to-end.

## Risks

- CI flakiness due to GPU/network dependencies; mitigate by keeping CI CPU-only and mocking external services where appropriate.
- Secret misconfiguration; mitigate with least-privilege identity and staged rollout.

## Rollback

- Revert workflow changes.
- Disable apply workflows and rely on manual Pulumi operations temporarily.

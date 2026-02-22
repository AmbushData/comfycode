# ComfyCode - Product Roadmap

**Last Updated**: 2026-02-22
**Roadmap Owner**: roadmap agent
**Strategic Vision**: ComfyCode transforms AI image generation from a manual, UI-bound process into a programmatic, reproducible, version-controlled workflow system. By abstracting infrastructure complexity and providing Python-native workflows, we empower developers to build production-grade AI pipelines without sacrificing control or scalability.

## Change Log
| Date & Time | Change | Rationale |
|-------------|--------|-----------|
| 2026-02-22 14:00 | Initial roadmap created | Establish strategic direction and track v0.1.x work |
| 2026-02-22 16:30 | Added Epic 0.7 (UI interop + bidirectional conversion) | Support flexible UX with optional ComfyUI UI usage |
| 2026-02-22 16:30 | Updated Active Release Tracker | Reflect plans executed for v0.1.1 |

---

## Master Product Objective

**Enable developers to build, test, and deploy production-grade AI image generation pipelines programmatically through Python-native workflows, with automated infrastructure provisioning and full version control.**

🚨 **IMMUTABLE** — Only user can modify this objective.

---

## Release v0.1.1 - Developer Onboarding Foundation
**Target Date**: 2026-03-01
**Strategic Goal**: Reduce time-to-first-success for new developers from "confused" to "generating images" in under 15 minutes.

### Epic 0.1: Comprehensive Developer Documentation
**Priority**: P0
**Status**: Planned

**User Story**:
As a **developer evaluating ComfyCode**,
I want **clear, complete documentation with quick-start examples**,
So that **I can understand the value proposition, install the package, and run my first workflow without external help**.

**Business Value**:
- Eliminates adoption friction for new developers
- Reduces support burden and repetitive questions
- Establishes professional credibility (polished docs = trusted project)
- Enables self-service evaluation and onboarding
- Measurable: GitHub stars, clone rate, issue quality improvement

**Dependencies**:
- None (foundational work)

**Acceptance Criteria** (outcome-focused):
- [ ] README includes installation instructions (pip install)
- [ ] README demonstrates CLI usage with concrete example
- [ ] README shows Python API workflow creation example
- [ ] README documents required environment variables / configuration
- [ ] README explains architectural layers (6 modules: config→runpod→comfyui→workflow→batch→pipeline)
- [ ] README includes API reference summary for key classes
- [ ] README provides development setup and testing instructions

**Constraints**:
- Must remain single README.md (no external docs site for v0.1.x)
- Keep concise: target 200-400 lines maximum
- Examples must be runnable without modification (use placeholder env vars clearly)

**Status Notes**:
- 2026-02-22: Epic defined; awaiting plan creation

---

## Release v0.2.0 - Production Readiness (Future)
**Target Date**: TBD
**Strategic Goal**: Enable confident production deployment with observability, error recovery, and cost optimization.

### Epic 0.2: Observability & Telemetry
**Priority**: P1
**Status**: Backlog

**User Story**:
As a **developer running ComfyCode in production**,
I want **structured logging, metrics, and execution traces**,
So that **I can monitor pipeline health, debug failures, and optimize costs without instrumenting code manually**.

**Business Value**:
- Reduces mean-time-to-resolution for production issues
- Enables data-driven capacity planning and cost optimization
- Differentiates from "toy" tools (production-grade = enterprise adoption)

**Dependencies**:
- Epic 0.1 (developers need docs before production features)

**Acceptance Criteria**:
- [ ] Structured JSON logging with severity levels
- [ ] Workflow execution tracing (start/end/duration per node)
- [ ] RunPod pod cost tracking (time, GPU tier)
- [ ] ComfyUI server health checks with retry logic
- [ ] Configurable log levels and output destinations

**Constraints**:
- Zero-dependency default (no mandatory telemetry service)
- Opt-in for external integrations (Prometheus, Datadog, etc.)

**Status Notes**:
- 2026-02-22: Defined for future; awaiting Epic 0.1 completion

---

### Epic 0.3: Error Recovery & Retry Logic
**Priority**: P1
**Status**: Backlog

**User Story**:
As a **developer processing batch workflows**,
I want **automatic retry on transient failures with exponential backoff**,
So that **temporary network issues or pod restarts don't fail my entire batch**.

**Business Value**:
- Improves reliability perception and user confidence
- Reduces wasted compute (failed batch = lost money/time)
- Enables "fire and forget" batch processing

**Dependencies**:
- Epic 0.2 (observability enables transparent retry logging)

**Acceptance Criteria**:
- [ ] Configurable retry attempts per workflow execution
- [ ] Exponential backoff with jitter
- [ ] Dead-letter queue for permanent failures
- [ ] Batch processor resumes from last successful item

**Status Notes**:
- 2026-02-22: Defined for future; prioritized after observability

---

### Epic 0.7: Workflow UI Interop & Bidirectional Conversion
**Priority**: P1
**Status**: Backlog

**User Story**:
As a **developer building ComfyCode workflows in Python**,
I want **bidirectional conversion between Python and ComfyUI workflows (JSON) with pleasant visual layout for the UI**,
So that **I can iterate programmatically most of the time while still using the ComfyUI UI when it’s helpful**.

**Business Value**:
- Enables a flexible user experience (Python-first + UI-assisted iteration)
- Reduces friction when importing existing UI workflows into code
- Makes it easier to debug, explore, and share workflows across developer/non-developer collaborators

**Dependencies**:
- Epic 0.1 (documentation + baseline workflow model)

**Acceptance Criteria** (outcome-focused):
- [ ] **JSON → Python** conversion remains supported and stable (existing CLI path)
- [ ] **Python → prompt JSON** export is supported for workflows built with ComfyCode
- [ ] **Prompt JSON → UI workflow JSON** export is supported with deterministic, visually readable node placement
- [ ] Exported UI workflow JSON can be imported into the ComfyUI UI without manual repairs
- [ ] Layout algorithm is deterministic (same graph → same positions) and avoids node overlap by default
- [ ] UI metadata is preserved when converting from UI JSON (positions retained unless reflow is requested)

**Constraints**:
- Keep Python-first execution path canonical; UI interop is optional tooling
- Avoid unsafe execution patterns for “code → JSON” export (must have guardrails/documented limitations)
- No new UX surfaces beyond CLI/API needed to support conversion workflows

**Status Notes**:
- 2026-02-22: Added in response to flexible UX requirement; requires format contract and layout strategy

---

## Release v0.3.0 - Ecosystem Integration (Future)
**Target Date**: TBD
**Strategic Goal**: Integrate with common developer workflows (CI/CD, cloud storage, notification systems).

### Epic 0.4: Cloud Storage Integration
**Priority**: P2
**Status**: Backlog

**User Story**:
As a **developer generating images at scale**,
I want **automatic upload to S3/Azure Blob/GCS after generation**,
So that **I don't manually transfer files and can integrate with downstream services**.

**Business Value**:
- Removes manual post-processing step
- Enables serverless architectures (generate → store → trigger)
- Supports high-volume use cases (storage separate from compute)

**Dependencies**:
- Epic 0.3 (need retry logic for storage failures)

**Acceptance Criteria**:
- [ ] Pluggable storage backend interface
- [ ] S3 adapter with multipart upload
- [ ] Azure Blob adapter
- [ ] GCS adapter
- [ ] Local filesystem adapter (default)
- [ ] Async upload (don't block workflow completion)

**Status Notes**:
- 2026-02-22: Defined for future; P2 due to workaround availability (users can upload manually)

---

## Backlog / Future Consideration

*(Epics not yet assigned to releases, in priority order)*

### Epic 0.5: Workflow Version Control & Diffing
**Priority**: P2
**Status**: Backlog

**User Story**:
As a **developer iterating on workflows**,
I want **semantic diffing of workflow changes**,
So that **I can review what changed between versions without parsing JSON manually**.

**Business Value**:
- Improves code review quality for workflow changes
- Reduces errors from copy-paste modifications
- Enables rollback to known-good configurations

**Status Notes**:
- 2026-02-22: Backlog; valuable but not blocking production use

---

### Epic 0.6: ComfyUI Plugin Management
**Priority**: P3
**Status**: Backlog

**User Story**:
As a **developer using custom ComfyUI nodes**,
I want **declarative plugin dependency specification**,
So that **my workflows are reproducible across different ComfyUI servers**.

**Business Value**:
- Enables true environment reproducibility
- Supports advanced use cases (custom models, experimental nodes)
- Differentiates from UI-only workflows (manifest-driven setup)

**Status Notes**:
- 2026-02-22: Backlog; low priority until user requests increase

---

## Active Release Tracker

**Current Working Release**: v0.1.1

| Plan ID | Title | UAT Status | Committed |
|---------|-------|------------|----------|
| 001 | README Developer Onboarding | Pending | No |
| 002 | uv sync + Dev Dependencies + README Corrections | Pending | No |

**Release Status**: 0 of 2 plans committed
**Ready for Release**: No
**Blocking Items**: DevOps version bump to v0.1.1 + UAT sign-off

### Previous Releases
| Version | Date | Plans Included | Status |
|---------|------|----------------|--------|
| v0.1.0 | (pre-roadmap) | Initial codebase | Released |

---

## Document Lifecycle Notes

**Orphan Sweep Status**: Initial roadmap creation — no orphans possible yet.

**Next Sweep**: After first plan/analysis/implementation cycle completes.

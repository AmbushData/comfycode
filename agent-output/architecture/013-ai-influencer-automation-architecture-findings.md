---
title: 013-ai-influencer-automation-architecture-findings.md
origin: Epic request (AI Influencer automation)
status: Active
---

# Architectural Findings — AI Influencer Automation Epic

**Date:** 2026-02-23
**Owner:** Architect

## Changelog
| Date | Change | Rationale |
|------|--------|-----------|
| 2026-02-23 | Initial assessment for influencer automation epic | Epic requires architectural review before planning |

---

## Context
The AI Influencer epic targets scalable, automated generation of hyper-realistic influencer content. Requirements include:
- Dynamic prompt generation (explicit, high-quality, persona-driven)
- Automated LoRA selection (multiple LoRAs per influencer, clothing/lingerie catalog)
- Batch workflows for dozens of influencers, each with variant clothing and prompt sets
- Storage integration (Azure Blob/local) for prompts, artifacts, and metadata
- Quality scoring, NSFW routing, and provenance tracking

---

## Architectural Assessment

### Current Architecture (ComfyCode)
- Python-first workflow engine (programmatic + template)
- Batch execution and parameter injection
- File-based artifact registry (repo metadata + Azure Blob for binaries)
- Workflow taxonomy (photo, lora, video)
- Agent roles: Workflow Expert, Tuner, VariantPlanner, QualityGate, LoRATrainer, DatasetCurator

### Gaps & Risks
- No prompt generator module (explicit prompt library, persona conditioning, scenario variation)
- No dynamic LoRA selection logic (prompt→LoRA mapping, multi-LoRA stacking)
- No clothing/lingerie catalog registry (per-influencer closet, metadata, batch selection)
- No batch workflow orchestration for influencer+clothing+prompt grids
- No quality scoring/NSFW routing integration in batch workflows
- No auto-updating documentation for workflow/artifact inventory

### Required Components
1. **Prompt Generator**: Persona-aware, scenario-driven, explicit prompt library; batch generation; storage integration
2. **LoRA Registry/Selector**: Metadata-driven LoRA catalog; prompt→LoRA mapping; multi-LoRA support
3. **Clothing Catalog**: Per-influencer closet; registry entries; batch selection logic
4. **Batch Workflow Orchestrator**: Grid execution (influencer × clothing × prompt); provenance tracking; output routing
5. **QualityGate Integration**: NSFW scoring, variant selection, routing
6. **Documentation Generator**: Inventory docs from registry/workflow/artifact manifests

### Integration Points
- Azure Blob Storage: artifact/prompt storage
- Repo: metadata, registry, workflow definitions
- ComfyUIClient: workflow execution
- RunPod: GPU runtime
- QualityGate: scoring/routing

---

## Recommendations
- Implement prompt generator as a modular, extensible component (persona, scenario, explicitness)
- Design LoRA registry with prompt-driven selection and multi-LoRA stacking
- Build clothing catalog registry with batch selection logic
- Extend batch workflow orchestration for influencer/clothing/prompt grids
- Integrate QualityGate for NSFW scoring/routing
- Automate documentation generation from registry/workflow/artifact manifests

---

## Verdict
APPROVED_WITH_CHANGES — Planning MUST address prompt generation, dynamic LoRA selection, clothing catalog, batch orchestration, and quality scoring/routing. Architecture is sound but requires new modules for automation and registry/catalog integration.

---

## Handoff
- Update system-architecture.md with findings and roadmap
- Proceed to planning phase for automation modules

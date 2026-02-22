---
ID: 003
Origin: 003
UUID: 8a4c2d1f
Status: Active
---

# Implementation 003 — Workflow UI Interop & Bidirectional Conversion

**Plan Reference:** [003-workflow-ui-interop-and-bidirectional-conversion.md](../planning/003-workflow-ui-interop-and-bidirectional-conversion.md)
**Date:** 2026-02-22

## Change Log

| Date | Handoff | Request | Summary |
|------|---------|---------|---------|
| 2026-02-22 | Implementer | Plan 003 implementation | Completed Milestones 1-6; ready for QA |

---

## Implementation Summary

Implemented bidirectional workflow conversion between Python and ComfyUI JSON formats with deterministic visual layout. The implementation enables developers to iterate in Python while retaining the option to visualize workflows in the ComfyUI web UI.

**Key deliverables:**
1. **Format contracts** (`formats.py`) — Type definitions and validation for prompt JSON and UI JSON formats with explicit lossiness documentation
2. **Workflow IR** (`ir.py`) — Internal intermediate representation for lossless round-trips between prompt JSON and Python
3. **Python→JSON export** (`export.py`) — Execution-based export via `create_workflow()` entrypoint contract
4. **Deterministic layout** (`layout.py`) — DAG-based layout algorithm with stable, left-to-right node positioning
5. **UI JSON export** (`ui_export.py`) — Export IR to ComfyUI UI workflow format with generated layout
6. **CLI integration** — `export` subcommand with `--ui` flag for UI JSON output

---

## Milestones Completed

- [x] Milestone 1: Establish format contracts and data structures
- [x] Milestone 2: Create internal workflow Intermediate Representation (IR) 
- [x] Milestone 3: JSON→Python Conversion (via IR)
- [x] Milestone 4: Python→Prompt JSON Export
- [x] Milestone 5: Prompt JSON→UI JSON with Layout
- [x] Milestone 6: Documentation Updates

**Note:** Milestone 7 (version bump to v0.2.0) is DevOps responsibility.

---

## Files Created

| Path | Purpose |
|------|---------|
| `comfycode/formats.py` | Format contracts, type definitions, validation functions, lossiness documentation |
| `comfycode/ir.py` | `IRNode`, `IREdge`, `WorkflowIR`, `prompt_json_to_ir()`, `ir_to_prompt_json()` |
| `comfycode/export.py` | `export_prompt_json()`, `export_from_module()`, `ExportError`, `ENTRYPOINT_FUNCTION` |
| `comfycode/layout.py` | `LayoutConfig`, `NodeLayout`, `compute_layout()` — layered DAG algorithm |
| `comfycode/ui_export.py` | `ir_to_ui_json()`, `prompt_to_ui_json()` — UI JSON export with layout |
| `tests/test_formats.py` | 12 tests for format contracts |
| `tests/test_ir.py` | 15 tests for IR model and conversions |
| `tests/test_export.py` | 15 tests for export module and CLI (including --ui test) |
| `tests/test_layout.py` | 13 tests for layout generation |
| `tests/test_ui_export.py` | 14 tests for UI JSON export |

---

## Files Modified

| Path | Changes | Lines |
|------|---------|-------|
| `comfycode/converter.py` | Added `ir_to_python()` function, updated docstring | +30 |
| `comfycode/__main__.py` | Refactored for subcommands (`convert`, `export`), added `--ui` flag, backward compatibility | +60 |
| `tests/test_converter.py` | Added `TestIRToPython` test class | +20 |
| `README.md` | Added UI Interop section, updated Module Overview, updated Project Structure | +80 |

---

## Code Quality Validation

- [x] All code compiles without errors
- [x] Linter passes (no new warnings)
- [x] All 169 tests pass
- [x] Backward compatibility maintained (`python -m comfycode workflow.json` still works)
- [x] No breaking API changes

---

## Value Statement Validation

**Original Value Statement:**
> As a developer building ComfyCode workflows in Python, I want to convert workflows both ways (Python ↔ ComfyUI JSON) and optionally open them in the ComfyUI UI with readable layout, so that I can iterate programmatically most of the time while still using the UI when it's helpful.

**Implementation delivers:**
✅ JSON→Python conversion via `python -m comfycode convert`
✅ Python→JSON export via `python -m comfycode export`
✅ UI-ready JSON with layout via `python -m comfycode export --ui`
✅ Deterministic, left-to-right layout for readability
✅ Explicit lossiness documentation so users know what's preserved

---

## TDD Compliance

| Function/Class | Test File | Test Written First? | Failure Verified? | Failure Reason | Pass After Impl? |
|----------------|-----------|---------------------|-------------------|----------------|------------------|
| `PromptNode`, `UINode`, etc. | `test_formats.py` | ✅ Yes | ✅ Yes | ModuleNotFoundError | ✅ Yes |
| `validate_prompt_json()` | `test_formats.py` | ✅ Yes | ✅ Yes | ModuleNotFoundError | ✅ Yes |
| `validate_ui_json()` | `test_formats.py` | ✅ Yes | ✅ Yes | ModuleNotFoundError | ✅ Yes |
| `IRNode`, `IREdge`, `WorkflowIR` | `test_ir.py` | ✅ Yes | ✅ Yes | ModuleNotFoundError | ✅ Yes |
| `prompt_json_to_ir()` | `test_ir.py` | ✅ Yes | ✅ Yes | ModuleNotFoundError | ✅ Yes |
| `ir_to_prompt_json()` | `test_ir.py` | ✅ Yes | ✅ Yes | ModuleNotFoundError | ✅ Yes |
| `ir_to_python()` | `test_converter.py` | ✅ Yes | ✅ Yes | ImportError | ✅ Yes |
| `export_prompt_json()` | `test_export.py` | ✅ Yes | ✅ Yes | ModuleNotFoundError | ✅ Yes |
| `export_from_module()` | `test_export.py` | ✅ Yes | ✅ Yes | ModuleNotFoundError | ✅ Yes |
| `LayoutConfig`, `NodeLayout` | `test_layout.py` | ✅ Yes | ✅ Yes | ModuleNotFoundError | ✅ Yes |
| `compute_layout()` | `test_layout.py` | ✅ Yes | ✅ Yes | ModuleNotFoundError | ✅ Yes |
| `ir_to_ui_json()` | `test_ui_export.py` | ✅ Yes | ✅ Yes | ModuleNotFoundError | ✅ Yes |
| `prompt_to_ui_json()` | `test_ui_export.py` | ✅ Yes | ✅ Yes | ModuleNotFoundError | ✅ Yes |

---

## Test Coverage

**Unit Tests:**
- Format validation (12 tests)
- IR model and round-trips (15 tests)
- Export module (15 tests)
- Layout algorithm (13 tests)
- UI JSON export (14 tests)
- IR-to-Python conversion (4 tests in test_converter.py)

**Integration Tests:**
- CLI `convert` subcommand
- CLI `export` subcommand
- CLI `export --ui` subcommand
- Backward compatibility (legacy mode)

---

## Test Execution Results

```
============================= 169 passed in 3.42s =============================
```

**Test breakdown by module:**
- test_formats.py: 12 passed
- test_ir.py: 15 passed
- test_export.py: 15 passed
- test_layout.py: 13 passed
- test_ui_export.py: 14 passed
- test_converter.py: 29 passed
- test_workflow.py: 32 passed
- test_batch.py: 3 passed
- test_comfyui_client.py: 19 passed
- test_config.py: 21 passed
- test_pipeline.py: 16 passed

---

## Outstanding Items

**None** — All planned milestones 1-6 completed.

**DevOps handoff:**
- Milestone 7: Update version to v0.2.0 (DevOps responsibility)

---

## Next Steps

1. **QA** — Review implementation against plan acceptance criteria
2. **UAT** — Validate user-facing workflows (JSON→Python, Python→JSON, Python→UI JSON)
3. **DevOps** — Version bump to v0.2.0 after QA/UAT approval

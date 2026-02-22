"""Structured batch processing.

:class:`BatchProcessor` accepts a base :class:`~comfycode.workflow.Workflow`
template and a list of *parameter dicts*, generates one workflow per item
(injecting the per-item parameters), and executes all of them sequentially
through a :class:`~comfycode.comfyui_client.ComfyUIClient`.

Each batch item is an arbitrary ``dict`` whose keys map to setter method
names on :class:`~comfycode.workflow.Workflow` (without the ``set_`` prefix)
or to ``(node_id, input_key)`` tuples for low-level overrides.  Recognised
high-level keys:

- ``positive_prompt``
- ``negative_prompt``
- ``checkpoint``
- ``seed``
- ``width`` / ``height``
- ``steps``
- ``cfg``
- ``sampler``
- ``scheduler``

Any unrecognised key is silently ignored, which keeps the API forward-
compatible as new setters are added to :class:`~comfycode.workflow.Workflow`.
"""

from __future__ import annotations

import copy
import logging
from typing import Any

from .comfyui_client import ComfyUIClient
from .workflow import Workflow

logger = logging.getLogger(__name__)

# Map parameter-dict key → Workflow setter method name.
_SETTER_MAP: dict[str, str] = {
    "positive_prompt": "set_positive_prompt",
    "negative_prompt": "set_negative_prompt",
    "checkpoint": "set_checkpoint",
    "seed": "set_seed",
    "steps": "set_steps",
    "cfg": "set_cfg",
    "sampler": "set_sampler",
    "scheduler": "set_scheduler",
}


class BatchResult:
    """Holds the outcome of a single batch item execution.

    Attributes
    ----------
    index:
        Zero-based position in the batch.
    params:
        The parameter dict used for this item.
    outputs:
        List of output dicts returned by :meth:`ComfyUIClient.run_workflow`.
    error:
        If the item failed, the exception that was raised; otherwise *None*.
    """

    def __init__(
        self,
        index: int,
        params: dict[str, Any],
        outputs: list[dict[str, Any]] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.index = index
        self.params = params
        self.outputs: list[dict[str, Any]] = outputs or []
        self.error = error

    @property
    def success(self) -> bool:
        """*True* when the item completed without error."""
        return self.error is None

    def __repr__(self) -> str:
        status = "ok" if self.success else f"error={self.error!r}"
        return f"<BatchResult index={self.index} {status}>"


class BatchProcessor:
    """Execute a list of parameterised workflow variants.

    Parameters
    ----------
    base_workflow:
        Template :class:`~comfycode.workflow.Workflow`.  A deep copy is
        taken for each batch item so the original is never mutated.
    client:
        A configured :class:`~comfycode.comfyui_client.ComfyUIClient`.
    skip_errors:
        When *True* (default) a failed item is recorded in the results but
        execution continues for subsequent items.  When *False* the first
        error propagates immediately.

    Examples
    --------
    >>> processor = BatchProcessor(base_workflow, client)
    >>> results = processor.run([
    ...     {"positive_prompt": "a red fox", "seed": 1},
    ...     {"positive_prompt": "a blue whale", "seed": 2},
    ... ])
    >>> for r in results:
    ...     print(r.index, r.success, r.outputs)
    """

    def __init__(
        self,
        base_workflow: Workflow,
        client: ComfyUIClient,
        *,
        skip_errors: bool = True,
    ) -> None:
        self._base = base_workflow
        self._client = client
        self._skip_errors = skip_errors

    def run(self, items: list[dict[str, Any]]) -> list[BatchResult]:
        """Run all *items* and return a :class:`BatchResult` for each.

        Parameters
        ----------
        items:
            List of parameter dicts.  See module docstring for recognised keys.
        """
        results: list[BatchResult] = []
        total = len(items)
        logger.info("Starting batch of %d item(s).", total)

        for idx, params in enumerate(items):
            logger.info("Batch item %d/%d: %s", idx + 1, total, params)
            print(f"\n[batch {idx + 1}/{total}] params={params}", flush=True)
            try:
                workflow = self._apply_params(params)
                outputs = self._client.run_workflow(workflow.build())
                results.append(BatchResult(index=idx, params=params, outputs=outputs))
                logger.info("Batch item %d completed – %d output(s).", idx + 1, len(outputs))
            except Exception as exc:  # noqa: BLE001
                logger.error("Batch item %d failed: %s", idx + 1, exc)
                result = BatchResult(index=idx, params=params, error=exc)
                results.append(result)
                if not self._skip_errors:
                    raise

        logger.info(
            "Batch complete: %d/%d succeeded.",
            sum(1 for r in results if r.success),
            total,
        )
        return results

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _apply_params(self, params: dict[str, Any]) -> Workflow:
        """Return a new :class:`Workflow` with *params* applied."""
        # Clone the base graph so each run is independent.
        wf = Workflow.from_dict(copy.deepcopy(self._base.build()))

        # Handle width+height together for set_dimensions.
        if "width" in params or "height" in params:
            # Fetch current values as defaults.
            current_w, current_h = self._current_dimensions(wf)
            w = params.get("width", current_w)
            h = params.get("height", current_h)
            wf.set_dimensions(w, h)

        for key, value in params.items():
            if key in ("width", "height"):
                continue  # handled above
            setter_name = _SETTER_MAP.get(key)
            if setter_name and hasattr(wf, setter_name):
                getattr(wf, setter_name)(value)
            # Low-level override: key is (node_id, input_key)
            elif isinstance(key, tuple) and len(key) == 2:
                node_id, input_key = key
                wf.set_node_input(str(node_id), input_key, value)

        return wf

    @staticmethod
    def _current_dimensions(wf: Workflow) -> tuple[int, int]:
        """Read current width/height from the first EmptyLatentImage node."""
        for node_id in wf.node_ids_by_class("EmptyLatentImage"):
            node = wf.get_node(node_id)
            w = node.get("inputs", {}).get("width", 512)
            h = node.get("inputs", {}).get("height", 512)
            return int(w), int(h)
        return 512, 512

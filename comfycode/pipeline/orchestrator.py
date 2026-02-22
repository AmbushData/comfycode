"""Top-level orchestration pipeline.

:class:`Pipeline` ties together all layers:

1. **Infrastructure** – optionally provisions a RunPod GPU pod.
2. **Execution** – creates a :class:`~comfycode.comfyui_client.ComfyUIClient`
   pointed at the ComfyUI server.
3. **Orchestration** – loads a :class:`~comfycode.workflow.Workflow`,
   optionally injects parameters, and runs it (single or batch).

The pipeline can be used in three modes:

* **Single run** – call :meth:`run` with optional parameter overrides.
* **Batch run** – call :meth:`run_batch` with a list of parameter dicts.
* **Manual** – access :attr:`workflow` and :attr:`client` directly for
  fine-grained control.

GPU pods are provisioned lazily on the first call to :meth:`run` or
:meth:`run_batch` if *auto_provision* is enabled, and are kept alive for
subsequent calls unless :meth:`teardown` is called explicitly.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from .batch import BatchProcessor, BatchResult
from comfycode.clients import ComfyUIClient
from comfycode.clients.comfyui import EventCallback
from comfycode.config import Config
from comfycode.clients import RunPodClient
from comfycode.workflows import Workflow

logger = logging.getLogger(__name__)


class Pipeline:
    """End-to-end AI image generation pipeline.

    Parameters
    ----------
    workflow_path:
        Path to the workflow JSON file to load.
    config:
        A :class:`~comfycode.config.Config` instance.  If *None*, a default
        config is constructed from environment variables.
    auto_provision:
        When *True* (default), a RunPod GPU pod is provisioned on demand if
        ``config.runpod_api_key`` is non-empty.  Set to *False* when the
        ComfyUI server is already running (e.g. local development).
    on_event:
        Optional callback for intermediate execution events.  Forwarded to
        :class:`~comfycode.comfyui_client.ComfyUIClient`.

    Examples
    --------
    Local ComfyUI server (no RunPod):

    >>> pipeline = Pipeline("workflows/txt2img.json", auto_provision=False)
    >>> outputs = pipeline.run(positive_prompt="a red fox", seed=42)

    Cloud execution with RunPod:

    >>> pipeline = Pipeline("workflows/txt2img.json")
    >>> outputs = pipeline.run(positive_prompt="a red fox", seed=42)
    >>> pipeline.teardown()
    """

    def __init__(
        self,
        workflow_path: str | Path,
        config: Config | None = None,
        *,
        auto_provision: bool = True,
        on_event: EventCallback | None = None,
    ) -> None:
        self._config = config or Config()
        self._auto_provision = auto_provision
        self._on_event = on_event
        self._workflow_path = Path(workflow_path)
        self._pod_id: str | None = None
        self._client: ComfyUIClient | None = None

        # Load the workflow template immediately so path errors surface early.
        self._workflow = Workflow.from_file(self._workflow_path)
        logger.info("Pipeline initialised with workflow %s", self._workflow_path)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def workflow(self) -> Workflow:
        """The current workflow template (may be mutated before running)."""
        return self._workflow

    @property
    def client(self) -> ComfyUIClient:
        """The :class:`~comfycode.comfyui_client.ComfyUIClient` instance.

        Raises
        ------
        RuntimeError
            If the pipeline has not been started yet (call :meth:`run` or
            :meth:`start` first).
        """
        if self._client is None:
            raise RuntimeError(
                "Pipeline client not initialised – call pipeline.start() first "
                "or use pipeline.run() which calls start() automatically."
            )
        return self._client

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Provision infrastructure and initialise the ComfyUI client.

        Safe to call multiple times; subsequent calls are no-ops.
        """
        if self._client is not None:
            return

        if self._auto_provision and self._config.runpod_api_key:
            runpod = RunPodClient(self._config)
            pod_id, host, port = runpod.provision_pod()
            self._pod_id = pod_id
            self._config.comfyui_host = host
            self._config.comfyui_port = port

        self._client = ComfyUIClient(self._config, on_event=self._on_event)
        logger.info(
            "ComfyUI client ready at %s", self._config.comfyui_base_url
        )

    def teardown(self) -> None:
        """Release resources: terminate any provisioned RunPod pod."""
        if self._pod_id and self._config.runpod_api_key:
            runpod = RunPodClient(self._config)
            runpod.terminate_pod(self._pod_id)
            self._pod_id = None
        self._client = None
        logger.info("Pipeline torn down.")

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run(self, **params: Any) -> list[dict[str, Any]]:
        """Run a single workflow with optional parameter overrides.

        Keyword arguments are the same as the parameter keys accepted by
        :class:`~comfycode.batch.BatchProcessor` (e.g. ``positive_prompt``,
        ``seed``, ``steps``, ``cfg``).

        Returns
        -------
        list[dict]
            Output artefacts from ComfyUI (see
            :meth:`~comfycode.comfyui_client.ComfyUIClient.run_workflow`).
        """
        self.start()

        # Ensure the output directory exists.
        os.makedirs(self._config.output_dir, exist_ok=True)

        logger.info("Running single workflow with params: %s", params)
        print(f"\n[pipeline] Running workflow: {self._workflow_path.name}", flush=True)
        if params:
            print(f"[pipeline] Parameters: {params}", flush=True)

        processor = BatchProcessor(self._workflow, self.client, skip_errors=False)
        results = processor.run([params] if params else [{}])
        return results[0].outputs if results else []

    def run_batch(self, items: list[dict[str, Any]]) -> list[BatchResult]:
        """Run a list of parameterised workflow variants.

        Parameters
        ----------
        items:
            List of parameter dicts (same format as :meth:`run` kwargs).

        Returns
        -------
        list[BatchResult]
            One :class:`~comfycode.batch.BatchResult` per item.
        """
        self.start()
        os.makedirs(self._config.output_dir, exist_ok=True)

        logger.info("Running batch of %d workflow(s).", len(items))
        print(f"\n[pipeline] Batch run: {len(items)} item(s)", flush=True)

        processor = BatchProcessor(self._workflow, self.client)
        return processor.run(items)

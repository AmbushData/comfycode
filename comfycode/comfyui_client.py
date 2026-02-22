"""ComfyUI execution layer.

Submits workflow prompts to a running ComfyUI server, streams execution
events over a WebSocket connection, and returns final image outputs.

Intermediate events (node start, progress ticks, latent previews, node
outputs) are logged at DEBUG level and also passed to an optional callback
so that callers can implement custom observability, dashboards, or early-
stop logic.
"""

from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from typing import Any, Callable

import requests
import websocket

from .config import Config

logger = logging.getLogger(__name__)

# Type alias for the intermediate-event callback.
EventCallback = Callable[[str, dict[str, Any]], None]

# Seconds between history-poll retries when WebSocket is not available.
_POLL_INTERVAL = 2
_HISTORY_TIMEOUT = 300


class ComfyUIError(Exception):
    """Raised when the ComfyUI server returns an error."""


class ComfyUIClient:
    """Client for the ComfyUI REST + WebSocket API.

    Parameters
    ----------
    config:
        A :class:`~comfycode.config.Config` instance.
    on_event:
        Optional callback invoked for every intermediate execution event.
        Signature: ``callback(event_type: str, data: dict) -> None``.

    Examples
    --------
    >>> client = ComfyUIClient(config)
    >>> outputs = client.run_workflow(workflow_dict)
    >>> for image_path in outputs:
    ...     print(image_path)
    """

    def __init__(
        self,
        config: Config,
        on_event: EventCallback | None = None,
    ) -> None:
        self._config = config
        self._on_event = on_event
        self._session = requests.Session()
        self._client_id = str(uuid.uuid4())

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_workflow(
        self, workflow: dict[str, Any], *, use_websocket: bool = True
    ) -> list[dict[str, Any]]:
        """Submit *workflow* to ComfyUI and return all output artefacts.

        Parameters
        ----------
        workflow:
            A ComfyUI *prompt* dict (the ``"prompt"`` value you would POST
            to ``/prompt``).
        use_websocket:
            When *True* (default) a WebSocket connection is opened to
            receive real-time intermediate events.  Set to *False* to fall
            back to HTTP polling (useful when WebSocket is unavailable).

        Returns
        -------
        list[dict]
            One dict per output node.  Each dict has the keys ``"node_id"``,
            ``"type"`` (e.g. ``"images"``), and ``"files"`` (list of file
            info dicts returned by ComfyUI).
        """
        prompt_id = self._queue_prompt(workflow)
        logger.info("Prompt queued – prompt_id=%s", prompt_id)

        if use_websocket:
            outputs = self._run_with_websocket(prompt_id)
        else:
            outputs = self._run_with_polling(prompt_id)

        logger.info("Prompt %s finished – %d output node(s)", prompt_id, len(outputs))
        return outputs

    def get_queue(self) -> dict[str, Any]:
        """Return the current ComfyUI queue state."""
        return self._get("/queue")

    def get_history(self, prompt_id: str) -> dict[str, Any]:
        """Return the execution history entry for *prompt_id*."""
        return self._get(f"/history/{prompt_id}")

    def interrupt(self) -> None:
        """Ask ComfyUI to interrupt the currently running prompt."""
        self._post("/interrupt", {})

    # ------------------------------------------------------------------
    # Private – HTTP helpers
    # ------------------------------------------------------------------

    def _queue_prompt(self, workflow: dict[str, Any]) -> str:
        payload = {"prompt": workflow, "client_id": self._client_id}
        data = self._post("/prompt", payload)
        prompt_id: str = data["prompt_id"]
        return prompt_id

    def _get(self, path: str) -> dict[str, Any]:
        url = self._config.comfyui_base_url + path
        resp = self._session.get(url, timeout=self._config.comfyui_timeout)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = self._config.comfyui_base_url + path
        resp = self._session.post(
            url,
            json=payload,
            timeout=self._config.comfyui_timeout,
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Private – WebSocket execution path
    # ------------------------------------------------------------------

    def _run_with_websocket(self, prompt_id: str) -> list[dict[str, Any]]:
        """Block until *prompt_id* completes, streaming intermediate events."""
        ws_url = f"{self._config.comfyui_ws_url}?clientId={self._client_id}"
        outputs: list[dict[str, Any]] = []
        done_event = threading.Event()
        error_holder: list[Exception] = []

        def on_message(ws: websocket.WebSocketApp, raw: str) -> None:
            try:
                msg: dict[str, Any] = json.loads(raw)
            except json.JSONDecodeError:
                logger.debug("WebSocket received non-JSON message: %r", raw)
                return

            msg_type: str = msg.get("type", "")
            data: dict[str, Any] = msg.get("data", {})

            # Only process events belonging to our prompt.
            if data.get("prompt_id") not in (None, prompt_id):
                return

            self._log_event(msg_type, data)
            if self._on_event:
                self._on_event(msg_type, data)

            if msg_type == "executed":
                node_id = data.get("node")
                node_output = data.get("output", {})
                for output_type, files in node_output.items():
                    outputs.append(
                        {"node_id": node_id, "type": output_type, "files": files}
                    )

            elif msg_type == "execution_error":
                error_holder.append(
                    ComfyUIError(
                        f"Execution error on node {data.get('node_id')!r}: "
                        f"{data.get('exception_message', 'unknown error')}"
                    )
                )
                done_event.set()

            elif msg_type == "execution_success":
                done_event.set()

        def on_error(ws: websocket.WebSocketApp, err: Exception) -> None:
            logger.warning("WebSocket error: %s", err)
            error_holder.append(err)
            done_event.set()

        ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
        )
        thread = threading.Thread(target=ws.run_forever, daemon=True)
        thread.start()

        done_event.wait(timeout=_HISTORY_TIMEOUT)
        ws.close()

        if error_holder:
            raise error_holder[0]
        if not done_event.is_set():
            raise ComfyUIError(
                f"Prompt {prompt_id!r} did not complete within {_HISTORY_TIMEOUT}s"
            )
        return outputs

    # ------------------------------------------------------------------
    # Private – HTTP polling execution path
    # ------------------------------------------------------------------

    def _run_with_polling(self, prompt_id: str) -> list[dict[str, Any]]:
        """Poll ``/history`` until *prompt_id* completes."""
        deadline = time.time() + _HISTORY_TIMEOUT
        while time.time() < deadline:
            history = self.get_history(prompt_id)
            entry = history.get(prompt_id)
            if entry:
                status = entry.get("status", {})
                if status.get("completed"):
                    return self._extract_outputs(prompt_id, entry)
                if status.get("status_str") == "error":
                    raise ComfyUIError(
                        f"Prompt {prompt_id!r} failed: {status.get('messages', [])}"
                    )
            time.sleep(_POLL_INTERVAL)
        raise ComfyUIError(
            f"Prompt {prompt_id!r} did not complete within {_HISTORY_TIMEOUT}s"
        )

    def _extract_outputs(
        self, prompt_id: str, history_entry: dict[str, Any]
    ) -> list[dict[str, Any]]:
        outputs: list[dict[str, Any]] = []
        for node_id, node_output in history_entry.get("outputs", {}).items():
            for output_type, files in node_output.items():
                outputs.append(
                    {"node_id": node_id, "type": output_type, "files": files}
                )
        return outputs

    # ------------------------------------------------------------------
    # Private – logging
    # ------------------------------------------------------------------

    def _log_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Log intermediate execution events for observability."""
        if event_type == "execution_start":
            logger.debug("[ComfyUI] Execution started (prompt_id=%s)", data.get("prompt_id"))
        elif event_type == "executing":
            node = data.get("node")
            if node is None:
                logger.debug("[ComfyUI] All nodes executed.")
            else:
                logger.debug("[ComfyUI] Executing node %s", node)
        elif event_type == "progress":
            value = data.get("value", 0)
            maximum = data.get("max", 1)
            pct = int(100 * value / maximum) if maximum else 0
            logger.debug("[ComfyUI] Progress %d/%d (%d%%)", value, maximum, pct)
            print(f"  [progress] {value}/{maximum} ({pct}%)", flush=True)
        elif event_type == "executed":
            node_id = data.get("node")
            output = data.get("output", {})
            logger.debug("[ComfyUI] Node %s produced output: %s", node_id, list(output.keys()))
            print(f"  [node {node_id}] output types: {list(output.keys())}", flush=True)
        elif event_type == "execution_cached":
            logger.debug("[ComfyUI] Cached nodes: %s", data.get("nodes", []))
        elif event_type == "execution_error":
            logger.error(
                "[ComfyUI] Execution error on node %s: %s",
                data.get("node_id"),
                data.get("exception_message"),
            )
        elif event_type == "execution_success":
            logger.debug("[ComfyUI] Execution succeeded (prompt_id=%s)", data.get("prompt_id"))
            print("  [execution_success]", flush=True)

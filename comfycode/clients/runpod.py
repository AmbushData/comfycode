"""RunPod infrastructure layer.

Handles on-demand provisioning and deprovisioning of GPU pods via the
RunPod REST API.  Workflow orchestration never needs to know *where* the
ComfyUI server is running – it only needs a ``(host, port)`` pair, which
this client returns after a pod becomes ready.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

from comfycode.config import Config

logger = logging.getLogger(__name__)

_RUNPOD_API_BASE = "https://api.runpod.io/v2"
_GRAPHQL_URL = "https://api.runpod.io/graphql"

# How long (seconds) to wait between pod-status poll attempts.
_POLL_INTERVAL = 10
# Maximum total seconds to wait for a pod to become ready.
_READY_TIMEOUT = 600


class RunPodError(Exception):
    """Raised when the RunPod API returns an unexpected response."""


class RunPodClient:
    """Manage RunPod GPU pod lifecycle.

    Parameters
    ----------
    config:
        A :class:`~comfycode.config.Config` instance that supplies the
        RunPod API key, template ID, and preferred GPU type.

    Examples
    --------
    >>> client = RunPodClient(config)
    >>> pod_id, host, port = client.provision_pod()
    >>> # … run workflows …
    >>> client.terminate_pod(pod_id)
    """

    def __init__(self, config: Config) -> None:
        self._config = config
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {config.runpod_api_key}",
                "Content-Type": "application/json",
            }
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def provision_pod(
        self,
        *,
        gpu_count: int = 1,
        container_disk_gb: int = 20,
        volume_in_gb: int = 0,
    ) -> tuple[str, str, int]:
        """Create a new RunPod GPU pod and wait until it is ready.

        Returns
        -------
        tuple[str, str, int]
            ``(pod_id, host, comfyui_port)`` where *host* is the public IP
            (or hostname) and *comfyui_port* is the forwarded port that
            the ComfyUI server inside the pod is listening on.

        Raises
        ------
        RunPodError
            If pod creation fails or the pod does not become ready within
            the timeout window.
        """
        logger.info(
            "Provisioning RunPod pod (gpu_type=%s, gpu_count=%d)…",
            self._config.runpod_gpu_type,
            gpu_count,
        )

        mutation = """
        mutation CreatePod(
          $name: String!
          $imageName: String!
          $gpuTypeId: String!
          $gpuCount: Int!
          $containerDiskInGb: Int!
          $volumeInGb: Int!
          $ports: String!
        ) {
          podFindAndDeployOnDemand(input: {
            name: $name
            imageName: $imageName
            gpuTypeId: $gpuTypeId
            gpuCount: $gpuCount
            containerDiskInGb: $containerDiskInGb
            volumeInGb: $volumeInGb
            ports: $ports
            startJupyter: false
            startSsh: false
          }) {
            id
            desiredStatus
            imageName
            machine {
              podHostId
            }
          }
        }
        """

        variables = {
            "name": "comfycode-pod",
            "imageName": self._config.runpod_template_id,
            "gpuTypeId": self._config.runpod_gpu_type,
            "gpuCount": gpu_count,
            "containerDiskInGb": container_disk_gb,
            "volumeInGb": volume_in_gb,
            "ports": f"{self._config.comfyui_port}/http",
        }

        response = self._graphql(mutation, variables)
        pod_data = response.get("data", {}).get("podFindAndDeployOnDemand")
        if not pod_data:
            raise RunPodError(f"Pod creation failed: {response}")

        pod_id: str = pod_data["id"]
        logger.info("Pod %s created – waiting for RUNNING state…", pod_id)

        host, port = self._wait_for_ready(pod_id)
        logger.info("Pod %s is ready at %s:%d", pod_id, host, port)
        return pod_id, host, port

    def terminate_pod(self, pod_id: str) -> None:
        """Terminate a running pod by its ID.

        Parameters
        ----------
        pod_id:
            The pod identifier returned by :meth:`provision_pod`.
        """
        logger.info("Terminating pod %s…", pod_id)
        mutation = """
        mutation TerminatePod($podId: String!) {
          podTerminate(input: { podId: $podId })
        }
        """
        self._graphql(mutation, {"podId": pod_id})
        logger.info("Pod %s terminated.", pod_id)

    def get_pod_status(self, pod_id: str) -> dict[str, Any]:
        """Return the current status dict for *pod_id*.

        Returns
        -------
        dict
            Raw pod status data from the RunPod API.
        """
        query = """
        query GetPod($podId: String!) {
          pod(input: { podId: $podId }) {
            id
            desiredStatus
            lastStatusChange
            runtime {
              uptimeInSeconds
              ports {
                ip
                isIpPublic
                privatePort
                publicPort
                type
              }
            }
          }
        }
        """
        response = self._graphql(query, {"podId": pod_id})
        pod_data = response.get("data", {}).get("pod")
        if pod_data is None:
            raise RunPodError(f"Pod {pod_id!r} not found")
        return pod_data

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _wait_for_ready(self, pod_id: str) -> tuple[str, int]:
        """Poll until *pod_id* is RUNNING and has a reachable endpoint."""
        deadline = time.time() + _READY_TIMEOUT
        while time.time() < deadline:
            status = self.get_pod_status(pod_id)
            if status.get("desiredStatus") == "RUNNING" and status.get("runtime"):
                ports = status["runtime"].get("ports", [])
                for port_entry in ports:
                    if port_entry.get("privatePort") == self._config.comfyui_port:
                        host = port_entry["ip"]
                        public_port = port_entry["publicPort"]
                        return host, public_port
            logger.debug("Pod %s not ready yet – retrying in %ds…", pod_id, _POLL_INTERVAL)
            time.sleep(_POLL_INTERVAL)
        raise RunPodError(
            f"Pod {pod_id!r} did not become ready within {_READY_TIMEOUT}s"
        )

    def _graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        """Execute a GraphQL request against the RunPod API."""
        resp = self._session.post(
            _GRAPHQL_URL,
            json={"query": query, "variables": variables},
            timeout=30,
        )
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        if "errors" in data:
            raise RunPodError(f"RunPod GraphQL error: {data['errors']}")
        return data

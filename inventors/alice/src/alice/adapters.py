"""Typed boundaries to research, simulation, CAD, and manufacturing tools."""

from __future__ import annotations

import hashlib
import json
import math
import os
import time
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .providers import (
    BoundedProcessOutputLimit,
    BoundedProcessTimeout,
    run_bounded_process,
)


class AdapterError(RuntimeError):
    pass


COMMAND_ADAPTER_CONTRACT_VERSION = "alice.command-adapter.v1"
COMMAND_ADAPTER_DIAGNOSTICS_OPERATION = "alice.adapter.diagnostics"


def canonical_adapter_input(operation: str, payload: Mapping[str, Any]) -> str:
    """Return the one canonical JSON envelope sent to an adapter process.

    Adapter implementations should use :func:`adapter_input_sha256` over the
    same logical ``operation`` and ``payload`` and return that digest as
    ``input_sha256``.  Keeping this encoding public prevents each adapter from
    inventing a subtly different hashing contract.
    """

    if not isinstance(operation, str) or not operation.strip():
        raise ValueError("adapter operation must be a non-empty string")
    if not isinstance(payload, Mapping):
        raise TypeError("adapter payload must be a mapping")
    try:
        return json.dumps(
            {"operation": operation, "payload": dict(payload)},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("adapter input must be canonical JSON") from exc


def adapter_input_sha256(operation: str, payload: Mapping[str, Any]) -> str:
    """Hash the canonical adapter input envelope with SHA-256."""

    return hashlib.sha256(
        canonical_adapter_input(operation, payload).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True, slots=True, init=False)
class AdapterReceipt:
    adapter: str
    run_id: str
    status: str
    evidence_class: str
    payload: dict[str, Any]
    input_sha256: str
    elapsed_seconds: float

    def __init__(
        self,
        adapter: str,
        run_id: str,
        status: str,
        evidence_class: str,
        payload: dict[str, Any],
        input_sha256: str | None = None,
        elapsed_seconds: float = 0.0,
        *,
        input_hash: str | None = None,
    ) -> None:
        """Create a receipt, accepting ``input_hash`` only as a legacy alias.

        The alias keeps the built-in Vibe adapter source-compatible while the
        serialized receipt and command-adapter wire contract use the precise
        ``input_sha256`` name.
        """

        if input_sha256 is not None and input_hash is not None and input_sha256 != input_hash:
            raise ValueError("input_sha256 and legacy input_hash disagree")
        digest = input_sha256 if input_sha256 is not None else input_hash
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or digest.lower() != digest
            or any(ch not in "0123456789abcdef" for ch in digest)
        ):
            raise ValueError("input_sha256 must be a lowercase SHA-256 digest")
        object.__setattr__(self, "adapter", adapter)
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "evidence_class", evidence_class)
        object.__setattr__(self, "payload", payload)
        object.__setattr__(self, "input_sha256", digest)
        object.__setattr__(self, "elapsed_seconds", elapsed_seconds)

    @property
    def input_hash(self) -> str:
        """Backward-compatible attribute alias for older in-process callers."""

        return self.input_sha256


class CommandAdapter:
    """Invoke a deterministic or sandboxed tool using one JSON message."""

    def __init__(
        self,
        name: str,
        command: Sequence[str],
        *,
        evidence_class: str,
        timeout_seconds: int = 1_800,
        max_output_bytes: int = 2_000_000,
        max_stderr_bytes: int = 65_536,
        shutdown_grace_seconds: float = 1.0,
        allowed_environment: Sequence[str] = ("PATH", "HOME"),
    ) -> None:
        if not command:
            raise ValueError(f"{name} command must not be empty")
        if (
            isinstance(timeout_seconds, bool)
            or not math.isfinite(float(timeout_seconds))
            or float(timeout_seconds) <= 0
        ):
            raise ValueError("timeout_seconds must be a positive finite number")
        for field_name, value in (
            ("max_output_bytes", max_output_bytes),
            ("max_stderr_bytes", max_stderr_bytes),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{field_name} must be a positive integer")
        if (
            isinstance(shutdown_grace_seconds, bool)
            or not math.isfinite(float(shutdown_grace_seconds))
            or float(shutdown_grace_seconds) <= 0
        ):
            raise ValueError(
                "shutdown_grace_seconds must be a positive finite number"
            )
        self.name = name
        self.command = tuple(command)
        self.evidence_class = evidence_class
        self.timeout_seconds = float(timeout_seconds)
        self.max_output_bytes = max_output_bytes
        self.max_stderr_bytes = max_stderr_bytes
        self.shutdown_grace_seconds = float(shutdown_grace_seconds)
        self.environment = {
            name: os.environ[name]
            for name in allowed_environment
            if name in os.environ
        }

    def invoke(self, operation: str, payload: dict[str, Any]) -> AdapterReceipt:
        encoded = canonical_adapter_input(operation, payload)
        # Hash the exact bytes sent, so even a caller mutating its input object
        # concurrently cannot separate the receipt binding from the envelope.
        input_sha256 = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        started = time.monotonic()
        try:
            result = run_bounded_process(
                self.command,
                input_bytes=encoded.encode("utf-8"),
                timeout_seconds=self.timeout_seconds,
                stdout_limit_bytes=self.max_output_bytes,
                stderr_limit_bytes=self.max_stderr_bytes,
                shutdown_grace_seconds=self.shutdown_grace_seconds,
                env=self.environment,
            )
        except BoundedProcessTimeout as exc:
            raise AdapterError(
                f"{self.name} invocation timed out after {self.timeout_seconds:g}s"
            ) from exc
        except BoundedProcessOutputLimit as exc:
            raise AdapterError(
                f"{self.name} {exc.stream} exceeded its byte limit"
            ) from exc
        except OSError as exc:
            raise AdapterError(
                f"{self.name} invocation could not start ({type(exc).__name__})"
            ) from exc
        if result.returncode != 0:
            raise AdapterError(
                f"{self.name} exited {result.returncode}; "
                f"stderr_sha256={result.stderr_sha256}; "
                f"stderr_bytes={result.stderr_bytes}"
            )
        try:
            raw = json.loads(result.stdout.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AdapterError(f"{self.name} returned invalid JSON") from exc
        if not isinstance(raw, dict):
            raise AdapterError(f"{self.name} response must be an object")
        returned_hash = raw.get("input_sha256")
        if returned_hash != input_sha256:
            if returned_hash is None:
                raise AdapterError(f"{self.name} receipt is missing input_sha256")
            raise AdapterError(f"{self.name} receipt input_sha256 does not match its input")
        status = raw.get("status")
        if status != "passed":
            raise AdapterError(
                f"{self.name} did not pass; receipt status is {status!r}"
            )
        response_payload = raw.get("payload", {})
        if not isinstance(response_payload, dict):
            raise AdapterError(f"{self.name} payload must be an object")
        run_id = str(raw.get("run_id") or input_sha256[:24])
        return AdapterReceipt(
            adapter=self.name,
            run_id=run_id,
            status=status,
            evidence_class=self.evidence_class,
            payload=response_payload,
            input_sha256=input_sha256,
            elapsed_seconds=time.monotonic() - started,
        )

    def diagnostics(self) -> dict[str, Any]:
        """Run the adapter's mandatory read-only readiness handshake.

        An external command is not considered production-ready merely because
        it can be spawned.  It must implement this operation without causing
        effects and attest its exact Alice wire-contract version, adapter name,
        authentication state, and currently observed capabilities.
        """

        receipt = self.invoke(
            COMMAND_ADAPTER_DIAGNOSTICS_OPERATION,
            {
                "adapter": self.name,
                "contract_version": COMMAND_ADAPTER_CONTRACT_VERSION,
            },
        )
        payload = receipt.payload
        capabilities = payload.get("capabilities", [])
        if payload.get("adapter") != self.name:
            raise AdapterError(f"{self.name} diagnostics adapter identity mismatch")
        if payload.get("contract_version") != COMMAND_ADAPTER_CONTRACT_VERSION:
            raise AdapterError(f"{self.name} diagnostics contract version mismatch")
        if payload.get("ready") is not True:
            raise AdapterError(f"{self.name} diagnostics did not report ready")
        if payload.get("authenticated") is not True:
            raise AdapterError(
                f"{self.name} diagnostics did not report authenticated"
            )
        if not isinstance(capabilities, list) or any(
            not isinstance(item, str) or not item.strip() for item in capabilities
        ):
            raise AdapterError(f"{self.name} diagnostics capabilities are invalid")
        if len(set(capabilities)) != len(capabilities):
            raise AdapterError(f"{self.name} diagnostics capabilities are not unique")
        return {
            "adapter": self.name,
            "ready": True,
            "authenticated": True,
            "contract_version": COMMAND_ADAPTER_CONTRACT_VERSION,
            "capabilities": sorted(capabilities),
            "diagnostic_run_id": receipt.run_id,
            "diagnostic_input_sha256": receipt.input_sha256,
        }


__all__ = [
    "AdapterError",
    "AdapterReceipt",
    "COMMAND_ADAPTER_CONTRACT_VERSION",
    "COMMAND_ADAPTER_DIAGNOSTICS_OPERATION",
    "CommandAdapter",
    "adapter_input_sha256",
    "canonical_adapter_input",
]

"""Durable protocol for one native coding-agent product run."""

from importlib import import_module

from workshop.workflow.agent_run import (
    AGENT_OUTCOME_STATUSES,
    AGENT_RUN_STAGES,
    AgentArtifact,
    AgentOutcome,
    AgentRun,
    AgentRunCheckpoint,
    DeterministicGateReceipt,
)


_NATIVE_HOST_EXPORTS = (
    "NativeRunPaths",
    "canonical_wish_bytes",
    "materialized_agent_instructions_sha256",
    "native_run_exists",
    "native_run_paths",
    "native_run_status",
    "native_stage_prompt",
    "resume_native_run",
    "start_native_run",
)


def __getattr__(name: str):
    """Load the whole-run host only when an application asks for it."""

    if name not in _NATIVE_HOST_EXPORTS:
        raise AttributeError("module %r has no attribute %r" % (__name__, name))
    value = getattr(import_module("workshop.workflow.native_run"), name)
    globals()[name] = value
    return value

__all__ = [
    "AGENT_OUTCOME_STATUSES",
    "AGENT_RUN_STAGES",
    "AgentArtifact",
    "AgentOutcome",
    "AgentRun",
    "AgentRunCheckpoint",
    "DeterministicGateReceipt",
    *_NATIVE_HOST_EXPORTS,
]

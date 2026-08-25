"""Typed failures callers can act on without parsing log prose."""

from typing import Optional


class WorkshopError(Exception):
    """Base class for Inventor Workshop errors."""


class ContractError(WorkshopError):
    """Input violated a stable Workshop contract."""


class ManifestError(ContractError):
    """An inventor manifest is missing or invalid."""


class ArtifactError(ContractError):
    """An artifact tree cannot be safely identified or packaged."""


class StateConflict(WorkshopError):
    """Durable state changed since the caller read it."""


class TransitionError(WorkshopError):
    """A lifecycle transition is illegal or lacks bound evidence."""


class LeaseBusy(WorkshopError):
    """Another live worker owns the product lease."""


class BudgetExceeded(WorkshopError):
    """A code-enforced spending limit would be exceeded."""


class EffectError(WorkshopError):
    """An external effect was rejected before success was proven."""


class AmbiguousEffectError(EffectError):
    """The remote outcome is unknown, so an unsafe retry is blocked."""


class ReceiptError(EffectError):
    """A remote response cannot produce a trustworthy Receipt."""


class ConceptProviderError(WorkshopError):
    """A real Concept capability provider failed a call.

    Covers the image provider, the exploded-view inspection, and the wish
    research a brief is derived from.

    Raised for a failure in the call itself — a non-retryable HTTP status, an
    exhausted retry budget, or a response that cannot be trusted (malformed,
    oversized, or naming something it was never offered). Misconfiguration
    caught at construction time (a missing key, base URL, or model) stays a
    :class:`ContractError`, matching every other Workshop integration.
    """


class AgentSessionError(WorkshopError):
    """One named agent-door role failed to produce a trustworthy result.

    Raised by ``AgentSessionDoor`` for every way a role's call can fail after
    a process is launched: a non-zero exit, a wall-clock or budget bound
    exceeded, a missing result file, or a result that does not match the
    role's declared shape. Always names the role and carries the actual
    elapsed time (and, when known, the actual cost) the call consumed, so a
    budget stays auditable on failure the same as it is on success.
    """

    def __init__(
        self,
        role: str,
        message: str,
        *,
        elapsed_seconds: float,
        spent_micros: Optional[int] = None,
    ) -> None:
        super().__init__("agent door role %r %s" % (role, message))
        self.role = role
        self.elapsed_seconds = elapsed_seconds
        self.spent_micros = spent_micros


# Workshop 0.3 compatibility names.
SendError = EffectError
AmbiguousSendError = AmbiguousEffectError
StampError = ReceiptError


# Compatibility for Workshop 0.1 callers. New code catches WorkshopError.
FoundationError = WorkshopError
CoreError = WorkshopError
PublishError = EffectError
AmbiguousPublishError = AmbiguousEffectError

"""Typed failures callers can act on without parsing log prose."""


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


class SendError(WorkshopError):
    """A Door operation was rejected before success was proven."""


class AmbiguousSendError(SendError):
    """The remote outcome is unknown, so an unsafe retry is blocked."""


class StampError(SendError):
    """A remote response is not strong enough to produce a trustworthy Stamp."""


# Compatibility for Workshop 0.1 callers. New code catches WorkshopError.
FoundationError = WorkshopError
CoreError = WorkshopError
PublishError = SendError
AmbiguousPublishError = AmbiguousSendError
ReceiptError = StampError

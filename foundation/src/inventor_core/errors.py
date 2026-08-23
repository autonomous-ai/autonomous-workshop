"""Typed failures callers can act on without parsing log prose."""


class CoreError(Exception):
    """Base class for inventor-core errors."""


class ContractError(CoreError):
    """Input violated a stable Foundation contract."""


class ManifestError(ContractError):
    """An inventor manifest is missing or invalid."""


class ArtifactError(ContractError):
    """An artifact tree cannot be safely identified or packaged."""


class StateConflict(CoreError):
    """Durable state changed since the caller read it."""


class TransitionError(CoreError):
    """A lifecycle transition is illegal or lacks bound evidence."""


class LeaseBusy(CoreError):
    """Another live worker owns the product lease."""


class BudgetExceeded(CoreError):
    """A code-enforced spending limit would be exceeded."""


class PublishError(CoreError):
    """A marketplace operation was rejected before success was proven."""


class AmbiguousPublishError(PublishError):
    """The remote outcome is unknown, so an unsafe retry is blocked."""


class ReceiptError(PublishError):
    """A remote response is not strong enough to prove publication state."""

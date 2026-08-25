"""Public ports for external Workshop integrations.

Concrete adapters remain in their qualified modules so importing this public
surface never opens a network client or composes a runtime.
"""

from workshop.runtime import Adapter
from workshop.integrations.ports import (
    AgentPort,
    CadPort,
    CadVerifierPort,
    DeliveryPort,
    EvaluatorPort,
    LaunchPort,
)

__all__ = [
    "Adapter",
    "AgentPort",
    "CadPort",
    "CadVerifierPort",
    "DeliveryPort",
    "EvaluatorPort",
    "LaunchPort",
]

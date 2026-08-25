"""Compatibility imports for ports now declared by their owning components."""

from __future__ import annotations

from workshop.deliver import DeliveryPort
from workshop.instructions import LaunchPort
from workshop.make import CadDoor, CadInspectionDoor, InspectionDoor, ModelDoor


# True aliases preserve the former integration-centric vocabulary without
# leaving the declarations in the adapter component.
AgentPort = ModelDoor
CadPort = CadDoor
CadVerifierPort = CadInspectionDoor
EvaluatorPort = InspectionDoor


__all__ = [
    "AgentPort",
    "CadPort",
    "CadVerifierPort",
    "DeliveryPort",
    "EvaluatorPort",
    "LaunchPort",
]

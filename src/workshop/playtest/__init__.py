"""Public Playtest contracts, evidence, and deterministic gameplay seams."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from workshop.playtest.contracts import PlaytestContext, Playtested
from workshop.playtest.evidence import GateResult, InspectionResult, PlaytestResult
from workshop.playtest.gameplay import (
    FINITE_GAME_SIMULATOR_SOURCE,
    ExecutableGame,
    GameTrace,
    LeagueConfig,
    LeagueReport,
    PlayerPolicy,
    RandomPlayer,
    run_game,
    run_league,
)
from workshop.playtest.service import Playtest


_LAZY_EXPORTS = {
    "CapabilityReleaseProof": ("workshop.playtest.release", "CapabilityReleaseProof"),
    "MovingMachineVerification": (
        "workshop.playtest.moving_machine",
        "MovingMachineVerification",
    ),
    "ReleaseProofSource": ("workshop.playtest.release", "ReleaseProofSource"),
    "WorkshopMovingMachineVerifier": (
        "workshop.playtest.moving_machine",
        "WorkshopMovingMachineVerifier",
    ),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attribute = target
    value = getattr(import_module(module_name), attribute)
    globals()[name] = value
    return value


__all__ = [
    "CapabilityReleaseProof",
    "ExecutableGame",
    "FINITE_GAME_SIMULATOR_SOURCE",
    "GameTrace",
    "GateResult",
    "InspectionResult",
    "LeagueConfig",
    "LeagueReport",
    "MovingMachineVerification",
    "PlayerPolicy",
    "Playtest",
    "PlaytestContext",
    "PlaytestResult",
    "Playtested",
    "RandomPlayer",
    "ReleaseProofSource",
    "WorkshopMovingMachineVerifier",
    "run_game",
    "run_league",
]

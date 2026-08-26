"""Workshop-owned composition of the default stage implementations."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from workshop.errors import ContractError


def configured_workshop_tools(
    existing=None,
    *,
    inventor_id: Optional[str] = None,
    runtime_root: Optional[Path] = None,
):
    """Merge the opt-in shared Codex workers into one Workshop tool set.

    The Workshop-owned Invent, Make, and Playtest workers are the default.
    ``WORKSHOP_AGENT_WORKERS=disabled`` is an explicit diagnostic escape hatch;
    normal Inventors never need an environment switch to receive the engine.
    Rewarded Release is also a shared default. Without Factory credentials
    it still creates, scores, and seals the local manual and product facts, then
    waits truthfully at the external handoff. Explicit caller tools always win
    field by field.

    Shared Playtest includes the pinned checkers provider and the narrow
    primitive moving-machine verifier. Deployments install authoritative
    science sources and private world consent/reference providers on
    ``LaneAwarePlaytester`` field by field; Inventors still keep the shared
    Playtest engine.

    ``WORKSHOP_INVENT_WORKER=codex`` remains a backward-compatible alias for
    the normal shared-worker default. It must never strand an older direct
    profile with Invent alone while silently removing Make, Playtest, and
    Release.
    """

    from workshop.workflow import WorkshopTools

    if existing is not None and not isinstance(existing, WorkshopTools):
        raise ContractError("configured Workshop tools must be a WorkshopTools value")
    selected = existing or WorkshopTools()
    worker_mode = os.environ.get("WORKSHOP_AGENT_WORKERS")
    if worker_mode not in (None, "codex", "disabled"):
        raise ContractError(
            "WORKSHOP_AGENT_WORKERS must be codex, disabled, or unset"
        )
    legacy_invent = os.environ.get("WORKSHOP_INVENT_WORKER")
    if legacy_invent not in (None, "codex"):
        raise ContractError("WORKSHOP_INVENT_WORKER must be codex or unset")
    if worker_mode == "disabled":
        return selected

    invent = selected.invent
    make = selected.make
    playtest = selected.playtest
    release = selected.release

    if invent is None:
        from workshop.invent.agent import CodexInventor

        invent = CodexInventor()

    from workshop.make.agent import CodexMaker
    from workshop.playtest.agent import LaneAwarePlaytester
    from workshop.playtest.gameplay import FINITE_GAME_SIMULATOR_SOURCE

    if make is None:
        make = CodexMaker(
            game_simulator_source=FINITE_GAME_SIMULATOR_SOURCE,
        )
    if playtest is None:
        playtest = LaneAwarePlaytester()

    if release is None:
        from workshop.release.agent import RewardedRelease

        site_writer = None
        factory_names = ("FACTORY_USERNAME", "FACTORY_PASSWORD")
        factory_environment_present = any(
            name in os.environ for name in factory_names
        )
        if factory_environment_present:
            from workshop.integrations.factory_agent import (
                FactoryAgentReleaseWriter,
                factory_credentials_from_environment,
            )
            from workshop.runtime.store import InventorStore

            if inventor_id is None:
                raise ContractError(
                    "Factory Release requires the selected inventor_id"
                )
            if runtime_root is None:
                raise ContractError(
                    "Factory Release requires a caller-supplied runtime_root"
                )
            try:
                selected_runtime = Path(runtime_root)
            except TypeError as exc:
                raise ContractError("Workshop runtime_root must be path-like") from exc
            if not selected_runtime.is_absolute():
                raise ContractError("Workshop runtime_root must be absolute")
            if selected_runtime.is_symlink():
                raise ContractError("Workshop runtime_root must not be a symlink")
            credentials = factory_credentials_from_environment(
                inventor_id,
                os.environ,
            )
            store = InventorStore(selected_runtime / "workshop.sqlite3")
            site_writer = FactoryAgentReleaseWriter(
                store,
                inventor_id,
                credentials,
            )
        release = RewardedRelease(site_writer)

    return WorkshopTools(
        invent=invent,
        make=make,
        playtest=playtest,
        release=release,
        deliver=selected.deliver,
    )


def configured_workshop(
    inventor_root: Path,
    lane: str,
    *,
    inventor_id: Optional[str] = None,
    tools=None,
    make=None,
    playtest=None,
    review_authenticator=None,
    runtime_root: Optional[Path] = None,
    max_rounds: int = 4,
):
    """Compose application defaults, then construct the pure workflow engine.

    This is the installed profiles' normal entry point. ``Workshop`` itself
    accepts only an explicit tool set, keeping provider/runtime construction in
    this outer application layer.
    """

    from workshop.workflow import Workshop, WorkshopTools

    if tools is not None and not isinstance(tools, WorkshopTools):
        raise ContractError("configured Workshop tools must be a WorkshopTools value")
    selected = tools or WorkshopTools()
    if playtest is not None and make is None:
        raise ContractError("custom Playtest requires custom Make")
    requested = WorkshopTools(
        invent=selected.invent,
        make=make if make is not None else selected.make,
        playtest=playtest if playtest is not None else selected.playtest,
        release=selected.release,
        deliver=selected.deliver,
    )
    composed = configured_workshop_tools(
        requested,
        inventor_id=inventor_id,
        runtime_root=runtime_root,
    )
    return Workshop(
        inventor_root,
        lane,
        inventor_id=inventor_id,
        tools=composed,
        make=make,
        playtest=playtest,
        review_authenticator=review_authenticator,
        runtime_root=runtime_root,
        max_rounds=max_rounds,
    )


__all__ = ["configured_workshop", "configured_workshop_tools"]

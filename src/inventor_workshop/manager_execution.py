"""Manager-owned execution of the shared Workshop engine.

The authoritative ``workshop wish`` path never executes an Inventor profile.
Taste is inert data. Declared custom Make and Playtest seams run one stage at a
time through the bounded contribution RPC; Invent, Instructions, Deliver,
credentials, reward loops, release policy, and durable state remain in this
trusted process.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Optional

from .contribution_rpc import ContributionHookClient, IsolationAdapter
from .errors import ContractError
from .handoff import ManagerAssignmentHandoff
from .manifest import load_manifest
from .manager_services import manager_service_forbidden_read_paths
from .toys import PLAYTHING_LANES
from .workshop import (
    CUSTOMIZATION_LEVELS,
    TrustedWorkshopEngine,
    Workshop,
    WorkshopTools,
)


def default_trusted_workshop_engine() -> TrustedWorkshopEngine:
    """Materialize the exact effect-free built-in Manager engine composition."""

    from .agent_instructions import RewardedInstructions
    from .agent_invent import CodexInventor
    from .agent_make import CodexMaker
    from .agent_playtest import LaneAwarePlaytester
    from .deliver import DefaultDeliver
    from .engine_provenance import (
        DEFAULT_STAGE_PROVIDER_IDS,
        describe_effective_engine,
    )
    from .manager import register_workshop_engine

    tools = WorkshopTools(
        invent=CodexInventor(),
        make=CodexMaker(),
        playtest=LaneAwarePlaytester(),
        instructions=RewardedInstructions(None),
        deliver=DefaultDeliver(),
    )
    components = {
        "invent": tools.invent,
        "make": tools.make,
        "playtest": tools.playtest,
        "instructions": tools.instructions,
        "deliver": tools.deliver,
    }
    return register_workshop_engine(
        tools,
        provider_ids=DEFAULT_STAGE_PROVIDER_IDS,
        provenance=describe_effective_engine(
            components, provider_ids=DEFAULT_STAGE_PROVIDER_IDS
        ),
    )


def manager_workshop_shape(card: Any) -> tuple[str, str]:
    """Return the exact lane and declared contribution level for one card."""

    current = getattr(card, "assert_manifest_current", None)
    if callable(current):
        current()
    try:
        root = Path(card.root)
    except (AttributeError, TypeError) as exc:
        raise ContractError("Manager execution requires a selected Inventor card") from exc
    manifest = load_manifest(root / "inventor.json")
    card_id = getattr(card, "inventor_id", None)
    if card_id != manifest.inventor_id:
        raise ContractError("selected Inventor card and manifest identities differ")
    lanes = tuple(
        capability
        for capability in manifest.capabilities
        if capability in PLAYTHING_LANES
    )
    levels = tuple(
        capability
        for capability in manifest.capabilities
        if capability in CUSTOMIZATION_LEVELS
    )
    if (
        len(lanes) != 1
        or len(levels) != 1
        or set(manifest.capabilities) != {lanes[0], levels[0]}
    ):
        raise ContractError(
            "selected Inventor manifest must declare exactly one lane and one known contribution level"
        )
    return lanes[0], levels[0]


def execute_manager_workshop(
    assignment: Any,
    *,
    action: str = "run",
    trusted_engine: Optional[TrustedWorkshopEngine] = None,
    runtime_root: Optional[Path] = None,
    workshop_factory: Any = Workshop,
    contribution_isolation: Optional[IsolationAdapter] = None,
) -> Mapping[str, Any]:
    """Run one assignment without executing its full profile.

    ``action`` supports durable ``run``/``resume`` plus a Deliver-only
    ``reconcile`` readback. Declared custom hooks receive only their exact Make
    or Playtest context in a credential-free child, and reconciliation installs
    inert seams that cannot invoke them. The exact assignment is checked before
    and after shared-engine work, and the returned result retains the Manager
    handoff binding expected by later continuations.
    """

    if action not in ("run", "resume", "reconcile"):
        raise ContractError(
            "Manager Workshop action must be run, resume, or reconcile"
        )
    assert_current = getattr(assignment, "assert_current", None)
    if not callable(assert_current):
        raise ContractError("Manager execution requires a current sealed assignment")
    assert_current()
    try:
        card = assignment.decision.selected.card
        wish = assignment.wish
        inventor_id = assignment.inventor_id
        playtest_rounds = assignment.playtest_rounds
    except AttributeError as exc:
        raise ContractError("Manager execution requires a complete assignment") from exc
    lane, level = manager_workshop_shape(card)
    if type(playtest_rounds) is not int or not 1 <= playtest_rounds <= 100:
        raise ContractError("Manager assignment Playtest rounds are invalid")
    if not callable(workshop_factory):
        raise ContractError("Manager Workshop factory must be callable")
    if contribution_isolation is not None and not callable(contribution_isolation):
        raise ContractError(
            "Manager contribution_isolation must be a trusted callable adapter"
        )

    selected_runtime = (
        Path(card.root) / ".workshop"
        if runtime_root is None
        else Path(runtime_root)
    )
    if not selected_runtime.is_absolute():
        raise ContractError("Manager Workshop runtime_root must be absolute")
    kwargs = {
        "inventor_id": inventor_id,
        "runtime_root": selected_runtime,
        "max_rounds": playtest_rounds,
    }
    if trusted_engine is None:
        # The first engine pass may create and score Instructions, but Factory
        # authority belongs to the later Manager continuation.  Supplying an
        # explicit local-only Instructions worker prevents a Manager-held
        # password (whose username is not known until after Match) from being
        # mistaken for a partial worker credential configuration.
        trusted_engine = default_trusted_workshop_engine()
    else:
        if not isinstance(trusted_engine, TrustedWorkshopEngine):
            raise ContractError(
                "Manager execution trusted_engine must be a registered engine"
            )
    kwargs["trusted_engine"] = trusted_engine
    if level in ("custom-make", "custom-playtest"):
        # Resolve every installed Manager-service entry point without loading
        # it.  The child can read the Python runtime, so its OS profile must
        # explicitly hide both provider import targets and the metadata that
        # would disclose them.  Resolution failure is deliberately fatal for
        # custom code; Taste-only inventors never enter this branch.
        contribution = None
        if action != "reconcile":
            manager_service_paths = manager_service_forbidden_read_paths()
            contribution = ContributionHookClient(
                card.root,
                level,
                isolation=contribution_isolation,
                forbidden_read_paths=manager_service_paths,
            )

        def custom_make(context):
            assert_current()
            if contribution is None:
                raise ContractError(
                    "Deliver reconciliation attempted to rerun custom Make"
                )
            try:
                return contribution.make(context)
            finally:
                assert_current()

        kwargs["make"] = custom_make
        implementation_sha256 = assignment.decision.selected.implementation_sha256
        custom_component_sha256 = {"make": implementation_sha256}
        if level == "custom-playtest":
            def custom_playtest(context):
                assert_current()
                if contribution is None:
                    raise ContractError(
                        "Deliver reconciliation attempted to rerun custom Playtest"
                    )
                try:
                    return contribution.playtest(context)
                finally:
                    assert_current()

            kwargs["playtest"] = custom_playtest
            custom_component_sha256["playtest"] = implementation_sha256
        kwargs["custom_component_sha256"] = custom_component_sha256
    if lane == "little-worlds":
        kwargs.update(
            {
                "world_inputs": getattr(assignment, "world_inputs", None),
                "world_evidence": getattr(assignment, "world_evidence", None),
            }
        )

    workshop = workshop_factory(card.root, lane, **kwargs)
    if action == "run":
        result = workshop.run(wish, playtest_rounds=playtest_rounds)
    elif action == "resume":
        result = workshop.resume(wish)
    else:
        result = workshop.reconcile_deliver(wish)
    to_dict = getattr(result, "to_dict", None)
    if not callable(to_dict):
        raise ContractError("Manager Workshop must return a typed WorkshopRun")
    payload = to_dict()
    if not isinstance(payload, Mapping):
        raise ContractError("Manager Workshop result must be one object")
    assert_current()
    handoff = ManagerAssignmentHandoff.from_assignment(assignment)
    return {**dict(payload), "manager_assignment": handoff.result_binding()}


__all__ = ["execute_manager_workshop", "manager_workshop_shape"]

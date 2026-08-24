"""The five-job Toy Workshop and its three inventor customization levels.

An inventor supplies Taste and may replace Make, or Make and Playtest. The
Workshop always owns the loop, exact artifact identity, Instructions, Deliver, and
truthful waiting for capabilities or real-world evidence that are not present.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from .deliver import DefaultDeliver
from .instructions import DefaultInstructions
from .errors import ContractError
from .jobs import (
    DeliverContext,
    Delivered,
    InstructionsContext,
    Made,
    MakeContext,
    Need,
    PlaytestContext,
    Playtested,
    ProductInstructions,
    WaitingFor,
    WorkshopRun,
)
from .make import Wish
from .runtime import Runtime
from .taste import load_taste
from .toys import ToyBlueprint, playful_make_request


MakeJob = Callable[[MakeContext], Made]
PlaytestJob = Callable[[PlaytestContext], Playtested]
InstructionsJob = Callable[[InstructionsContext], ProductInstructions]
DeliverJob = Callable[[DeliverContext], Delivered]

CUSTOMIZATION_LEVELS = ("taste-only", "custom-make", "custom-playtest")


def _callable_or_none(value: Any, label: str) -> None:
    if value is not None and not callable(value):
        raise ContractError("%s must be callable or absent" % label)


def _inside(path: Path, root: Path, label: str) -> None:
    try:
        path.resolve(strict=True).relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise ContractError("%s must stay inside its Workshop workspace" % label) from exc


def _playtest_policy_needs(
    blueprint: ToyBlueprint, playtested: Playtested
) -> tuple[Need, ...]:
    """Return evidence the lane still needs before Instructions may begin.

    A custom Playtest can decide how to obtain evidence, but it cannot silently
    narrow the Workshop policy. Result IDs are the blueprint capability names.
    The invented-game release gate additionally validates the meaning of its
    two highest-risk results instead of accepting a conveniently named pass.
    """

    by_id = {result.playtest_id: result for result in playtested.evidence.results}
    needs = [
        Need(
            "playtest",
            capability,
            "The custom Playtest did not return this required lane result.",
            "Return an artifact-bound PlaytestResult whose ID is %r, or wait for the real capability."
            % capability,
        )
        for capability in blueprint.required_capabilities("playtest")
        if capability not in by_id
    ]

    if blueprint.lane != "invented-games":
        return tuple(needs)

    simulation = by_id.get("game-simulation")
    if simulation is not None and simulation.passed:
        evidence = simulation.evidence
        styles = evidence.get("player_styles", ())
        required_styles = {"optimizing", "social", "exploratory", "adversarial"}
        simulation_is_real = (
            evidence.get("evidence_class") == "ai-simulation"
            and type(evidence.get("completed_games")) is int
            and evidence["completed_games"] >= 1_000
            and evidence.get("executable") is True
            and isinstance(styles, (list, tuple))
            and all(isinstance(style, str) for style in styles)
            and required_styles <= set(styles)
        )
        if not simulation_is_real:
            needs.append(
                Need(
                    "playtest",
                    "game-simulation",
                    "An invented game needs executable evidence from at least 1,000 seeded games across all four player styles.",
                    "Return game-simulation evidence_class=ai-simulation, executable=true, completed_games>=1000, and optimizing/social/exploratory/adversarial player_styles.",
                )
            )

    # Keep one actionable request per capability even when a malformed result
    # and a missing-result check converge on the same policy requirement.
    unique = {}
    for need in needs:
        unique.setdefault(need.capability, need)
    return tuple(unique.values())


@dataclass(frozen=True)
class WorkshopTools:
    """Shared capabilities installed once for every inventor in one Workshop."""

    make: Optional[MakeJob] = None
    playtest: Optional[PlaytestJob] = None
    instructions: Optional[InstructionsJob] = None
    deliver: Optional[DeliverJob] = None

    def __post_init__(self) -> None:
        for value, label in (
            (self.make, "Workshop Make"),
            (self.playtest, "Workshop Playtest"),
            (self.instructions, "Workshop Instructions"),
            (self.deliver, "Workshop Deliver"),
        ):
            _callable_or_none(value, label)


def _missing_make(context: MakeContext) -> Made:
    del context
    raise WaitingFor(
        Need(
            "make",
            "model-and-cad-maker",
            "This Workshop has no configured model and parametric CAD maker.",
            "Install the shared model/CAD worker backed by the locked CAD and STEP-parts skills.",
        )
    )


def _missing_playtest(context: PlaytestContext) -> Playtested:
    capabilities = context.blueprint.required_capabilities("playtest")
    raise WaitingFor(
        *(
            Need(
                "playtest",
                capability,
                "This exact Make still needs %s evidence." % capability,
                "Configure the shared Playtest capability; never replace missing evidence with an inventor self-score.",
            )
            for capability in capabilities
        )
    )


class Workshop:
    """Run one inventor through Wish -> Make <-> Playtest -> Instructions -> Deliver.

    With neither override, the inventor authors only ``TASTE.md``. A Make override
    creates the middle level. Make plus Playtest creates the maximum level.
    """

    def __init__(
        self,
        inventor_root: Path,
        lane: str,
        *,
        tools: Optional[WorkshopTools] = None,
        make: Optional[MakeJob] = None,
        playtest: Optional[PlaytestJob] = None,
        runtime_root: Optional[Path] = None,
        max_rounds: int = 4,
    ) -> None:
        requested_root = Path(inventor_root)
        if requested_root.is_symlink():
            raise ContractError("inventor root must not be a symlink")
        try:
            root = requested_root.resolve(strict=True)
        except OSError as exc:
            raise ContractError("cannot resolve inventor root") from exc
        if not root.is_dir():
            raise ContractError("inventor root must be a directory")
        _callable_or_none(make, "inventor Make")
        _callable_or_none(playtest, "inventor Playtest")
        if playtest is not None and make is None:
            raise ContractError("custom Playtest requires custom Make")
        if type(max_rounds) is not int or not 1 <= max_rounds <= 100:
            raise ContractError("max_rounds must be an integer from 1 to 100")

        selected_tools = tools or WorkshopTools()
        selected_runtime = Path(runtime_root) if runtime_root else root / ".workshop"
        if not selected_runtime.is_absolute():
            raise ContractError("Workshop runtime_root must be absolute")
        if selected_runtime.is_symlink():
            raise ContractError("Workshop runtime_root must not be a symlink")

        self.inventor_root = root
        self.taste = load_taste(root)
        self.blueprint = ToyBlueprint.for_lane(lane)
        self.tools = selected_tools
        self.make_job: MakeJob = make or selected_tools.make or _missing_make
        self.playtest_job: PlaytestJob = (
            playtest or selected_tools.playtest or _missing_playtest
        )
        self.instructions_job: InstructionsJob = (
            selected_tools.instructions or DefaultInstructions()
        )
        self.deliver_job: DeliverJob = selected_tools.deliver or DefaultDeliver()
        self.runtime_root = selected_runtime
        self.max_rounds = max_rounds
        if playtest is not None:
            self.customization_level = "custom-playtest"
        elif make is not None:
            self.customization_level = "custom-make"
        else:
            self.customization_level = "taste-only"

    @property
    def lane(self) -> str:
        return self.blueprint.lane

    def preview(self, wish: Wish) -> Mapping[str, Any]:
        """Return the exact Taste-bound playful brief shared Make receives."""

        return playful_make_request(wish, self.taste, self.blueprint)

    def _runtime(self) -> Runtime:
        return Runtime(self.runtime_root / "workshop.sqlite3")

    @staticmethod
    def _advance(
        runtime: Runtime,
        product_id: str,
        to_job: str,
        *,
        artifact_sha256: Optional[str],
        payload: Mapping[str, Any],
        lease_token: str,
    ) -> Mapping[str, Any]:
        product = runtime.get_product(product_id)
        source = product["stage"]
        legal = {
            "wish": ("make",),
            "make": ("make", "playtest"),
            "playtest": ("playtest", "make", "instructions"),
            "instructions": ("instructions", "deliver"),
            "deliver": ("deliver",),
        }
        if to_job not in legal.get(source, ()):
            raise ContractError("illegal Workshop job move %s -> %s" % (source, to_job))
        return runtime._transition(
            product_id,
            source,
            to_job,
            product["revision"],
            artifact_sha256,
            dict(payload),
            lease_token,
        )

    def _wait(
        self,
        runtime: Runtime,
        wish: Wish,
        job: str,
        round_number: int,
        waiting: WaitingFor,
        lease_token: str,
        playtest_rounds: int,
        *,
        artifact_sha256: Optional[str] = None,
        instructions_sha256: Optional[str] = None,
    ) -> WorkshopRun:
        if any(need.job != job for need in waiting.needs):
            raise ContractError("waiting capability belongs to a different Workshop job")
        self._advance(
            runtime,
            wish.product_id,
            job,
            artifact_sha256=artifact_sha256,
            payload={
                "status": "waiting",
                "round": round_number,
                "needs": [need.to_dict() for need in waiting.needs],
            },
            lease_token=lease_token,
        )
        return WorkshopRun(
            wish.product_id,
            "waiting",
            job,
            round_number,
            artifact_sha256,
            instructions_sha256,
            waiting.needs,
            playtest_rounds=playtest_rounds,
        )

    def run(
        self, wish: Wish, *, playtest_rounds: Optional[int] = None
    ) -> WorkshopRun:
        """Start one product and run until delivered, waiting, or bounded stop."""

        if not isinstance(wish, Wish):
            raise ContractError("Workshop.run requires a Wish")
        wish.assert_valid()
        selected_rounds = self.max_rounds if playtest_rounds is None else playtest_rounds
        if type(selected_rounds) is not int or not 1 <= selected_rounds <= 100:
            raise ContractError("playtest_rounds must be an integer from 1 to 100")
        self.taste.assert_current()
        runtime = self._runtime()
        runtime.register_product(
            wish.product_id,
            "wish",
            {
                "wish": wish.to_dict(),
                "taste_sha256": self.taste.sha256,
                "blueprint_sha256": self.blueprint.sha256,
                "lane": self.lane,
                "customization_level": self.customization_level,
                "playtest_rounds": selected_rounds,
            },
        )
        lease = runtime.acquire_lease(wish.product_id, "toy-workshop")
        try:
            run_root = self.runtime_root / "runs" / wish.product_id
            if run_root.exists():
                if run_root.is_symlink() or not run_root.is_dir() or any(run_root.iterdir()):
                    raise ContractError("new Workshop run directory must be fresh and empty")
            else:
                run_root.mkdir(parents=True, mode=0o700)
            run_root = run_root.resolve(strict=True)
            self._advance(
                runtime,
                wish.product_id,
                "make",
                artifact_sha256=None,
                payload={"status": "working", "round": 1},
                lease_token=lease,
            )

            feedback = ()
            made: Optional[Made] = None
            playtested: Optional[Playtested] = None
            round_number = 0
            for round_number in range(1, selected_rounds + 1):
                round_root = run_root / ("round-%03d" % round_number)
                make_workspace = (round_root / "make").absolute()
                make_context = MakeContext(
                    wish,
                    self.taste,
                    self.blueprint,
                    round_number,
                    make_workspace,
                    feedback,
                    selected_rounds,
                )
                try:
                    made = self.make_job(make_context)
                except WaitingFor as waiting:
                    return self._wait(
                        runtime,
                        wish,
                        "make",
                        round_number,
                        waiting,
                        lease,
                        selected_rounds,
                    )
                if not isinstance(made, Made):
                    raise ContractError("Make must return Made")
                _inside(made.artifact_root, make_workspace, "Made artifact")
                made.assert_current()
                if made.product.get("lane") != self.lane:
                    raise ContractError("Make returned a product for another plaything lane")
                self.taste.assert_current()
                self._advance(
                    runtime,
                    wish.product_id,
                    "playtest",
                    artifact_sha256=made.artifact_sha256,
                    payload={
                        "status": "working",
                        "round": round_number,
                        "artifact_sha256": made.artifact_sha256,
                    },
                    lease_token=lease,
                )

                playtest_workspace = (round_root / "playtest").absolute()
                playtest_context = PlaytestContext(
                    wish,
                    self.taste,
                    self.blueprint,
                    round_number,
                    made,
                    playtest_workspace,
                    selected_rounds,
                )
                try:
                    playtested = self.playtest_job(playtest_context)
                except WaitingFor as waiting:
                    return self._wait(
                        runtime,
                        wish,
                        "playtest",
                        round_number,
                        waiting,
                        lease,
                        selected_rounds,
                        artifact_sha256=made.artifact_sha256,
                    )
                if not isinstance(playtested, Playtested):
                    raise ContractError("Playtest must return Playtested")
                playtested.assert_artifact(made.artifact_sha256)
                made.assert_current()
                if playtested.passed:
                    policy_needs = _playtest_policy_needs(self.blueprint, playtested)
                    if policy_needs:
                        return self._wait(
                            runtime,
                            wish,
                            "playtest",
                            round_number,
                            WaitingFor(*policy_needs),
                            lease,
                            selected_rounds,
                            artifact_sha256=made.artifact_sha256,
                        )
                    self._advance(
                        runtime,
                        wish.product_id,
                        "instructions",
                        artifact_sha256=made.artifact_sha256,
                        payload={
                            "status": "working",
                            "round": round_number,
                            "evidence_artifact_sha256": (
                                playtested.evidence.evidence_artifact_sha256
                            ),
                        },
                        lease_token=lease,
                    )
                    break
                feedback = tuple(
                    item
                    for item in playtested.feedback
                    if item.severity in ("improve", "block")
                )
                if not feedback:
                    raise ContractError(
                        "a failed Playtest must return actionable improve or block feedback"
                    )
                if round_number == selected_rounds:
                    self._advance(
                        runtime,
                        wish.product_id,
                        "playtest",
                        artifact_sha256=made.artifact_sha256,
                        payload={
                            "status": "stopped",
                            "round": round_number,
                            "feedback": [item.to_dict() for item in feedback],
                        },
                        lease_token=lease,
                    )
                    return WorkshopRun(
                        wish.product_id,
                        "stopped",
                        "playtest",
                        round_number,
                        made.artifact_sha256,
                        playtest_rounds=selected_rounds,
                    )
                self._advance(
                    runtime,
                    wish.product_id,
                    "make",
                    artifact_sha256=made.artifact_sha256,
                    payload={
                        "status": "working",
                        "round": round_number + 1,
                        "feedback": [item.to_dict() for item in feedback],
                    },
                    lease_token=lease,
                )

            if made is None or playtested is None or not playtested.passed:
                raise ContractError("Workshop ended without an approved Make")
            instructions_workspace = (run_root / "instructions").absolute()
            instructions_context = InstructionsContext(
                wish,
                self.taste,
                self.blueprint,
                made,
                playtested,
                instructions_workspace,
            )
            try:
                product_instructions = self.instructions_job(instructions_context)
            except WaitingFor as waiting:
                return self._wait(
                    runtime,
                    wish,
                    "instructions",
                    round_number,
                    waiting,
                    lease,
                    selected_rounds,
                    artifact_sha256=made.artifact_sha256,
                )
            if not isinstance(product_instructions, ProductInstructions):
                raise ContractError(
                    "Instructions must return ProductInstructions"
                )
            _inside(
                product_instructions.root,
                instructions_workspace,
                "Instructions result",
            )
            product_instructions.assert_current()
            if (
                product_instructions.product_artifact_sha256
                != made.artifact_sha256
            ):
                raise ContractError(
                    "Instructions describe different product bytes"
                )
            self._advance(
                runtime,
                wish.product_id,
                "deliver",
                artifact_sha256=made.artifact_sha256,
                payload={
                    "status": "working",
                    "round": round_number,
                    "instructions_sha256": (
                        product_instructions.instructions_sha256
                    ),
                },
                lease_token=lease,
            )
            deliver_context = DeliverContext(wish, made, product_instructions)
            try:
                delivered = self.deliver_job(deliver_context)
            except WaitingFor as waiting:
                return self._wait(
                    runtime,
                    wish,
                    "deliver",
                    round_number,
                    waiting,
                    lease,
                    selected_rounds,
                    artifact_sha256=made.artifact_sha256,
                    instructions_sha256=(
                        product_instructions.instructions_sha256
                    ),
                )
            if not isinstance(delivered, Delivered):
                raise ContractError("Deliver must return Delivered")
            delivered.assert_context(deliver_context)
            self._advance(
                runtime,
                wish.product_id,
                "deliver",
                artifact_sha256=made.artifact_sha256,
                payload={
                    "status": "delivered",
                    "round": round_number,
                    "instructions_sha256": (
                        product_instructions.instructions_sha256
                    ),
                    "delivery": delivered.to_dict(),
                },
                lease_token=lease,
            )
            return WorkshopRun(
                wish.product_id,
                "delivered",
                "deliver",
                round_number,
                made.artifact_sha256,
                product_instructions.instructions_sha256,
                delivery=delivered,
                playtest_rounds=selected_rounds,
            )
        finally:
            runtime.release_lease(wish.product_id, lease)


# Compatibility imports for callers that used this module as the old offline
# demo location. They are not part of the five-job design.
from .offline import (  # noqa: E402,F401
    OfflineInspector,
    OfflineMaker,
    OfflineMuse,
    OfflineProvingGround,
    offline_forge,
    offline_workbench,
)


__all__ = [
    "CUSTOMIZATION_LEVELS",
    "DeliverJob",
    "InstructionsJob",
    "MakeJob",
    "PlaytestJob",
    "Workshop",
    "WorkshopTools",
    "offline_workbench",
]

"""ABO's Playtest: what it can measure, and what it still waits for.

The lane requires four results — `agent-playtest`, `game-simulation`,
`mechanical-test` and `print-test` — and every passing one has to be
`evidence_class=ai-simulation`, name its evaluator and exact version, and
reference sealed evidence by hash.

`game-simulation` is connected: it runs the imported seeded harness against the
engine bytes inside the revision under test, counts only completed games, and
returns a truthful `Need` rather than a passing result when the deadline
arrives short of a thousand. The other three are not written yet, and this seam
says so with a typed `Need` instead of returning a conveniently named pass.

**Why this file is not called `playtest.py`.** The design sketches ABO's three
seams as `concept.py`, `make.py` and `playtest.py`. The first two keep those
names; this one cannot. `harness/table_run.py` imports the simulation harness as
a bare `import playtest`, and a module of that name at the inventor root would
shadow the vendored one — silently handing a vendored file this module instead
of the harness it expects. The vendored bytes are locked and are not edited to
route around a name, so the adapter moves instead.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from inventor_workshop.artifacts import build_artifact_manifest
from inventor_workshop.errors import ContractError
from inventor_workshop.jobs import Need, PlaytestContext, Playtested, WaitingFor
from inventor_workshop.models import PlaytestResult
from inventor_workshop.playtest import Playtest

import config
import feedback as abo_feedback
import manufacturing
import model_seats
import simulation
from game import GameRecord
from make import ENGINE_DIRECTORY, ENGINE_FILENAME, RULES_FILENAME, load_engine

EVIDENCE_DIRECTORY = "evidence"

MANUFACTURING: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("mechanical-test", manufacturing.MECHANICAL_CHECKS),
    ("print-test", manufacturing.PRINT_CHECKS),
)


def _seal(evidence_root: Path, name: str, payload: Mapping[str, Any]) -> Tuple[str, str]:
    """Write one evidence file and return its path and digest.

    Evidence is sealed separately from the product so a finding can improve the
    next Make without changing the exact bytes that were tested.
    """

    evidence_root.mkdir(parents=True, mode=0o700, exist_ok=True)
    relative = "%s.json" % name
    path = evidence_root / relative
    body = json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n"
    path.write_text(body, encoding="utf-8")
    return relative, hashlib.sha256(body.encode("utf-8")).hexdigest()


def simulation_need(outcome: simulation.SimulationOutcome) -> Need:
    """The truthful short return: how far it got, and nothing dressed up."""

    return Need(
        "playtest",
        "game-simulation",
        "The simulation reached its deadline with %d completed games, short of "
        "the %d this lane requires. Games abandoned at the turn cap, at the "
        "deadline, or on a rules gap are excluded: %s."
        % (
            outcome.completed_games,
            simulation.MINIMUM_COMPLETED_GAMES,
            ", ".join(
                "%s %d" % (key.replace("_", " "), value)
                for key, value in sorted(outcome.evidence["abandoned"].items())
            ),
        ),
        "Give the simulation a longer deadline or a faster engine and run it "
        "again. Never report a pass over a smaller sample, and never extend the "
        "deadline silently to reach the floor.",
    )


class AboPlaytest:
    """`PlaytestContext -> Playtested` for ABO."""

    def __init__(
        self,
        *,
        simulation_settings: Optional[Mapping[str, Any]] = None,
        evidence_root: Optional[Path] = None,
        seat_transport: Optional[Any] = None,
        model_seat_games: int = 4,
        brief: Optional[Any] = None,
    ) -> None:
        # The brief's millimetres are what geometry is measured against. It
        # travels with the concept, and `PlaytestContext` does not carry one,
        # so it is supplied here or read back from the revision's own facts.
        self.brief = brief
        self.simulation_settings = dict(simulation_settings or {})
        self.evidence_root = evidence_root
        # Absent a transport, one is built from the ABO-scoped environment.
        # Absent that too, the run parks: a passing `agent-playtest` is never
        # assembled from scripted policies, which have no roles and no reports.
        self.seat_transport = seat_transport
        self.model_seat_games = model_seat_games

    def __call__(self, context: PlaytestContext) -> Playtested:
        if not isinstance(context, PlaytestContext):
            raise ContractError("ABO's Playtest requires a PlaytestContext")
        context.made.assert_current()

        engine_path = (
            context.made.artifact_root / ENGINE_DIRECTORY / ENGINE_FILENAME
        )
        if not engine_path.is_file():
            raise ContractError(
                "the revision under test carries no engine at %s/%s; there is "
                "nothing to play" % (ENGINE_DIRECTORY, ENGINE_FILENAME)
            )
        engine = load_engine(engine_path)
        seats = int(engine.PLAYERS[0])

        needs = []
        seat_summary = None
        seat_games: Sequence[Mapping[str, Any]] = ()
        try:
            seat_summary, seat_games = self._play_model_seats(context, engine, seats)
        except model_seats.ModelSeatsUnavailable as unavailable:
            needs.append(
                Need(
                    "playtest",
                    "agent-playtest",
                    "Every seat's decision has to be made by an independent "
                    "model, and %s." % unavailable,
                    "Configure %s, or run against a live model-seat endpoint. "
                    "A scripted policy has no role and no report, so it can "
                    "never stand in for a seat here."
                    % ", ".join(config.MODEL_SEAT_ENV_NAMES),
                )
            )

        outcome = simulation.run_simulation(
            engine,
            artifact_sha256=context.made.artifact_sha256,
            seats=seats,
            # The model-seat games are `game-simulation`'s `social` style. The
            # two results keep their own evidence files; this is a reference.
            social_sample=(
                model_seats.social_sample(seat_summary)
                if seat_summary is not None
                else None
            ),
            **self.simulation_settings,
        )

        measured = self._measure_manufacturing(context)
        for name, evidence in measured.items():
            if not evidence["passed"]:
                # An unrun check is not a pass, so a result carrying one waits
                # rather than passing on the strength of what did run.
                needs.append(
                    Need(
                        "playtest",
                        name,
                        "%s did not pass: %s."
                        % (
                            name,
                            "; ".join(
                                filter(
                                    None,
                                    (
                                        "failed %s" % ", ".join(evidence["failed"])
                                        if evidence["failed"]
                                        else "",
                                        "unmeasured %s"
                                        % ", ".join(evidence["unmeasured"])
                                        if evidence["unmeasured"]
                                        else "",
                                    ),
                                )
                            ),
                        ),
                        "Install the locked CAD skill's mesh toolchain and pin a "
                        "printer, material and slicing profile, then measure "
                        "again. An unmeasured check never counts as a pass.",
                    )
                )

        if not outcome.meets_floor:
            # The floor is not negotiable and the short return is the honest
            # outcome, so this is a `Need` rather than a failing result over a
            # sample that was never big enough to mean anything.
            needs.append(simulation_need(outcome))
        if needs:
            raise WaitingFor(*needs)

        # Reached only once every adapter above is connected and the floor is
        # met. Kept whole rather than stubbed so the assembly it will use is
        # the assembly that is reviewed.
        return self._assemble(context, outcome, seat_summary, seat_games, measured)

    def _measure_manufacturing(self, context: PlaytestContext) -> Dict[str, Any]:
        """Deterministic measurement over the exact geometry in the revision."""

        brief = self.brief or _brief_from(context)
        measured: Dict[str, Any] = {}
        for name, required in MANUFACTURING:
            if name == "mechanical-test":
                taken = manufacturing.measure_mechanical(context.made, brief)
            else:
                taken = manufacturing.measure_print(context.made, brief)
            evidence = manufacturing.assemble(
                name, taken, made=context.made, required=required
            )
            manufacturing.assert_no_image_evidence(evidence)
            measured[name] = evidence
        return measured

    def _play_model_seats(self, context: PlaytestContext, engine, seats: int):
        """Model seats play this revision, or the run says why they did not."""

        transport = self.seat_transport
        if transport is None:
            transport = model_seats.HttpModelSeats.from_env()
        # A recording is evidence about the run it came from. Refusing it here
        # is what stops a replayed transcript becoming a claim about these bytes.
        model_seats.assert_can_be_evidence(transport)
        rules_path = context.made.artifact_root / ENGINE_DIRECTORY / RULES_FILENAME
        if not rules_path.is_file():
            raise ContractError(
                "the revision under test carries no rules at %s/%s; a seat "
                "cannot be briefed on a game the product does not contain"
                % (ENGINE_DIRECTORY, RULES_FILENAME)
            )
        record = GameRecord.from_dict(
            json.loads(rules_path.read_text(encoding="utf-8"))
        )
        games = [
            model_seats.play_model_seat_game(
                engine,
                record,
                transport,
                seats=seats,
                game_index=index,
                seed=90_000 + index,
                turn_cap=int(getattr(engine, "MAX_TURNS", 200)),
            )
            for index in range(self.model_seat_games)
        ]
        for game in games:
            model_seats.assert_no_cross_seat_leak(game)
        summary = model_seats.summarize(games)
        model_seats.assert_roles_are_distinct(summary)
        return summary, games

    def _assemble(
        self,
        context: PlaytestContext,
        outcome: simulation.SimulationOutcome,
        seat_summary: Optional[Mapping[str, Any]],
        seat_games: Sequence[Mapping[str, Any]],
        measured: Optional[Mapping[str, Any]] = None,
    ) -> Playtested:
        evidence_root = Path(
            self.evidence_root or (context.workspace / EVIDENCE_DIRECTORY)
        )
        config_sha256 = simulation.config_digest(**self.simulation_settings)
        results = []

        relative, digest = _seal(evidence_root, "game-simulation", outcome.evidence)
        results.append(
            PlaytestResult.create(
                "game-simulation",
                outcome.passed,
                context.made.artifact_sha256,
                outcome.evidence,
                simulation.EVALUATOR,
                simulation.EVALUATOR_VERSION,
                config_sha256,
                relative,
                digest,
            )
        )

        if seat_summary is not None:
            # A separate result with a separate evidence file, because it
            # answers a different question: the distinct roles and what they
            # reported, rather than the sample size and the properties.
            evidence = dict(seat_summary)
            evidence["artifact_sha256"] = context.made.artifact_sha256
            evidence["games_detail"] = list(seat_games)
            relative, digest = _seal(evidence_root, "agent-playtest", evidence)
            results.append(
                PlaytestResult.create(
                    "agent-playtest",
                    bool(evidence.get("completed_games")),
                    context.made.artifact_sha256,
                    evidence,
                    model_seats.EVALUATOR,
                    model_seats.EVALUATOR_VERSION,
                    config_sha256,
                    relative,
                    digest,
                )
            )

        for name, evidence in dict(measured or {}).items():
            relative, digest = _seal(evidence_root, name, evidence)
            results.append(
                PlaytestResult.create(
                    name,
                    bool(evidence["passed"]),
                    context.made.artifact_sha256,
                    evidence,
                    manufacturing.EVALUATOR,
                    manufacturing.EVALUATOR_VERSION,
                    config_sha256,
                    relative,
                    digest,
                )
            )

        manifest = build_artifact_manifest(
            evidence_root.resolve(strict=True), created_at="content-addressed"
        )
        # Every finding that prevented a pass leaves as feedback the next round
        # can act on, at the severity design decision D6 gives it.
        findings = abo_feedback.collect(
            simulation_evidence=outcome.evidence,
            seat_evidence=seat_summary,
            manufacturing_evidence=measured,
        )
        return Playtested(
            Playtest(context.made.artifact_manifest, tuple(results), None, manifest),
            findings,
        )


def abo_playtest(context: PlaytestContext) -> Playtested:
    """The seam the profile wires in."""

    return AboPlaytest()(context)


def _brief_from(context: PlaytestContext):
    """The brief's facts, recovered from the revision Make wrote them into."""

    from inventor_workshop.jobs import ConceptBrief, ConceptComponent

    from make import BRIEF_FILENAME

    path = context.made.artifact_root / BRIEF_FILENAME
    if not path.is_file():
        raise ContractError(
            "geometry is measured against the brief's millimetres and this "
            "revision carries no brief.json; supply the brief to ABO's Playtest "
            "or have Make write it into the product"
        )
    value = json.loads(path.read_text(encoding="utf-8"))
    return ConceptBrief(
        value["object"],
        value["category"],
        value["envelope_mm"],
        value["wall_mm"],
        value["features"],
        value["print"],
        tuple(ConceptComponent(**item) for item in value["components"]),
        value.get("fits"),
        tuple(value.get("assumptions", ())),
    )


__all__ = [
    "AboPlaytest",
    "EVIDENCE_DIRECTORY",
    "MANUFACTURING",
    "abo_playtest",
    "simulation_need",
]

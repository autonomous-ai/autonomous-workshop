"""ABO's Make: compile the sealed rules, and build the pieces to the numbers.

Two things go into one immutable product tree. The first is an executable model
of the rules — the file Playtest will run thousands of times, written inside the
product so the evidence binds to the same bytes a customer would receive. The
second is STEP-first parametric CAD for every component the brief names, built
through this repository's locked CAD skill.

The engine is a *translation* of the sealed rules and nothing more. Where the
rules do not say what happens, Make either refuses and names the rule that is
silent, or records the reading it took as a declared assumption naming the rule,
the question, the reading chosen and the alternative — which Playtest then
exercises both ways. It never invents a rule to make an unplayable game run,
and it never repairs a game the rules describe badly: a rules gap comes back as
a finding against the rules, because the fix belongs in the design.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Tuple

from inventor_workshop.errors import ContractError
from inventor_workshop.jobs import (
    ConceptBrief,
    Made,
    MakeContext,
    Need,
    WaitingFor,
)

import config
from cad_compat import assert_cad_source_supported
from game import GameRecord, RULE_PHASES, WIN_PHASE

ENGINE_FILENAME = "engine.py"
ENGINE_DIRECTORY = "rules"
RULES_FILENAME = "idea.json"
CAD_DIRECTORY = "cad"
PRODUCT_DESCRIPTOR = "product.json"
BRIEF_FILENAME = "brief.json"

# The contract the imported simulation harness drives an engine through. ABO
# uses this one rather than `gameplay.py`'s because it is what its rules
# engineer writes against and what `harness/playtest.py` calls; see the design's
# first non-goal.
REQUIRED_CALLS: Tuple[str, ...] = (
    "new_game",
    "player_to_move",
    "legal_moves",
    "apply_move",
    "is_over",
    "scores",
    "winners",
)
REQUIRED_META: Tuple[str, ...] = ("PLAYERS", "MAX_TURNS", "HIDDEN_INFO")
HIDDEN_INFORMATION_CALLS: Tuple[str, ...] = ("observation", "determinize")
ASSUMPTION_FIELDS: Tuple[str, ...] = ("id", "rule", "question", "chosen", "alternative")


class RulesGap(RuntimeError):
    """The rules do not say what happens, and no reading was declared.

    Carried as an exception rather than returned so it cannot be mistaken for a
    build problem: this is a finding against the rules, and the next round
    answers it in the design.
    """

    def __init__(self, rule: str, question: str) -> None:
        self.rule = rule
        self.question = question
        super().__init__("rules:%s is silent: %s" % (rule, question))


@dataclass(frozen=True)
class CompiledEngine:
    """The engine source, and what the compiler says it had to decide."""

    source: str
    assumptions: Sequence[Mapping[str, str]] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.source, str) or not self.source.strip():
            raise ContractError("a compiled engine must be Python source")
        declared = tuple(dict(item) for item in self.assumptions)
        for item in declared:
            missing = [name for name in ASSUMPTION_FIELDS if not item.get(name)]
            if missing:
                raise ContractError(
                    "a declared assumption must name %s; %r is missing %s"
                    % (", ".join(ASSUMPTION_FIELDS), item.get("id", "?"), missing)
                )
        object.__setattr__(self, "assumptions", declared)


# Sealed rules in, one engine out. Raises `RulesGap` rather than guessing.
EngineCompiler = Callable[[GameRecord], CompiledEngine]

# One component's parametric CAD source, built to the brief's millimetres.
CadBuilder = Callable[["ComponentBuild"], str]


@dataclass(frozen=True)
class ComponentBuild:
    """What a CAD builder is told about one part, and nothing else.

    The brief facts are handed over explicitly so the geometry stays traceable
    to them: `traceability` is written beside the source and says which stated
    number decided which dimension.
    """

    key: str
    brief: ConceptBrief
    record: GameRecord

    @property
    def component(self):
        return self.brief.component(self.key)

    @property
    def traceability(self) -> Dict[str, Any]:
        component = self.component
        facts: Dict[str, Any] = {
            "component": self.key,
            "dimensions_mm": list(component.dimensions_mm),
            "wall_mm": self.brief.wall_mm,
            "envelope_mm": list(self.brief.envelope_mm),
            "print_orientation": self.brief.print["orientation"],
            "print_supports": self.brief.print["supports"],
            "interfaces": component.interfaces,
        }
        if self.brief.fits is not None:
            facts["fits"] = dict(self.brief.fits)
        return facts


def load_engine(path: Path):
    """Import an engine file the way the simulation harness imports it."""

    spec = importlib.util.spec_from_file_location(
        "abo_engine_%s" % Path(path).stem, path
    )
    if spec is None or spec.loader is None:
        raise ContractError("cannot import the engine at %s" % path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # noqa: BLE001 - any import failure is one problem
        raise ContractError("the engine failed to import: %s" % exc) from exc
    return module


def engine_contract(engine) -> Dict[str, Any]:
    """What the engine declares about itself, refusing an incomplete claim."""

    findings = []
    for name in REQUIRED_CALLS:
        if not callable(getattr(engine, name, None)):
            findings.append("contract: engine has no callable `%s`" % name)
    for name in REQUIRED_META:
        if getattr(engine, name, None) is None:
            findings.append("contract: engine has no `%s`" % name)
    if findings:
        raise ContractError(
            "the compiled engine is not a usable model of the rules:\n  - %s"
            % "\n  - ".join(findings)
        )

    players = getattr(engine, "PLAYERS")
    try:
        seats = (int(players[0]), int(players[1]))
    except (TypeError, ValueError, IndexError) as exc:
        raise ContractError("engine PLAYERS must be a (min, max) seat range") from exc
    if seats[0] < 1 or seats[1] < seats[0]:
        raise ContractError("engine PLAYERS %r is not a seat range" % (players,))

    hidden = bool(getattr(engine, "HIDDEN_INFO"))
    if hidden:
        # Hidden information is enforced by the engine or it is not enforced.
        # A game that declares it and cannot show one seat's view has not hidden
        # anything; it has only said that it meant to.
        missing = [
            name
            for name in HIDDEN_INFORMATION_CALLS
            if not callable(getattr(engine, name, None))
        ]
        if missing:
            raise ContractError(
                "the engine declares hidden information but exposes no %s, so "
                "nothing stops a seat being shown the whole state"
                % " or ".join(missing)
            )
    return {
        "seats_supported": list(seats),
        "max_turns": int(getattr(engine, "MAX_TURNS")),
        "hidden_information": hidden,
        "move_kinds": sorted(str(kind) for kind in getattr(engine, "MOVE_KINDS", ()) or ()),
        "admin_kinds": sorted(str(kind) for kind in getattr(engine, "ADMIN_KINDS", ()) or ()),
        "assumptions": [
            dict(item) for item in (getattr(engine, "ASSUMPTIONS", ()) or ())
        ],
    }


def assert_engine_plays(engine, seats: int, turn_cap: int) -> Dict[str, Any]:
    """Drive a fresh game to a terminal state using only enumerated moves.

    A game that cannot be started, or that cannot end, is returned as a finding
    against the rules rather than absorbed into the engine.
    """

    import random

    rng = random.Random(0)
    try:
        state = engine.new_game(seats, rng)
    except Exception as exc:  # noqa: BLE001
        raise ContractError(
            "the sealed rules describe a game that cannot be started: %s" % exc
        ) from exc
    turns = 0
    while turns < turn_cap:
        if engine.is_over(state):
            return {"started": True, "terminated": True, "turns": turns}
        moves = engine.legal_moves(state)
        if not moves:
            raise ContractError(
                "the sealed rules reach a position with no legal move and no "
                "ending after %d turns; the game cannot be played to a "
                "conclusion" % turns
            )
        state = engine.apply_move(state, moves[rng.randrange(len(moves))], rng)
        turns += 1
    raise ContractError(
        "the sealed rules describe a game that did not terminate within %d "
        "turns; that is a finding against the rules, not a cap to raise"
        % turn_cap
    )


def assert_hidden_information_holds(engine, seats: int) -> None:
    """A seat sees its own view, and resampling leaves that view alone."""

    import random

    if not bool(getattr(engine, "HIDDEN_INFO")):
        return
    rng = random.Random(1)
    state = engine.new_game(seats, rng)
    for seat in range(seats):
        view = engine.observation(state, seat)
        resampled = engine.determinize(state, seat, rng)
        if engine.observation(resampled, seat) != view:
            raise ContractError(
                "resampling the hidden state for seat %d changed what that seat "
                "may see; a resampler that alters a seat's own view is not "
                "hiding information, it is inventing it" % seat
            )


class AboMake:
    """`MakeContext -> Made` for ABO."""

    def __init__(
        self,
        engine_compiler: Optional[EngineCompiler] = None,
        cad_builder: Optional[CadBuilder] = None,
        step_generator: Optional[Callable[[Path, Sequence[str]], None]] = None,
    ) -> None:
        self.engine_compiler = engine_compiler
        self.cad_builder = cad_builder
        # The generator is the locked skill. It is a seam only so an offline
        # check can prove the contracts *around* geometry — component
        # correspondence, the engine inside the product, the revision hash —
        # on a machine with no CAD toolchain. A substituted generator never
        # makes a claim about geometry; the manufacturing results measure that,
        # and they refuse an unmeasured check rather than passing it.
        self.step_generator = step_generator

    # -- the job --------------------------------------------------------

    def __call__(self, context: MakeContext) -> Made:
        if not isinstance(context, MakeContext):
            raise ContractError("ABO's Make requires a MakeContext")
        needs = []
        if self.engine_compiler is None:
            needs.append(
                Need(
                    "make",
                    "rules-engine-compiler",
                    "Playtest runs the rules, so the sealed rules have to become "
                    "an executable engine, and no compiler is configured.",
                    "Configure ABO's rules-engine compiler (the "
                    "board-game-rules-engineer agent, or a fixture for an "
                    "offline check); never ship a game with no runnable model "
                    "of its own rules.",
                )
            )
        if self.cad_builder is None:
            needs.append(
                Need(
                    "make",
                    "step-first-cad-builder",
                    "Every component in the brief needs parametric CAD source "
                    "and validated STEP geometry, and no CAD builder is "
                    "configured.",
                    "Configure ABO's CAD builder over the repository's locked "
                    "skills/cad; never describe geometry that was not built.",
                )
            )
        if context.concept_images is None:
            needs.append(
                Need(
                    "make",
                    "concept-images",
                    "ABO builds to a sealed concept — the rules come from it and "
                    "the brief's millimetres govern the geometry — and this "
                    "round carries no concept.",
                    "Run Concept before Make; never build to a design that was "
                    "described but not decided.",
                )
            )
        if needs:
            raise WaitingFor(*needs)
        assert context.concept_images is not None

        concept = context.concept_images
        # The rules are sealed inside the concept root, under the same hash as
        # the pixels. Re-reading them here rather than carrying them in memory
        # is what makes a mid-round rules edit fail the seal re-check.
        concept.assert_current()
        record = GameRecord.from_root(concept.root)
        brief = concept.brief

        root = Path(context.workspace)
        if root.exists():
            if root.is_symlink() or not root.is_dir() or any(root.iterdir()):
                raise ContractError("Make workspace must be fresh and empty")
        else:
            root.mkdir(parents=True, mode=0o700)
        root = root.resolve(strict=True)

        contract = self._write_engine(root, record)
        components = self._build_cad(root, brief, record)

        product = {
            "title": record.title,
            "summary": record.central_idea,
            "lane": context.blueprint.lane,
            "slug": record.slug,
            "round": context.round,
            "components": [item.key for item in brief.components],
            "engine": "%s/%s" % (ENGINE_DIRECTORY, ENGINE_FILENAME),
            "rules": "%s/%s" % (ENGINE_DIRECTORY, RULES_FILENAME),
            "engine_contract": contract,
            "cad": components,
            "concept_sha256": concept.concept_sha256,
            "rules_sha256": _digest(record.to_dict()["rules"]),
        }
        # The brief travels with the build. Playtest measures geometry against
        # its millimetres, and a revision that does not carry the numbers it was
        # built to cannot be checked against them later.
        (root / BRIEF_FILENAME).write_text(
            json.dumps(brief.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (root / PRODUCT_DESCRIPTOR).write_text(
            json.dumps(product, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        made = Made.from_root(root, product)
        _assert_no_concept_pixels(concept, made)
        return made

    # -- the engine -----------------------------------------------------

    def _write_engine(self, root: Path, record: GameRecord) -> Dict[str, Any]:
        assert self.engine_compiler is not None
        try:
            compiled = self.engine_compiler(record)
        except RulesGap as gap:
            # Refuse, naming the exact rule that is silent. Make does not get to
            # decide what the rules meant.
            raise ContractError(
                "Make refused to compile an engine: rule %s is silent on %s. "
                "That is a finding against the rules — the next round answers "
                "it in the design, and Make never invents a rule to make an "
                "unplayable game run." % (gap.rule, gap.question)
            ) from gap
        if not isinstance(compiled, CompiledEngine):
            raise ContractError("ABO's engine compiler must return a CompiledEngine")

        directory = root / ENGINE_DIRECTORY
        directory.mkdir(mode=0o700, parents=True)
        path = directory / ENGINE_FILENAME
        path.write_text(compiled.source, encoding="utf-8")
        # The rules travel with the engine that translates them. Playtest needs
        # them to brief a model seat, and a customer holding the product should
        # not have to go back to a sealed concept to read the game.
        (directory / RULES_FILENAME).write_text(record.to_json(), encoding="utf-8")

        engine = load_engine(path)
        contract = engine_contract(engine)

        # Every reading the compiler had to take must be declared in the engine
        # itself, where Playtest can find it and play both ways.
        declared = {str(item.get("id")) for item in contract["assumptions"]}
        promised = {str(item.get("id")) for item in compiled.assumptions}
        if promised - declared:
            raise ContractError(
                "the compiler declared assumptions the engine does not carry "
                "(%s); a reading Playtest cannot find is a reading nothing "
                "exercises" % ", ".join(sorted(promised - declared))
            )
        for item in contract["assumptions"]:
            missing = [name for name in ASSUMPTION_FIELDS if not item.get(name)]
            if missing:
                raise ContractError(
                    "engine assumption %r is missing %s; a declared reading has "
                    "to name the rule, the question, the reading taken and the "
                    "alternative, or it is not a declaration"
                    % (item.get("id", "?"), missing)
                )
            if not _names_a_rule(str(item.get("rule")), record):
                raise ContractError(
                    "engine assumption %r is about %r, which is not a rule this "
                    "game has" % (item.get("id"), item.get("rule"))
                )

        if contract["assumptions"]:
            # A declaration Playtest cannot flip is a declaration nothing
            # exercises, which is the same as not declaring it at all.
            choices = getattr(engine, "CHOICES", None)
            if not isinstance(choices, dict):
                raise ContractError(
                    "the engine declares %d assumption(s) but carries no CHOICES "
                    "mapping, so neither reading can be played; a reading that "
                    "cannot be exercised is not a declaration"
                    % len(contract["assumptions"])
                )
            unwired = [
                str(item.get("id"))
                for item in contract["assumptions"]
                if str(item.get("id")) not in choices
            ]
            if unwired:
                raise ContractError(
                    "the engine declares assumption(s) %s that its CHOICES "
                    "mapping does not carry" % ", ".join(sorted(unwired))
                )
            contract["choices"] = dict(choices)

        seats = max(record.players_min, contract["seats_supported"][0])
        contract["play_through"] = assert_engine_plays(
            engine, seats, contract["max_turns"]
        )
        assert_hidden_information_holds(engine, seats)
        if record.players_max > contract["seats_supported"][1]:
            raise ContractError(
                "the rules support up to %d seats and the engine only %d"
                % (record.players_max, contract["seats_supported"][1])
            )
        return contract

    # -- the geometry ---------------------------------------------------

    def _build_cad(
        self, root: Path, brief: ConceptBrief, record: GameRecord
    ) -> Dict[str, Any]:
        assert self.cad_builder is not None
        scripts = config.cad_scripts_root()
        # `gen` is a directory package the skill runs as `python3 <dir>`, the
        # same way the imported gate invokes it.
        if not (scripts / "gen" / "__main__.py").is_file():
            raise WaitingFor(
                Need(
                    "make",
                    "locked-cad-skill",
                    "STEP geometry is built through this repository's locked CAD "
                    "skill, and its scripts are not present.",
                    "Restore skills/cad; ABO never vendors a second copy and "
                    "never substitutes a described part for a built one.",
                )
            )

        directory = root / CAD_DIRECTORY
        directory.mkdir(mode=0o700, parents=True)
        built: Dict[str, Any] = {}
        for component in brief.components:
            build = ComponentBuild(component.key, brief, record)
            source = self.cad_builder(build)
            if not isinstance(source, str) or not source.strip():
                raise ContractError(
                    "ABO's CAD builder must return parametric source for %s"
                    % component.key
                )
            assert_cad_source_supported(source, "%s CAD source" % component.key)
            source_path = directory / ("%s.step.py" % component.key)
            source_path.write_text(source, encoding="utf-8")
            (directory / ("%s.facts.json" % component.key)).write_text(
                json.dumps(build.traceability, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            built[component.key] = {
                "source": "%s/%s" % (CAD_DIRECTORY, source_path.name),
                "facts": "%s/%s.facts.json" % (CAD_DIRECTORY, component.key),
            }

        generate = self.step_generator or self._generate_step_through_locked_skill
        generate(directory, tuple(built))
        generated = self._collect_step(directory, tuple(built))
        for key, outcome in generated.items():
            built[key].update(outcome)

        # STEP is the primary artifact and a mesh is derived from it. A mesh
        # with no STEP behind it would be geometry nobody validated.
        for key, entry in built.items():
            if entry.get("mesh") and not entry.get("step"):
                raise ContractError(
                    "component %s has a mesh with no STEP artifact behind it" % key
                )
        return built

    def _generate_step_through_locked_skill(
        self, directory: Path, keys: Sequence[str]
    ) -> None:
        """Run the locked skill's generator over the sources just written.

        Runs with the CAD project as its working directory, so the catalog scan
        stays inside the product tree. See `cad_compat.py`.
        """

        scripts = config.cad_scripts_root()
        argv = [
            str(config.interpreter()),
            str(scripts / "gen"),
            *["%s.step.py" % key for key in keys],
            "--write",
            "--json",
        ]
        completed = subprocess.run(
            argv,
            cwd=str(directory),
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise WaitingFor(
                Need(
                    "make",
                    "cad-toolchain",
                    "The locked CAD skill could not generate STEP geometry: %s"
                    % (completed.stderr.strip()[-500:] or "no output"),
                    "Install the locked skill's requirements (cadgen and its "
                    "dependencies, plus scipy) and run again; never record a "
                    "component as built when its geometry did not generate.",
                )
            )

    def _collect_step(self, directory: Path, keys: Sequence[str]) -> Dict[str, Any]:
        """Record what the generator actually wrote, refusing what it did not."""

        outcome: Dict[str, Any] = {}
        for key in keys:
            step = directory / ("%s.step" % key)
            entry: Dict[str, Any] = {}
            if step.is_file():
                entry["step"] = "%s/%s" % (CAD_DIRECTORY, step.name)
            else:
                raise ContractError(
                    "the locked CAD skill wrote no STEP artifact for %s" % key
                )
            mesh = directory / ("%s.stl" % key)
            if mesh.is_file():
                entry["mesh"] = "%s/%s" % (CAD_DIRECTORY, mesh.name)
            outcome[key] = entry
        return outcome


# ---------------------------------------------------------------------------


def _digest(value: Any) -> str:
    import hashlib

    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _names_a_rule(rule: str, record: GameRecord) -> bool:
    if rule in RULE_PHASES or rule == WIN_PHASE:
        return True
    return any(
        rule == "%s[%d]" % (phase, index) for phase, index, _step in record.steps
    )


def _assert_no_concept_pixels(concept, made: Made) -> None:
    """A concept says what to build; it can never stand in as a picture of it."""

    reused = concept.image_digests() & {
        entry.sha256 for entry in made.artifact_manifest.entries
    }
    if reused:
        raise ContractError(
            "Make returned a product carrying concept image bytes; a concept is "
            "an instruction, never evidence of what was made"
        )


__all__ = [
    "ASSUMPTION_FIELDS",
    "AboMake",
    "BRIEF_FILENAME",
    "CAD_DIRECTORY",
    "CadBuilder",
    "CompiledEngine",
    "ComponentBuild",
    "ENGINE_DIRECTORY",
    "ENGINE_FILENAME",
    "EngineCompiler",
    "HIDDEN_INFORMATION_CALLS",
    "PRODUCT_DESCRIPTOR",
    "REQUIRED_CALLS",
    "REQUIRED_META",
    "RULES_FILENAME",
    "RulesGap",
    "assert_engine_plays",
    "assert_hidden_information_holds",
    "engine_contract",
    "load_engine",
]

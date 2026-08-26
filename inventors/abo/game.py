"""ABO's game record: the invented game, and the check that it is one game.

For an abstract game the pieces are the rules. A brief that locks a component
breakdown before the rules exist locks a bill nothing decided, so ABO invents
the whole game at Concept and this module is what it invents *into*: a closed
record carrying the title, the central idea, the seats, the playtime, the
complete rules with a per-step declaration of the components each step touches,
the component bill with quantities, and art direction written in form language.

The record serializes to exactly the `idea.json` shape the imported
`harness/rules_check.py` was written against, so the deterministic
rules-versus-bill check runs over it unmodified. Nothing in that check involves
model judgement: it answers one question — do the rules and the box of pieces
describe the same game? — and ABO adds two more that the Wish and the printer
decide, not opinion: is the Wish structural rather than decorative, and can
every distinction a player must make be made by shape alone.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple


GAME_RECORD_DIRECTORY = "game"
GAME_RECORD_FILENAME = "idea.json"
GAME_CHECK_FILENAME = "rules_check.json"

RULE_PHASES: Tuple[str, ...] = ("setup", "turn", "end")
WIN_PHASE = "win"

# ABO's Taste caps distinct piece types low, and Workshop's ConceptBrief caps
# components at twelve. The lower of the two is the one that bites.
MAX_PIECE_TYPES = 6

_NAME = re.compile(r"^[a-z][a-z0-9_]{1,62}$")
_SLUG = re.compile(r"^[a-z][a-z0-9-]{1,62}$")

# No colour and no material is assigned anywhere in this pipeline: every part
# is printed, and the customer chooses the filament. A rule, a component, or an
# art-direction line that leans on one of these words is asking a player to
# make a distinction the object cannot carry.
COLOUR_WORDS = frozenset(
    """
    amber azure beige black blue bronze brown crimson cyan gold golden green
    grey gray hue indigo ivory lilac magenta maroon mauve olive orange pink
    purple red scarlet silver tan teal turquoise violet white yellow
    colour color colours colors coloured colored colouring coloring
    bicolour bicolor two-tone tone-on-tone shade shaded tint tinted
    """.split()
)
MATERIAL_WORDS = frozenset(
    """
    wood wooden oak walnut birch bamboo brass copper steel aluminium aluminum
    metal metallic plastic acrylic resin glass ceramic stone marble leather
    felt cardboard paper linen cloth fabric
    """.split()
)
# Shape is what a printed piece can actually carry, and what ABO's Taste asks
# art direction to be written in.
FORM_WORDS = frozenset(
    """
    silhouette footprint height relief chamfer fillet notch notches notched
    pierced hole holes bore groove ridge rib flange taper bevel profile
    outline edge corner facet step tier column prism wedge dome concave convex
    thickness depth width diameter radius curvature
    """.split()
)


class GameRecordError(ValueError):
    """The record is not a description of one complete, playable game."""


def _text(value: Any, label: str, maximum: int = 4_000) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > maximum
        or any(ord(character) < 32 and character not in "\n\t" for character in value)
    ):
        raise GameRecordError("%s must be bounded, non-empty text" % label)
    return value.strip()


def _positive_int(value: Any, label: str, maximum: int = 100_000) -> int:
    if type(value) is not int or not 1 <= value <= maximum:
        raise GameRecordError("%s must be a positive whole number" % label)
    return value


def _dimensions_mm(value: Any, label: str) -> Tuple[float, float, float]:
    if isinstance(value, (str, bytes, Mapping)) or not isinstance(value, Sequence):
        raise GameRecordError("%s must be three millimetre dimensions" % label)
    numbers = tuple(value)
    if len(numbers) != 3:
        raise GameRecordError("%s must be three millimetre dimensions" % label)
    out = []
    for index, number in enumerate(numbers):
        if type(number) not in (int, float) or not 0 < float(number) <= 100_000:
            raise GameRecordError(
                "%s dimension %d must be a positive millimetre measurement"
                % (label, index + 1)
            )
        out.append(float(number))
    return (out[0], out[1], out[2])


def words_of(text: str) -> Tuple[str, ...]:
    cleaned = "".join(
        character.casefold() if (character.isalnum() or character == "-") else " "
        for character in text
    )
    return tuple(word for word in cleaned.split() if word)


def concept_key_for(bill_name: str) -> str:
    """The ConceptBrief key for one bill line.

    Bill names are the vocabulary the rules' `uses` lists speak, so they stay
    exactly as the record wrote them. Concept keys are a different alphabet —
    lowercase and hyphenated so a filename can carry one — and this is the only
    place the two are translated.
    """

    return bill_name.replace("_", "-").strip("-")


@dataclass(frozen=True)
class GameComponent:
    """One line of the component bill: a part type, and how many of it."""

    name: str
    qty: int
    desc: str
    form: str
    dimensions_mm: Sequence[float]
    placement: str
    interfaces: str
    per_player: Optional[int] = None

    def __post_init__(self) -> None:
        name = _text(self.name, "component name", 64)
        if not _NAME.fullmatch(name):
            raise GameRecordError(
                "component name %r must be lowercase words joined by underscores, "
                "because the rules' `uses` lists name components by exactly this "
                "string" % name
            )
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "qty", _positive_int(self.qty, "component %s qty" % name))
        object.__setattr__(self, "desc", _text(self.desc, "component %s desc" % name))
        object.__setattr__(self, "form", _text(self.form, "component %s form" % name))
        object.__setattr__(
            self, "placement", _text(self.placement, "component %s placement" % name)
        )
        object.__setattr__(
            self, "interfaces", _text(self.interfaces, "component %s interfaces" % name)
        )
        object.__setattr__(
            self,
            "dimensions_mm",
            _dimensions_mm(self.dimensions_mm, "component %s dimensions_mm" % name),
        )
        if self.per_player is not None:
            object.__setattr__(
                self,
                "per_player",
                _positive_int(self.per_player, "component %s per_player" % name),
            )

    @property
    def concept_key(self) -> str:
        return concept_key_for(self.name)

    def to_dict(self) -> Dict[str, Any]:
        """The upstream `idea.json` bill line, plus what a brief needs.

        `name`, `qty`, `desc` and `per_player` are the fields the imported
        check reads. The rest is ABO's own and is ignored by it.
        """

        value: Dict[str, Any] = {
            "name": self.name,
            "qty": self.qty,
            "desc": self.desc,
            "form": self.form,
            "dimensions_mm": list(self.dimensions_mm),
            "placement": self.placement,
            "interfaces": self.interfaces,
        }
        if self.per_player is not None:
            value["per_player"] = self.per_player
        return value


@dataclass(frozen=True)
class RuleStep:
    """One step of the rules, and the components it reaches for."""

    text: str
    uses: Sequence[str] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "text", _text(self.text, "rule step text"))
        if isinstance(self.uses, (str, bytes, Mapping)) or not isinstance(
            self.uses, Sequence
        ):
            raise GameRecordError(
                "a rule step's `uses` must be a list of component bill names, "
                "even when it is empty"
            )
        uses = tuple(_text(item, "rule step use", 64) for item in self.uses)
        if len(set(uses)) != len(uses):
            raise GameRecordError("a rule step must not name the same component twice")
        object.__setattr__(self, "uses", uses)

    def to_dict(self) -> Dict[str, Any]:
        return {"text": self.text, "uses": list(self.uses)}


@dataclass(frozen=True)
class WishHook:
    """One stated element of the Wish, and the structure it became.

    This is what makes the Wish-is-structural rule checkable rather than
    asserted. A hook that points at the title is a label; a hook that points at
    a rule step or a component is mechanism.
    """

    wish_element: str
    becomes: str
    target: str

    BECOMES = ("rule", "component", "board", "title")

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "wish_element", _text(self.wish_element, "wish hook element", 500)
        )
        if self.becomes not in WishHook.BECOMES:
            raise GameRecordError(
                "a wish hook must become one of %s" % ", ".join(WishHook.BECOMES)
            )
        object.__setattr__(self, "target", _text(self.target, "wish hook target", 500))

    @property
    def is_structural(self) -> bool:
        return self.becomes in ("rule", "component", "board")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "wish_element": self.wish_element,
            "becomes": self.becomes,
            "target": self.target,
        }


@dataclass(frozen=True)
class DesignContract:
    """What this design is for, and the ceiling it agrees to stay under.

    The complexity budget is the record's own declaration, which is what makes
    exceeding it a design defect rather than a matter of taste: the design said
    where its own ceiling was and then went through it.
    """

    core_experience: str
    core_mechanism: str
    must_preserve: Sequence[str]
    anti_goals: Sequence[str]
    kill_criteria: Sequence[str]
    max_rule_words: int
    max_action_types: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "core_experience", _text(self.core_experience, "core_experience")
        )
        object.__setattr__(
            self, "core_mechanism", _text(self.core_mechanism, "core_mechanism")
        )
        for name in ("must_preserve", "anti_goals", "kill_criteria"):
            value = getattr(self, name)
            if isinstance(value, (str, bytes, Mapping)) or not isinstance(
                value, Sequence
            ):
                raise GameRecordError("design contract %s must be a list" % name)
            entries = tuple(_text(item, "design contract %s entry" % name) for item in value)
            if not entries:
                raise GameRecordError(
                    "design contract %s must say something; an empty list is not a "
                    "contract" % name
                )
            object.__setattr__(self, name, entries)
        object.__setattr__(
            self, "max_rule_words", _positive_int(self.max_rule_words, "max_rule_words")
        )
        object.__setattr__(
            self,
            "max_action_types",
            _positive_int(self.max_action_types, "max_action_types"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "core_experience": self.core_experience,
            "core_mechanism": self.core_mechanism,
            "must_preserve": list(self.must_preserve),
            "anti_goals": list(self.anti_goals),
            "kill_criteria": list(self.kill_criteria),
            "complexity_budget": {
                "max_rule_words": self.max_rule_words,
                "max_action_types": self.max_action_types,
            },
        }


@dataclass(frozen=True)
class GameRecord:
    """One complete invented game, at the granularity Make will build."""

    slug: str
    title: str
    central_idea: str
    players_min: int
    players_max: int
    playtime_min: int
    setup: Sequence[RuleStep]
    turn: Sequence[RuleStep]
    end: Sequence[RuleStep]
    win: RuleStep
    components: Sequence[GameComponent]
    art_direction: Sequence[str]
    action_types: Sequence[str]
    design_contract: DesignContract
    wish_hooks: Sequence[WishHook] = field(default_factory=tuple)

    schema_version = 2

    def __post_init__(self) -> None:
        slug = _text(self.slug, "game slug", 64)
        if not _SLUG.fullmatch(slug):
            raise GameRecordError(
                "game slug %r must be lowercase words joined by hyphens" % slug
            )
        object.__setattr__(self, "slug", slug)
        object.__setattr__(self, "title", _text(self.title, "game title", 200))
        object.__setattr__(
            self, "central_idea", _text(self.central_idea, "game central idea")
        )
        object.__setattr__(
            self, "players_min", _positive_int(self.players_min, "players min", 12)
        )
        object.__setattr__(
            self, "players_max", _positive_int(self.players_max, "players max", 12)
        )
        if self.players_max < self.players_min:
            raise GameRecordError("game seat range must not run backwards")
        object.__setattr__(
            self, "playtime_min", _positive_int(self.playtime_min, "playtime_min", 1_000)
        )
        for phase in RULE_PHASES:
            steps = tuple(getattr(self, phase))
            if not steps or not all(isinstance(item, RuleStep) for item in steps):
                raise GameRecordError(
                    "the %s phase needs at least one RuleStep; a game with no %s "
                    "phase cannot be played to a conclusion" % (phase, phase)
                )
            object.__setattr__(self, phase, steps)
        if not isinstance(self.win, RuleStep):
            raise GameRecordError("the win condition must be a RuleStep")
        components = tuple(self.components)
        if not components or not all(
            isinstance(item, GameComponent) for item in components
        ):
            raise GameRecordError("a physical game needs GameComponent bill lines")
        if len({item.name for item in components}) != len(components):
            raise GameRecordError("component bill names must be unique")
        if len({item.concept_key for item in components}) != len(components):
            raise GameRecordError(
                "two component names collapse to one concept key; every part type "
                "must stay separable by name as well as by shape"
            )
        object.__setattr__(self, "components", components)
        art = tuple(_text(item, "art direction line") for item in self.art_direction)
        if not art:
            raise GameRecordError(
                "art direction must say how the pieces read, in form language"
            )
        object.__setattr__(self, "art_direction", art)
        actions = tuple(_text(item, "action type", 200) for item in self.action_types)
        if not actions:
            raise GameRecordError("a game must name the action types its turn offers")
        if len(set(actions)) != len(actions):
            raise GameRecordError("action types must be distinct")
        object.__setattr__(self, "action_types", actions)
        if not isinstance(self.design_contract, DesignContract):
            raise GameRecordError("a game record requires a DesignContract")
        hooks = tuple(self.wish_hooks)
        if not all(isinstance(item, WishHook) for item in hooks):
            raise GameRecordError("wish hooks must be WishHook records")
        object.__setattr__(self, "wish_hooks", hooks)

    # -- reading ---------------------------------------------------------

    @property
    def steps(self) -> Tuple[Tuple[str, int, RuleStep], ...]:
        """Every rule step in the record, with the phase and index naming it."""

        found = []
        for phase in RULE_PHASES:
            for index, step in enumerate(getattr(self, phase), 1):
                found.append((phase, index, step))
        found.append((WIN_PHASE, 1, self.win))
        return tuple(found)

    @property
    def bill_names(self) -> Tuple[str, ...]:
        return tuple(item.name for item in self.components)

    def component(self, name: str) -> GameComponent:
        for item in self.components:
            if item.name == name:
                return item
        raise GameRecordError("the bill does not contain component %r" % name)

    @property
    def rules_text(self) -> str:
        return "\n".join(step.text for _phase, _index, step in self.steps)

    # -- writing ---------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """The record as `idea.json`.

        Field-for-field what `harness/rules_check.py` reads, so the imported
        check runs over ABO's record with nothing translated on the way in.
        """

        return {
            "schema_version": GameRecord.schema_version,
            "slug": self.slug,
            "title": self.title,
            "central_idea": self.central_idea,
            "players": {"min": self.players_min, "max": self.players_max},
            "playtime_min": self.playtime_min,
            "components": [item.to_dict() for item in self.components],
            "rules": {
                "setup": [item.to_dict() for item in self.setup],
                "turn": [item.to_dict() for item in self.turn],
                "end": [item.to_dict() for item in self.end],
                "win": self.win.to_dict(),
            },
            "art_direction": list(self.art_direction),
            "action_types": list(self.action_types),
            "design_contract": self.design_contract.to_dict(),
            "wish_hooks": [item.to_dict() for item in self.wish_hooks],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "GameRecord":
        """Read a record back, so sealed rules are recoverable verbatim."""

        if not isinstance(value, Mapping):
            raise GameRecordError("a game record must be a JSON object")
        try:
            rules = value["rules"]
            players = value["players"]
            contract = value["design_contract"]
            budget = contract["complexity_budget"]
            return cls(
                slug=value["slug"],
                title=value["title"],
                central_idea=value["central_idea"],
                players_min=players["min"],
                players_max=players["max"],
                playtime_min=value["playtime_min"],
                setup=tuple(
                    RuleStep(item["text"], item["uses"]) for item in rules["setup"]
                ),
                turn=tuple(
                    RuleStep(item["text"], item["uses"]) for item in rules["turn"]
                ),
                end=tuple(RuleStep(item["text"], item["uses"]) for item in rules["end"]),
                win=RuleStep(rules["win"]["text"], rules["win"]["uses"]),
                components=tuple(
                    GameComponent(
                        name=item["name"],
                        qty=item["qty"],
                        desc=item["desc"],
                        form=item["form"],
                        dimensions_mm=item["dimensions_mm"],
                        placement=item["placement"],
                        interfaces=item["interfaces"],
                        per_player=item.get("per_player"),
                    )
                    for item in value["components"]
                ),
                art_direction=tuple(value["art_direction"]),
                action_types=tuple(value["action_types"]),
                design_contract=DesignContract(
                    core_experience=contract["core_experience"],
                    core_mechanism=contract["core_mechanism"],
                    must_preserve=tuple(contract["must_preserve"]),
                    anti_goals=tuple(contract["anti_goals"]),
                    kill_criteria=tuple(contract["kill_criteria"]),
                    max_rule_words=budget["max_rule_words"],
                    max_action_types=budget["max_action_types"],
                ),
                wish_hooks=tuple(
                    WishHook(item["wish_element"], item["becomes"], item["target"])
                    for item in value.get("wish_hooks", ())
                ),
            )
        except (KeyError, TypeError) as exc:
            raise GameRecordError("game record is missing %s" % exc) from exc

    @classmethod
    def from_root(cls, concept_root: Path) -> "GameRecord":
        """Recover the exact rules a sealed concept was drawn from."""

        path = Path(concept_root) / GAME_RECORD_DIRECTORY / GAME_RECORD_FILENAME
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))


# ---------------------------------------------------------------------------
# The consistency check
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CheckResult:
    """What the deterministic check found, and what kind of answer it needs.

    `disposition` carries the upstream distinction ABO keeps: a design that
    went through its own declared ceiling must *subtract* (`rework`), while a
    rules gap or an omission must be *described better* (`clarify`). Design
    decision D6 maps the two onto Feedback severity.
    """

    passed: bool
    findings: Tuple[str, ...]
    disposition: Optional[str]
    problem_id: Optional[str]
    rules_sha256: str
    bill_sha256: str
    checker: str
    checker_version: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pass": self.passed,
            "findings": list(self.findings),
            "disposition": self.disposition,
            "problem_id": self.problem_id,
            # The recorded result names the exact rules and bill it was
            # computed over, so a later reader can tell whether it still
            # describes the game in front of them.
            "rules_sha256": self.rules_sha256,
            "bill_sha256": self.bill_sha256,
            "checker": self.checker,
            "checker_version": self.checker_version,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"

    @property
    def is_complexity_overrun(self) -> bool:
        return self.problem_id == "complexity-budget"


def _digest(value: Any) -> str:
    import hashlib

    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _imported_check(record_dict: Mapping[str, Any]) -> Tuple[list, Optional[str], Optional[str]]:
    """Run the imported rules-versus-bill check, unmodified.

    Imported lazily and by path so `harness/` stays a vendored tree rather than
    a package this repository maintains.
    """

    import importlib.util
    import sys

    from config import HARNESS_ROOT

    name = "abo_harness_rules_check"
    module = sys.modules.get(name)
    if module is None:
        spec = importlib.util.spec_from_file_location(
            name, HARNESS_ROOT / "rules_check.py"
        )
        if spec is None or spec.loader is None:
            raise GameRecordError("cannot load the imported rules check")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    findings = list(module.check(dict(record_dict)))
    disposition, problem_id = module.finding_disposition(findings)
    return findings, disposition, problem_id


def check_game(record: GameRecord) -> CheckResult:
    """Prove the rules and the box of pieces describe the same game.

    Mechanical throughout, and deliberately opinion-free: whether the game is
    any *good* is what Playtest measures and what the lenses judge. This says
    only whether it is one game.
    """

    if not isinstance(record, GameRecord):
        raise GameRecordError("the consistency check requires a GameRecord")
    value = record.to_dict()
    findings, disposition, problem_id = _imported_check(value)

    # ABO's own ceiling, above the record's self-declared one. Taste caps
    # distinct piece types low because component count is a learnability cost,
    # and a mechanically clean design does not excuse it.
    if len(record.components) > MAX_PIECE_TYPES:
        findings.append(
            "design_contract:complexity_budget: %d distinct piece types exceed "
            "the declared maximum %d"
            % (len(record.components), MAX_PIECE_TYPES)
        )
        disposition, problem_id = "rework", "complexity-budget"

    return CheckResult(
        passed=not findings,
        findings=tuple(findings),
        disposition=disposition,
        problem_id=problem_id,
        rules_sha256=_digest(value["rules"]),
        bill_sha256=_digest(value["components"]),
        checker="abo-rules-check",
        checker_version="1.0.0",
    )


# ---------------------------------------------------------------------------
# The two rules the Wish and the printer decide
# ---------------------------------------------------------------------------


def wish_is_structural(record: GameRecord, objective: str) -> Tuple[str, ...]:
    """Findings where the Wish decorates the game instead of shaping it.

    The test is the one the spec states: if the meaningful content of the Wish
    can be removed without changing the game's structure, rules, or pieces,
    the requested product was not made. A hook onto the title is exactly that
    removal — the name changes and the game does not.
    """

    findings = []
    hooks = tuple(record.wish_hooks)
    if not hooks:
        findings.append(
            "wish: the record traces nothing in the game back to the Wish; a "
            "game that would be the same game for any Wish did not answer this one"
        )
        return tuple(findings)

    structural = [hook for hook in hooks if hook.is_structural]
    if not structural:
        findings.append(
            "wish: every hook onto the Wish is a name or a label (%s); removing "
            "the Wish would leave the rules, the board, and the pieces untouched"
            % ", ".join(sorted({hook.becomes for hook in hooks}))
        )

    # A hook has to point at something that exists, or it is a claim rather
    # than a trace.
    names = set(record.bill_names)
    rule_targets = {
        "%s[%d]" % (phase, index) for phase, index, _step in record.steps
    }
    rule_targets.update({WIN_PHASE, *RULE_PHASES})
    for hook in structural:
        if hook.becomes == "component" and hook.target not in names:
            findings.append(
                "wish: hook %r claims to become component %r, which the bill "
                "does not contain" % (hook.wish_element, hook.target)
            )
        if hook.becomes == "rule" and hook.target not in rule_targets:
            findings.append(
                "wish: hook %r claims to become rule step %r, which the rules do "
                "not contain" % (hook.wish_element, hook.target)
            )

    # And the Wish's own words have to appear somewhere the game is decided,
    # not only where it is named. A record can satisfy the hook list on paper
    # and still be a stock game with a new title.
    stated = set(words_of(objective))
    titular = set(words_of(record.title)) | set(words_of(record.slug))
    mechanism = set(words_of(record.rules_text))
    for component in record.components:
        mechanism |= set(words_of(component.name))
        mechanism |= set(words_of(component.desc))
    mechanism |= set(words_of(record.design_contract.core_mechanism))
    meaningful = stated - _COMMON_WISH_WORDS
    if meaningful and not (meaningful & mechanism) and (meaningful & titular):
        findings.append(
            "wish: the Wish's own words reach the title and nothing else; the "
            "rules, the bill, and the core mechanism never mention what was asked for"
        )
    return tuple(findings)


# Words a Wish uses to be a Wish rather than to say what it wants.
_COMMON_WISH_WORDS = frozenset(
    """
    a an and are as at be by can could for from game games have i in is it its
    like make makes making me my of on or play played player players playing
    please should so that the their them they this to two up us want wants
    we what which who will wish wished wishes with would you your
    abstract strategy board tabletop quick hard easy simple fun new original
    """.split()
)


def colour_free(record: GameRecord) -> Tuple[str, ...]:
    """Findings where a distinction a player must make needs colour or material.

    No colour and no material is assigned anywhere in this pipeline. A rule
    that says "move a black piece" describes a game this Workshop cannot make,
    and the failure would not show up until somebody held the box.
    """

    findings = []

    def scan(text: str, where: str) -> None:
        found = sorted(set(words_of(text)) & (COLOUR_WORDS | MATERIAL_WORDS))
        if found:
            kind = "colour" if set(found) & COLOUR_WORDS else "material"
            findings.append(
                "%s: distinguishes by %s (%s); every distinction a player must "
                "make has to be carried by shape, because this pipeline assigns "
                "neither colour nor material" % (where, kind, ", ".join(found))
            )

    for phase, index, step in record.steps:
        scan(step.text, "rules:%s[%d]" % (phase, index))
    for component in record.components:
        scan(component.name, "bill:%s" % component.name)
        scan(component.desc, "bill:%s desc" % component.name)
        scan(component.form, "bill:%s form" % component.name)
    for index, line in enumerate(record.art_direction, 1):
        scan(line, "art_direction[%d]" % index)

    # Art direction must additionally be written *in* form language rather than
    # merely avoid colour, or "make it look nice" would pass.
    spoken = set(words_of(" ".join(record.art_direction)))
    if not spoken & FORM_WORDS:
        findings.append(
            "art_direction: says nothing in form language; a piece is told apart "
            "by silhouette, footprint, height, relief, notch count, or pierced "
            "feature, and art direction that names none of those has not "
            "directed anything"
        )
    return tuple(findings)


def assert_playable_record(record: GameRecord, objective: str) -> CheckResult:
    """The whole gate in front of a brief: consistent, structural, colour-free.

    Returns the recorded check result on a pass and refuses on a failure. It is
    never a pass with a warning attached — a breakdown that fails any of the
    three is not returned as satisfying the Wish.
    """

    result = check_game(record)
    findings = list(result.findings)
    findings.extend(wish_is_structural(record, objective))
    findings.extend(colour_free(record))
    if findings == list(result.findings) and result.passed:
        return result
    disposition = result.disposition or "clarify"
    problem_id = result.problem_id
    if len(findings) > len(result.findings) and problem_id is None:
        disposition = "rework"
    raise GameRecordError(
        "the invented game was refused by %d finding(s):\n  - %s\nDisposition: %s%s"
        % (
            len(findings),
            "\n  - ".join(findings),
            disposition,
            "\nProblem-ID: %s" % problem_id if problem_id else "",
        )
    )


def write_game_record(
    concept_root: Path, record: GameRecord, result: CheckResult
) -> Tuple[Path, Path]:
    """Seal the game beside the pixels, under the concept root."""

    directory = Path(concept_root) / GAME_RECORD_DIRECTORY
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    record_path = directory / GAME_RECORD_FILENAME
    check_path = directory / GAME_CHECK_FILENAME
    record_path.write_text(record.to_json(), encoding="utf-8")
    check_path.write_text(result.to_json(), encoding="utf-8")
    return record_path, check_path


__all__ = [
    "COLOUR_WORDS",
    "CheckResult",
    "DesignContract",
    "FORM_WORDS",
    "GAME_CHECK_FILENAME",
    "GAME_RECORD_DIRECTORY",
    "GAME_RECORD_FILENAME",
    "GameComponent",
    "GameRecord",
    "GameRecordError",
    "MATERIAL_WORDS",
    "MAX_PIECE_TYPES",
    "RULE_PHASES",
    "RuleStep",
    "WIN_PHASE",
    "WishHook",
    "assert_playable_record",
    "check_game",
    "colour_free",
    "concept_key_for",
    "wish_is_structural",
    "words_of",
    "write_game_record",
]

"""Turning findings into feedback the next round can act on.

Every finding that prevents a pass leaves here as a `Feedback` record naming the
area, what was observed, the evidence it came from, a severity, and the concrete
change to make. A finding addressed to the game names the rule it is about,
because "the game is unbalanced" is not something a next round can do anything
with and "win[1] gives seat 0 a 62% win rate" is.

Design decision D6 sets the severity. Upstream carried three budgets — repair,
rework and clarify — and a `clarify`-versus-`rework` disposition on every gate
failure. Workshop has one budget, `playtest_rounds`, and one vocabulary. The
disposition survives as severity and area:

* a defect in how the game **functions**, or a failed manufacturing
  measurement, is `block` — the design has to change;
* an **ambiguity or incompleteness** in the rules is `improve` — the design has
  to be described better.

Both send the game back through the loop; only the wording of the fix differs.
The upstream after-the-fact check that a clarification stayed out of the
mechanics is dropped, and deliberately: under Workshop both dispositions spend
the same single allowance, so there is no cheaper lane for a clarification to
launder a design flaw into, which is the exact failure that check existed to
catch.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from inventor_workshop.jobs import Feedback

# The areas ABO speaks in. `rules` and `game` are answered in the design;
# `geometry` and `manufacturing` are answered in the build.
AREA_RULES = "rules"
AREA_GAME = "game"
AREA_GEOMETRY = "geometry"
AREA_MANUFACTURING = "manufacturing"

# A finding in one of these areas invalidates the design itself, so the next
# round revises the sealed game rather than working around it in CAD.
DESIGN_AREAS = frozenset((AREA_RULES, AREA_GAME))

# Where a finding names a rule, it looks like `setup[2]`, `turn[1]`, `end[1]`
# or `win[1]`.
RULE_REFERENCE = re.compile(r"\b((?:setup|turn|end|win)\[\d+\])")
RULE_PHRASE = re.compile(r"\brule ((?:setup|turn|end|win)\[\d+\])")


def _invalidates(area: str) -> Tuple[str, ...]:
    """Which jobs a finding in this area sends back.

    A finding about the design invalidates Concept, so the next round revises
    the sealed rules and bill. A finding about the build leaves the design
    standing — redrawing the concept for a geometry fault would be exactly the
    drift the loop exists to prevent.
    """

    if area in DESIGN_AREAS:
        return ("concept", "make", "playtest", "instructions", "deliver")
    return ("make", "playtest", "instructions", "deliver")


def rule_named_in(text: str) -> str:
    """The rule a finding is about, or an empty string."""

    match = RULE_PHRASE.search(text) or RULE_REFERENCE.search(text)
    return match.group(1) if match else ""


def simulation_feedback(evidence: Mapping[str, Any]) -> List[Feedback]:
    """Findings from seeded play, at the severity D6 gives them."""

    found: List[Feedback] = []
    reference = "game-simulation"

    for index, finding in enumerate(evidence.get("findings", ()), 1):
        area, severity, change = _classify_simulation(finding, evidence)
        rule = rule_named_in(finding)
        if area in DESIGN_AREAS and not rule:
            # A finding addressed to the game has to name the rule it is about.
            rule = _rule_from_context(finding, evidence)
        found.append(
            Feedback(
                code="sim-%02d" % index,
                area=area,
                severity=severity,
                finding=_with_rule(finding, rule),
                change=change,
                evidence_refs=(reference,),
                invalidates=_invalidates(area),
            )
        )

    balance = dict(evidence.get("seat_advantage", {}))
    if balance and float(balance.get("edge", 0.0)) > 0.0:
        found.append(
            Feedback(
                code="sim-seat-advantage",
                area=AREA_GAME,
                severity="block",
                finding=(
                    "Seat %s wins %.1f%% of a balanced, seat-swapped sample, and "
                    "even the pessimistic end of the interval puts it %.1f points "
                    "above a fair share. Rule win[1] decides who wins, so that is "
                    "where the asymmetry is settled."
                    % (
                        balance.get("best_seat"),
                        100 * float(balance.get("best_seat_rate", 0.0)),
                        100 * float(balance.get("edge", 0.0)),
                    )
                ),
                change=(
                    "Give the second seat compensation the rules state — a "
                    "different opening allowance, or a tie broken the other way "
                    "— and re-measure over a seat-swapped sample."
                ),
                evidence_refs=(reference,),
                invalidates=_invalidates(AREA_GAME),
            )
        )

    ladder = list(evidence.get("skill_ladder", ()))
    weak = [
        rung
        for rung in ladder
        if rung.get("rung") == "optimizing-vs-greedy"
        and float(rung.get("edge", 0.0)) <= 0.0
    ]
    for rung in weak:
        found.append(
            Feedback(
                code="sim-skill-ladder",
                area=AREA_GAME,
                severity="block",
                finding=(
                    "Lookahead does not beat greedy (%.0f%% over %d games), so "
                    "the position is not deep however rule win[1] reads on paper."
                    % (100 * float(rung.get("win_rate", 0.0)), int(rung.get("games", 0)))
                ),
                change=(
                    "Buy depth from the board's structure rather than from "
                    "another action type: widen what a placement affects, or "
                    "make the run condition reach further across the grid."
                ),
                evidence_refs=(reference,),
                invalidates=_invalidates(AREA_GAME),
            )
        )
    return found


def _classify_simulation(
    finding: str, evidence: Mapping[str, Any]
) -> Tuple[str, str, str]:
    """Area, severity and the change to make, for one simulation finding."""

    lowered = finding.casefold()
    if lowered.startswith("assumptions:"):
        if "could not be shown" in lowered:
            return (
                AREA_RULES,
                "improve",
                "Either write the rule so the reading is not needed, or remove "
                "the declaration — a reading nothing exercises is not one.",
            )
        # A reading that changed the outcome is an incompleteness in the rules:
        # the rules must say which one is meant. That is a description problem,
        # which D6 makes an improvement rather than a block.
        return (
            AREA_RULES,
            "improve",
            "State in the rule itself which reading is meant, so the engine "
            "translates it rather than choosing it.",
        )
    if lowered.startswith("styles:"):
        return (
            AREA_GAME,
            "block",
            "Give the collapsed styles something to disagree about, or declare "
            "one style instead of two.",
        )
    if lowered.startswith("termination:"):
        return (
            AREA_GAME,
            "block",
            "Make rule end[1] reachable from every position the rules allow, so "
            "a game cannot run past its own ending.",
        )
    if lowered.startswith("contract:"):
        # A declared move kind that is never legal, never chosen, or not
        # actually administrative is a fake decision: a defect in how the game
        # functions rather than in how it is written.
        return (
            AREA_GAME,
            "block",
            "Remove the move kind, or give it a position in which taking it is "
            "the better choice.",
        )
    del evidence
    return (
        AREA_GAME,
        "block",
        "Change the rule this finding names so the measurement moves.",
    )


def _rule_from_context(finding: str, evidence: Mapping[str, Any]) -> str:
    """The rule a finding is about, where the finding did not name one."""

    for entry in evidence.get("assumption_readings", ()) or ():
        if str(entry.get("id", "")) and str(entry["id"]) in finding:
            return str(entry.get("rule", ""))
    # A finding about how the game is won is about the rule that decides it.
    return "win[1]"


def _with_rule(finding: str, rule: str) -> str:
    if not rule or rule in finding:
        return finding
    return "%s (rule %s)" % (finding, rule)


def manufacturing_feedback(name: str, evidence: Mapping[str, Any]) -> List[Feedback]:
    """A failed measurement blocks; an unrun one is an improvement.

    Both are answered in the build rather than in the design, so neither sends
    the sealed game back to Concept.
    """

    import manufacturing

    found: List[Feedback] = []
    for index, entry in enumerate(manufacturing.findings(evidence), 1):
        parts = list(entry.get("parts", ()))
        found.append(
            Feedback(
                code="%s-%02d" % (name, index),
                area=AREA_MANUFACTURING if entry["severity"] == "block" else AREA_GEOMETRY,
                severity=entry["severity"],
                finding="%s: %s%s"
                % (
                    entry["check"],
                    entry["finding"],
                    " (%s)" % ", ".join(parts) if parts else "",
                ),
                change=_manufacturing_change(entry),
                evidence_refs=(name,),
                invalidates=_invalidates(AREA_MANUFACTURING),
            )
        )
    return found


def _manufacturing_change(entry: Mapping[str, Any]) -> str:
    check = str(entry.get("check", ""))
    if entry.get("severity") == "improve":
        return (
            "Configure what this check needs and measure again; an unmeasured "
            "check never counts as a pass, so %s cannot pass until it runs." % check
        )
    if check == "bed-fit":
        return (
            "Shrink the part to the configured usable envelope, or split it and "
            "declare it as tiled."
        )
    if check == "interference-in-declared-poses":
        return "Move the named parts apart in that pose, or change the fit that puts them there."
    if check == "dimensions-against-brief":
        return "Build to the brief's stated millimetres; where a picture and a number disagree, the number governs."
    return "Change the geometry so this measurement passes, and measure again."


def seat_feedback(evidence: Mapping[str, Any]) -> List[Feedback]:
    """What the model seats reported, as findings about the game."""

    found: List[Feedback] = []
    for index, report in enumerate(evidence.get("seat_reports", ()), 1):
        lowered = report.casefold()
        if lowered.startswith("rules question"):
            area, severity = AREA_RULES, "improve"
            change = (
                "Answer the question inside the rule itself so the next reader "
                "does not have to ask it."
            )
        elif lowered.startswith("the rules ran out"):
            area, severity = AREA_RULES, "improve"
            change = "Write the rule that covers the position play reached."
        elif lowered.startswith("decision-free turns"):
            area, severity = AREA_GAME, "block"
            change = (
                "Give rule turn[1] a second thing worth weighing, or remove the "
                "turn that offers nothing."
            )
        else:
            area, severity = AREA_GAME, "block"
            change = (
                "The game gets smaller once it is worked out; buy depth from the "
                "board's structure rather than from another action type."
            )
        rule = rule_named_in(report) or ("turn[1]" if area == AREA_GAME else "win[1]")
        found.append(
            Feedback(
                code="seat-%02d" % index,
                area=area,
                severity=severity,
                # A seat's report is a finding about the game. It is never
                # evidence that anybody enjoyed playing it.
                finding=_with_rule(report, rule),
                change=change,
                evidence_refs=("agent-playtest",),
                invalidates=_invalidates(area),
            )
        )
    return found


def collect(
    *,
    simulation_evidence: Mapping[str, Any] = None,
    seat_evidence: Mapping[str, Any] = None,
    manufacturing_evidence: Mapping[str, Mapping[str, Any]] = None,
) -> Tuple[Feedback, ...]:
    """Every finding that prevented a pass, as feedback the next round can use."""

    found: List[Feedback] = []
    if simulation_evidence:
        found.extend(simulation_feedback(simulation_evidence))
    if seat_evidence:
        found.extend(seat_feedback(seat_evidence))
    for name, evidence in dict(manufacturing_evidence or {}).items():
        found.extend(manufacturing_feedback(name, evidence))
    return tuple(found)


def design_feedback(feedback: Sequence[Feedback]) -> Tuple[Feedback, ...]:
    """The findings the next round answers in the design rather than in CAD."""

    return tuple(item for item in feedback if "concept" in item.invalidates)


def build_feedback(feedback: Sequence[Feedback]) -> Tuple[Feedback, ...]:
    return tuple(item for item in feedback if "concept" not in item.invalidates)


__all__ = [
    "AREA_GAME",
    "AREA_GEOMETRY",
    "AREA_MANUFACTURING",
    "AREA_RULES",
    "DESIGN_AREAS",
    "build_feedback",
    "collect",
    "design_feedback",
    "manufacturing_feedback",
    "rule_named_in",
    "seat_feedback",
    "simulation_feedback",
]

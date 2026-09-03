"""Shared fixtures for the Daydream tests; not a test module itself."""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict

from workshop.contributors.extensions import fingerprint_extension_skill
from workshop.daydream.contracts import (
    DAYDREAM_IDEA_KIND,
    DAYDREAM_PROVENANCE_INPUTS,
    DAYDREAM_VERDICT_KIND,
    DaydreamProvenance,
    Idea,
    NoveltyReport,
    SealedDaydream,
    THESIS_VERDICT_CHECKS,
    VERDICT_CHECKS,
    Verdict,
    VerdictRisk,
    render_brief,
)


SAMPLE_DAYDREAM_ID = "daydream-20260902-101500-0badcafe"
SAMPLE_CREATED_AT = "2026-09-02T10:15:00Z"
SAMPLE_TASTE_SHA256 = "a" * 64


def sample_idea_dict() -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": DAYDREAM_IDEA_KIND,
        "title": "Ladder Drop",
        "one_liner": (
            "Flip a printed ladder and a captive bead clicks down every rung by "
            "gravity alone."
        ),
        "held_form": (
            "A palm-sized wooden-looking ladder with a bead that lives inside its rails, "
            "round-shouldered like a toy from a rug."
        ),
        "before_after": (
            "Before: the bead rests in the top cup of the upright ladder. After: the "
            "ladder is flipped and the bead rests in the cup at the other end."
        ),
        "what_you_do": "Hold the ladder upright, flip it end over end, and set it down.",
        "what_happens": (
            "The bead tumbles rung by rung with an audible click at each step, "
            "then rests in a cup at the bottom until the next flip."
        ),
        "why_it_is_new": (
            "The rungs are cams that hold the bead until the flip passes vertical, "
            "so the drop is paced by geometry rather than by chance."
        ),
        "prior_art": [
            {
                "name": "Jacob's ladder",
                "how_this_differs": (
                    "No ribbons or flipping tiles; a single captive bead steps down "
                    "fixed cam rungs."
                ),
            },
            {
                "name": "Marble run",
                "how_this_differs": (
                    "Nothing is assembled and the bead never leaves the body; the "
                    "flip is the reset."
                ),
            },
        ],
        "taste_fit": {
            "honors": ["Motion comes from geometry and gravity alone"],
            "steers_clear_of": ["Decorative objects with no repeatable interaction"],
        },
        "parts_estimate": 2,
        "keywords": ["ladder", "bead", "gravity", "click"],
    }


def horn_tip_paraphrase_dict() -> Dict[str, Any]:
    raw = sample_idea_dict()
    raw.update(
        {
            "title": "Crescent Rocker",
            "one_liner": (
                "A tiny crescent desk rocker that tips when you press its horn "
                "with a fingertip."
            ),
            "what_you_do": "Press the rounded horn with a fingertip.",
            "what_happens": "It tips, then gravity walks it back to rest on its outer curve.",
            "keywords": ["crescent", "rocker", "horn"],
        }
    )
    return raw


def sample_idea() -> Idea:
    return Idea.parse(sample_idea_dict())


def sample_thesis_dict() -> Dict[str, Any]:
    """A schema-v2 creative product thesis with live-source provenance."""

    observed_at = "2026-09-02T10:15:00Z"
    return {
        "schema_version": 2,
        "kind": DAYDREAM_IDEA_KIND,
        "title": "Ladder Drop",
        "one_liner": "Flip a pocket ladder and hear one captive bead compose a gravity rhythm.",
        "opportunity": {
            "world_scan": {
                "observed_at": observed_at,
                "scope": "English primary research on screen fatigue and direct reporting on small offline rituals",
                "evergreen": False,
                "signals": [
                    {
                        "title": "Adults are actively reducing leisure screen time",
                        "url": "https://example.org/research/offline-leisure",
                        "published_at": "2026-08-28T09:00:00Z",
                        "insight": "People seek tiny repeatable breaks that do not become another tracked task.",
                    },
                    {
                        "title": "Small tactile rituals return to shared desks",
                        "url": "https://example.net/report/tactile-rituals",
                        "published_at": None,
                        "insight": "A short physical action can mark a transition without demanding sustained attention.",
                    },
                ],
            },
            "human_tension": "People want a brief reset that feels consequential without opening another app or beginning a project.",
            "why_now": "Current screen-reduction behavior makes a self-ending physical ritual useful, while the tension remains durable beyond the trend.",
            "physical_opportunity": "Turn one flip into a paced sequence the hand starts and gravity finishes.",
        },
        "experience": {
            "physical_form": "A pocket ladder whose rails protect one visible captive bead and frame each gravity step.",
            "action": "Turn the ladder end over end once, then hold still.",
            "response": "Gravity advances the bead through a succession of geometric catches without another input.",
            "payoff": "Distinct clicks slow and then resolve, giving the flip a tiny composed ending.",
            "anti_generic_signature": "One input releases a visibly and audibly paced descent whose rhythm comes from changing catch geometry.",
            "theme_strip_test": "Without the ladder name or styling, the unequal gravity-paced catches still create a distinct action-response rhythm.",
            "invent_freedom": "Invent may change the catch geometry and outer form, but must preserve one-flip initiation, visible paced descent, and self-ending rhythm.",
        },
        "why_it_is_new": "Unlike a marble run or Jacob's ladder, one captive body crosses unequal geometric catches after a single reset, making timing the play signature rather than a continuous roll or linked flip.",
        "prior_art": [
            {
                "name": "Jacob's ladder",
                "url": "https://example.org/toys/jacobs-ladder",
                "observed_at": observed_at,
                "how_this_differs": "No linked flipping blocks; one captive body is released once and paced by fixed catches.",
            },
            {
                "name": "Marble run",
                "url": "https://example.net/toys/marble-run",
                "observed_at": observed_at,
                "how_this_differs": "The path is a closed handheld reset and its unequal pauses, not free rolling, are the payoff.",
            },
        ],
        "taste_fit": {
            "honors": ["Motion comes from geometry and gravity alone"],
            "steers_clear_of": ["Decorative objects with no repeatable interaction"],
        },
        "proof": {
            "mode": "visual-state",
            "observable": "A fixed view must distinguish the bead at every catch and the two end states; a short state sequence must establish the unequal pacing.",
            "kill_criteria": [
                "The bead or its successive catches cannot be distinguished in the declared view.",
                "The descent reads as one ordinary continuous roll rather than unequal paced steps.",
            ],
        },
        "route_floor": "spark",
        "parts_estimate": 2,
        "keywords": ["gravity", "paced-descent", "captive-bead", "one-flip"],
    }


def sample_thesis() -> Idea:
    return Idea.parse(sample_thesis_dict())


def sample_provenance(
    route: str = "spark", idea: Idea | None = None
) -> DaydreamProvenance:
    selected = sample_thesis() if idea is None else idea
    assert selected.opportunity is not None
    values = {
        name: hashlib.sha256(name.encode("utf-8")).hexdigest()
        for name in DAYDREAM_PROVENANCE_INPUTS
    }
    values["taste"] = SAMPLE_TASTE_SHA256
    values["vault_snapshot"] = None
    values["world_scan"] = hashlib.sha256(
        json.dumps(
            selected.opportunity.world_scan.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()
    values["prior_art"] = hashlib.sha256(
        json.dumps(
            [entry.to_dict() for entry in selected.prior_art],
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()
    return DaydreamProvenance(route=route, input_sha256s=values)


def horn_tip_thesis_dict() -> Dict[str, Any]:
    raw = sample_thesis_dict()
    raw.update(
        {
            "title": "Crescent Rocker",
            "one_liner": "A tiny crescent desk rocker that tips when you press its horn with a fingertip.",
            "why_it_is_new": "A fingertip press tips the crescent and its outer curve walks it back to rest.",
            "keywords": ["crescent", "rocker", "horn"],
        }
    )
    raw["experience"].update(
        {
            "physical_form": "A tiny one-piece crescent with a rounded horn.",
            "action": "Press the rounded horn with a fingertip.",
            "response": "The whole crescent tips forward along its outer curve.",
            "payoff": "Gravity walks it back to rest.",
            "anti_generic_signature": "The horn press turns the crescent body into its own rocker.",
            "theme_strip_test": "Without styling, a fingertip tips a curved body that rocks back to rest.",
            "invent_freedom": "Preserve the press-to-tip rocker motion and one-piece crescent body.",
        }
    )
    return raw


def sample_novelty() -> NoveltyReport:
    return NoveltyReport(
        status="new",
        max_similarity=0.0,
        nearest=(),
        reason="no prior work to compare against",
    )


def build_verdict_dict(decision: str = "build") -> Dict[str, Any]:
    risks = [] if decision == "build" else [
        {"kind": "hidden-signature", "detail": "The bead's cam rungs are inside the rails."}
    ]
    checks = {name: True for name in VERDICT_CHECKS}
    if decision != "build":
        checks["moving_part_visible_in_both_states"] = False
    return {
        "schema_version": 1,
        "kind": DAYDREAM_VERDICT_KIND,
        "decision": decision,
        "checks": checks,
        "confidence": 0.8 if decision == "build" else 0.25,
        "risks": risks,
        "advice": "Keep the ladder body; put the bead on the outside of the rails.",
    }


def build_thesis_verdict_dict(
    decision: str = "build",
    *,
    daydream_id: str = SAMPLE_DAYDREAM_ID,
    idea_sha256: str | None = None,
    taste_sha256: str = SAMPLE_TASTE_SHA256,
    route: str = "spark",
) -> Dict[str, Any]:
    risks = [] if decision == "build" else [
        {
            "kind": "proof-mismatch",
            "detail": "The proposed evidence does not distinguish paced catches from a continuous roll.",
        }
    ]
    checks = {name: True for name in THESIS_VERDICT_CHECKS}
    if decision != "build":
        checks["proof_observable"] = False
    return {
        "schema_version": 2,
        "kind": DAYDREAM_VERDICT_KIND,
        "daydream_id": daydream_id,
        "idea_sha256": idea_sha256 or sample_thesis().sha256,
        "taste_sha256": taste_sha256,
        "route": route,
        "decision": decision,
        "checks": checks,
        "confidence": 0.8 if decision == "build" else 0.25,
        "risks": risks,
        "advice": "Keep the one-flip ritual; make the unequal catch sequence independently observable.",
    }


def sample_verdict(decision: str = "build") -> Verdict:
    return Verdict.parse(build_verdict_dict(decision))


def sample_sealed(**overrides: Any) -> SealedDaydream:
    idea = overrides.pop("idea", sample_idea())
    values: Dict[str, Any] = dict(
        daydream_id=SAMPLE_DAYDREAM_ID,
        inventor_id="sample",
        inventor_name="Sample",
        taste_sha256=SAMPLE_TASTE_SHA256,
        manager_id="codex",
        seed={
            "moment": "a rainy Sunday at a kitchen table",
            "twist": "gravity is the only motor",
        },
        created_at=SAMPLE_CREATED_AT,
        idea=idea,
        idea_sha256=idea.sha256,
        novelty=sample_novelty(),
        session={"status": "completed", "used_web_search": True},
        brief=render_brief(idea, inventor_name="Sample", inventor_id="sample"),
    )
    values.update(overrides)
    return SealedDaydream(**values)


def inventor_bundle(root: Path) -> Path:
    """Copy of the schema-v8 ``sample`` Inventor fixture from the contributors tests."""

    folder = root / "sample"
    folder.mkdir(parents=True)
    (folder / "TASTE.md").write_text(
        "---\n"
        "name: Sample\n"
        "description: Makes specific physical playthings for test Wishes.\n"
        "---\n"
        "# Taste\nSpecific and useful.\n\n"
        "## Promises\nMotion comes from geometry and gravity alone\n\n"
        "## Rejections\nDecorative objects with no repeatable interaction\n",
        encoding="utf-8",
    )
    skill_name = "sample-inventor"
    skill = folder / "skills" / skill_name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\n"
        "name: sample-inventor\n"
        "description: Apply Sample's specialist judgment inside one Workshop run.\n"
        "---\n"
        "# Sample Inventor\nRead the exact Taste and obey the Manager.\n",
        encoding="utf-8",
    )
    fingerprint = fingerprint_extension_skill(skill.resolve(), expected_name=skill_name)
    (folder / "inventor.json").write_text(
        json.dumps(
            {
                "schema_version": 8,
                "id": "sample",
                "status": "experimental",
                "source": {"kind": "local"},
                "extensions": [
                    {
                        "kind": "codex-skill",
                        "name": skill_name,
                        "path": "skills/%s" % skill_name,
                        "artifact_sha256": fingerprint.artifact_sha256,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return folder


def horn_tip_catalog(root: Path) -> Path:
    """Write a one-toy public catalog shaped like the source checkout's ``toys/``."""

    toy = root / "toys" / "pico-press-horn-tip"
    (toy / "wish").mkdir(parents=True)
    (toy / "wish" / "wish.json").write_text(
        json.dumps(
            {
                "kind": "autonomous-workshop.public-wish-binding",
                "product_id": "wish-20260827-173926-02d670f7",
                "public_title": "Horn Tip",
                "public_summary": (
                    "A tiny one-piece crescent desk rocker. Press a rounded horn "
                    "with a fingertip and it tips, then gravity walks it back to "
                    "rest on its outer curve."
                ),
                "objective": "I wish for a tiny one-piece crescent desk rocker",
                "schema_version": 1,
            }
        ),
        encoding="utf-8",
    )
    return root

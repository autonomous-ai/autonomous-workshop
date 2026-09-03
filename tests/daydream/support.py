"""Shared fixtures for the Daydream tests; not a test module itself."""

import json
from pathlib import Path
from typing import Any, Dict

from workshop.contributors.extensions import fingerprint_extension_skill
from workshop.daydream.contracts import (
    DAYDREAM_IDEA_KIND,
    Idea,
    NoveltyReport,
    SealedDaydream,
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


def sample_novelty() -> NoveltyReport:
    return NoveltyReport(
        status="new",
        max_similarity=0.0,
        nearest=(),
        reason="no prior work to compare against",
    )


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
        "# Taste\nSpecific and useful.\n",
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

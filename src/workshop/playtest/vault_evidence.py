"""Playtest evidence rows: what one sealed round teaches the game vault.

:func:`build_rows` turns a sealed Playtest contract into one row per feedback
item, tagged with the design-vault mechanisms the concept resolved to and the
anti-pattern of the confirmed vault lead that named it.  The host posts the
confirmed rows and the dismissed leads to the vault API
(:mod:`workshop.invent.gamevault`); they land on the anti-pattern nodes every
later run reads through its phase snapshot, so nothing is kept locally.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Optional, Sequence

from workshop.errors import ContractError


PROVENANCE_WEIGHTS = (
    ("physical", 4),
    ("deterministic", 3),
    ("codex", 2),
    ("agent", 2),
)
DEFAULT_WEIGHT = 1

_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")


def provenance_weight(evidence_class: Optional[str]) -> int:
    """How much a row is worth: measurements outrank model assessments."""

    lowered = (evidence_class or "").casefold()
    for prefix, weight in PROVENANCE_WEIGHTS:
        if lowered.startswith(prefix):
            return weight
    return DEFAULT_WEIGHT


def build_rows(
    product_id: str,
    round_index: int,
    playtested: Mapping[str, Any],
    leads: Sequence[Mapping[str, Any]],
    mechanisms: Sequence[str],
) -> list[dict[str, Any]]:
    """One row per feedback item of a sealed Playtest contract.

    The symptom is the anti-pattern of a confirmed vault lead that named the
    feedback item; every other row keeps ``symptom: null``.  The weight comes
    from the strongest ``evidence_class`` among the checks the item cites.
    """

    if not isinstance(product_id, str) or _IDENTIFIER.fullmatch(product_id) is None:
        raise ContractError("evidence product_id is invalid")
    if type(round_index) is not int or round_index < 1:
        raise ContractError("evidence round must be a positive integer")
    checks = {item["check_id"]: item for item in playtested.get("checks", ())}
    class_by_ref = {
        item["evidence_ref"]: (item.get("observations") or {}).get("evidence_class")
        for item in checks.values()
    }
    answers = (checks.get("agent-playtest", {}).get("observations") or {}).get("vault_leads", [])
    lead_by_id = {lead["id"]: lead for lead in leads if isinstance(lead, Mapping) and "id" in lead}
    symptom_by_code: dict[str, str] = {}
    for answer in answers:
        if (
            isinstance(answer, Mapping)
            and answer.get("verdict") == "confirmed"
            and isinstance(answer.get("feedback_code"), str)
            and answer.get("lead") in lead_by_id
        ):
            nodes = lead_by_id[answer["lead"]].get("nodes") or []
            if len(nodes) == 2:
                symptom_by_code[answer["feedback_code"]] = nodes[1]
    observed = max((item.get("observed_at", "") for item in checks.values()), default="")
    rows = []
    for item in playtested.get("feedback", ()):
        refs = item.get("evidence_refs") or ()
        classes = [class_by_ref.get(ref) for ref in refs]
        weight = max((provenance_weight(kind) for kind in classes), default=DEFAULT_WEIGHT)
        strongest = max(classes, key=provenance_weight, default=None)
        rows.append(
            {
                "ref": "%s#r%d:%s" % (product_id, round_index, item["code"]),
                "product_id": product_id,
                "round": round_index,
                "code": item["code"],
                "area": item["area"],
                "severity": item["severity"],
                "finding": item["finding"],
                "change": item["change"],
                "mechanisms": sorted({str(node) for node in mechanisms if node}),
                "symptom": symptom_by_code.get(item["code"]),
                "evidence_class": strongest,
                "weight": weight,
                "observed_at": observed,
            }
        )
    return rows


SEVERITY_TO_VAULT = {"block": "high", "improve": "medium"}


def gamevault_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """The rows a confirmed vault lead named, in the vault API's evidence shape.

    Only a row whose ``symptom`` is an anti-pattern node has a home in the
    vault; every other finding stays in the sealed Playtest contract.
    """

    result = []
    for row in rows:
        symptom = row.get("symptom")
        if not isinstance(symptom, str) or not symptom.startswith("anti-patterns/"):
            continue
        result.append(
            {
                "slug": row["product_id"],
                "id": "r%04d-%s" % (row["round"], row["code"]),
                "symptom": symptom,
                "claim": " ".join(str(row["finding"]).split()),
                "fix_tried": " ".join(str(row["change"]).split()),
                "severity": SEVERITY_TO_VAULT.get(row["severity"], "low"),
                "survived_rounds": 1,
                "source": "workshop-playtest",
                "round": row["round"],
            }
        )
    return result


MAX_DESIGN_LESSONS = 3


def gamevault_design(
    product_id: str,
    round_index: int,
    *,
    concept: Mapping[str, Any],
    mechanisms: Sequence[str],
    verdict: str,
    scores: Optional[Mapping[str, Any]],
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """The product's own ``games/<product_id>`` page, in the vault API's shape.

    Every wish leaves a game node behind: ``uses`` the mechanisms the vault
    resolved from the sealed concept, ``exhibits`` the anti-patterns this
    Playtest confirmed, and carries the round's verdict, median scores, and
    up to three confirmed findings as lessons.  ``rows`` are the rows
    :func:`gamevault_rows` produced for the same round.
    """

    title = concept.get("title")
    summary = concept.get("summary")
    return {
        "slug": product_id,
        "name": " ".join(str(title).split())[:120] if isinstance(title, str) and title.strip() else product_id,
        "summary": " ".join(str(summary).split())[:900] if isinstance(summary, str) else "",
        "mechanisms": sorted({str(item) for item in mechanisms}),
        "exhibits": sorted({str(row["symptom"]) for row in rows}),
        "round": round_index,
        "verdict": str(verdict),
        "scores": {
            str(key): value
            for key, value in (scores or {}).items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        },
        "lessons": [str(row["claim"])[:220] for row in rows[:MAX_DESIGN_LESSONS]],
    }


def gamevault_dismissals(
    dismissals: Sequence[Mapping[str, Any]], *, product_id: str, round_index: int
) -> list[dict[str, Any]]:
    """Dismissed leads in the vault API's review shape: one DISMISSED row each."""

    result = []
    for item in dismissals:
        nodes = item.get("nodes") or ()
        if len(nodes) != 2 or not isinstance(item.get("lead"), str):
            continue
        result.append(
            {
                "slug": product_id,
                "id": "r%04d-%s" % (round_index, item["lead"]),
                "symptom": nodes[1],
                "why": " ".join(str(item.get("why", "")).split()) or "no reason given",
            }
        )
    return result


__all__ = [
    "build_rows",
    "gamevault_dismissals",
    "gamevault_rows",
    "provenance_weight",
]

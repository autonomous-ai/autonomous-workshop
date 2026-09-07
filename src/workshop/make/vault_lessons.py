"""Make lessons: what one Make outcome teaches the game vault, and back.

The write path mirrors :mod:`workshop.playtest.vault_evidence`. Rows are built
only from host-verified Make outcomes (a failed CAD gate, a token-budget stop)
and from the Manager's own sealed statements (a Make-to-Invent revision
request, a Make need the host recorded). Each row is classified onto one
anti-pattern node by failure class; a failure that is a protocol slip rather
than a design lesson yields no row. The host posts the rows through the same
queue Playtest uses, so a vault that is unreachable now receives them before
the next phase fetches its snapshot.

The read path, :func:`make_lessons`, is the bounded list every Invent and Make
packet carries as ``make_lessons``: the newest evidence banked on the
anti-patterns the concept's mechanisms risk, plus the Make failure classes
themselves, each with the vault's recorded fixes. Ten bullets at most, so it
rides the prompt instead of replacing the vault.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Optional, Sequence

from workshop.errors import ContractError
from workshop.invent.vault import Vault, VaultError, evidence_rows, normalize_path
from workshop.invent.vault_writes import (
    DEFAULT_WEIGHT,
    SEVERITY_TO_VAULT,
    gamevault_design,
    provenance_weight,
)

MAKE_SOURCE = "workshop-make"
MAX_MAKE_LESSONS = 10
MAX_LESSON_CHARS = 220
MAX_LESSON_FIXES = 3
MAX_LESSONS_PER_NODE = 3
MAX_FAILURES = 32

_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_CODE = re.compile(r"[^a-z0-9]+")

# Host failure codes that describe a slip in the run protocol, not the design.
PROTOCOL_CODES = frozenset(
    {
        "make-contract-invalid",
        "make-artifact-invalid",
        "make-product-metadata-invalid",
        "make-production-parts-missing",
        "make-part-colours-missing",
        "declared-cad-output-changed",
    }
)

# Failure class -> anti-pattern slug, matched by keyword against the failure
# code and its finding. First match wins; order runs from the most specific
# Make wall to the most general.
FAILURE_CLASSES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "likeness-wall",
        ("likeness", "iou", "silhouette", "resembl", "look like", "looks like", "stalled"),
    ),
    (
        "unbounded-repair-loop",
        (
            "token limit",
            "token budget",
            "token cap",
            "round budget",
            "repair attempt",
            "rereview",
            "re-review",
            "exhausted",
        ),
    ),
    (
        "feature-below-process-resolution",
        ("nozzle", "process resolution", "minimum feature", "too small to print"),
    ),
    (
        "underbuilt-shell",
        ("thickness", "thin wall", "thin-wall", "min_wall", "underbuilt", "wall gate"),
    ),
    (
        "sealed-volume-overlap",
        ("overlap", "interfer", "intersect", "clearance", "collide", "collision"),
    ),
    (
        "unswept-drive-cycle",
        ("motion", "drive cycle", "jam", "binds", "binding", "stroke", "linkage", "cam "),
    ),
    (
        "support-dependent-geometry",
        ("overhang", "support", "bed fit", "bed-fit", "build plate", "print-preflight"),
    ),
    (
        "impossible-assembly-path",
        ("assembly path", "cannot be assembled", "captive", "insertion"),
    ),
    (
        "unstable-contact-footprint",
        ("topple", "tip over", "stability", "footprint", "centre of mass", "center of mass"),
    ),
)


def classify_make_failure(code: str, text: str = "") -> Optional[str]:
    """The anti-pattern node one Make failure belongs to, or ``None``.

    Protocol codes never become lessons. Everything else is matched by keyword
    against the code and the finding; an unmatched failure yields ``None`` so
    the vault never receives a row with no failure mode.
    """

    if not isinstance(code, str) or not code:
        raise ContractError("make failure code must be text")
    if code in PROTOCOL_CODES:
        return None
    haystack = " %s %s " % (code.replace("-", " ").lower(), " ".join(str(text or "").split()).lower())
    for slug, keywords in FAILURE_CLASSES:
        if any(keyword in haystack for keyword in keywords):
            return "anti-patterns/" + slug
    return None


def build_make_rows(
    product_id: str,
    round_index: int,
    failures: Sequence[Mapping[str, Any]],
    mechanisms: Sequence[str],
) -> list[dict[str, Any]]:
    """One row per classified Make failure, in the Playtest row shape.

    Each failure names its ``code``, ``finding``, and ``evidence_class``
    (``deterministic-...`` for host gates, ``codex-...`` for the Manager's own
    statements), optionally ``change`` (what was tried), ``severity``
    (``block`` or ``improve``, default ``block``) and ``observed_at``.
    """

    if not isinstance(product_id, str) or _IDENTIFIER.fullmatch(product_id) is None:
        raise ContractError("make evidence product_id is invalid")
    if type(round_index) is not int or round_index < 1:
        raise ContractError("make evidence round must be a positive integer")
    if len(failures) > MAX_FAILURES:
        raise ContractError("make evidence holds too many failures")
    rows = []
    seen: set[str] = set()
    for item in failures:
        if not isinstance(item, Mapping):
            raise ContractError("make failures must be mappings")
        code = item.get("code")
        finding = " ".join(str(item.get("finding") or "").split())
        if not isinstance(code, str) or not code or not finding:
            raise ContractError("make failure needs a code and a finding")
        symptom = classify_make_failure(code, finding)
        if symptom is None:
            continue
        slug = _CODE.sub("-", code.lower()).strip("-")[:60] or "failure"
        if slug in seen:
            slug = "%s-%d" % (slug, len(rows) + 1)
        seen.add(slug)
        evidence_class = item.get("evidence_class")
        severity = item.get("severity") or "block"
        if severity not in ("block", "improve"):
            raise ContractError("make failure severity must be block or improve")
        rows.append(
            {
                "ref": "%s#r%d:%s" % (product_id, round_index, slug),
                "product_id": product_id,
                "round": round_index,
                "code": slug,
                "area": "make",
                "severity": severity,
                "finding": finding,
                "change": " ".join(str(item.get("change") or "").split()),
                "mechanisms": sorted({str(node) for node in mechanisms if node}),
                "symptom": symptom,
                "evidence_class": evidence_class if isinstance(evidence_class, str) else None,
                "weight": (
                    provenance_weight(evidence_class)
                    if isinstance(evidence_class, str)
                    else DEFAULT_WEIGHT
                ),
                "observed_at": str(item.get("observed_at") or ""),
            }
        )
    return rows


def gamevault_make_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Make rows in the vault API's evidence shape, tagged ``workshop-make``."""

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
                "claim": str(row["finding"])[:MAX_LESSON_CHARS],
                "fix_tried": str(row.get("change") or "")[:120],
                "severity": SEVERITY_TO_VAULT.get(row["severity"], "low"),
                "survived_rounds": 1,
                "source": MAKE_SOURCE,
                "round": row["round"],
            }
        )
    return result


def gamevault_make_design(
    product_id: str,
    round_index: int,
    *,
    concept: Mapping[str, Any],
    mechanisms: Sequence[str],
    verdict: str,
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """The product's ``games/<product_id>`` page after one Make outcome.

    Spark and Forge runs never reach Playtest, so this is the only page they
    leave behind: the mechanisms they used, the Make anti-patterns they
    exhibited, and a ``make-*`` verdict. A later Playtest rewrites the same
    page with its own verdict and scores.
    """

    if not isinstance(verdict, str) or not verdict.startswith("make-"):
        raise ContractError("make design verdict must start with make-")
    return gamevault_design(
        product_id,
        round_index,
        concept=concept,
        mechanisms=mechanisms,
        verdict=verdict,
        scores=None,
        rows=rows,
    )


def _lesson_rank(row: Mapping[str, str]) -> tuple[int, int]:
    # A lead the run dismissed explains why a risk did not apply; it ranks
    # after every confirmed row. Workshop products then come first: their
    # rows carry the run trail a Manager can open.
    dismissed = 1 if row["text"].startswith("DISMISSED") else 0
    return (dismissed, 0 if row["ref"].startswith("wish-") else 1)


def make_lessons(
    vault: Optional[Vault],
    concept: Optional[Mapping[str, Any]],
    *,
    limit: int = MAX_MAKE_LESSONS,
) -> list[dict[str, Any]]:
    """The bounded lessons list an Invent or Make packet carries.

    Anti-patterns come from two places: the ``risks`` of every mechanism the
    concept resolves to, then the Make failure classes themselves when the
    vault knows them. Each contributes its banked evidence rows, newest first,
    Workshop products before harvested sources, with the vault's recorded
    fixes. A vault-less phase, or a concept naming no known mechanism, still
    yields the Make-class lessons; nothing is invented.
    """

    if type(limit) is not int or limit < 1:
        raise ContractError("make lessons limit must be a positive integer")
    if vault is None:
        return []
    targets: list[str] = []
    if concept:
        try:
            resolved = vault.resolve_concept_mechanisms(concept)
        except VaultError:
            resolved = {}
        for path in resolved.values():
            if path is None:
                continue
            node = vault.nodes.get(normalize_path(path))
            if node is None:
                continue
            for risk in node["relations"].get("risks", ()):
                risk = normalize_path(str(risk))
                if risk.startswith("anti-patterns/") and risk not in targets:
                    targets.append(risk)
    for slug, _keywords in FAILURE_CLASSES:
        path = "anti-patterns/" + slug
        if path in vault.nodes and path not in targets:
            targets.append(path)
    per_node: list[list[dict[str, Any]]] = []
    for path in targets:
        node = vault.nodes[path]
        fixes = [
            normalize_path(str(fix))
            for fix in tuple(node["relations"].get("mitigated-by", ()))[:MAX_LESSON_FIXES]
        ]
        rows = evidence_rows(node["notes"])
        ordered = sorted(
            enumerate(reversed(rows)), key=lambda item: (_lesson_rank(item[1]), item[0])
        )
        per_node.append(
            [
                {
                    "anti_pattern": path,
                    "ref": row["ref"][:120],
                    "lesson": row["text"][:MAX_LESSON_CHARS],
                    "fixes": fixes,
                }
                for _index, row in ordered[:MAX_LESSONS_PER_NODE]
            ]
        )
    # Round-robin across anti-patterns so one well-documented risk cannot
    # crowd out the Make wall the run is most likely to hit.
    lessons: list[dict[str, Any]] = []
    depth = 0
    while len(lessons) < limit and any(len(rows) > depth for rows in per_node):
        for rows in per_node:
            if depth < len(rows) and len(lessons) < limit:
                lessons.append(rows[depth])
        depth += 1
    return lessons


__all__ = [
    "FAILURE_CLASSES",
    "MAKE_SOURCE",
    "MAX_LESSONS_PER_NODE",
    "MAX_MAKE_LESSONS",
    "PROTOCOL_CODES",
    "build_make_rows",
    "classify_make_failure",
    "gamevault_make_design",
    "gamevault_make_rows",
    "make_lessons",
]

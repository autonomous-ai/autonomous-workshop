"""Cross-run Playtest evidence: what earlier runs already broke on.

Until now every run started from a blank page.  This ledger banks each sealed
Playtest's feedback as one row per finding, tagged with the design-vault
mechanisms the sealed concept resolved to and weighted by how the finding was
observed, and hands the next run the rows that share its mechanisms.

Four rules keep this from becoming the machine agreeing with itself:

- a run never sees its own rows;
- provenance is ranked and a model never outranks a measurement:
  ``physical-receipt`` (4) > ``deterministic-digital-check`` (3) >
  ``codex-authored`` assessments (2) > anything else (1);
- the recalled block is capped, so a reader handed the same ten rows every
  run does not stop looking after the tenth;
- nothing is dropped silently: rows that name no vault symptom keep
  ``symptom: null`` and are counted.

The ledger is host state under ``$WORKSHOP_HOME/evidence/evidence.jsonl`` and
can always be rebuilt from the host's own gate receipts and the sealed
contracts they bind (:func:`harvest`).  Confirmed vault leads are also written
back to the host-owned vault's anti-pattern nodes; dismissals go to a review
queue for a human, never straight into the graph.
"""

from __future__ import annotations

import hashlib
import json
import re
import stat
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from workshop.errors import ContractError, StateConflict
from workshop.playtest.native import NativePlaytested


LEDGER_RELATIVE = Path("evidence") / "evidence.jsonl"
REVIEW_RELATIVE = Path("vault") / "_review"
VAULT_RELATIVE = Path("vault")
RECALL_LIMIT = 10
MAX_LEDGER_BYTES = 32 * 1024 * 1024
PROVENANCE_WEIGHTS = (
    ("physical", 4),
    ("deterministic", 3),
    ("codex", 2),
    ("agent", 2),
)
DEFAULT_WEIGHT = 1
_ROW_FIELDS = frozenset(
    (
        "ref",
        "product_id",
        "round",
        "code",
        "area",
        "severity",
        "finding",
        "change",
        "mechanisms",
        "symptom",
        "evidence_class",
        "weight",
        "observed_at",
    )
)
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


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


def _validate_row(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != _ROW_FIELDS:
        raise StateConflict("evidence ledger row fields are invalid")
    if not isinstance(value["ref"], str) or type(value["round"]) is not int:
        raise StateConflict("evidence ledger row identity is invalid")
    if not isinstance(value["mechanisms"], list) or type(value["weight"]) is not int:
        raise StateConflict("evidence ledger row tags are invalid")
    return dict(value)


def ledger_path(home: Path) -> Path:
    return Path(home) / LEDGER_RELATIVE


def read_ledger(home: Path) -> list[dict[str, Any]]:
    path = ledger_path(home)
    if path.is_symlink():
        raise StateConflict("evidence ledger must be a regular file")
    if not path.exists():
        return []
    if not stat.S_ISREG(path.lstat().st_mode):
        raise StateConflict("evidence ledger must be a regular file")
    if path.stat().st_size > MAX_LEDGER_BYTES:
        raise StateConflict("evidence ledger exceeds its size limit")
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(_validate_row(json.loads(line)))
        except ValueError as exc:
            raise StateConflict("evidence ledger line %d is not JSON" % number) from exc
    return rows


def append_rows(home: Path, rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    """Append new rows; a ref already banked is kept as it was."""

    existing = {row["ref"] for row in read_ledger(home)}
    fresh = [_validate_row(row) for row in rows if row.get("ref") not in existing]
    if fresh:
        path = ledger_path(home)
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            for row in fresh:
                handle.write(_canonical(row) + "\n")
        path.chmod(0o600)
    return {"written": len(fresh), "kept": len(rows) - len(fresh)}


def recall(
    home: Path,
    mechanisms: Sequence[str],
    *,
    exclude_product: Optional[str] = None,
    limit: int = RECALL_LIMIT,
) -> list[dict[str, Any]]:
    """The strongest banked rows sharing a mechanism with this concept.

    Ranked by provenance weight, then by how many mechanisms they share, then
    newest first; capped so the block cannot become the whole prompt.
    """

    wanted = {str(node) for node in mechanisms if node}
    if not wanted:
        return []
    candidates = []
    for row in read_ledger(home):
        if exclude_product is not None and row["product_id"] == exclude_product:
            continue
        shared = len(wanted & set(row["mechanisms"]))
        if shared:
            candidates.append((row["weight"], shared, row["observed_at"], row["ref"], row))
    # stable sorts, weakest key first: ref (asc), newest first, most shared, heaviest
    candidates.sort(key=lambda item: item[3])
    candidates.sort(key=lambda item: item[2], reverse=True)
    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [item[4] for item in candidates[: max(0, int(limit))]]


def write_back(
    home: Path,
    rows: Sequence[Mapping[str, Any]],
    dismissals: Sequence[Mapping[str, Any]],
    *,
    product_id: str,
    round_index: int,
) -> dict[str, int]:
    """Bank confirmed rows on host vault nodes; queue dismissals for a human.

    Only the host-owned vault under ``$WORKSHOP_HOME/vault`` is written; the
    seed shipped with Workshop is never modified.  A missing host vault means
    nothing to write.  Appending is idempotent by row ref.
    """

    vault = Path(home) / VAULT_RELATIVE
    banked = queued = 0
    if not vault.is_dir() or vault.is_symlink():
        return {"banked": 0, "queued": 0}
    for row in rows:
        symptom = row.get("symptom")
        if not isinstance(symptom, str) or not symptom.startswith("anti-patterns/"):
            continue
        node = vault / (symptom + ".md")
        if node.is_symlink() or not node.is_file():
            continue
        text = node.read_text(encoding="utf-8")
        marker = "- [%s]" % row["ref"]
        if marker in text:
            continue
        line = "%s %s: %s (fix tried: %s)" % (
            marker,
            row["severity"],
            " ".join(str(row["finding"]).split())[:300],
            " ".join(str(row["change"]).split())[:200],
        )
        if re.search(r"^## Notes\s*$", text, re.M):
            text = text.rstrip("\n") + "\n" + line + "\n"
        else:
            text = text.rstrip("\n") + "\n\n## Notes\n" + line + "\n"
        node.write_text(text, encoding="utf-8")
        banked += 1
    if dismissals:
        review = vault / "_review"
        review.mkdir(mode=0o700, exist_ok=True)
        target = review / ("%s-r%d.md" % (product_id, round_index))
        if not target.exists():
            lines = [
                "# Dismissed vault leads: %s round %d" % (product_id, round_index),
                "",
                "Each line is a lead the Playtest dismissed against the sealed revision.",
                "A lead dismissed for the same reason by several products is a graph",
                "edge to fix; delete this file once the vault has been updated.",
                "",
            ]
            for item in dismissals:
                lines.append(
                    "- %s -> %s: %s"
                    % (
                        " -> ".join(item.get("nodes") or ()),
                        item.get("lead"),
                        " ".join(str(item.get("why", "")).split())[:300],
                    )
                )
            target.write_text("\n".join(lines) + "\n", encoding="utf-8")
            target.chmod(0o600)
            queued = len(dismissals)
    return {"banked": banked, "queued": queued}


def review_queue(home: Path) -> list[dict[str, Any]]:
    review = Path(home) / REVIEW_RELATIVE
    if not review.is_dir():
        return []
    entries = []
    for path in sorted(review.glob("*.md")):
        if path.is_symlink():
            continue
        text = path.read_text(encoding="utf-8")
        entries.append(
            {
                "file": path.name,
                "dismissals": sum(1 for line in text.splitlines() if line.startswith("- ")),
            }
        )
    return entries


def harvest(home: Path, runs_root: Path, state_root: Path) -> dict[str, Any]:
    """Rebuild the ledger from the host's own Playtest gate receipts.

    Every ``state/<product>/gates/*-playtest.json`` names the sealed contract
    and its hash; the contract is re-read from the run and re-verified before
    a row is banked.  Mechanisms and confirmed leads are read from the sealed
    checks, so a rebuilt ledger matches what the host wrote at seal time.
    """

    state_root = Path(state_root)
    runs_root = Path(runs_root)
    rows: list[dict[str, Any]] = []
    products = 0
    unreadable: list[str] = []
    if state_root.is_dir():
        for product_dir in sorted(state_root.iterdir()):
            gates = product_dir / "gates"
            if not gates.is_dir() or product_dir.is_symlink():
                continue
            products += 1
            for gate in sorted(gates.glob("*-playtest.json")):
                try:
                    document = json.loads(gate.read_bytes().decode("utf-8"))
                    evidence = document["evidence"]
                    checks = evidence["checks"]
                    relative = evidence["artifact_path"]
                    expected = evidence["artifact_sha256"]
                except (OSError, UnicodeError, ValueError, KeyError, TypeError):
                    unreadable.append("%s/%s" % (product_dir.name, gate.name))
                    continue
                sealed = runs_root / product_dir.name / "workspace" / Path(*str(relative).split("/"))
                try:
                    content = sealed.read_bytes()
                except OSError:
                    unreadable.append("%s/%s" % (product_dir.name, gate.name))
                    continue
                if hashlib.sha256(content).hexdigest() != expected:
                    unreadable.append("%s/%s" % (product_dir.name, gate.name))
                    continue
                try:
                    playtested = NativePlaytested.from_mapping(json.loads(content.decode("utf-8")))
                except (ContractError, ValueError, UnicodeError):
                    unreadable.append("%s/%s" % (product_dir.name, gate.name))
                    continue
                mechanisms = checks.get("mechanisms") or []
                leads = checks.get("vault_leads") or []
                rows.extend(
                    build_rows(
                        product_dir.name,
                        int(checks.get("round") or playtested.round),
                        playtested.to_dict(),
                        leads,
                        mechanisms,
                    )
                )
    path = ledger_path(home)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.write_text("".join(_canonical(_validate_row(row)) + "\n" for row in rows), encoding="utf-8")
    path.chmod(0o600)
    return {"rows": len(rows), "products": products, "unreadable": unreadable}


__all__ = [
    "LEDGER_RELATIVE",
    "RECALL_LIMIT",
    "append_rows",
    "build_rows",
    "harvest",
    "ledger_path",
    "provenance_weight",
    "read_ledger",
    "recall",
    "review_queue",
    "write_back",
]

"""Workshop's deterministic inventor-selection handoff, before Spark Make.

The native Manager authors the choice. These functions only bind it to the
Wish and frozen roster and serialize a host-private receipt. The caller owns
safe file I/O, the run mutation lock, and the single native session. A receipt
is setup state, never a Match/Make gate, product artifact, or successful Goal.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from workshop._validation import require_sha256
from workshop.errors import ContractError
from workshop.match.native import InventorRoster, MatchRankingEntry, NativeMatchAssignment
from workshop.product.blueprints import ToyBlueprint


INVENTOR_SELECTION_CAPABILITY_PATH = (
    ".agents/skills/autonomous-workshop/references/inventor-selection-v1.md"
)
INVENTOR_SELECTION_MARKER_NAME = ".workshop-inventor-selection.json"
INVENTOR_SELECTION_RECEIPT_NAME = "inventor-selection.json"
INVENTOR_SELECTION_MARKER_KIND = "autonomous-workshop.inventor-selection-ready"
INVENTOR_SELECTION_RECEIPT_KIND = "autonomous-workshop.inventor-selection-receipt"
MAX_SELECTION_BYTES = 4 * 1024 * 1024


def selection_enabled(checkpoint: Any) -> bool:
    """Only a new marked Spark protocol gains the setup boundary."""

    return (
        checkpoint.effort == "spark"
        and INVENTOR_SELECTION_CAPABILITY_PATH in checkpoint.input_sha256s
    )


def _context(checkpoint: Any, roster: InventorRoster) -> dict[str, Any]:
    if not selection_enabled(checkpoint):
        raise ContractError("inventor selection requires a marked Spark run")
    if not isinstance(roster, InventorRoster):
        raise ContractError("inventor selection requires the immutable roster")
    capability = checkpoint.input_sha256s[INVENTOR_SELECTION_CAPABILITY_PATH]
    require_sha256(capability, "inventor selection capability sha256")
    require_sha256(checkpoint.wish_sha256, "inventor selection Wish sha256")
    require_sha256(checkpoint.checkpoint_sha256, "inventor selection checkpoint sha256")
    if not isinstance(checkpoint.product_id, str) or not checkpoint.product_id:
        raise ContractError("inventor selection product identity is invalid")
    return {
        "product_id": checkpoint.product_id,
        "wish_sha256": checkpoint.wish_sha256,
        "capability_sha256": capability,
        "inventor_roster_sha256": roster.roster_sha256,
    }


def _canonical(value: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("inventor selection must contain finite JSON") from exc


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate selection key")
        result[key] = value
    return result


def _marker(content: bytes) -> Mapping[str, Any]:
    if not isinstance(content, bytes) or not 1 <= len(content) <= MAX_SELECTION_BYTES:
        raise ContractError("inventor selection marker size is invalid")
    try:
        value = json.loads(content.decode("utf-8"), object_pairs_hook=_strict_object)
    except (UnicodeError, ValueError) as exc:
        raise ContractError("inventor selection marker must contain strict JSON") from exc
    if not isinstance(value, dict):
        raise ContractError("inventor selection marker must be an object")
    _canonical(value)  # Refuse NaN/Infinity without requiring cosmetic encoding.
    return value


def selection_source(assignment: NativeMatchAssignment) -> dict[str, Any]:
    """The unchanged compound Make finalizer consumes these existing fields."""

    return {
        "selected_inventor_id": assignment.selected_inventor_id,
        "ranking": [entry.to_dict() for entry in assignment.ranking],
    }


def selection_packet(
    checkpoint: Any,
    roster: InventorRoster,
    assignment: NativeMatchAssignment | None = None,
) -> dict[str, Any]:
    """Return the host-written inputs.workshop_selection packet."""

    context = _context(checkpoint, roster)
    if assignment is not None:
        assignment.assert_context(wish_sha256=checkpoint.wish_sha256, roster=roster)
    return {
        "schema_version": 1,
        "kind": "autonomous-workshop.inventor-selection-input",
        **context,
        "status": "selected" if assignment is not None else "pending",
        "marker_path": INVENTOR_SELECTION_MARKER_NAME,
        "checkpoint_sha256": checkpoint.checkpoint_sha256,
        "assignment": None if assignment is None else assignment.to_dict(),
    }


def selection_receipt(
    marker_bytes: bytes,
    *,
    checkpoint: Any,
    roster: InventorRoster,
) -> dict[str, Any]:
    """Validate native selection, not design, and create one durable receipt."""

    context = _context(checkpoint, roster)
    marker = _marker(marker_bytes)
    expected = {
        "schema_version", "kind", "product_id", "checkpoint_sha256",
        "wish_sha256", "inventor_roster_sha256", "selected_inventor_id", "ranking",
    }
    if set(marker) != expected:
        raise ContractError("inventor selection marker fields are invalid")
    if (
        type(marker["schema_version"]) is not int
        or marker["schema_version"] != 1
        or marker["kind"] != INVENTOR_SELECTION_MARKER_KIND
        or marker["checkpoint_sha256"] != checkpoint.checkpoint_sha256
        or any(marker[key] != context[key] for key in (
            "product_id", "wish_sha256", "inventor_roster_sha256"
        ))
    ):
        raise ContractError("inventor selection marker belongs to different host inputs")
    if not isinstance(marker["ranking"], list):
        raise ContractError("inventor selection ranking must be an array")
    selected = roster.inventor(marker["selected_inventor_id"])
    assignment = NativeMatchAssignment(
        wish_sha256=checkpoint.wish_sha256,
        inventor_roster_sha256=roster.roster_sha256,
        selected_inventor_id=selected.inventor_id,
        selected_agent_path=selected.agent_path,
        selected_agent_sha256=selected.agent_sha256,
        selected_source_manifest_sha256=selected.source_manifest_sha256,
        selected_taste_sha256=selected.taste_sha256,
        blueprint_sha256=ToyBlueprint().sha256,
        ranking=tuple(MatchRankingEntry.from_mapping(row) for row in marker["ranking"]),
    )
    assignment.assert_context(wish_sha256=checkpoint.wish_sha256, roster=roster)
    identity = {
        "schema_version": 1,
        "kind": INVENTOR_SELECTION_RECEIPT_KIND,
        "selection_origin": "native-manager",
        **context,
        "selected_at_checkpoint_sha256": checkpoint.checkpoint_sha256,
        "marker_sha256": hashlib.sha256(marker_bytes).hexdigest(),
        "assignment": assignment.to_dict(),
    }
    return {**identity, "receipt_sha256": hashlib.sha256(_canonical(identity)).hexdigest()}


def pinned_selection_receipt(
    *,
    checkpoint: Any,
    roster: InventorRoster,
    required_inventor_id: str,
) -> dict[str, Any]:
    """Bind the user's exact --inventor choice without asking a model to pick.

    The host must pass the override from the immutable Wish, not infer an
    override merely because a deployment happens to expose one Inventor.
    """

    context = _context(checkpoint, roster)
    if (
        len(roster.inventors) != 1
        or roster.inventors[0].inventor_id != required_inventor_id
    ):
        raise ContractError("explicit inventor selection requires the exact narrowed roster")
    authored = {
        "schema_version": 1,
        "kind": INVENTOR_SELECTION_MARKER_KIND,
        "product_id": context["product_id"],
        "checkpoint_sha256": checkpoint.checkpoint_sha256,
        "wish_sha256": context["wish_sha256"],
        "inventor_roster_sha256": context["inventor_roster_sha256"],
        "selected_inventor_id": required_inventor_id,
        "ranking": [{
            "inventor_id": required_inventor_id,
            "rationale": "The Wish explicitly selects this exact inventor.",
        }],
    }
    receipt = selection_receipt(_canonical(authored), checkpoint=checkpoint, roster=roster)
    receipt["selection_origin"] = "user-override"
    identity = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    receipt["receipt_sha256"] = hashlib.sha256(_canonical(identity)).hexdigest()
    return receipt


def assignment_from_receipt(
    receipt: Mapping[str, Any],
    *,
    checkpoint: Any,
    roster: InventorRoster,
) -> NativeMatchAssignment:
    """Reuse the selected inventor after interruptions and checkpoint refreshes."""

    context = _context(checkpoint, roster)
    expected = {
        "schema_version", "kind", "selection_origin", *context,
        "selected_at_checkpoint_sha256", "marker_sha256", "assignment", "receipt_sha256",
    }
    if not isinstance(receipt, Mapping) or set(receipt) != expected:
        raise ContractError("inventor selection receipt fields are invalid")
    if (
        type(receipt["schema_version"]) is not int or receipt["schema_version"] != 1
        or receipt["kind"] != INVENTOR_SELECTION_RECEIPT_KIND
        or receipt["selection_origin"] not in ("native-manager", "user-override")
        or any(receipt[key] != value for key, value in context.items())
    ):
        raise ContractError("inventor selection receipt belongs to different host inputs")
    for key in ("selected_at_checkpoint_sha256", "marker_sha256", "receipt_sha256"):
        require_sha256(receipt[key], "inventor selection %s" % key)
    identity = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    if hashlib.sha256(_canonical(identity)).hexdigest() != receipt["receipt_sha256"]:
        raise ContractError("inventor selection receipt hash is invalid")
    assignment = NativeMatchAssignment.from_mapping(receipt["assignment"])
    assignment.assert_context(wish_sha256=checkpoint.wish_sha256, roster=roster)
    if receipt["selection_origin"] == "user-override" and len(roster.inventors) != 1:
        raise ContractError("explicit inventor selection receipt requires the narrowed roster")
    return assignment


def selection_prompt() -> str:
    """Setup work is deliberately not native_stage_prompt('make')."""

    return (
        "Follow local AGENTS.md and the autonomous-workshop skill. Read STAGE.json "
        "and references/inventor-selection-v1.md under that skill. You are in the "
        "Workshop inventor-selection setup boundary, BEFORE Make. Do not create "
        "a Make Goal, load the Make reference, do product research, design, or CAD, "
        "or invoke any stage finalizer. Select from the immutable roster and "
        "persist the checkpoint-bound selection marker exactly as the reference "
        "describes. This is setup in the one existing native session, not another "
        "Goal, product stage, or product pass. Return immediately after writing "
        "the marker. Workshop will resume this exact session for Make with the "
        "selected inventor; preserve unfinished selection work on interruption."
    )

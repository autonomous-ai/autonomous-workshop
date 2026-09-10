import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from workshop.errors import ContractError
from workshop.match.native import InventorRoster, InventorRosterEntry
from workshop.workflow.inventor_selection import (
    INVENTOR_SELECTION_CAPABILITY_PATH,
    INVENTOR_SELECTION_MARKER_KIND,
    MAX_SELECTION_BYTES,
    assignment_from_receipt,
    pinned_selection_receipt,
    selection_enabled,
    selection_packet,
    selection_prompt,
    selection_receipt,
    selection_source,
)


def context(ids=("alice", "soren")):
    checkpoint = SimpleNamespace(
        effort="spark", product_id="wish-selection-test", wish_sha256="a" * 64,
        checkpoint_sha256="b" * 64,
        input_sha256s={INVENTOR_SELECTION_CAPABILITY_PATH: "c" * 64},
    )
    roster = InventorRoster(tuple(
        InventorRosterEntry(
            inventor_id=name, agent_path=".codex/agents/%s.toml" % name,
            agent_sha256="d" * 64, source_manifest_sha256="e" * 64,
            taste_sha256="f" * 64,
        )
        for name in ids
    ))
    return checkpoint, roster


def marker(checkpoint, roster):
    ids = [entry.inventor_id for entry in roster.inventors]
    # Deliberately prefer the last roster entry: Python must not rank it.
    ids.reverse()
    return {
        "schema_version": 1, "kind": INVENTOR_SELECTION_MARKER_KIND,
        "product_id": checkpoint.product_id,
        "checkpoint_sha256": checkpoint.checkpoint_sha256,
        "wish_sha256": checkpoint.wish_sha256,
        "inventor_roster_sha256": roster.roster_sha256,
        "selected_inventor_id": ids[0],
        "ranking": [{"inventor_id": name, "rationale": "Owns the wished-for mechanism"}
                    for name in ids],
    }


def encoded(value):
    return json.dumps(value, indent=2).encode()


def rehash(receipt):
    identity = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    receipt["receipt_sha256"] = hashlib.sha256(json.dumps(
        identity, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode()).hexdigest()


@pytest.mark.parametrize("effort,marked,expected", [
    ("spark", True, True), ("spark", False, False),
    ("forge", True, False), ("quest", True, False), (None, True, False),
])
def test_only_new_marked_spark_gains_setup(effort, marked, expected):
    checkpoint, roster = context()
    checkpoint.effort = effort
    if not marked:
        checkpoint.input_sha256s.clear()
    assert selection_enabled(checkpoint) is expected
    if not expected:
        with pytest.raises(ContractError, match="marked Spark"):
            selection_packet(checkpoint, roster)


def test_native_choice_receipt_survives_checkpoint_refresh_without_reranking():
    checkpoint, roster = context()
    pending = selection_packet(checkpoint, roster)
    assert pending["status"] == "pending"
    assert pending["assignment"] is None
    authored = marker(checkpoint, roster)
    content = encoded(authored)
    receipt = selection_receipt(content, checkpoint=checkpoint, roster=roster)
    assert receipt["marker_sha256"] == hashlib.sha256(content).hexdigest()
    assert receipt["selected_at_checkpoint_sha256"] == checkpoint.checkpoint_sha256
    assert "gate" not in receipt and "passed" not in receipt

    checkpoint.checkpoint_sha256 = "9" * 64
    assignment = assignment_from_receipt(receipt, checkpoint=checkpoint, roster=roster)
    assert assignment.selected_inventor_id == "soren"
    assert assignment.ranked_inventor_ids == ("soren", "alice")
    selected = selection_packet(checkpoint, roster, assignment)
    assert selected["status"] == "selected"
    assert selected["assignment"] == assignment.to_dict()
    assert selection_source(assignment) == {
        key: authored[key] for key in ("selected_inventor_id", "ranking")
    }


def test_explicit_inventor_uses_the_exact_narrowed_roster():
    checkpoint, roster = context(("alice",))
    authored = marker(checkpoint, roster)
    receipt = selection_receipt(encoded(authored), checkpoint=checkpoint, roster=roster)
    assert assignment_from_receipt(receipt, checkpoint=checkpoint, roster=roster).selected_inventor_id == "alice"
    authored["selected_inventor_id"] = "soren"
    authored["ranking"] = [{"inventor_id": "soren", "rationale": "Unauthorized replacement"}]
    with pytest.raises(ContractError, match="absent"):
        selection_receipt(encoded(authored), checkpoint=checkpoint, roster=roster)


def test_user_override_is_bound_without_a_native_selection_request():
    checkpoint, roster = context(("alice",))
    receipt = pinned_selection_receipt(
        checkpoint=checkpoint, roster=roster, required_inventor_id="alice",
    )
    assert receipt["selection_origin"] == "user-override"
    checkpoint.checkpoint_sha256 = "9" * 64
    assignment = assignment_from_receipt(receipt, checkpoint=checkpoint, roster=roster)
    assert assignment.selected_inventor_id == "alice"
    assert selection_packet(checkpoint, roster, assignment)["status"] == "selected"


@pytest.mark.parametrize("ids,required", [(("alice", "soren"), "alice"), (("alice",), "soren")])
def test_host_cannot_infer_or_substitute_an_explicit_override(ids, required):
    checkpoint, roster = context(ids)
    with pytest.raises(ContractError, match="exact narrowed roster"):
        pinned_selection_receipt(checkpoint=checkpoint, roster=roster, required_inventor_id=required)


@pytest.mark.parametrize("key,value", [
    ("schema_version", True), ("schema_version", 2), ("kind", "make-pass"),
    ("product_id", "another-wish"), ("checkpoint_sha256", "0" * 64),
    ("wish_sha256", "0" * 64), ("inventor_roster_sha256", "0" * 64),
    ("ranking", "soren"), ("ranking", []),
    ("selected_inventor_id", "alice"),
])
def test_rejects_stale_or_malformed_markers(key, value):
    checkpoint, roster = context()
    authored = marker(checkpoint, roster)
    authored[key] = value
    with pytest.raises(ContractError):
        selection_receipt(encoded(authored), checkpoint=checkpoint, roster=roster)


@pytest.mark.parametrize("change", ["missing", "duplicate", "unknown", "extra", "empty-reason"])
def test_existing_match_contract_enforces_full_exact_roster(change):
    checkpoint, roster = context()
    authored = marker(checkpoint, roster)
    if change == "missing":
        authored["ranking"].pop()
    elif change == "duplicate":
        authored["ranking"][1] = copy.deepcopy(authored["ranking"][0])
    elif change == "unknown":
        authored["ranking"][1]["inventor_id"] = "outsider"
    elif change == "extra":
        authored["ranking"][1]["score"] = 10
    else:
        authored["ranking"][1]["rationale"] = ""
    with pytest.raises(ContractError):
        selection_receipt(encoded(authored), checkpoint=checkpoint, roster=roster)


@pytest.mark.parametrize("content", [
    b"", b"[]", b"{", b"\xff", b'{"a":1,"a":2}',
    b'{"a": NaN}', b" " * (MAX_SELECTION_BYTES + 1),
])
def test_bad_json_cannot_select_an_inventor(content):
    checkpoint, roster = context()
    with pytest.raises(ContractError):
        selection_receipt(content, checkpoint=checkpoint, roster=roster)


@pytest.mark.parametrize("key", ["product_id", "wish_sha256", "capability_sha256", "inventor_roster_sha256"])
def test_private_receipt_cannot_be_replayed_for_another_context(key):
    checkpoint, roster = context()
    receipt = selection_receipt(encoded(marker(checkpoint, roster)), checkpoint=checkpoint, roster=roster)
    receipt[key] = "other-product" if key == "product_id" else "0" * 64
    rehash(receipt)
    with pytest.raises(ContractError, match="different host inputs"):
        assignment_from_receipt(receipt, checkpoint=checkpoint, roster=roster)


def test_private_receipt_hash_and_exact_assignment_are_verified():
    checkpoint, roster = context()
    receipt = selection_receipt(encoded(marker(checkpoint, roster)), checkpoint=checkpoint, roster=roster)
    receipt["assignment"]["selected_taste_sha256"] = "0" * 64
    with pytest.raises(ContractError, match="receipt hash"):
        assignment_from_receipt(receipt, checkpoint=checkpoint, roster=roster)
    rehash(receipt)
    with pytest.raises(ContractError, match="assignment"):
        assignment_from_receipt(receipt, checkpoint=checkpoint, roster=roster)


def test_setup_prompt_and_skill_order_selection_before_any_make_goal():
    prompt = selection_prompt()
    assert "BEFORE Make" in prompt
    assert "Do not create a Make Goal" in prompt
    assert "Return immediately" in prompt
    assert "exact session for Make" in prompt
    root = Path(__file__).resolve().parents[2]
    skill = (root / ".agents/product-run/.agents/skills/autonomous-workshop/SKILL.md").read_text()
    assert skill.index("inputs.workshop_selection") < skill.index("[references/make.md]")
    reference = (root / ".agents/product-run" / INVENTOR_SELECTION_CAPABILITY_PATH).read_text()
    assert "do not search for a replacement" in reference
    assert "reuse `selected_inventor_id`" in reference
    assert "The existing Make finalizer remains" in reference

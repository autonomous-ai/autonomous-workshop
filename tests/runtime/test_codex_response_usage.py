"""Exact per-response accounting across native resumes and remote compaction."""

import copy
import json
from pathlib import Path

import pytest

from workshop.runtime.codex_usage import (
    COUNTERS, UsageUnavailable, read_product_usage, read_thread_usage,
)
from tests.runtime.test_codex_usage import ROOT, CHILD, counters, usage, write


TURN_A = "01a07960-0000-7000-8000-000000000001"
TURN_B = "01a07960-0000-7000-8000-000000000002"


def six(n):
    value = counters(n)
    return {**value, "total_tokens": value["input_tokens"] + value["output_tokens"]}


def boundary(turn):
    return {"type": "event_msg", "payload": {"type": "task_started", "turn_id": turn}}


def start(thread=ROOT, parent=None):
    source = "exec" if parent is None else {"subagent": {"thread_spawn": {"parent_thread_id": parent}}}
    return [
        {"type": "session_meta", "payload": {
            "id": thread, "session_id": ROOT, "cwd": "/toy", "cli_version": "0.153.4", "source": source,
        }}, boundary(TURN_A),
        {"type": "turn_context", "payload": {"model": "gpt-6-astra"}},
    ]


def response(name, n, total, *, turn=TURN_A, turn_total=None, thread=ROOT):
    return {"type": "token_usage_record", "timestamp": "2026-09-07T01:00:00Z", "payload": {
        "thread_id": thread, "session_id": ROOT, "turn_id": turn,
        "root_turn_id": TURN_A, "response_id": "resp_" + name,
        "usage": six(n), "turn_token_usage": six(total if turn_total is None else turn_total),
        "thread_token_usage": six(total),
    }}


def notification(total, last):
    return usage(total, last_token_usage=counters(last))


def completed_events(thread=ROOT, parent=None):
    first = response("first", 100, 100, thread=thread)
    compact = response("compact", 100, 300, thread=thread)
    context_size = notification(200, 0)
    context_size["payload"]["info"]["last_token_usage"]["total_tokens"] = 23921
    return start(thread, parent) + [
        first, notification(100, 100), copy.deepcopy(first), notification(100, 100),
        response("second", 100, 200, thread=thread), notification(200, 100),
        compact,
        {"type": "compacted", "payload": {"latest_token_usage_record": compact["payload"],
             "replacement_history": [first, compact, response("embedded-only", 900000, 900300, thread=thread)]}},
        context_size, copy.deepcopy(context_size), boundary(TURN_B),
        response("resumed", 100, 400, turn=TURN_B, turn_total=100, thread=thread),
        notification(200, 100),  # Native restored an old counter baseline.
        response("final", 100, 500, turn=TURN_B, turn_total=200, thread=thread),
        notification(300, 100),
    ]


def read(tmp_path, events):
    return read_thread_usage(write(tmp_path, events), thread_id=ROOT, workspace=Path("/toy"))


def test_response_ledger_counts_compaction_once_and_survives_restored_notification_baseline(tmp_path):
    events = completed_events()
    first = read(tmp_path, events)
    second = read(tmp_path, events)
    assert first == second
    assert first["tokens"] == counters(500)
    assert first["models"] == ["gpt-6-astra"]
    assert first["status"] == "observed"


def test_child_session_binds_root_session_but_keeps_its_own_thread_and_turn_totals(tmp_path):
    write(tmp_path, completed_events())
    write(tmp_path, completed_events(CHILD, ROOT), CHILD)
    result = read_product_usage(tmp_path, thread_id=ROOT, workspace=Path("/toy"))
    assert result["tokens"] == counters(1000)
    assert result["total_tokens"] == 1100
    assert {item["thread_id"] for item in result["threads"]} == {ROOT, CHILD}


@pytest.mark.parametrize("drop", ["first", "middle", "last", "middle-and-notification"])
def test_missing_response_coverage_never_falls_back_to_notifications(tmp_path, drop):
    events = start() + [response("a", 100, 100), notification(100, 100),
                        response("b", 100, 200), notification(200, 100),
                        response("c", 100, 300), notification(300, 100)]
    index = {"first": 3, "middle": 5, "last": 7, "middle-and-notification": 5}[drop]
    del events[index:index + (2 if drop == "middle-and-notification" else 1)]
    with pytest.raises(UsageUnavailable, match="coverage"):
        read(tmp_path, events)


@pytest.mark.parametrize("payload", [None, [], {}, {"schema_version": 2}])
def test_known_ledger_kind_with_invalid_payload_cannot_select_legacy(tmp_path, payload):
    events = start() + [notification(100, 100), {"type": "token_usage_record", "payload": payload}]
    with pytest.raises(UsageUnavailable):
        read(tmp_path, events)


def test_partial_legacy_then_ledger_is_rejected_even_with_valid_ledger_totals(tmp_path):
    with pytest.raises(UsageUnavailable, match="earlier notification coverage"):
        read(tmp_path, start() + [notification(100, 100), response("a", 100, 100)])


@pytest.mark.parametrize("field,value", [
    ("thread_id", CHILD), ("session_id", CHILD), ("turn_id", TURN_B),
    ("root_turn_id", "not-a-uuid"), ("response_id", ""),
    ("response_id", "x" * 257), ("response_id", "resp_\nprivate"),
    ("schema_version", 2),
])
def test_response_identity_and_shape_are_exact(tmp_path, field, value):
    row = response("a", 100, 100)
    row["payload"][field] = value
    with pytest.raises(UsageUnavailable):
        read(tmp_path, start() + [row])


@pytest.mark.parametrize("kind", ["usage", "turn_token_usage", "thread_token_usage"])
@pytest.mark.parametrize("counter", list(COUNTERS) + ["total_tokens"])
def test_every_counter_must_be_valid_and_additive(tmp_path, kind, counter):
    rows = [response("a", 100, 100), response("b", 100, 200)]
    value = rows[-1]["payload"][kind]
    value[counter] += 1
    if counter in ("input_tokens", "output_tokens"):
        value["total_tokens"] += 1
    with pytest.raises(UsageUnavailable):
        read(tmp_path, start() + rows)


@pytest.mark.parametrize("bad", [True, -1, 1.5, "100", None])
def test_invalid_response_counter_types_fail_closed(tmp_path, bad):
    row = response("a", 100, 100)
    row["payload"]["usage"]["input_tokens"] = bad
    with pytest.raises(UsageUnavailable):
        read(tmp_path, start() + [row])


@pytest.mark.parametrize("change", ["usage", "root_turn_id", "turn_total", "thread_total"])
def test_conflicting_repeated_response_id_fails_without_double_charge(tmp_path, change):
    first = response("a", 100, 100)
    repeated = copy.deepcopy(first)
    if change == "usage":
        repeated["payload"]["usage"] = six(200)
    elif change == "root_turn_id":
        repeated["payload"]["root_turn_id"] = TURN_B
    else:
        repeated["payload"]["turn_token_usage" if change == "turn_total" else "thread_token_usage"] = six(200)
    with pytest.raises(UsageUnavailable, match="conflicting"):
        read(tmp_path, start() + [first, repeated])


def test_compaction_response_is_charged_before_any_notification(tmp_path):
    events = start() + [response("a", 100, 100), notification(100, 100), response("compact", 100, 200),
                        {"type": "compacted", "payload": {}}]
    assert read(tmp_path, events)["tokens"] == counters(200)


@pytest.mark.parametrize("change", ["no-compaction", "changed-total", "nonzero-last", "different-task", "no-prior-notification"])
def test_zero_usage_exception_requires_exact_post_compaction_evidence(tmp_path, change):
    compact = response("compact", 100, 200)
    events = start() + [response("a", 100, 100), notification(100, 100), compact]
    if change != "no-compaction":
        events.append({"type": "compacted", "payload": {"latest_token_usage_record": compact["payload"]}})
    if change == "different-task":
        events.append(boundary(TURN_B))
    if change == "no-prior-notification":
        del events[4]
    events.append(notification(200 if change == "changed-total" else 100,
                               50 if change == "nonzero-last" else 0))
    with pytest.raises(UsageUnavailable, match="coverage"):
        read(tmp_path, events)


def test_zero_token_response_is_observed_and_pending_child_remains_pending(tmp_path):
    write(tmp_path, start() + [response("zero", 0, 0)])
    write(tmp_path, start(CHILD, ROOT), CHILD)
    result = read_product_usage(tmp_path, thread_id=ROOT, workspace=Path("/toy"))
    assert result["total_tokens"] == 0
    assert {item["thread_id"]: item["status"] for item in result["threads"]} == {ROOT: "observed", CHILD: "pending"}


def test_partial_last_ledger_append_preserves_only_completed_prefix(tmp_path):
    path = write(tmp_path, start() + [response("a", 100, 100)])
    with path.open("a") as stream:
        stream.write('{"type":"token_usage_record","payload":')
    assert read_thread_usage(path, thread_id=ROOT, workspace=Path("/toy"))["tokens"] == counters(100)


def test_large_compaction_embedded_copies_never_charge_again(tmp_path):
    from workshop.runtime.codex_usage import MAX_LINE_BYTES
    row = response("a", 100, 100)
    compact = response("compact", 100, 200)
    events = start() + [row, notification(100, 100), compact, {
        "type": "compacted", "message": "x" * (MAX_LINE_BYTES + 1),
        "payload": {"latest_token_usage_record": compact["payload"]},
        "replacement_history": [row, response("embedded-only", 900000, 900200)],
    }, notification(100, 0)]
    assert read(tmp_path, events)["tokens"] == counters(200)


@pytest.mark.parametrize("metadata", [None, {}, "missing-response", "conflicting-response"])
def test_unaccounted_compaction_cannot_authorize_zero_usage_notification(tmp_path, metadata):
    first = response("a", 100, 100)
    missing = response("compact", 100, 200)["payload"]
    if metadata == "missing-response":
        reference = missing
    elif metadata == "conflicting-response":
        reference = {**first["payload"], "usage": six(200)}
    else:
        reference = metadata
    events = start() + [first, notification(100, 100), {
        "type": "compacted", "payload": {"latest_token_usage_record": reference},
    }, notification(100, 0)]
    with pytest.raises(UsageUnavailable):
        read(tmp_path, events)


def test_missing_compaction_response_cannot_borrow_an_unnotified_normal_response(tmp_path):
    events = start() + [response("a", 100, 100), notification(100, 100), response("b", 100, 200), {
        "type": "compacted", "payload": {
            "latest_token_usage_record": response("missing-compact", 100, 300)["payload"],
        },
    }, notification(100, 0)]
    with pytest.raises(UsageUnavailable, match="compaction.*coverage"):
        read(tmp_path, events)


@pytest.mark.parametrize("final_total, accepted", [(200, True), (300, False)])
def test_stale_duplicate_cannot_hide_a_missing_later_response(tmp_path, final_total, accepted):
    events = start() + [response("a", 100, 100), notification(100, 100),
        response("b", 100, 200), notification(100, 100), notification(final_total, 100)]
    if accepted:
        assert read(tmp_path, events)["tokens"] == counters(200)
    else:
        with pytest.raises(UsageUnavailable, match="coverage"):
            read(tmp_path, events)

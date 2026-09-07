import json
from pathlib import Path

import pytest

from workshop.runtime.codex_usage import (
    COUNTERS, UsageUnavailable, read_product_usage, read_thread_usage,
)

ROOT = "01a0795e-0efd-76e2-91a9-aa019980ede0"
CHILD = "01a0795f-26fd-7902-be2c-2256ed347770"


def counters(n=100):
    return dict(zip(COUNTERS, (n, n // 2, 0, n // 10, n // 20)))


def usage(n=100, **changes):
    value = {"type": "event_msg", "timestamp": "2026-09-07T01:00:00Z", "payload": {
        "type": "token_count", "info": {
            "total_token_usage": counters(n), "last_token_usage": counters(n),
        },
    }}
    value["payload"]["info"].update(changes)
    return value


def records(thread=ROOT, parent=None, cwd="/toy", version="0.153.4"):
    return [
        {"type": "session_meta", "payload": {"id": thread, "cwd": cwd,
         "cli_version": version, "source": "exec" if parent is None else {
             "subagent": {"thread_spawn": {"parent_thread_id": parent}}}}},
        {"type": "event_msg", "payload": {"type": "task_started", "turn_id": "first"}},
        {"type": "turn_context", "payload": {"model": "gpt-6-astra"}},
    ]


def write(tmp_path, events, name=ROOT):
    path = tmp_path / "2026/09/07" / ("rollout-" + name + ".jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(event) + "\n" for event in events))
    return path


def test_counts_resumes_and_deduplicates_notifications(tmp_path):
    events = records() + [usage(), usage(), usage(200)] + [
        {"type": "event_msg", "payload": {"type": "task_started", "turn_id": "second"}},
        usage(), usage(),
    ]
    result = read_thread_usage(write(tmp_path, events), thread_id=ROOT, workspace=Path("/toy"))
    assert result["tokens"] == counters(300)
    assert result["status"] == "observed"


def test_followup_task_keeps_cumulative_usage_then_process_resume_resets(tmp_path):
    events = records() + [usage(200)] + [
        {"type": "event_msg", "payload": {"type": "task_started", "turn_id": "followup"}},
        usage(300, last_token_usage=counters(100)),
        usage(300, last_token_usage=counters(100)),
        usage(400, last_token_usage=counters(100)),
        {"type": "event_msg", "payload": {"type": "task_started", "turn_id": "resume"}},
        usage(100),
    ]
    result = read_thread_usage(write(tmp_path, events), thread_id=ROOT, workspace=Path("/toy"))
    assert result["tokens"] == counters(500)


def test_product_counts_child_followup_without_reset_or_double_charge(tmp_path):
    write(tmp_path, records() + [usage(100)])
    write(tmp_path, records(CHILD, ROOT) + [usage(200),
        {"type": "event_msg", "payload": {"type": "task_started", "turn_id": "followup"}},
        usage(300, last_token_usage=counters(100)),
    ], CHILD)
    result = read_product_usage(tmp_path, thread_id=ROOT, workspace=Path("/toy"))
    assert result["total_tokens"] == 440


@pytest.mark.parametrize("current,last", [(300, 50), (100, 50), (300, 200)])
def test_followup_with_unexplained_baseline_fails_closed(tmp_path, current, last):
    events = records() + [usage(200),
        {"type": "event_msg", "payload": {"type": "task_started", "turn_id": "followup"}},
        usage(current, last_token_usage=counters(last)),
    ]
    with pytest.raises(UsageUnavailable, match="baseline"):
        read_thread_usage(write(tmp_path, events), thread_id=ROOT, workspace=Path("/toy"))


@pytest.mark.parametrize(("thread", "parent"), [(ROOT, None), (CHILD, ROOT)])
def test_continued_tasks_then_process_reset_count_each_request_once(tmp_path, thread, parent):
    events = records(thread, parent) + [usage(100), usage(200)] + [
        {"type": "event_msg", "payload": {"type": "task_started", "turn_id": "second"}},
        usage(300, last_token_usage=counters(100)),
        usage(300, last_token_usage=counters(100)),
        usage(400, last_token_usage=counters(100)),
        {"type": "event_msg", "payload": {"type": "task_started", "turn_id": "third"}},
        usage(100), usage(200),
    ]

    result = read_thread_usage(
        write(tmp_path, events, thread), thread_id=thread, workspace=Path("/toy"),
    )

    assert result["tokens"] == counters(600)
    assert result["status"] == "observed"


@pytest.mark.parametrize("last", [
    counters(50),  # Unaccounted gap before the first request in the new task.
    counters(200),  # Overlapping usage is equally ambiguous.
    {**counters(100), "cached_input_tokens": 49},
    {**counters(100), "cache_write_input_tokens": 1},
    {**counters(100), "output_tokens": 11},
    {**counters(100), "reasoning_output_tokens": 4},
])
def test_continued_task_requires_exact_baseline_for_every_counter(tmp_path, last):
    events = records() + [usage(200),
        {"type": "event_msg", "payload": {"type": "task_started", "turn_id": "second"}},
        usage(300, last_token_usage=last),
    ]

    with pytest.raises(UsageUnavailable, match="task baseline is ambiguous"):
        read_thread_usage(write(tmp_path, events), thread_id=ROOT, workspace=Path("/toy"))


def test_regressing_task_without_reset_baseline_fails_closed(tmp_path):
    events = records() + [usage(200),
        {"type": "event_msg", "payload": {"type": "task_started", "turn_id": "second"}},
        usage(100, last_token_usage=counters(50)),
    ]

    with pytest.raises(UsageUnavailable, match="task baseline is ambiguous"):
        read_thread_usage(write(tmp_path, events), thread_id=ROOT, workspace=Path("/toy"))


def test_descendants_pending_and_unrelated_payloads(tmp_path):
    write(tmp_path, records() + [usage()])
    child = write(tmp_path, records(CHILD, ROOT), CHILD)
    other = write(tmp_path, records("unrelated", cwd="/elsewhere"), "unrelated")
    with other.open("a") as stream:
        stream.write("not conversation JSON\n")  # Only metadata may be inspected.
    result = read_product_usage(tmp_path, thread_id=ROOT, workspace=Path("/toy"))
    assert result["total_tokens"] == 110
    assert {t["status"] for t in result["threads"]} == {"pending", "observed"}
    with child.open("a") as stream:
        stream.write(json.dumps(usage(200)) + "\n")
        stream.write('{"partial":')
    result = read_product_usage(tmp_path, thread_id=ROOT, workspace=Path("/toy"))
    assert result["total_tokens"] == 330


def test_duplicate_unrelated_session_identity_is_ignored(tmp_path):
    write(tmp_path, records() + [usage()])
    write(tmp_path, records("unrelated", cwd="/elsewhere"), "unrelated-first")
    write(tmp_path, records("unrelated", cwd="/elsewhere"), "unrelated-second")

    result = read_product_usage(tmp_path, thread_id=ROOT, workspace=Path("/toy"))

    assert result["total_tokens"] == 110
    assert [thread["thread_id"] for thread in result["threads"]] == [ROOT]


@pytest.mark.parametrize(("duplicate_id", "parent"), [
    (ROOT, None),
    (CHILD, ROOT),
])
def test_duplicate_selected_session_identity_fails_closed(
    tmp_path, duplicate_id, parent,
):
    write(tmp_path, records() + [usage()])
    if duplicate_id == CHILD:
        write(tmp_path, records(CHILD, ROOT) + [usage()], "child-first")
    write(
        tmp_path,
        records(duplicate_id, parent) + [usage()],
        "duplicate-selected",
    )

    with pytest.raises(UsageUnavailable, match="ambiguous native session identity"):
        read_product_usage(tmp_path, thread_id=ROOT, workspace=Path("/toy"))


@pytest.mark.parametrize("events", [
    records(version="0.153.5") + [usage()],
    records(cwd="/elsewhere") + [usage()],
    records() + [usage(200, last_token_usage=counters(100))],
    records() + [usage(200), usage(100)],
    records() + [usage(total_token_usage={**counters(), "input_tokens": True})],
    records() + [usage(total_token_usage={**counters(), "cached_input_tokens": 101})],
    records() + [usage(total_token_usage={**counters(), "reasoning_output_tokens": 11})],
    records() + [records()[1]],
])
def test_invalid_usage_fails_closed(tmp_path, events):
    with pytest.raises(UsageUnavailable):
        read_thread_usage(write(tmp_path, events), thread_id=ROOT, workspace=Path("/toy"))


def test_descendant_with_different_workspace_is_not_silently_omitted(tmp_path):
    write(tmp_path, records() + [usage()])
    write(tmp_path, records(CHILD, ROOT, cwd="/different") + [usage()], CHILD)
    with pytest.raises(UsageUnavailable, match="binding"):
        read_product_usage(tmp_path, thread_id=ROOT, workspace=Path("/toy"))


def test_symlinks_and_duplicate_keys_fail_closed(tmp_path):
    path = write(tmp_path, records() + [usage()])
    link = tmp_path / "link"
    link.symlink_to(path)
    with pytest.raises(UsageUnavailable):
        read_thread_usage(link, thread_id=ROOT, workspace=Path("/toy"))
    with path.open("a") as stream:
        stream.write('{"type":"event_msg","type":"event_msg"}\n')
    with pytest.raises(UsageUnavailable, match="duplicate"):
        read_thread_usage(path, thread_id=ROOT, workspace=Path("/toy"))

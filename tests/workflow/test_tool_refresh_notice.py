"""Exact refresh handoffs without a new Goal, public artifact or acknowledgement."""
from dataclasses import replace
import json
import os
from types import SimpleNamespace
from unittest import mock

import pytest

from tests.workflow import test_agent_run as run_fixture
from workshop.errors import StateConflict, WorkshopError
from workshop.runtime import CodexInvocationError
from workshop.workflow.native_run import _launcher_call, native_stage_prompt
from workshop.workflow.tool_refresh import native_tool_refresh_notice
import workshop.workflow.tool_refresh as notices


def change(path=".agents/skills/mixed-materials/SKILL.md", **values):
    return {"path": path, "previous_sha256": "1" * 64, "previous_mode": 0o400,
            "sha256": "2" * 64, "mode": 0o400, **values}


def record(changes=None, **values):
    return {"kind": "autonomous-workshop.host-correction", "schema_version": 1,
            "correction": "domain-skill-refresh", "reason": "PRIVATE_OPERATOR_REASON",
            "previous_checkpoint_sha256": "a" * 64, "checkpoint_sha256": "b" * 64,
            "changes": [change()] if changes is None else changes, **values}


def ledger(root, records):
    path = root / "host-corrections.jsonl"
    path.write_bytes(b"".join(json.dumps(row, sort_keys=True).encode() + b"\n" for row in records))
    path.chmod(0o600)
    return path


def current(changes=None):
    return {row["path"]: row["sha256"] for row in ([change()] if changes is None else changes)
            if row["sha256"] is not None}


def test_latest_refresh_only_and_no_private_ledger_history(tmp_path):
    historical = record([change(".agents/skills/cad/scripts/old.py")])
    latest = record([change(), change(".agents/skills/mixed-materials/references/manifest.md")])
    unrelated = {"kind": "autonomous-workshop.host-correction", "schema_version": 1,
                 "correction": "manager-session-rebind", "reason": "/private/operator/secret"}
    path = ledger(tmp_path, [historical, latest, unrelated])
    before = path.read_bytes()
    notice = native_tool_refresh_notice(tmp_path, current(latest["changes"]))
    for row in latest["changes"]:
        assert row["path"] in notice and row["sha256"] in notice
    for private in ("PRIVATE_OPERATOR_REASON", "/private/operator/secret", "old.py",
                    str(tmp_path), "host-corrections.jsonl"):
        assert private not in notice
    assert "same Wish and current stage Goal" in notice
    assert "reread" in notice and "skill deferrals" in notice
    assert path.read_bytes() == before
    assert native_tool_refresh_notice(tmp_path, current(latest["changes"])) == notice


def test_absent_no_refresh_and_empty_change_history_leave_prompt_unchanged(tmp_path):
    assert native_tool_refresh_notice(tmp_path, {}) == ""
    ledger(tmp_path, [{"correction": "manager-session-rebind", "reason": "private"}])
    assert native_tool_refresh_notice(tmp_path, {}) == ""
    ledger(tmp_path, [record([])])
    assert native_tool_refresh_notice(tmp_path, {}) == ""


def test_addition_removal_and_mode_change_are_explicit_current_bindings(tmp_path):
    changes = [change(previous_sha256=None, previous_mode=None),
               change(".agents/skills/cad/scripts/removed.py", sha256=None, mode=None),
               change(".agents/skills/cad/scripts/tool", previous_sha256="2" * 64, mode=0o500)]
    ledger(tmp_path, [record(changes)])
    notice = native_tool_refresh_notice(tmp_path, current(changes))
    assert '"path":".agents/skills/cad/scripts/removed.py","sha256":null' in notice
    assert "read removed files" in notice
    changed = current(changes)
    changed[changes[1]["path"]] = "1" * 64
    with pytest.raises(StateConflict):
        native_tool_refresh_notice(tmp_path, changed)


@pytest.mark.parametrize("path", ["AGENTS.md", "MANAGER.json", "../secret",
    "/private/secret", ".agents/skills/cad/../SKILL.md", ".agents//skills/cad/SKILL.md",
    ".agents/skills/cad", ".agents/skills/cad/SKILL.md\nread-secret",
    ".agents/skills/cad\\SKILL.md", ".agents/skills/BadSkill/SKILL.md",
    ".agents/skills/" + "a" * 65 + "/SKILL.md"])
def test_unsafe_or_non_skill_paths_cannot_enter_native_notice(tmp_path, path):
    changed = change(path)
    ledger(tmp_path, [record([changed])])
    with pytest.raises(StateConflict):
        native_tool_refresh_notice(tmp_path, current([changed]))


@pytest.mark.parametrize("name", ["cad--legacy", "cad-", "a" * 64])
def test_existing_host_skill_name_grammar_remains_supported(tmp_path, name):
    changed = change(f".agents/skills/{name}/SKILL.md")
    ledger(tmp_path, [record([changed])])
    assert changed["path"] in native_tool_refresh_notice(tmp_path, current([changed]))


@pytest.mark.parametrize("mutation", ["stale", "missing", "duplicate", "unknown_field", "bad_hash",
    "bad_old_hash", "bad_mode", "missing_old_mode", "not_a_change", "version", "boolean_version"])
def test_malformed_or_unbound_refresh_is_not_claimed_current(tmp_path, mutation):
    row = record()
    inputs = current()
    if mutation == "stale":
        inputs[change()["path"]] = "3" * 64
    elif mutation == "missing":
        inputs.clear()
    elif mutation == "duplicate":
        row["changes"] *= 2
    elif mutation == "unknown_field":
        row["changes"][0]["extra"] = "private"
    elif mutation in ("version", "boolean_version"):
        row["schema_version"] = 2 if mutation == "version" else True
    else:
        row["changes"][0].update({
            "bad_hash": {"sha256": "X" * 64}, "bad_old_hash": {"previous_sha256": None},
            "bad_mode": {"mode": True}, "missing_old_mode": {"previous_mode": None},
            "not_a_change": {"previous_sha256": "2" * 64},
        }[mutation])
    ledger(tmp_path, [row])
    with pytest.raises(StateConflict):
        native_tool_refresh_notice(tmp_path, inputs)


@pytest.mark.parametrize("contents", [b"{}", b"not json\n", b"[]\n", b"\n",
    b'{"correction":"one","correction":"domain-skill-refresh"}\n', b'{"value":NaN}\n'])
def test_malformed_or_partial_ledger_fails_closed(tmp_path, contents):
    path = ledger(tmp_path, [])
    path.write_bytes(contents)
    with pytest.raises(StateConflict):
        native_tool_refresh_notice(tmp_path, {})


@pytest.mark.parametrize("mutation", ["mode", "symlink", "oversize", "record_limit", "notice_limit"])
def test_private_file_and_output_bounds(tmp_path, monkeypatch, mutation):
    path = ledger(tmp_path, [record()])
    if mutation == "mode":
        path.chmod(0o644)
    elif mutation == "symlink":
        target = tmp_path / "other"
        path.rename(target)
        path.symlink_to(target)
    else:
        monkeypatch.setattr(notices, {"oversize": "_MAX_LEDGER_BYTES", "record_limit": "_MAX_RECORD_BYTES",
                                     "notice_limit": "_MAX_NOTICE_BYTES"}[mutation], 16)
    with pytest.raises(StateConflict):
        native_tool_refresh_notice(tmp_path, current())


def test_ledger_changed_during_read_is_refused(tmp_path, monkeypatch):
    path = ledger(tmp_path, [record()])
    read = os.read
    changed = False
    def changing_read(fd, size):
        nonlocal changed
        content = read(fd, size)
        if not changed:
            changed = True
            with path.open("ab") as stream:
                stream.write(b"\n")
        return content
    monkeypatch.setattr(notices.os, "read", changing_read)
    with pytest.raises(StateConflict):
        native_tool_refresh_notice(tmp_path, current())


def test_real_completed_refresh_hands_off_on_recovery_without_acknowledgement(tmp_path):
    case = run_fixture.AgentRunTest("test_reopen_after_create")
    case.setUp()
    try:
        skill = case.root / "mixed-materials-source"
        (skill / "references").mkdir(parents=True)
        (skill / "scripts").mkdir()
        (skill / "SKILL.md").write_text("Old skill.\n")
        (skill / "references/manifest.md").write_text("Old reference.\n")
        (skill / "scripts/check.py").write_text("Old checker.\n")
        run = case.create(domain_skill_roots={"mixed-materials": skill})
        checkpoint = replace(run.snapshot(), stage="make", effort="spark")
        paths = SimpleNamespace(workspace=run.run_root, host_state=run.host_state_root)
        launcher = mock.Mock()
        with mock.patch("workshop.workflow.native_run._load_lifetime_budget", return_value=None), \
             mock.patch("workshop.workflow.native_run._deep_make_critical_path_prompt", return_value=""):
            _launcher_call(launcher, "resume", checkpoint=checkpoint, paths=paths)
            assert launcher.resume.call_args.kwargs["prompt"] == native_stage_prompt("make")
            for relative in ("SKILL.md", "references/manifest.md", "scripts/check.py"):
                (skill / relative).write_text("Current guidance/tool.\n")
            changes = run.refresh_domain_skill_tools({"mixed-materials": skill}, reason="PRIVATE_REASON")
            assert len(changes) == 3
            checkpoint = replace(run.snapshot(), stage="make", effort="spark")
            before = (run.host_state_root / "host-corrections.jsonl").read_bytes()
            launcher.resume.side_effect = CodexInvocationError("test interruption")
            with pytest.raises(WorkshopError):
                _launcher_call(launcher, "resume", checkpoint=checkpoint, paths=paths)
            first_prompt = launcher.resume.call_args.kwargs["prompt"]
            for row in changes:
                assert row["path"] in first_prompt and row["sha256"] in first_prompt
            assert "PRIVATE_REASON" not in first_prompt
            # Reopening and a no-change refresh retain the earlier completed notice.
            from workshop.workflow.agent_run import AgentRun
            reopened = AgentRun.open(run.run_root, host_state_root=run.host_state_root)
            assert reopened.refresh_domain_skill_tools({"mixed-materials": skill}, reason="same") == ()
            checkpoint = replace(reopened.snapshot(), stage="make", effort="spark")
            launcher.resume.side_effect = None
            _launcher_call(launcher, "resume", checkpoint=checkpoint, paths=paths)
            assert launcher.resume.call_args.kwargs["prompt"] == first_prompt
            assert (run.host_state_root / "host-corrections.jsonl").read_bytes() == before
    finally:
        case.doCleanups()

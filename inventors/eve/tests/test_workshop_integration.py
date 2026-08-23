"""Integration tests for Eve's real Workshop execution boundaries."""
from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path
from unittest import mock

import pytest

from inventor_workshop import Clockwork, HttpResponse
from inventor_workshop.errors import ContractError

from eve import config, workshop_bridge, journal, send
from eve.queue import Game


class RecordingTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, method, url, headers, body, timeout):
        self.calls.append((method, url, headers, body, timeout))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


@pytest.fixture()
def sendable_game(tmp_path: Path):
    games = tmp_path / "games"
    game_dir = games / "vigil-station"
    build = game_dir / "build"
    build.mkdir(parents=True)
    (game_dir / "rules.md").write_text("# Vigil Station\n", encoding="utf-8")
    (build / "rail.stl").write_bytes(b"solid rail\nendsolid rail\n")
    cfg = config.Config(
        root=tmp_path,
        games_dir=games,
        loops_dir=tmp_path / "loops",
        queue_path=tmp_path / "loops" / "queue.json",
        journal_path=tmp_path / "loops" / "journal.jsonl",
        ledger_path=tmp_path / "loops" / "ledger.json",
    )
    cfg.shop_api = "https://panda-social-api.autonomous.ai"
    cfg.shop_token = "test-bearer"
    cfg.shop_owner_id = "owner-eve"
    cfg.shop_configured = True
    game = Game(
        slug="vigil-station",
        title="Vigil Station",
        stage="ship",
        identity="like Hive plus a printed indexed rail",
        idea="Move one indexed rail to redirect a shared marker.",
        mech="a printed indexed rail",
    )
    workshop_bridge.snapshot_built_game(game_dir, title=game.title)
    return cfg, game, game_dir


def _draft_design():
    return {
        "id": "design-1",
        "slug": "vigil-station",
        "owner_id": "owner-eve",
        "root_id": "design-1",
        "current_history_id": "history-1",
        "published_history_id": None,
        "status": "draft",
        "project_url": "https://cdn.example/vigil-station/",
    }


def _response(status, document):
    return HttpResponse(status, {}, json.dumps(document).encode("utf-8"))


def test_send_runs_through_workshop_and_persists_exact_stamp(sendable_game):
    cfg, game, game_dir = sendable_game
    transport = RecordingTransport([_response(201, _draft_design())])

    real_builder = workshop_bridge.pack_artifact
    with mock.patch.object(
        workshop_bridge,
        "pack_artifact",
        wraps=real_builder,
    ) as workshop_pack_builder:
        result = send.send_design(cfg, game, transport=transport)

    assert result["ok"] is True
    assert result["send_state"] == "succeeded"
    assert workshop_pack_builder.call_count == 1
    assert [call[0] for call in transport.calls] == ["POST"]
    assert (game_dir / "project.json").is_file(), \
        "Make binds the Shop Door manifest into the selected artifact"

    packed = Path(result["pack"]["path"])
    with zipfile.ZipFile(packed) as archive:
        assert archive.namelist()[-1] == "_inventor-artifact.json"
        assert "project.json" in archive.namelist()
        assert all(item.compress_type == zipfile.ZIP_STORED for item in archive.infolist())

    persisted = json.loads((game_dir / "sent.json").read_text())
    assert persisted["send_id"] == result["send_id"]
    assert persisted["stamp"] == result["stamp"]
    assert persisted["stamp"]["pack_sha256"] == result["pack"]["pack_sha256"]
    assert persisted["stamp"]["artifact_sha256"] == result["pack"]["artifact_sha256"]
    resnapshot = workshop_bridge.snapshot_built_game(game_dir)
    assert resnapshot["artifact_sha256"] == result["pack"]["artifact_sha256"]

    intent = workshop_bridge.send_state(cfg, game.slug)
    assert intent["state"] == "succeeded"
    assert intent["receipt"] == persisted["stamp"]
    events = journal.open_journal(cfg).read()
    recorded = [row for row in events if row.get("event") == "sent_shop"]
    assert recorded[-1]["send_id"] == result["send_id"]
    assert recorded[-1]["stamp"] == result["stamp"]
    assert recorded[-1]["producer"] == "inventor_workshop"


def test_ambiguous_send_is_durable_and_second_call_cannot_post(sendable_game):
    cfg, game, game_dir = sendable_game
    transport = RecordingTransport([OSError("connection reset after upload")])

    first = send.send_design(cfg, game, transport=transport)
    # Even changed bytes keep the same logical product binding. A new Pack
    # must not bypass the unresolved effect and create a duplicate design.
    (game_dir / "rules.md").write_text(
        "# Vigil Station\n\ncorrected after the lost response\n",
        encoding="utf-8",
    )
    second = send.send_design(cfg, game, transport=transport)

    assert first["blocked"] is True and first["state"] == "unknown"
    assert second["blocked"] is True and second["state"] == "unknown"
    assert first["send_id"] == second["send_id"]
    assert len(transport.calls) == 1, \
        "Sender must fence a retry after the Shop Door may have accepted the first POST"
    assert not (game_dir / "sent.json").exists()

    projection = json.loads(
        (game_dir / workshop_bridge.SEND_PROJECTION_NAME).read_text()
    )
    assert projection["authority"] == "state/clockwork.sqlite3"
    assert projection["send_id"] == first["send_id"]
    assert projection["state"] == "unknown"
    intent = workshop_bridge.send_state(cfg, game.slug)
    assert intent["state"] == "unknown"
    assert intent["effect_token"] is None


def test_offline_shop_skip_does_not_create_clockwork_state(sendable_game):
    cfg, game, _game_dir = sendable_game
    cfg.shop_token = ""
    cfg.shop_configured = False

    result = send.send_design(cfg, game)

    assert result["skipped"] is True
    assert not (cfg.root / "state" / workshop_bridge.CLOCKWORK_STATE_NAME).exists()
    assert not (cfg.root / "state" / workshop_bridge.LEGACY_STATE_NAME).exists()


def test_unpackable_bytes_are_a_graceful_local_refusal(sendable_game):
    cfg, game, game_dir = sendable_game
    (game_dir / "notes.txt").write_text(
        "accidentally copied bot token 1234567:" + ("A" * 32),
        encoding="utf-8",
    )
    transport = RecordingTransport([])

    result = send.send_design(cfg, game, transport=transport)

    assert result["ok"] is False
    assert result["blocked"] is False
    assert "secret rule" in result["error"]
    assert transport.calls == []
    assert not (game_dir / "sent.json").exists()
    assert not (cfg.root / "state" / workshop_bridge.CLOCKWORK_STATE_NAME).exists()
    events = journal.open_journal(cfg).read()
    assert events[-1]["event"] == "send_refused"


def test_send_refuses_when_pack_differs_from_make_selection(sendable_game):
    cfg, game, game_dir = sendable_game
    transport = RecordingTransport([])

    with mock.patch.object(
        workshop_bridge,
        "build_pack",
        return_value={"artifact_sha256": "0" * 64},
    ):
        result = send.send_design(cfg, game, transport=transport)

    assert result["ok"] is False
    assert result["blocked"] is False
    assert "changed between Make selection and Pack staging" in result["error"]
    assert transport.calls == []
    assert not (game_dir / "sent.json").exists()
    assert not (cfg.root / "state" / workshop_bridge.CLOCKWORK_STATE_NAME).exists()


def test_unsafe_slug_is_refused_before_any_path_or_remote_effect(sendable_game):
    cfg, game, _game_dir = sendable_game
    game.slug = "../escape"
    transport = RecordingTransport([])

    result = send.send_to_shop(cfg, game)

    assert result["ok"] is False
    assert "send slug" in result["error"]
    assert transport.calls == []
    assert not (cfg.root / "escape" / "README.md").exists()


@pytest.mark.skipif(
    not hasattr(os, "mkfifo") or not hasattr(os, "symlink"),
    reason="special-file staging checks require POSIX",
)
@pytest.mark.parametrize("kind", ["fifo", "symlink"])
def test_staging_refuses_fifo_and_symlink_without_transport(sendable_game, kind):
    cfg, game, game_dir = sendable_game
    unsafe = game_dir / ("agent.pipe" if kind == "fifo" else "rules-link.md")
    if kind == "fifo":
        os.mkfifo(unsafe)
    else:
        os.symlink(game_dir / "rules.md", unsafe)
    transport = RecordingTransport([])

    result = send.send_design(cfg, game, transport=transport)

    assert result["ok"] is False
    assert (
        kind in result["error"]
        or "special file" in result["error"]
        or "not a regular file" in result["error"]
    )
    assert transport.calls == []
    assert not (game_dir / "sent.json").exists()


@pytest.mark.parametrize("legacy_name", workshop_bridge.LEGACY_STATE_NAMES)
def test_existing_legacy_state_file_is_reused_without_splitting(
    sendable_game, legacy_name
):
    cfg, game, game_dir = sendable_game
    state = cfg.root / "state"
    state.mkdir()
    legacy = state / legacy_name
    Clockwork(legacy)

    result = send.send_design(
        cfg,
        game,
        transport=RecordingTransport([_response(201, _draft_design())]),
    )

    assert result["ok"] is True
    assert workshop_bridge.workshop_state_path(cfg) == legacy
    assert result["clockwork_state"] == str(legacy)
    projection = json.loads(
        (game_dir / workshop_bridge.SEND_PROJECTION_NAME).read_text()
    )
    assert projection["authority"] == "state/%s" % legacy_name
    assert not (state / workshop_bridge.CLOCKWORK_STATE_NAME).exists()


@pytest.mark.parametrize("legacy_name", workshop_bridge.LEGACY_PACK_DIRECTORIES)
def test_existing_legacy_pack_directory_is_reused(sendable_game, legacy_name):
    cfg, game, _game_dir = sendable_game
    legacy_packets = cfg.root / "state" / legacy_name
    legacy_packets.mkdir(parents=True)

    result = send.send_design(
        cfg,
        game,
        transport=RecordingTransport([_response(201, _draft_design())]),
    )

    assert result["ok"] is True
    assert Path(result["packet"]["path"]).parent == legacy_packets
    assert not (
        cfg.root / "state" / workshop_bridge.PACK_DIRECTORY
    ).exists()


def test_two_state_files_fail_closed(sendable_game):
    cfg, _game, _game_dir = sendable_game
    state = cfg.root / "state"
    state.mkdir()
    (state / workshop_bridge.LEGACY_STATE_NAME).write_bytes(b"legacy")
    (state / workshop_bridge.CLOCKWORK_STATE_NAME).write_bytes(b"current")

    with pytest.raises(ContractError, match="multiple Eve Clockwork state"):
        workshop_bridge.clockwork_path(cfg)


def test_launch_and_publish_modules_are_compatibility_only_aliases():
    from eve import launch, publish

    assert launch.launch_design is send.send_design
    assert launch.launch_to_portal is send.send_to_shop
    assert publish.import_design is send.send_design
    assert publish.publish_to_store is send.send_to_shop

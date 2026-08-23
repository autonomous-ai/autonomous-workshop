"""Integration tests for Eve's real Foundation execution boundaries."""
from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path
from unittest import mock

import pytest

from inventor_core.panda import HttpResponse

from eve import config, core_adapter, journal, publish
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
def publication(tmp_path: Path):
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
    cfg.store_base_url = "https://panda-social-api.autonomous.ai"
    cfg.store_bearer = "test-bearer"
    cfg.panda_owner_id = "owner-eve"
    cfg.store_configured = True
    game = Game(
        slug="vigil-station",
        title="Vigil Station",
        stage="ship",
        identity="like Hive plus a printed indexed rail",
        idea="Move one indexed rail to redirect a shared marker.",
        mech="a printed indexed rail",
    )
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


def test_store_import_runs_through_core_and_persists_exact_receipt(publication):
    cfg, game, game_dir = publication
    transport = RecordingTransport([_response(201, _draft_design())])

    real_builder = core_adapter.core_artifacts.build_publish_packet
    with mock.patch.object(
        core_adapter.core_artifacts,
        "build_publish_packet",
        wraps=real_builder,
    ) as core_packet_builder:
        result = publish.import_design(cfg, game, transport=transport)

    assert result["ok"] is True
    assert core_packet_builder.call_count == 1
    assert [call[0] for call in transport.calls] == ["POST"]
    assert not (game_dir / "project.json").exists(), \
        "project.json is injected into staging, never Eve's source tree"

    packet = Path(result["packet"]["path"])
    with zipfile.ZipFile(packet) as archive:
        assert archive.namelist()[-1] == "_inventor-artifact.json"
        assert "project.json" in archive.namelist()
        assert all(item.compress_type == zipfile.ZIP_STORED for item in archive.infolist())

    persisted = json.loads((game_dir / "published.json").read_text())
    assert persisted["intent_id"] == result["intent_id"]
    assert persisted["receipt"] == result["receipt"]
    assert persisted["receipt"]["packet_sha256"] == result["packet"]["packet_sha256"]
    assert persisted["receipt"]["artifact_sha256"] == result["packet"]["artifact_sha256"]

    intent = core_adapter.publication_state(cfg, game.slug)
    assert intent["state"] == "succeeded"
    assert intent["receipt"] == persisted["receipt"]
    events = journal.open_journal(cfg).read()
    recorded = [row for row in events if row.get("event") == "published_store"]
    assert recorded[-1]["intent_id"] == result["intent_id"]
    assert recorded[-1]["receipt"] == result["receipt"]
    assert recorded[-1]["producer"] == "inventor_core"


def test_ambiguous_import_is_durable_and_second_call_cannot_post(publication):
    cfg, game, game_dir = publication
    transport = RecordingTransport([OSError("connection reset after upload")])

    first = publish.import_design(cfg, game, transport=transport)
    # Even changed bytes keep the same logical product binding. A new packet
    # must not bypass the unresolved effect and create a duplicate design.
    (game_dir / "rules.md").write_text(
        "# Vigil Station\n\ncorrected after the lost response\n",
        encoding="utf-8",
    )
    second = publish.import_design(cfg, game, transport=transport)

    assert first["blocked"] is True and first["state"] == "unknown"
    assert second["blocked"] is True and second["state"] == "unknown"
    assert first["intent_id"] == second["intent_id"]
    assert len(transport.calls) == 1, \
        "core must fence a retry after Panda may have accepted the first POST"
    assert not (game_dir / "published.json").exists()

    projection = json.loads(
        (game_dir / core_adapter.CORE_PUBLICATION_PROJECTION).read_text()
    )
    assert projection["authority"] == "state/inventor-core.sqlite3"
    assert projection["intent_id"] == first["intent_id"]
    assert projection["state"] == "unknown"
    intent = core_adapter.publication_state(cfg, game.slug)
    assert intent["state"] == "unknown"
    assert intent["effect_token"] is None


def test_offline_store_skip_does_not_create_core_state(publication):
    cfg, game, _game_dir = publication
    cfg.store_bearer = ""
    cfg.store_configured = False

    result = publish.import_design(cfg, game)

    assert result["skipped"] is True
    assert not (cfg.root / "state" / core_adapter.CORE_STATE_NAME).exists()


def test_unpublishable_bytes_are_a_graceful_local_refusal(publication):
    cfg, game, game_dir = publication
    (game_dir / "notes.txt").write_text(
        "accidentally copied bot token 1234567:" + ("A" * 32),
        encoding="utf-8",
    )
    transport = RecordingTransport([])

    result = publish.import_design(cfg, game, transport=transport)

    assert result["ok"] is False
    assert result["blocked"] is False
    assert "secret rule" in result["error"]
    assert transport.calls == []
    assert not (game_dir / "published.json").exists()
    events = journal.open_journal(cfg).read()
    assert events[-1]["event"] == "publish_refused"


def test_unsafe_slug_is_refused_before_any_path_or_remote_effect(publication):
    cfg, game, _game_dir = publication
    game.slug = "../escape"
    transport = RecordingTransport([])

    result = publish.publish_to_store(cfg, game)

    assert result["ok"] is False
    assert "publication slug" in result["error"]
    assert transport.calls == []
    assert not (cfg.root / "escape" / "README.md").exists()


@pytest.mark.skipif(
    not hasattr(os, "mkfifo") or not hasattr(os, "symlink"),
    reason="special-file staging checks require POSIX",
)
@pytest.mark.parametrize("kind", ["fifo", "symlink"])
def test_staging_refuses_fifo_and_symlink_without_transport(publication, kind):
    cfg, game, game_dir = publication
    unsafe = game_dir / ("agent.pipe" if kind == "fifo" else "rules-link.md")
    if kind == "fifo":
        os.mkfifo(unsafe)
    else:
        os.symlink(game_dir / "rules.md", unsafe)
    transport = RecordingTransport([])

    result = publish.import_design(cfg, game, transport=transport)

    assert result["ok"] is False
    assert kind in result["error"] or "special file" in result["error"]
    assert transport.calls == []
    assert not (game_dir / "published.json").exists()

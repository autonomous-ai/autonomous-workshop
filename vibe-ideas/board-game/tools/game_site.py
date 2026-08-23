#!/usr/bin/env python3
"""Build and serve the table-run replay and hot-seat play website.

The replay is static data, generated from the recorded choice indices by the
same engine that produced the table. Hot-seat play stays server-backed for the
same reason: translating every game's Python rules into JavaScript would create
a second rulebook that can silently disagree with the gate.

Usage:
    python board-game/tools/game_site.py build board-game/ideas/<slug>
    python board-game/tools/game_site.py serve board-game/ideas/<slug>
"""

from __future__ import annotations

import argparse
import copy
import json
import random
import re
import secrets
import shutil
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

import playtest  # noqa: E402


ASSETS = Path(__file__).resolve().parents[1] / "site"


def _idea_dir(path: Path) -> Path:
    return path.parent if path.is_file() else path


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _public_frame(eng, state, turn: int, previous: dict | None = None) -> dict:
    over = bool(eng.is_over(state))
    actor = None if over else int(eng.player_to_move(state))
    moves = [] if over else list(eng.legal_moves(state))
    # observation() is the engine's visibility boundary. Using the active
    # seat's view makes replay useful for hidden-information games without
    # baking privileged state into a static website.
    observed_for = 0 if actor is None else actor
    observation = playtest.canonical(
        playtest.observe(eng, copy.deepcopy(state), observed_for))
    return {
        "turn": turn,
        "actor": actor,
        "observed_for": observed_for,
        "over": over,
        "scores": [round(float(score), 2) for score in eng.scores(state)],
        "winners": list(eng.winners(state)) if over else [],
        "observation": observation,
        "legal_moves": [str(move) for move in moves],
        "previous": previous,
    }


def replay_frames(eng, session: dict) -> list[dict]:
    """Replay a recorded session and keep one visible frame per decision."""
    rng = random.Random(session["seed"])
    state = eng.new_game(session["seats"], rng)
    frames = [_public_frame(eng, state, 0)]
    for turn, entry in enumerate(session.get("moves", [])):
        moves = eng.legal_moves(state)
        choice = int(entry["choice"])
        if choice >= len(moves) or str(moves[choice]) != entry["move"]:
            raise playtest.EngineBroken(
                f"site replay: turn {turn} no longer matches the engine")
        previous = {
            "seat": entry.get("seat"),
            "move": entry.get("move", ""),
            "why": entry.get("why", ""),
            "decision": entry.get("decision", "unstated"),
            "note": entry.get("note"),
            "by": entry.get("by", "player"),
        }
        try:
            state = eng.apply_move(state, moves[choice], rng)
        except Exception as exc:
            if not playtest.is_undefined(exc):
                raise
            stopped = _public_frame(eng, state, turn + 1, previous)
            stopped["undefined"] = str(exc)
            frames.append(stopped)
            break
        frames.append(_public_frame(eng, state, turn + 1, previous))
    return frames


def _session_path(table_dir: Path, value: str) -> Path:
    path = Path(value)
    if path.is_file():
        return path
    candidate = table_dir / path.name
    if candidate.is_file():
        return candidate
    raise FileNotFoundError(value)


def collect_runs(idea_dir: Path, eng) -> list[dict]:
    table_dir = idea_dir / "playtest" / "table"
    runs = []
    for summary_path in sorted(table_dir.glob("run_*.json"),
                               key=lambda path: path.stat().st_mtime,
                               reverse=True):
        summary = _json(summary_path)
        games = []
        stale_games = 0
        for record in summary.get("games", []):
            try:
                session_path = _session_path(table_dir, record["session"])
                session = _json(session_path)
                frames = replay_frames(eng, session)
            except (FileNotFoundError, KeyError, ValueError,
                    playtest.EngineBroken) as exc:
                # A rules rework invalidates old choice indices. Keeping those
                # games in the selector would make an obsolete run look like
                # current evidence. Count it on the run, but do not offer it.
                stale_games += 1
                continue
            games.append({**record, "session": session_path.name,
                          "frames": frames})
        if games:
            runs.append({
                "name": summary_path.stem.removeprefix("run_"),
                "model": summary.get("model", "unknown"),
                "wire": summary.get("wire", "unknown"),
                "seconds": summary.get("seconds"),
                "usage": summary.get("usage", {}),
                "rules_questions": summary.get("rules_questions", []),
                "debriefs": summary.get("debriefs", []),
                "stale_games_omitted": stale_games,
                "games": games,
            })
    return runs


def build_site(path: Path) -> Path:
    idea_dir = _idea_dir(path.resolve())
    idea = _json(idea_dir / "idea.json")
    eng = playtest.load_engine(idea_dir / "playtest" / "engine.py")
    output = idea_dir / "playtest" / "site"
    output.mkdir(parents=True, exist_ok=True)
    for name in ("index.html", "app.js", "styles.css"):
        shutil.copyfile(ASSETS / name, output / name)
    data = {
        "slug": getattr(eng, "SLUG", idea_dir.name),
        "title": idea.get("title", idea_dir.name),
        "concept": idea.get("concept", ""),
        "players": idea.get("players", {}),
        "rules": idea.get("rules", {}),
        "runs": collect_runs(idea_dir, eng),
    }
    (output / "data.json").write_text(json.dumps(data, indent=2),
                                       encoding="utf-8")
    # Keep data.json for normal HTTP serving and diagnostics, but also embed
    # the same payload so a file:// link can replay games without a browser
    # blocking a local fetch. Escape closing tags before placing JSON inside a
    # script element; game text is allowed to contain arbitrary prose.
    index_path = output / "index.html"
    embedded = json.dumps(data).replace("</", "<\\/")
    index = index_path.read_text(encoding="utf-8")
    marker = '<script src="app.js"></script>'
    index = index.replace(
        marker,
        f'<script id="game-data" type="application/json">{embedded}</script>\n'
        f'  {marker}',
    )
    index_path.write_text(index, encoding="utf-8")
    return index_path


class GameStore:
    """In-memory hot-seat games, always advanced by the source engine."""

    def __init__(self, eng):
        self.eng = eng
        self.games: dict[str, dict] = {}

    def new(self, seats: int, seed: int) -> dict:
        problems = (playtest.validate_engine(self.eng)
                    or playtest.table_guard(self.eng, seats, seed))
        if problems:
            raise ValueError("; ".join(problems))
        rng = random.Random(seed)
        game_id = secrets.token_urlsafe(12)
        self.games[game_id] = {
            "state": self.eng.new_game(seats, rng), "rng": rng,
            "turn": 0, "history": [],
        }
        return {"game_id": game_id,
                "frame": self.frame(game_id)}

    def frame(self, game_id: str) -> dict:
        game = self.games[game_id]
        previous = game["history"][-1] if game["history"] else None
        return _public_frame(self.eng, game["state"], game["turn"], previous)

    def move(self, game_id: str, choice: int) -> dict:
        game = self.games[game_id]
        state = game["state"]
        if self.eng.is_over(state):
            raise ValueError("the game is already over")
        moves = self.eng.legal_moves(state)
        if choice < 0 or choice >= len(moves):
            raise ValueError(f"choice must be between 0 and {len(moves) - 1}")
        seat = int(self.eng.player_to_move(state))
        move = moves[choice]
        game["history"].append({"seat": seat, "move": str(move),
                                "by": "human"})
        game["state"] = self.eng.apply_move(state, move, game["rng"])
        game["turn"] += 1
        return self.frame(game_id)


def serve(path: Path, host: str, port: int) -> None:
    idea_dir = _idea_dir(path.resolve())
    site = build_site(idea_dir).parent
    eng = playtest.load_engine(idea_dir / "playtest" / "engine.py")
    store = GameStore(eng)

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(site), **kwargs)

        def log_message(self, fmt, *args):
            sys.stderr.write("site  " + fmt % args + "\n")

        def _reply(self, status: int, body: dict) -> None:
            raw = json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_POST(self):
            try:
                size = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(size) or b"{}")
                route = urlparse(self.path).path
                if route == "/api/games":
                    result = store.new(int(body["seats"]), int(body["seed"]))
                else:
                    match = re.fullmatch(r"/api/games/([^/]+)/moves", route)
                    if not match:
                        self._reply(404, {"error": "not found"})
                        return
                    result = {"frame": store.move(match.group(1),
                                                   int(body["choice"]))}
                self._reply(200, result)
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                self._reply(400, {"error": str(exc)})

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"GAME SITE http://{host}:{server.server_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("build", "serve"):
        item = sub.add_parser(command)
        item.add_argument("idea_dir", type=Path)
        if command == "serve":
            item.add_argument("--host", default="127.0.0.1")
            item.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    if args.command == "build":
        print(f"GAME SITE {build_site(args.idea_dir)}")
    else:
        serve(args.idea_dir, args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

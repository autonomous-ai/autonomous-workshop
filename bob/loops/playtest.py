"""Playtest kit — the engine contract, the sim runner, and the table stub.

THE ENGINE CONTRACT (an agent writes this file; code judges it)
===============================================================

``games/<slug>/playtest/engine.py`` is a plain Python module (stdlib only)
exposing exactly:

- ``new_game(n_players, seed) -> state`` — fresh game state; ``seed`` makes
  every source of in-game randomness reproducible.
- ``player_to_move(state) -> int`` — seat index 0..n-1.
- ``legal_moves(state) -> list`` — every legal move, [] only when over.
- ``apply(state, move) -> state`` — NEW state; never mutate the input
  (policies branch from one state many times).
- ``is_over(state) -> bool``
- ``winners(state) -> list[int]`` — [] while running; one seat for a win;
  several for a shared win/draw.
- ``scores(state) -> list[float]`` — per-seat progress-toward-winning, every
  turn. This trace is what lead-change/drama/greedy metrics read; a game
  whose scores only move at the end will measure as flat, because to the
  instruments it IS flat.
- ``observation(state, seat) -> str`` — what THIS seat may know, as prose.
  LLM table seats see only this (hidden info stays hidden by construction).
- ``ASSUMPTIONS: list[str]`` — every rules gap the engine writer had to
  close, REGISTERED instead of guessed. "A rules gap found while writing
  the engine is worth more than any number below" (vibe-ideas §1.5).
- ``IDEA_SHA: str`` — sha256 hex of the exact ``idea.json`` the engine was
  written from. The loader refuses a mismatch: vibe-ideas got burned twice
  by mtime-only staleness checks, so verdict-to-version binding is by
  content hash, in the artifact itself (the stale-verdict receipt).

Everything downstream — ``loops/simmetrics.simulate`` and the LLM table —
drives the game ONLY through these calls. The table loop is code, not an
agent, and seats choose moves BY INDEX from ``legal_moves``: a seat cannot
cheat, misremember a rule, or soften a dull game, because the process has
no way to express any of that.

TABLE REPORT FORMAT (interface pinned here; loop lands with the invent-loop
builder — this module owns only the sim half):

- transcript: ``games/<slug>/playtest/table_<k>.json`` —
  ``{"idea_sha", "seats": [{"seat", "model", "persona"}], "question",
  "n_players", "seed", "moves": [{"turn", "seat", "legal_count",
  "choice_index", "comment"}], "verdicts": {"would_play_again": [...],
  "agency": [...], "confusion_events": [...]}}``. Replayable from seed +
  choice indices, so a mid-run engine edit is caught.
- summary: ``games/<slug>/playtest/table_report.json`` — one row per table:
  question asked, per-seat votes, confusion count, idea_sha.
"""

import ast
import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile

from loops import simmetrics


class EngineContractError(RuntimeError):
    """The engine module does not honor the contract in this file's docstring."""


class StaleEngineError(EngineContractError):
    """Engine was written from a different idea.json than the one on disk.

    Stale-verdict receipt: any number computed from this engine would judge
    a game that no longer exists. Regenerate the engine from the current
    idea.json (build_engine_prompt gives the writer everything it needs).
    """


#: Every attribute an engine must expose (IDEA_SHA/ASSUMPTIONS checked apart).
ENGINE_API = ("new_game", "player_to_move", "legal_moves", "apply",
              "is_over", "winners", "scores", "observation")

#: Import whitelist for agent-written engines. An engine is a pure rules
#: module, so the only stdlib it legitimately needs is deterministic
#: data/algorithm plumbing. The engine execs IN-PROCESS (load_engine), so
#: anything past this list — io, os, process, dynamic import, reflection —
#: is a lever on the scorer itself: a reward-seeking engine could
#: monkeypatch loops.simmetrics or rewrite state/ (review 2026-08-22).
#: This lint is the minimal hardening; the real fix — subprocess isolation
#: — is designed in knowledge/PROPOSALS.md (2026-08-22) and not yet built.
ENGINE_IMPORT_WHITELIST = frozenset(
    {"random", "math", "itertools", "collections", "functools", "copy",
     "typing"})

#: Tokens no engine has any business containing, anywhere in the file:
#: file/OS access, process spawning, dynamic import, and the reflection
#: calls that reach the loader's globals. Word-boundary regexes so prose
#: like "those." or "open information" cannot false-positive; a hit in a
#: docstring still refuses — fail-closed, an engine is cheap to regenerate.
ENGINE_BANNED_TOKENS = (
    ("open(", re.compile(r"\bopen\s*\(")),
    ("os.", re.compile(r"\bos\s*\.")),
    ("sys.", re.compile(r"\bsys\s*\.")),
    ("subprocess", re.compile(r"\bsubprocess\b")),
    ("importlib", re.compile(r"\bimportlib\b")),
    ("__import__", re.compile(r"__import__")),
    ("eval(", re.compile(r"\beval\s*\(")),
    ("exec(", re.compile(r"\bexec\s*\(")),
    ("globals(", re.compile(r"\bglobals\s*\(")),
    ("setattr(", re.compile(r"\bsetattr\s*\(")),
)


def _home(home=None):
    """Resolve BOB_HOME. Read env INSIDE the function — never at import time
    (CONTRACTS §6: import-time env reads make modules untestable)."""
    if home:
        return os.path.abspath(home)
    env = os.environ.get("BOB_HOME")
    if env:
        return os.path.abspath(env)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _game_dir(slug, home=None):
    return os.path.join(_home(home), "games", slug)


def _atomic_write_json(path, payload):
    """tmp + os.replace in the destination dir — never a cross-device rename,
    never a half-written JSON visible to a concurrent reader (CONTRACTS §6)."""
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def idea_sha(slug, home=None):
    """sha256 hex of games/<slug>/idea.json — the version every verdict binds to."""
    path = os.path.join(_game_dir(slug, home), "idea.json")
    if not os.path.exists(path):
        raise FileNotFoundError(
            "%s not found — the game must be ruled (idea.json written) "
            "before the playtest kit can run" % path)
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def _lint_engine_source(path, source):
    """Refuse engine source that reaches outside the rules sandbox.

    Runs BEFORE exec — a banned construct that already executed is not a
    refusal, it is a breach. Raises EngineContractError naming the
    offending line so the invent loop can park the game with a receipt.
    Two passes: banned tokens by line (names the line), then imports via
    ast (catches function-level imports too, not just module top).
    """
    for lineno, line in enumerate(source.splitlines(), 1):
        for token, pattern in ENGINE_BANNED_TOKENS:
            if pattern.search(line):
                raise EngineContractError(
                    "engine %s refused: banned token %r on line %d: %r — "
                    "engines are pure rules modules (whitelist imports: "
                    "%s); regenerate the engine"
                    % (path, token, lineno, line.strip(),
                       ", ".join(sorted(ENGINE_IMPORT_WHITELIST))))
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return  # exec_module will raise the honest SyntaxError itself
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            # Relative imports have module=None — refused ("" never
            # whitelisted): an engine has no package to be relative to.
            names = [node.module or ""]
        else:
            continue
        for name in names:
            if name.split(".")[0] not in ENGINE_IMPORT_WHITELIST:
                raise EngineContractError(
                    "engine %s refused: line %d imports %r — engines may "
                    "import only {%s}; regenerate the engine"
                    % (path, node.lineno, name,
                       ", ".join(sorted(ENGINE_IMPORT_WHITELIST))))


def load_engine(path, expected_idea_sha=None):
    """Import an engine module from an absolute path and verify the contract.

    ``expected_idea_sha``: pass the sha256 of the idea.json you believe you
    are judging; a mismatch raises StaleEngineError instead of quietly
    scoring the wrong game. Pass None only for engines that have no
    idea.json (reference fixtures).
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            "engine not found at %s — run the ENGINE phase first "
            "(build_engine_prompt(slug) makes the writer prompt)" % path)
    # Unique module name per (path, content): two games' engines — or two
    # versions of one engine — must never collide in sys.modules.
    with open(path, "rb") as handle:
        content = handle.read()
    content_hash = hashlib.sha256(content).hexdigest()[:12]
    mod_name = "bob_engine_%s" % content_hash
    if mod_name in sys.modules:
        engine = sys.modules[mod_name]
    else:
        # Lint before exec: agent-written code runs in-process, so the
        # refusal must come while it is still text (see ENGINE_BANNED_TOKENS).
        _lint_engine_source(path, content.decode("utf-8", "replace"))
        spec = importlib.util.spec_from_file_location(mod_name, path)
        engine = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(engine)
        sys.modules[mod_name] = engine

    missing = [fn for fn in ENGINE_API if not callable(getattr(engine, fn, None))]
    if missing:
        raise EngineContractError(
            "engine %s is missing callable(s) %s — the contract in "
            "loops/playtest.py names all eight; regenerate the engine"
            % (path, ", ".join(missing)))
    assumptions = getattr(engine, "ASSUMPTIONS", None)
    if not isinstance(assumptions, list) or not all(
            isinstance(a, str) for a in assumptions):
        raise EngineContractError(
            "engine %s must define ASSUMPTIONS: list[str] (may be empty, "
            "but registered gaps beat guessed rules)" % path)
    embedded = getattr(engine, "IDEA_SHA", None)
    if not isinstance(embedded, str) or not embedded:
        raise EngineContractError(
            "engine %s must embed IDEA_SHA (sha256 of the idea.json it was "
            "written from) — verdicts bind to versions by content hash" % path)
    if expected_idea_sha is not None and embedded != expected_idea_sha:
        raise StaleEngineError(
            "engine %s was written from idea.json sha %s but the current "
            "idea.json is %s — the idea changed after the engine was "
            "written. Regenerate the engine; do NOT score with this one "
            "(stale-verdict receipt: vibe-ideas was burned twice)"
            % (path, embedded[:12], expected_idea_sha[:12]))
    return engine


def _player_range(idea):
    """Parse the player-count range out of idea.json.

    Accepts "2-4", "2", 2, [2, 4], {"min": 2, "max": 4} — rules writers are
    agents, and a parser that only takes one spelling turns format drift
    into a crashed tick.
    """
    raw = idea.get("players")
    if raw is None:
        raise ValueError(
            'idea.json has no "players" field — the rules doc must pin a '
            'player-count range (e.g. "2-4") before simulation')
    if isinstance(raw, int):
        return [raw]
    if isinstance(raw, dict) and "min" in raw and "max" in raw:
        lo, hi = int(raw["min"]), int(raw["max"])
        return list(range(lo, hi + 1))
    if isinstance(raw, (list, tuple)) and len(raw) == 2:
        return list(range(int(raw[0]), int(raw[1]) + 1))
    if isinstance(raw, str):
        match = re.match(r"^\s*(\d+)\s*(?:-\s*(\d+))?\s*$", raw)
        if match:
            lo = int(match.group(1))
            hi = int(match.group(2)) if match.group(2) else lo
            return list(range(lo, hi + 1))
    raise ValueError(
        "cannot parse players=%r from idea.json — use \"2-4\", [2, 4], "
        "{\"min\": 2, \"max\": 4}, or a single integer" % (raw,))


def build_engine_prompt(slug, home=None):
    """Compose the engine-writer prompt: contract + idea.json + instructions.

    The writer gets the contract and the idea — never thresholds, weights,
    or judge rubrics (METR: reward hacking 43x likelier when the model can
    see the scorer; the engine writer is a generator, so it stays blind).
    """
    idea_path = os.path.join(_game_dir(slug, home), "idea.json")
    if not os.path.exists(idea_path):
        raise FileNotFoundError(
            "%s not found — cannot prompt an engine writer without the "
            "idea.json it must implement" % idea_path)
    with open(idea_path, "rb") as handle:
        raw = handle.read()
    sha = hashlib.sha256(raw).hexdigest()
    idea_text = raw.decode("utf-8")

    contract = __doc__.split("TABLE REPORT FORMAT")[0].strip()
    return """You are writing games/%(slug)s/playtest/engine.py — a complete,
stdlib-only Python 3.9 implementation of the game specified in idea.json
below. Code, not you, will play thousands of games through it.

%(contract)s

HARD REQUIREMENTS
- Set exactly: IDEA_SHA = "%(sha)s"
  (that is the sha256 of the idea.json you are implementing; the loader
  refuses the engine if the idea changes after you write it).
- ASSUMPTIONS: every place the rules were ambiguous or silent, close the gap
  and REGISTER it as one string in the ASSUMPTIONS list. Never guess
  silently — a rules gap found while writing the engine is worth more than
  any metric downstream.
- apply(state, move) returns a NEW state and never mutates its input.
- All randomness derives from the seed given to new_game — same seed, same
  game. No wall-clock, no os.urandom, no global random module state.
- scores(state) must move DURING play (progress-toward-winning per seat),
  not only at the end.

THE IDEA (games/%(slug)s/idea.json, sha256 %(sha)s):
%(idea)s
""" % {"slug": slug, "contract": contract, "sha": sha, "idea": idea_text}


def run_sim(slug, home=None, n_games=1000, seed=0):
    """Load the engine, run the full battery per player count, write the report.

    Writes ``games/<slug>/playtest/sim_report.json`` (atomic) carrying the
    idea_sha it judged, per-player-count SimReports, threshold table, and
    an overall verdict. Returns the report dict.
    """
    expected = idea_sha(slug, home)
    engine_path = os.path.join(_game_dir(slug, home), "playtest", "engine.py")
    engine = load_engine(engine_path, expected_idea_sha=expected)

    idea_json_path = os.path.join(_game_dir(slug, home), "idea.json")
    with open(idea_json_path) as handle:
        idea = json.load(handle)

    by_players = {}
    for count in _player_range(idea):
        by_players[str(count)] = simmetrics.simulate(
            engine, count, n_games=n_games, seed=seed)

    all_pass = all(rep["verdicts"]["all_pass"] for rep in by_players.values())
    report = {
        "slug": slug,
        "idea_sha": expected,
        "engine_assumptions": list(engine.ASSUMPTIONS),
        "n_games": n_games,
        "seed": seed,
        "by_players": by_players,
        "thresholds": simmetrics.thresholds(),
        "verdicts": {
            "all_pass": all_pass,
            "per_players": {
                count: rep["verdicts"]["all_pass"]
                for count, rep in by_players.items()
            },
        },
    }
    out_path = os.path.join(_game_dir(slug, home), "playtest", "sim_report.json")
    _atomic_write_json(out_path, report)
    return report


def llm_table(slug, seats, ask=None):
    """LLM seats play real games through the engine — NOT IMPLEMENTED HERE.

    Interface (pinned so the sim half and the table half agree):
    - ``seats``: list of seat specs [{"model": ..., "persona": ...}, ...] —
      one model per seat, each table carries ONE distinct ``ask`` question.
    - Seats receive ``observation(state, seat)`` plus an indexed legal-move
      list and answer with an INDEX. The loop is code, not an agent.
    - Output files: table_<k>.json transcripts + table_report.json summary,
      formats documented in this module's docstring, every file embedding
      the idea_sha it judged.
    """
    from loops import tablerun  # wired at integration: the table half landed
    return tablerun.run_tables(slug)

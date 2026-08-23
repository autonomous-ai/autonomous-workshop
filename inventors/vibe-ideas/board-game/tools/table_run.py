"""table_run.py — the played half of gate R1c. One model per seat, no agent.

`playtest.py` plays a game several thousand times with scripted policies and
measures what a policy can measure: whether it ends, whether the first seat
wins, whether looking ahead helps. Three things stay out of its reach, and all
three need somebody who is trying to win and can say what that was like:

1. Where the rules failed to say, found by running into it with a plan rather
   than by reading the prose with a checklist.
2. Which turns had no decision in them. A policy always picks something; only
   a player can report that seven options were the same option.
3. Whether the game got smaller. A game dies the evening somebody works it
   out, and the only witness to that is a player who was there the first time
   and had to think.

This file is the harness that makes those three measurable, and there is no
agent anywhere in it. The loop that renders a position, sends it to the seat
whose turn it is, reads back one index and applies it is completely
deterministic, so it is code. That is not a style preference. An LLM running
this loop can play a turn for a player who is slow, quietly answer a rules
question it should have recorded as a finding, show one seat what another seat
is holding, or run the game again because the first one was dull. Every one of
those was a written prohibition in an earlier design, and a prohibition is a
thing you hope holds. Here they are not prohibited, they are absent: this
process has no way to express them.

A seat is one plain HTTPS call per decision and nothing else. It has no tools,
no filesystem, and no way to reach `playtest.json`, the engine, or another
seat's messages. It chooses by index out of a list the engine generated, so it
cannot make an illegal move or misremember the board, and it is shown
`observation(state, seat)` and never the state, so in a hidden-information
game it cannot see what it should not. An agent framework was tried here and
removed: everything its loop adds — tools, a filesystem, turns of its own — is
surface without capability when the whole job is to answer one question, and
the one concrete thing it did add was handing the seat 28 tool schemas with
`Read` among them. `urllib` from the standard library is now the whole client,
so there is nothing to install and nothing to keep in step with a release.

Speaks either wire format, selected with --wire, since an endpoint that offers
both will price and cache them differently and that is worth being able to
measure. The whole conversation is resent every turn, which is what makes the
prompt cache worth marking rather than assuming.

Reads PLAYTEST_BASE_URL, PLAYTEST_API_KEY and PLAYTEST_MODEL from the
environment, or from the repo's `.env` when they are not there, so a
credential never has to be typed where something might quote it back.

Usage:

    .venv/bin/python board-game/tools/table_run.py board-game/ideas/deep-claim \
        --wire anthropic

Writes one session per game to <idea_dir>/playtest/table/<label>.json, in the
same format `playtest.py table` writes, so any game replays from its seed and
recorded choices and an engine edited mid-run is caught rather than absorbed.
Writes the run summary to <idea_dir>/playtest/table/run_<wire>.json.
Builds <idea_dir>/playtest/site/index.html from those sessions. Replay is
static; player-vs-player hot-seat play is served by `game_site.py serve` so it
uses the same engine rather than a JavaScript rewrite of the rules.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import playtest  # noqa: E402  (path is set immediately above)
import animation_gate  # noqa: E402
import game_site  # noqa: E402

# A reply that does not parse is re-asked this many times before the run stops.
# Two is deliberate: one retry absorbs a model that wrapped its answer in
# prose, and a seat that cannot produce `CHOICE <n>` twice running is a broken
# configuration, not a bad turn, and should fail loudly rather than be papered
# over with a policy move that the report would then read as a player's.
MAX_REPLY_RETRIES = 2
REQUEST_TIMEOUT = 300.0
# A gateway 5xx is the upstream being busy, and a busy gateway stays busy for
# longer than a few seconds: this budget started at three tries over 24s and a
# run died on the first call of a game because the previous run had just
# pushed 165 requests through the same endpoint. Doubling each time gives
# roughly two minutes of patience, which costs nothing when the endpoint is
# healthy and is the difference between a finished run and a wasted one when
# it is not.
GATEWAY_RETRIES = 5
RETRY_BACKOFF = 4.0
# Generous, because a reasoning model spends most of this on scratch work the
# player never sees and runs out mid-thought at anything tighter. Measured on
# minimax-m3 against deep-claim: a first move took about 2000 tokens of
# thinking before it wrote a line.
DEFAULT_MAX_TOKENS = 8192

# On a reasoning-tier model, thinking is on by default (a template-level
# `enable_thinking` on the gateway) and, without a cap, is billed against the
# same max_tokens as the answer. Millbind showed the failure mode: a clean 200
# SSE stream whose only block was `thinking`, which consumed every max_tokens
# and never opened a text block, so a text-delta-only client read a perfectly
# valid response as "(empty reply)". The fix is to bound thinking explicitly
# so it can never eat the answer budget. 8192 for thought (the owner's call),
# and max_tokens raised well above it so the answer keeps guaranteed room.
THINKING_BUDGET = 8192
# max_tokens must exceed THINKING_BUDGET by at least the answer's needs. The
# address line (CHOICE/WHY/DECISION) is small, but give it real headroom.
DEFAULT_MAX_TOKENS = 16000

# Above roughly this many options a turn, a seat stops being able to answer at
# all. Measured on millbind, whose midgame offers 110 placements: four
# buffered attempts 504'd at the endpoint's 60-second ceiling and four
# streamed ones came back empty after 53-78s, the model having spent its whole
# budget weighing options and never reaching a line of output. The list is not
# truncated to fit, because a seat choosing from a shortened list is not
# playing the game, and the branching factor is itself the finding.
PLAYABLE_BRANCHING = 60
ANTHROPIC_VERSION = "2023-06-01"
USER_AGENT = "board-game-table/1.0 (playtest gate R1c)"

# A base URL either carries its own version segment or expects the client to
# add one, and getting it wrong is a 404 rather than anything informative.
VERSIONED = re.compile(r"/v\d+$")


def backoff_total(attempts: int) -> float:
    """The sleeping the retries have done, which is NOT how long they took.

    Named for what it is, because the old name went into an error message as
    "after 6 attempts over 252s" and read as wall clock. It is not: the
    requests themselves are missing from it, and on a gateway that holds a
    dead request for its full 60-second ceiling they are most of the time.
    That run actually took about 484s, and the halved figure is what led to a
    confident and wrong reading of how fast the gateway gives up.
    """
    return RETRY_BACKOFF * (2 ** (attempts + 1) - 1)


def retry_after(headers) -> float | None:
    try:
        value = headers.get("retry-after") if headers else None
        return min(float(value), 120.0) if value else None
    except (TypeError, ValueError):
        return None


def api_path(base_url: str, tail: str) -> str:
    """`tail` is `messages` or `chat/completions`, without a version."""
    base = base_url.rstrip("/")
    return f"{base}/{tail}" if VERSIONED.search(base) else f"{base}/v1/{tail}"

# What a seat is told, kept as prose in files rather than as strings in here,
# because these are the part of this tool most worth editing and the person
# with something to say about how a playtester should behave should not have
# to open a Python file to say it.
PROMPTS = Path(__file__).resolve().parents[1] / "prompts"
PLAYER_BRIEF = PROMPTS / "player.md"
BREAKER_BRIEF = PROMPTS / "breaker.md"

TABLE_GAMES = 4


# ---------------------------------------------------------------------------
# The brief a seat is given
# ---------------------------------------------------------------------------

def load_env_file(names: tuple) -> None:
    """Fill in the named variables from the repo's `.env`, and nothing else.

    An `export` typed into a terminal does not reach a tool that opens its own
    shell, so the credential has to live in a file. Only the names this tool
    needs are read, and no value is ever printed: whoever runs this should not
    have to hand their key to anything that might quote it back.
    """
    path = Path(__file__).resolve().parents[2] / ".env"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.removeprefix("export ").partition("=")
        key = key.strip()
        if key in names and not os.environ.get(key):
            os.environ[key] = value.strip().strip('"').strip("'")


def render_rules(idea: dict) -> str:
    """The rulebook, with the same step ids the rest of the pipeline uses.

    A player who wants to raise a rules question has to be able to point at
    the step that defeated it, and `rules:turn[5]` only means something if the
    numbering it saw is the numbering `rules_check.py` and the engine use.
    """
    out = [f"# {idea.get('title', idea.get('slug', '?'))}", "",
           idea.get("concept", ""), ""]
    players = idea.get("players") or {}
    out.append(f"Players: {players.get('min', '?')} to {players.get('max', '?')}.")
    out.append("")
    out.append("## Components")
    for comp in idea.get("components") or []:
        out.append(f"- {comp.get('name', '?')} x{comp.get('qty', '?')}: "
                   f"{comp.get('desc', '')}")
    out.append("")
    out.append("## Rules")
    for phase, body in (idea.get("rules") or {}).items():
        out.append(f"### {phase}")
        # Phases are lists of steps, except the ones that are a single clause
        # (`win` usually is). Both shapes get an id, because a player pointing
        # at `rules:win` has to be able to point at it the same way the engine
        # and rules_check.py do.
        if isinstance(body, list):
            for i, step in enumerate(body):
                text = step.get("text", "") if isinstance(step, dict) else step
                out.append(f"rules:{phase}[{i}]  {text}")
        elif isinstance(body, dict):
            text = body.get("text")
            out.append(f"rules:{phase}  "
                       + (text if text else json.dumps(body, indent=1)))
        else:
            out.append(f"rules:{phase}  {body}")
        out.append("")
    return "\n".join(out)


def seat_system_prompt(brief: str, rules: str, seat: int, seats: int,
                       breaker: bool) -> str:
    """Brief plus rulebook, both static for the whole run.

    They go in the system prompt rather than in the first turn's message
    because a player at a table has the rulebook beside it the whole evening,
    not recited once and taken away. That it is also the only large block that
    never changes, and so the only one a prompt cache can hold, is a happy
    coincidence and not the reason.
    """
    parts = [brief]
    if breaker:
        parts.append(BREAKER_BRIEF.read_text(encoding="utf-8").strip())
    parts.append(f"# You are seat {seat} of {seats}\n\n"
                 f"Seat numbers and the {seats}-player table are stable for "
                 f"all four games. You keep everything you learn during this "
                 f"run.")
    parts.append("# The rules of this game\n\n" + rules)
    return "\n\n".join(parts)


def prior_iteration_experience(idea_dir: Path) -> dict[int, list[str]]:
    """Return only what prior player seats said they learned.

    Rework snapshots intentionally exclude machine statistics, review
    verdicts, engines, and hidden state. Game 4 is an experienced-player
    challenge, not permission to hand a player the harness's answer.
    """
    learned: dict[int, list[str]] = {}
    history = idea_dir / "history" / "reworks"
    for path in sorted(history.glob("*.json")):
        try:
            experience = (json.loads(path.read_text(encoding="utf-8"))
                          .get("table_experience"))
        except (OSError, ValueError):
            continue
        if not experience:
            continue
        source = str(experience.get("source") or path.name)
        for debrief in experience.get("debriefs") or []:
            try:
                seat = int(debrief["seat"])
            except (KeyError, TypeError, ValueError):
                continue
            text = str(debrief.get("text") or "").strip()
            if text:
                learned.setdefault(seat, []).append(
                    f"[{source} {debrief.get('game', '?')}] {text}")
    # Keep the newest evidence when a long-lived design has many iterations.
    return {seat: entries[-24:] for seat, entries in learned.items()}


# ---------------------------------------------------------------------------
# The seats
# ---------------------------------------------------------------------------

class Seats:
    """One conversation per seat, one round trip per decision.

    Stateless on the wire and therefore trivially auditable: every byte a seat
    has ever been shown is in `self.history[key]`, so a reader can check for
    themselves that no seat saw another seat's observation. That auditability
    is the reason there is no agent framework here and no session held open
    somewhere else; the whole state of this table is two dicts in one process.
    """

    def __init__(self, base_url: str, api_key: str, model: str, wire: str,
                 max_tokens: int, cache: bool, stream: bool = False):
        self.name = wire + ("/cached" if cache else "") + ("/stream" if stream else "")
        self.stream = stream
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.wire = wire
        self.max_tokens = max_tokens
        self.cache = cache
        self.system: dict = {}
        self.history: dict = {}

    async def open_seat(self, key: str, system: str) -> None:
        self.system[key] = system
        self.history[key] = []

    def _body(self, key: str) -> tuple:
        system, messages = self.system[key], self.history[key]
        if self.wire == "openai":
            return (api_path(self.base_url, "chat/completions"),
                    {"Authorization": f"Bearer {self.api_key}",
                     "content-type": "application/json"},
                    {"model": self.model, "max_tokens": self.max_tokens,
                     "stream": self.stream,
                     # Streaming otherwise omits usage entirely, and a run
                     # that cannot say what it spent is not a measurement.
                     **({"stream_options": {"include_usage": True}}
                        if self.stream else {}),
                     "messages": [{"role": "system", "content": system}]
                                 + messages})
        block = {"type": "text", "text": system}
        if self.cache:
            # The brief and the rulebook never change for the whole run, so
            # this one marker is the difference between paying for the
            # rulebook once and paying for it on every decision.
            block["cache_control"] = {"type": "ephemeral"}
        return (api_path(self.base_url, "messages"),
                {"x-api-key": self.api_key,
                 "authorization": f"Bearer {self.api_key}",
                 "anthropic-version": ANTHROPIC_VERSION,
                 "content-type": "application/json"},
                {"model": self.model, "max_tokens": self.max_tokens,
                 "stream": self.stream,
                 # Cap thinking so it cannot consume the whole max_tokens and
                 # leave no room for a text block. Without this, a reasoning
                 # model returns a 200 SSE stream of `thinking` deltas that
                 # never opens a text block, which a text-only reader sees as
                 # an empty reply. See THINKING_BUDGET.
                 "thinking": {"type": "enabled",
                              "budget_tokens": THINKING_BUDGET},
                 "system": [block], "messages": messages})

    def _post(self, url: str, headers: dict, payload: dict) -> dict:
        """POST and return the reply text and its usage, streamed or not.

        Which is better is a property of the endpoint AND of how long the
        seat thinks, which is why this answer changed twice. On narrow
        positions buffered wins: five interleaved pairs of the same prompt ran
        3.4-4.2s buffered and returned 5 of 5, against 3.7-63s streamed and
        4 of 5. That measurement is still true and it is not the one that
        matters, because a run does not die on a narrow position.

        On the position that actually kills runs — Millbind's turn 5, 114
        legal moves — four interleaved pairs each way:

            buffered  1 of 4 usable: 504 at 60.3s, 504 at 60.2s,
                      an empty reply that spent all 8192 output tokens,
                      and one CHOICE that landed at 58.9s
            streamed  3 of 4 usable, no 504 at all: one empty reply at the
                      same 8192 cap, then 6083, 4740 and 5018 output tokens
                      returning a CHOICE in 35-37s

        The mechanism is the same in both halves and explains both. This seat
        needs five to eight thousand output tokens to weigh a hundred options,
        the gateway kills a request that has been silent for 60 seconds, and
        a buffered request is silent for its whole life. Streaming keeps
        bytes moving so the ceiling never applies, which is why it wins here
        and lost on a prompt that answered in four seconds.

        The remaining failure is not the wire and streaming does not touch it:
        a seat that spends the entire 8192-token budget deliberating returns
        nothing on either transport. That one is the width of the position.
        """
        # urllib announces itself as `Python-urllib/3.x`, which a gateway
        # behind Cloudflare rejects outright with a 403 and error code 1010
        # before the request reaches the model at all. Naming the tool is both
        # what fixes it and what an operator reading their own access log
        # would want to see.
        headers = dict(headers, **{"user-agent": USER_AGENT})
        if self.stream:
            headers["accept"] = "text/event-stream"
        body = json.dumps(payload).encode("utf-8")
        began = time.monotonic()
        for attempt in range(GATEWAY_RETRIES + 1):
            req = urllib.request.Request(url, data=body, headers=headers,
                                         method="POST")
            try:
                with urllib.request.urlopen(req,
                                            timeout=REQUEST_TIMEOUT) as resp:
                    return (self._consume(resp) if self.stream
                            else self._buffered(json.loads(
                                resp.read().decode("utf-8"))))
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", "replace")[:800]
                # A gateway 502/503/504 is the upstream being slow or busy,
                # not the request being wrong, and a run that dies forty
                # decisions in on one of them has thrown away everything it
                # paid for. A 4xx is our mistake and retrying it just spends
                # the same money twice.
                if exc.code < 500 or attempt == GATEWAY_RETRIES:
                    raise RuntimeError(
                        f"{exc.code} from {url} after {attempt + 1} attempts "
                        f"over {time.monotonic() - began:.0f}s "
                        f"({backoff_total(attempt):.0f}s of it waiting to "
                        f"retry): {detail}") from None
                # `Retry-After` when the gateway says how long it wants, since
                # guessing shorter than it asked is how a retry storm starts.
                time.sleep(retry_after(exc.headers) or RETRY_BACKOFF * 2 ** attempt)
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt == GATEWAY_RETRIES:
                    raise RuntimeError(
                        f"{url} unreachable after {attempt + 1} attempts "
                        f"over {time.monotonic() - began:.0f}s "
                        f"({backoff_total(attempt):.0f}s of it waiting to "
                        f"retry): {exc}") from None
                time.sleep(RETRY_BACKOFF * 2 ** attempt)
        raise RuntimeError(f"{url}: retries exhausted")

    def _buffered(self, data: dict) -> dict:
        """One JSON body, folded into the same shape the stream reader gives."""
        if self.wire == "openai":
            message = (data.get("choices") or [{}])[0].get("message") or {}
            text = message.get("content") or ""
        else:
            # `text` blocks only. A reasoning model also sends `thinking`
            # blocks, and those are its scratch work rather than its answer.
            text = "".join(b.get("text", "") for b in data.get("content", [])
                           if b.get("type") == "text")
        return {"text": text, "usage": data.get("usage") or {}}

    def _consume(self, resp) -> dict:
        """Fold an SSE stream back into the one text and one usage we want.

        Both wires send `data:` lines carrying JSON, and differ only in what
        the JSON says: one nests the token under `delta.text`, the other under
        `delta.content`, and each reports usage in its own place and its own
        moment. Anything unparseable is skipped rather than raised on, because
        a keep-alive comment or a field added next release must not end a game
        forty decisions in.
        """
        chunks: list = []
        usage: dict = {}
        for raw in resp:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if not payload or payload == "[DONE]":
                continue
            try:
                event = json.loads(payload)
            except ValueError:
                continue
            if self.wire == "openai":
                for choice in event.get("choices") or []:
                    piece = (choice.get("delta") or {}).get("content")
                    if piece:
                        chunks.append(piece)
                if event.get("usage"):
                    usage = event["usage"]
            else:
                kind = event.get("type")
                if kind == "content_block_delta":
                    delta = event.get("delta") or {}
                    # `text_delta` only. A `thinking_delta` is the model's
                    # scratch work and is not what the seat answered.
                    if delta.get("type") == "text_delta" and delta.get("text"):
                        chunks.append(delta["text"])
                elif kind == "message_start":
                    usage.update((event.get("message") or {}).get("usage") or {})
                elif kind == "message_delta":
                    usage.update(event.get("usage") or {})
        return {"text": "".join(chunks), "usage": usage}

    async def ask(self, key: str, text: str) -> tuple:
        self.history[key].append({"role": "user", "content": text})
        url, headers, payload = self._body(key)
        data = await asyncio.to_thread(self._post, url, headers, payload)
        reply = data["text"]
        raw = data["usage"] or {}
        if self.wire == "openai":
            # The two wires count the prompt differently and the difference is
            # silent: `prompt_tokens` is the whole prompt with the cached part
            # inside it, while Anthropic's `input_tokens` counts only what was
            # not served from cache. Reported as-is they look like one wire
            # costing twice the other for the same four games. Both are
            # normalised to "in = what was not cached", so in + cached is the
            # prompt on either.
            cached = (raw.get("prompt_tokens_details")
                      or {}).get("cached_tokens", 0) or 0
            usage = {"in": max((raw.get("prompt_tokens") or 0) - cached, 0),
                     "out": raw.get("completion_tokens", 0),
                     "cached": cached}
        else:
            usage = {"in": raw.get("input_tokens", 0),
                     "out": raw.get("output_tokens", 0),
                     "cached": raw.get("cache_read_input_tokens", 0),
                     "cache_write": raw.get("cache_creation_input_tokens", 0)}
        # Not every endpoint prices its own responses, but one that does knows
        # better than any table we could keep here, so it is taken when
        # offered and simply absent when it is not.
        usage["cost"] = raw.get("cost")
        self.history[key].append({"role": "assistant", "content": reply})
        return reply, usage


class StdioSeats:
    """Interactive transport for an external, isolated seat orchestrator.

    The normal transport owns one HTTPS conversation per seat. Codex runs in
    environments where those credentials may deliberately be unavailable, so
    this transport exposes the same boundary as newline-delimited JSON:
    ``open`` supplies a seat's immutable system prompt and ``ask`` supplies
    only that seat's next observation. The caller must keep one independent
    conversation per key and return exactly one JSON reply line.

    Game state, legality, routing, replay files, leak checks and summaries all
    remain inside this process. This is a transport substitution, not a policy
    fallback and not permission to synthesize a transcript.
    """

    name = "codex-stdio"

    @staticmethod
    def _emit(event: dict) -> None:
        print("TABLE_STDIO " + json.dumps(event, separators=(",", ":")),
              flush=True)

    async def open_seat(self, key: str, system: str) -> None:
        self._emit({"event": "open", "key": key, "system": system})

    async def ask(self, key: str, text: str) -> tuple:
        self._emit({"event": "ask", "key": key, "text": text})
        raw = await asyncio.to_thread(sys.stdin.readline)
        if not raw:
            raise RuntimeError("stdio seat orchestrator closed input")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"stdio seat reply is not JSON: {exc}") from exc
        if data.get("key") != key:
            raise RuntimeError(
                f"stdio seat reply routed to {data.get('key')!r}, expected {key!r}")
        reply = data.get("text")
        if not isinstance(reply, str):
            raise RuntimeError("stdio seat reply has no string `text`")
        return reply, {"in": 0, "out": 0, "cached": 0,
                       "cache_write": 0, "cost": None}


# ---------------------------------------------------------------------------
# Reading a reply
# ---------------------------------------------------------------------------

THINK_RE = re.compile(r"<(\w+:)?think(ing)?>.*?</(\w+:)?think(ing)?>",
                      re.S | re.I)
OPEN_THINK_RE = re.compile(r"^.*?</(\w+:)?think(ing)?>", re.S | re.I)


def strip_thinking(text: str) -> str:
    """Remove a reasoning block the endpoint left inside the reply.

    A reasoning model's scratch work is supposed to arrive in its own field,
    and some gateways put it there and some leave the raw `<think>` tags in
    the content, sometimes both from the same endpoint on different requests.
    Either way it is not the player's answer, and a `CHOICE 4` that appears
    while the model is still weighing options is not the move it settled on,
    so a stray tag has to be cut rather than searched.
    """
    cleaned = THINK_RE.sub("", text)
    # A think block that opened and never closed means the reply was cut off
    # mid-thought and there is no answer in it. One that closes without an
    # opening tag is the tail of a block whose start was trimmed upstream, and
    # everything after the close is the real reply.
    if "</think>" in cleaned.lower() or "think>" in cleaned.lower():
        cleaned = OPEN_THINK_RE.sub("", cleaned)
    return cleaned.strip()


CHOICE_RE = re.compile(r"^\s*CHOICE\s+(\d+)\s*$", re.M)
WHY_RE = re.compile(r"^\s*WHY\s+(.+)$", re.M)
DECISION_RE = re.compile(r"^\s*DECISION\s+(forced|indifferent|scripted|real)"
                         r"\s*$", re.M | re.I)
# The boolean this replaced could not tell "one legal move" from "several
# moves that all end the same" from "a move that scores and that I had
# already decided three turns ago". Four seats read it four ways and the
# third meaning, the one that actually kills a game, had nowhere to go.
DECISIONS = ("forced", "indifferent", "scripted", "real")
QUESTION_RE = re.compile(r"^\s*RULES QUESTION\s+(.+)$", re.M)
NOTE_RE = re.compile(r"^\s*NOTE\s+(.+)$", re.M)


def parse_reply(text: str, n_moves: int) -> dict | None:
    """None when the reply cannot be read as a move.

    Deliberately strict about CHOICE and forgiving about everything else. A
    missing WHY costs one line of the report; a CHOICE guessed out of prose
    costs the integrity of the session file, because the recorded index is
    what the whole game replays from.
    """
    text = strip_thinking(text)
    match = CHOICE_RE.search(text)
    if not match:
        return None
    choice = int(match.group(1))
    if not 0 <= choice < n_moves:
        return None
    why = WHY_RE.search(text)
    dec = DECISION_RE.search(text)
    kind = dec.group(1).lower() if dec else "unstated"
    return {
        "choice": choice,
        "why": why.group(1).strip() if why else "",
        "decision": kind,
        # Kept so the aggregates and `playtest.py table` keep working. Only
        # `real` is a decision; the other three are three different ways of
        # not having had one, which is exactly what the boolean could not say.
        "arbitrary": kind != "real",
        "question": [m.strip() for m in QUESTION_RE.findall(text)],
        "note": [m.strip() for m in NOTE_RE.findall(text)],
    }


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------

class Run:
    def __init__(self, eng, idea_dir: Path, seats: Seats, compact: bool):
        self.eng = eng
        self.idea_dir = idea_dir
        self.seats = seats
        self.compact = compact
        self.usage = {"in": 0, "out": 0, "cached": 0, "cache_write": 0,
                      "cost_usd": 0.0, "calls": 0}
        self.open_seats: set = set()
        self.questions: list = []
        self.debriefs: list = []
        self.games: list = []
        self.sent: dict = {}
        self.experience_injections: list = []

    def _bill(self, usage: dict) -> None:
        # A gateway is entitled to send `null` for a counter it does not
        # track, and several do, so every field is coerced rather than
        # trusted. A crash here would be a crash a dozen decisions into a run
        # that had already been paid for.
        for key in ("in", "out", "cached", "cache_write"):
            self.usage[key] += int(usage.get(key) or 0)
        self.usage["cost_usd"] += float(usage.get("cost") or 0.0)
        self.usage["calls"] += 1

    async def ensure_seat(self, seat: int, system: str) -> None:
        key = f"seat{seat}"
        if key not in self.open_seats:
            await self.seats.open_seat(key, system)
            self.open_seats.add(key)

    async def ask_seat(self, seat: int, text: str, where: str = "?") -> str:
        self.sent.setdefault(seat, []).append(text)
        reply, usage = await self.seats.ask(f"seat{seat}", text)
        self._bill(usage)
        # Scanned here rather than only on move replies, because a player that
        # held a question back until the debrief has still found one, and the
        # first real run lost exactly that: a seat ended its debrief with a
        # literal RULES QUESTION line while the run file reported none.
        for text_ in QUESTION_RE.findall(strip_thinking(reply)):
            self.questions.append({"game": where, "seat": seat,
                                   "turn": None, "text": text_.strip()})
        return reply

    async def inject_prior_experience(self, seats: int,
                                      learned: dict[int, list[str]]) -> None:
        """Give prior-iteration player experience only before game four."""
        for seat in range(seats):
            entries = learned.get(seat) or []
            if entries:
                packet = "\n\n".join(entries)
                prompt = (
                    "PRIOR ITERATION EXPERIENCE\n"
                    "Only now, before the fourth game, you may use the notes "
                    "below from your own seat in earlier rules iterations. "
                    "Those rules may be obsolete. Transfer strategic lessons, "
                    "but judge every move against the current rulebook. Do not "
                    "treat an old reviewer conclusion as fact.\n\n" + packet +
                    "\n\nReply in one sentence with the single prior lesson "
                    "you will test in game four.")
            else:
                prompt = (
                    "PRIOR ITERATION EXPERIENCE\n"
                    "No archived player experience exists for your seat. Game "
                    "four therefore continues only with what you learned in "
                    "games one through three. Say that plainly in one sentence.")
            reply = await self.ask_seat(seat, prompt, "BEFORE GAME 4")
            self.experience_injections.append({
                "seat": seat, "available": bool(entries),
                "sources": len(entries), "text": reply.strip(),
            })

    def leaked_seats(self) -> list:
        """Was any seat ever sent a position addressed to a different seat?

        Routing is done by code here, so this should always come back empty.
        That is exactly why it is worth checking: one misrouted block in a
        hidden-information game destroys the run's value and leaves no trace
        anybody would notice afterwards, and a claim of "structurally
        impossible" is worth more when something verifies it every run.
        """
        bad = set()
        for seat, texts in self.sent.items():
            for text in texts:
                for other in re.findall(r"^YOU ARE seat (\d+)", text, re.M):
                    if int(other) != seat:
                        bad.add(f"seat {seat} was sent a block for seat {other}")
        return sorted(bad)

    def abandon(self, session: dict, label: str, why: str):
        """Write the partial game before giving up, whatever gave up.

        It is a seed and a list of choices, so it is the reproduction:
        whoever picks this up walks straight back to the position that could
        not be answered, and that position is the finding. There are two ways
        a turn ends a run — the seat sends something unreadable, or the
        gateway sends nothing — and only the first one used to save. The
        second is the one that fires on a wide position, so the case that
        most needed a reproduction was the case that left none.
        """
        session["abandoned_at"] = len(session["moves"])
        session["abandoned_because"] = why
        out = self.idea_dir / "playtest" / "table" / f"{label}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(session, indent=2), encoding="utf-8")
        return out

    async def play_game(self, seats: int, seed: int, label: str,
                        systems: dict, game_no: int,
                        knowledge_mode: str) -> dict:
        eng = self.eng
        session = {
            "slug": getattr(eng, "SLUG", self.idea_dir.name),
            "idea_dir": str(self.idea_dir),
            "engine": str(self.idea_dir / "playtest" / "engine.py"),
            "seats": seats, "seed": seed, "scripted": {},
            "agent_turns": 0, "finish_with": "greedy",
            "seed_blind": playtest.seed_blind(eng, seats),
            "wire": self.seats.name,
            "knowledge_mode": knowledge_mode,
            "handed_over_at": None, "moves": [],
        }
        state, rng = playtest.replay(eng, session)
        last_seen = {s: 0 for s in range(seats)}
        stuck = False
        undefined = None

        for seat in range(seats):
            await self.ensure_seat(seat, systems[seat])

        while not eng.is_over(state):
            try:
                moves = eng.legal_moves(state)
            except Exception as exc:
                if not playtest.is_undefined(exc):
                    raise
                undefined = str(exc)
                break
            if not moves:
                stuck = True
                break
            seat = int(eng.player_to_move(state))
            block = "\n".join(
                playtest.played_lines(session, last_seen[seat])
                + [playtest.render_table(eng, session, state, label,
                                         self.compact)])
            # One line per decision, before the request rather than after it.
            # A run that dies inside a four-minute retry sequence should say
            # which turn and how wide the position was while it is still
            # hanging, not in a traceback that mentions neither.
            print(f"    {label} t{len(session['moves'])} seat{seat} "
                  f"{len(moves)} moves", flush=True)
            parsed = None
            asked_before = len(self.questions)
            rejected = []
            for attempt in range(MAX_REPLY_RETRIES + 1):
                prompt = block if attempt == 0 else (
                    f"That reply had no readable `CHOICE <n>` with n between 0 "
                    f"and {len(moves) - 1}. Send only the lines the brief asks "
                    f"for: CHOICE, WHY, then DECISION with one of "
                    f"{', '.join(DECISIONS)}.")
                try:
                    reply = await self.ask_seat(seat, prompt, label)
                except Exception as exc:
                    # A gateway that gives up is the same loss as a seat that
                    # answers in prose: the position that caused it is the
                    # finding, and without the game so far nobody can get back
                    # to it. This path used to raise straight out and leave no
                    # file at all, which is how a 504 after four minutes told
                    # us nothing about which turn it died on.
                    out = self.abandon(
                        session, label,
                        f"seat {seat} got no reply from the gateway on a "
                        f"position offering {len(moves)} moves: "
                        f"{type(exc).__name__}: {exc}")
                    raise SystemExit(
                        f"TABLE ERROR seat {seat} got no reply in game "
                        f"{label} at turn {len(session['moves'])}, on a "
                        f"position offering {len(moves)} moves. The game so "
                        f"far is saved at {out}, so the position replays. "
                        f"{type(exc).__name__}: {exc}") from exc
                parsed = parse_reply(reply, len(moves))
                if parsed:
                    break
                rejected.append(reply)
            if not parsed:
                # The old message said "fix the seat or the brief" and showed
                # nothing to fix it with, which is the least useful shape an
                # error can take. An empty reply, a refusal and a model that
                # answered in prose are three different problems and only the
                # text tells them apart.
                shown = "\n  ---\n".join(
                    (repr(r[:400]) if r.strip() else "(empty reply)")
                    for r in rejected)
                out = self.abandon(
                    session, label,
                    f"seat {seat} returned nothing readable on a position "
                    f"offering {len(moves)} moves")
                raise SystemExit(
                    f"TABLE ERROR seat {seat} could not produce a readable "
                    f"CHOICE after {MAX_REPLY_RETRIES + 1} attempts in game "
                    f"{label}, on a position offering {len(moves)} moves. "
                    f"Do not let a policy finish this game and call the "
                    f"result a player's. The game so far is saved at "
                    f"{out}, so the position replays. What it actually sent:"
                    f"\n  {shown}")

            # ask_seat already recorded any question in those replies. Stamp
            # the turn onto the ones this turn produced, and only those: a
            # question left over from the previous game's debrief has no turn
            # and must not borrow one.
            for entry in self.questions[asked_before:]:
                entry["turn"] = len(session["moves"])
            session["moves"].append({
                "seat": seat, "choice": parsed["choice"],
                "move": str(moves[parsed["choice"]]), "by": "player",
                "why": parsed["why"], "arbitrary": parsed["arbitrary"],
                "decision": parsed["decision"],
                "note": parsed["note"] or None,
            })
            try:
                state = eng.apply_move(state, moves[parsed["choice"]], rng)
            except Exception as exc:
                # The engine reaching a place the rules do not cover is the
                # single most valuable thing this whole stage can produce, and
                # it arrives as an exception. Ending the run on a stack trace
                # would throw away the game that got there, and the game that
                # got there is the reproduction: a seed and a list of choices
                # that walks anybody straight back to the gap.
                if not playtest.is_undefined(exc):
                    raise
                undefined = str(exc)
                session["undefined_after_move"] = len(session["moves"])
                break
            last_seen[seat] = len(session["moves"])

        session["undefined"] = undefined
        over = eng.is_over(state)
        scores = [round(s, 2) for s in eng.scores(state)]
        winners = list(eng.winners(state)) if over else []
        out = self.idea_dir / "playtest" / "table" / f"{label}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(session, indent=2), encoding="utf-8")

        decisions = len(session["moves"])
        arbitrary = sum(1 for m in session["moves"] if m["arbitrary"])
        record = {
            "label": label, "seats": seats, "seed": seed,
            "knowledge_mode": knowledge_mode,
            "seed_blind": session["seed_blind"], "stuck": stuck,
            "finished": over, "decisions": decisions, "scores": scores,
            "winners": winners, "undefined": undefined,
            "arbitrary_rate": round(arbitrary / max(decisions, 1), 3),
            "decisions_by_seat": {
                str(s): {k: sum(1 for m in session["moves"]
                                if m["seat"] == s and m.get("decision") == k)
                         for k in DECISIONS + ("unstated",)}
                for s in range(seats)},
            "arbitrary_by_seat": {
                str(s): round(
                    sum(1 for m in session["moves"]
                        if m["seat"] == s and m["arbitrary"])
                    / max(sum(1 for m in session["moves"] if m["seat"] == s), 1),
                    3)
                for s in range(seats)},
            "session": str(out),
        }
        self.games.append(record)

        if undefined:
            self.questions.append({"game": label, "seat": None,
                                   "turn": decisions,
                                   "text": f"ENGINE REFUSED: {undefined}"})
        await self.collect_debriefs(seats, label, scores, winners, game_no,
                                    stuck, over, undefined)
        return record

    async def collect_debriefs(self, seats: int, label: str, scores: list,
                               winners: list, game_no: int, stuck: bool,
                               over: bool, undefined: str | None = None
                               ) -> None:
        """Scores and the winner go to every seat, and nothing else.

        A group playing the same game several times in an evening knows who
        won the last one, and the memory that builds on that is the only way
        the "did this game get smaller" question can be answered at all. What
        does not go out is any hidden state the game itself never reveals.
        """
        if undefined:
            # The players are told the rules ran out and what the rules were
            # silent about, because a person at a table would be looking at
            # the same jam and would have an opinion about it. What they must
            # not be told is how to resolve it, which is the whole finding.
            ending = ("The game stopped mid-play. "
                      "The rules do not cover the position it reached:"
                      "\n\n" + undefined + "\n\n"
                      "Nobody is going to rule on that. Debrief on the "
                      "game up to that point, and say whether you saw it "
                      "coming.")
        elif stuck:
            ending = ("The game stopped: nobody had a legal move and the rules "
                      "do not say what happens then.")
        elif not over:
            ending = "The game hit the turn cap without reaching an ending."
        else:
            ending = f"Final scores {scores}. Winner(s): seat(s) {winners}."
        extra = ("" if game_no == 1 else
                 "\n\nThis was not your first game here, so add the two extra "
                 "lines the brief asks for from the second game on.")
        for seat in range(seats):
            reply = await self.ask_seat(
                seat, f"GAME OVER  {label}\n{ending}\n\nDebrief now, in six "
                      f"lines or fewer, following your brief.{extra}", label)
            self.debriefs.append({"game": label, "seat": seat,
                                  "text": reply.strip()})

    async def closing_question(self, seats_seen: set) -> None:
        for seat in sorted(seats_seen):
            reply = await self.ask_seat(
                seat, "The run is over. Answer the last question in your "
                      "brief: did this game get smaller?", "RUN END")
            self.debriefs.append({"game": "RUN END", "seat": seat,
                                  "text": reply.strip()})


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_schedule(text: str) -> list:
    """Parse an explicit schedule; production validation permits max:4 only."""
    out = []
    for chunk in filter(None, (c.strip() for c in text.split(","))):
        seats, _, count = chunk.partition(":")
        out.append((int(seats), int(count or 1)))
    return out


async def run(args: argparse.Namespace) -> int:
    idea_dir = args.idea_dir.parent if args.idea_dir.is_file() else args.idea_dir
    idea_file = idea_dir / "idea.json"
    engine_path = args.engine or (idea_dir / "playtest" / "engine.py")
    if not engine_path.is_file():
        print(f"TABLE ERROR no engine at {engine_path}")
        return 2
    if not idea_file.is_file():
        print(f"TABLE ERROR no idea.json at {idea_file}")
        return 2
    animation_failure, _ = animation_gate.evidence(idea_dir)
    if animation_failure:
        print("TABLE ERROR rule animation gate is incomplete: "
              + animation_failure)
        return 2
    if engine_path.stat().st_mtime < idea_file.stat().st_mtime:
        print(f"TABLE ERROR {engine_path.name} is older than idea.json — the "
              f"rules changed after this engine was written, so seating players "
              f"on it would play rules that no longer exist. Have "
              f"board-game-rules-engineer verify/re-stamp the engine against the "
              f"current idea.json before running.")
        return 2

    eng = playtest.load_engine(engine_path)
    idea = json.loads(idea_file.read_text(encoding="utf-8"))
    label_prefix = (args.label_prefix or
                    f"i{hashlib.sha256(idea_file.read_bytes()).hexdigest()[:8]}-g")
    players = idea.get("players") or {}
    try:
        max_players = int(players["max"])
    except (KeyError, TypeError, ValueError):
        print("TABLE ERROR idea.json has no valid players.max")
        return 2
    schedule = (parse_schedule(args.schedule) if args.schedule
                else [(max_players, TABLE_GAMES)])
    total_games = sum(count for _, count in schedule)
    if total_games != TABLE_GAMES or any(
            seats != max_players for seats, _ in schedule):
        print(f"TABLE ERROR the table protocol is exactly {TABLE_GAMES} games "
              f"at players.max ({max_players}); got {args.schedule!r}")
        return 2

    for seats, _ in schedule:
        problems = (playtest.validate_engine(eng)
                    or playtest.table_guard(eng, seats, args.seed))
        if problems:
            print("TABLE ERROR " + "; ".join(problems))
            return 2

    # A session file is the only record of what a player actually chose, and
    # no rerun re-derives it: the same seed and the same prompt will not give
    # the same game back. So a label that already exists stops the run before
    # a token is spent, rather than after, and stops it here rather than on
    # game four when three games have already been paid for.
    total = total_games
    clashes = [p for p in
               (idea_dir / "playtest" / "table" / f"{label_prefix}{i}.json"
                for i in range(1, total + 1)) if p.exists()]
    if clashes and not args.overwrite:
        print("TABLE ERROR these sessions already exist and this run would "
              "destroy them: " + ", ".join(p.name for p in clashes)
              + ". Use a different --label-prefix, or --overwrite if you "
                "genuinely mean to discard what a previous table played.")
        return 2

    if args.wire == "stdio":
        base_url = api_key = ""
        model = args.model or "codex-agent"
    else:
        load_env_file(("PLAYTEST_BASE_URL", "PLAYTEST_API_KEY", "PLAYTEST_MODEL"))
        base_url = os.environ.get("PLAYTEST_BASE_URL", "").strip()
        api_key = os.environ.get("PLAYTEST_API_KEY", "").strip()
        model = args.model or os.environ.get("PLAYTEST_MODEL", "").strip()
        missing = [name for name, value in
                   (("PLAYTEST_BASE_URL", base_url),
                    ("PLAYTEST_API_KEY", api_key),
                    ("PLAYTEST_MODEL", model)) if not value]
        if missing:
            print("TABLE ERROR set " + ", ".join(missing))
            return 2

    # The machine half, if it has run, already knows how wide this game's
    # turns are. Saying so before the first request costs nothing and is
    # cheaper than discovering it forty decisions in.
    #
    # Read the WIDEST position, not the median. A run does not die on a
    # typical turn, it dies on the worst one it meets, and one unanswerable
    # position ends the game whatever the other ninety-nine look like.
    # Millbind is the case that proves it: median 53, which is under the
    # threshold and printed nothing, and a maximum of 118 that killed every
    # attempt on turn seven. The median stays in the message because a game
    # that is wide everywhere and a game with one wide opening are different
    # problems and the pair of numbers tells them apart.
    report = idea_dir / "playtest.json"
    if report.is_file():
        try:
            stats = json.loads(report.read_text(encoding="utf-8"))["stats"]
            widest = max(
                (block["competent"]["branching_max"],
                 block["competent"]["branching_median"], seats)
                for seats, block in stats["seats"].items()
                if block.get("competent", {}).get("branching_max"))
            if widest[0] > PLAYABLE_BRANCHING:
                print(f"WIDE  playtest.json records positions of up to "
                      f"{widest[0]:.0f} legal moves at {widest[2]} players "
                      f"(median {widest[1]:.0f}). Past about "
                      f"{PLAYABLE_BRANCHING} a seat spends its whole budget "
                      f"weighing options and returns nothing, so expect this "
                      f"run to stop on an empty reply or a gateway timeout at "
                      f"the first such position. That is a fact about the "
                      f"game's branching factor, not a transport problem, and "
                      f"truncating the list to fit would measure a different "
                      f"game.")
        except (KeyError, ValueError, TypeError):
            pass

    seats_client = (StdioSeats() if args.wire == "stdio" else
                    Seats(base_url, api_key, model, args.wire,
                          args.max_tokens, not args.no_cache, args.stream))

    brief = PLAYER_BRIEF.read_text(encoding="utf-8").strip()
    rules = render_rules(idea)
    widest = max(seats for seats, _ in schedule)
    systems = {s: seat_system_prompt(brief, rules, s, widest,
                                     s == args.breaker_seat)
               for s in range(widest)}

    started = time.monotonic()
    run_state = Run(eng, idea_dir, seats_client, args.compact)
    prior_experience = prior_iteration_experience(idea_dir)
    seats_seen: set = set()
    game_no = 0
    for seats, count in schedule:
        for _ in range(count):
            game_no += 1
            if game_no == 4:
                await run_state.inject_prior_experience(seats, prior_experience)
            label = f"{label_prefix}{game_no}"
            seed = args.seed + game_no * 13
            seats_seen |= set(range(seats))
            knowledge_mode = (
                "fresh" if game_no == 1 else
                "current-run-experienced" if game_no in {2, 3} else
                "current-and-prior-iteration-experienced")
            record = await run_state.play_game(seats, seed, label,
                                               systems, game_no, knowledge_mode)
            print(f"  {label}  {seats}p seed {seed}  "
                  f"{record['decisions']} decisions  "
                  f"scores {record['scores']}  winners {record['winners']}"
                  f"  arbitrary {record['arbitrary_rate']:.0%}")
    await run_state.closing_question(seats_seen)

    elapsed = time.monotonic() - started
    summary = {
        "slug": getattr(eng, "SLUG", idea_dir.name),
        "wire": seats_client.name, "model": model,
        "breaker_seat": args.breaker_seat,
        "seconds": round(elapsed, 1),
        "usage": run_state.usage,
        "leaks": run_state.leaked_seats(),
        "games": run_state.games,
        "rules_questions": run_state.questions,
        "debriefs": run_state.debriefs,
        "experience_injections": run_state.experience_injections,
        "protocol": {
            "games": TABLE_GAMES,
            "players": max_players,
            "game_modes": [
                "fresh", "current-run-experienced",
                "current-run-experienced",
                "current-and-prior-iteration-experienced",
            ],
        },
    }
    # The name carries the wire and the cache setting, so running the same
    # games under both and comparing does not overwrite the first answer
    # with the second.
    slug = re.sub(r"[^a-z0-9]+", "_", seats_client.name.lower()).strip("_")
    out = idea_dir / "playtest" / "table" / f"run_{slug}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    site = game_site.build_site(idea_dir)

    use = run_state.usage
    total_in = use["in"] + use["cached"]
    print(f"\nTABLE RUN {seats_client.name}  {len(run_state.games)} games, "
          f"{sum(g['decisions'] for g in run_state.games)} decisions, "
          f"{elapsed:.0f}s")
    print(f"  tokens  in {total_in} (cached {use['cached']}, "
          f"{use['cached'] / max(total_in, 1):.0%}), out {use['out']}, "
          f"calls {use['calls']}"
          + (f", cost ${use['cost_usd']:.4f}" if use["cost_usd"] else ""))
    tally = {k: 0 for k in DECISIONS + ("unstated",)}
    for game in run_state.games:
        for counts in game["decisions_by_seat"].values():
            for k, n in counts.items():
                tally[k] += n
    total = sum(tally.values()) or 1
    print("  decisions  " + ", ".join(
        f"{k} {tally[k]} ({tally[k]/total:.0%})" for k in DECISIONS
        if tally[k]) + (f", unstated {tally['unstated']}"
                        if tally["unstated"] else ""))
    print(f"  rules questions raised in play: {len(run_state.questions)}")
    gaps = [g for g in run_state.games if g["undefined"]]
    if gaps:
        print(f"  RULES RAN OUT in {len(gaps)}/{len(run_state.games)} games:")
        for g in gaps:
            print(f"    {g['label']} after {g['decisions']} decisions: "
                  f"{g['undefined'][:160]}")
    leaks = run_state.leaked_seats()
    if leaks:
        print("  LEAK  a seat was sent something addressed to another seat: "
              + ", ".join(leaks))
    if any(g["seed_blind"] for g in run_state.games):
        print("  SEED BLIND  this engine deals the same opening every time, "
              "so games at one seat count are one game repeated")
    print(f"  summary {out}")
    print(f"  replay {site}")
    print(f"  player vs player  python board-game/tools/game_site.py serve "
          f"{idea_dir}")
    return 0


def main(argv: list | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("idea_dir", type=Path)
    ap.add_argument("--schedule", default="",
                    help="override syntax retained for reproducibility; the "
                         "only accepted production shape is four games at "
                         "idea.json players.max")
    ap.add_argument("--wire", choices=("anthropic", "openai", "stdio"),
                    default="anthropic")
    ap.add_argument("--stream", action=argparse.BooleanOptionalAction,
                    default=True,
                    help="consume the reply as server-sent events. On by "
                         "default: a buffered request that goes quiet for a "
                         "minute is a request this gateway kills, and a seat "
                         "thinking about a wide position goes quiet for "
                         "exactly that long. --no-stream to compare")
    ap.add_argument("--no-cache", action="store_true",
                    help="anthropic wire only: drop the cache_control marker "
                         "on the static brief, to measure what it saves")
    ap.add_argument("--model", default="")
    ap.add_argument("--engine", type=Path, default=None)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--label-prefix", default="",
                    help="session prefix; by default derived from the current "
                         "idea.json hash so different rules iterations cannot "
                         "overwrite one another")
    ap.add_argument("--overwrite", action="store_true",
                    help="allow this run to replace existing session files")
    ap.add_argument("--breaker-seat", type=int, default=0)
    ap.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    ap.add_argument("--compact", action="store_true", default=True)
    ap.add_argument("--no-compact", dest="compact", action="store_false")
    return asyncio.run(run(ap.parse_args(argv)))


if __name__ == "__main__":
    sys.exit(main())

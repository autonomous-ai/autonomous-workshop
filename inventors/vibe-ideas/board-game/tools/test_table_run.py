"""test_table_run.py — fixtures for the played table, with no model.

`table_run.py` cannot be tested against a real endpoint on every change: it
would cost money, it would be slow, and worst of all its answers would move
between runs, so a failure would never tell you whether the harness broke or
the model had an off day. So the model is replaced by a local HTTP server that
answers deterministically, and everything that is actually this file's job
becomes checkable: that a seat only ever sees its own position, that a reply
is parsed strictly, that an unreadable reply stops the run instead of being
quietly played by a policy, that the session written replays through
`playtest.py`, and that the token accounting adds up.

The one thing these fixtures cannot check is whether the players say anything
worth reading. That needs a real model and it is what a real run is for.

    .venv/bin/python board-game/tools/test_table_run.py
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import re
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import playtest  # noqa: E402
import table_run  # noqa: E402
import animation_gate  # noqa: E402

MOVE_LINE = re.compile(r"^  (\d+)  ", re.M)

# Fixed so the accounting is checkable by multiplication rather than by trust.
USAGE = {"input_tokens": 10, "output_tokens": 5,
         "cache_read_input_tokens": 7, "cache_creation_input_tokens": 0}

# A game small enough to finish in a handful of decisions, so a fixture run is
# a second rather than a minute, and simple enough that the expected scores can
# be worked out by hand: each seat takes tokens off a shared pile and the
# largest total wins.
ENGINE = '''
"""engine.py — fixture, an executable model of nothing in particular."""


class Undefined(Exception):
    """The rules do not say."""


SLUG = "fixture"
PLAYERS = (2, 4)
MAX_TURNS = 40
MOVE_KINDS = ("take",)
HIDDEN_INFO = False
ASSUMPTIONS = []
CHOICES = {}


def new_game(n_players, rng):
    pile = [1, 2, 3, 4, 5, 6, 7, 8]
    rng.shuffle(pile)
    return {"pile": pile, "held": [[] for _ in range(n_players)],
            "seat": 0, "n": n_players}


def player_to_move(state):
    return state["seat"]


def legal_moves(state):
    return [("take", i) for i in range(len(state["pile"]))]


def apply_move(state, move, rng):
    state["held"][state["seat"]].append(state["pile"].pop(move[1]))
    state["seat"] = (state["seat"] + 1) % state["n"]
    return state


def is_over(state):
    return not state["pile"]


def scores(state):
    return [float(sum(h)) for h in state["held"]]


def winners(state):
    best = max(scores(state))
    return [i for i, s in enumerate(scores(state)) if s == best]
'''

IDEA = {
    "slug": "fixture", "title": "Fixture", "concept": "Take tokens.",
    "players": {"min": 2, "max": 4}, "playtime_min": 5,
    "components": [{"name": "token", "qty": 8, "desc": "A token."}],
    "rules": {"setup": [{"text": "Shuffle the pile."}],
              "turn": [{"text": "Take one token."}],
              "win": {"text": "Most points wins."}},
}


def text_of(content) -> str:
    """A message body is a string on one wire and a list of blocks on another.

    The tool has to write both, so the stand-in endpoint has to read both,
    and the newlines have to survive: the fixture model finds its move by
    matching the numbered list in the position block, exactly as a real one
    would.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content
                         if isinstance(b, dict))
    return str(content)


class Gone(Exception):
    """The gateway giving up, as distinct from the model answering badly."""


class Endpoint:
    """A model that always takes the first option, and can be told to misbehave."""

    def __init__(self, mode: str = "good"):
        self.mode = mode
        self.seen: list = []
        self.bodies: list = []
        self.server = HTTPServer(("127.0.0.1", 0), self._handler())
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever,
                                       daemon=True)
        self.thread.start()

    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    def _answer(self, text: str) -> str:
        self.seen.append(text)
        if "Debrief now" in text or "get smaller" in text:
            # A question held back until the debrief is still a question, and
            # a run that only scans move replies loses it.
            return ("Nothing mattered.\nI would not play again.\n"
                    "RULES QUESTION rules:win never says who breaks a tie")
        if self.mode == "unreadable":
            return "I think I will take the small one, it seems wise."
        if self.mode == "gateway_dies" and len(self.seen) > 1:
            raise Gone()
        if self.mode == "out_of_range":
            return "CHOICE 999\nWHY off the end\nDECISION real"
        idx = MOVE_LINE.search(text)
        return (f"CHOICE {idx.group(1) if idx else 0}\n"
                f"WHY first option\nDECISION indifferent")

    def _handler(self):
        endpoint = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):
                return

            def _sse(self, events: list) -> None:
                """The only shape the tool accepts, on either wire.

                Buffered replies are not supported and must not be, because a
                real endpoint answered a buffered request with 38 seconds and
                an empty body, then answered the same prompt streamed in 4.
                A fixture that served JSON would let that regression back in.
                """
                self.send_response(200)
                self.send_header("content-type", "text/event-stream")
                self.end_headers()
                for event in events:
                    self.wfile.write(f"data: {json.dumps(event)}\n\n".encode())
                self.wfile.write(b"data: [DONE]\n\n")
                self.wfile.flush()

            def _buffered(self, reply: str, openai: bool) -> None:
                if openai:
                    payload = {"choices": [{"message": {"content": reply}}],
                               "usage": {
                                   "prompt_tokens":
                                       (USAGE["input_tokens"]
                                        + USAGE["cache_read_input_tokens"]),
                                   "completion_tokens": USAGE["output_tokens"],
                                   "prompt_tokens_details": {
                                       "cached_tokens":
                                           USAGE["cache_read_input_tokens"]}}}
                else:
                    payload = {"content": [
                        # Scratch work alongside the answer, which must not
                        # reach the parser on this path either.
                        {"type": "thinking", "text": "CHOICE 7 maybe? no."},
                        {"type": "text", "text": reply}], "usage": USAGE}
                raw = json.dumps(payload).encode()
                self.send_response(200)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def _openai(self, reply: str) -> None:
                self._sse([
                    {"choices": [{"delta": {"content": reply}}]},
                    {"choices": [], "usage": {
                        # The whole prompt, cached part included: the other
                        # wire's field excludes it, and a harness that adds
                        # the two on this one reports double.
                        "prompt_tokens": (USAGE["input_tokens"]
                                          + USAGE["cache_read_input_tokens"]),
                        "completion_tokens": USAGE["output_tokens"],
                        "prompt_tokens_details": {
                            "cached_tokens":
                                USAGE["cache_read_input_tokens"]}}},
                ])

            def _anthropic(self, reply: str) -> None:
                self._sse([
                    {"type": "message_start",
                     "message": {"usage": {
                         "input_tokens": USAGE["input_tokens"],
                         "cache_read_input_tokens":
                             USAGE["cache_read_input_tokens"],
                         "cache_creation_input_tokens": 0}}},
                    {"type": "content_block_start", "index": 0,
                     "content_block": {"type": "text", "text": ""}},
                    # Scratch work on the same stream, which must not reach
                    # the parser: a CHOICE the model wrote while still
                    # weighing is not the move it settled on.
                    {"type": "content_block_delta", "index": 0,
                     "delta": {"type": "thinking_delta",
                               "thinking": "CHOICE 7 maybe? no."}},
                    {"type": "content_block_delta", "index": 0,
                     "delta": {"type": "text_delta", "text": reply}},
                    {"type": "content_block_stop", "index": 0},
                    {"type": "message_delta",
                     "usage": {"output_tokens": USAGE["output_tokens"]}},
                    {"type": "message_stop"},
                ])

            def do_POST(self):
                size = int(self.headers["content-length"])
                body = json.loads(self.rfile.read(size))
                endpoint.bodies.append(body)
                try:
                    reply = endpoint._answer(
                        text_of(body["messages"][-1]["content"]))
                except Gone:
                    self.send_response(504)
                    self.send_header("content-length", "0")
                    self.end_headers()
                    return
                openai = self.path.endswith("/chat/completions")
                if not body.get("stream"):
                    self._buffered(reply, openai)
                elif openai:
                    self._openai(reply)
                else:
                    self._anthropic(reply)

        return Handler


def make_idea(root: Path) -> Path:
    idea_dir = root / "fixture"
    (idea_dir / "playtest").mkdir(parents=True)
    (idea_dir / "idea.json").write_text(json.dumps(IDEA), encoding="utf-8")
    (idea_dir / "playtest" / "engine.py").write_text(ENGINE, encoding="utf-8")
    return idea_dir


def summary_of(idea_dir: Path) -> dict:
    """The one run summary in this idea's table directory.

    Named by the transport, so hard-coding `run_anthropic_cached.json` here
    made three cases fail the day the streaming default flipped — a change
    that affected none of what they check. A case that does not care which
    wire it ran on should not have to be edited when the wire changes.
    """
    found = sorted((idea_dir / "playtest" / "table").glob("run_*.json"))
    if len(found) != 1:
        raise AssertionError(f"wanted one run summary, found {found}")
    return json.loads(found[0].read_text(encoding="utf-8"))


def run_table(idea_dir: Path, endpoint: Endpoint, extra: list) -> int:
    idea_path = idea_dir / "idea.json"
    if idea_path.is_file():
        video = idea_dir / animation_gate.VIDEO_REL
        video.parent.mkdir(parents=True, exist_ok=True)
        video.write_bytes(b"approved fixture animation")
        video_hash = animation_gate.sha256(video)
        (idea_dir / animation_gate.MANIFEST_REL).write_text(json.dumps({
            "idea_sha256": animation_gate.sha256(idea_path),
            "video_sha256": video_hash,
            "video": str(animation_gate.VIDEO_REL),
        }), encoding="utf-8")
        (idea_dir / animation_gate.REVIEW_REL).write_text(
            f"Verdict: PASS\nVideo SHA256: {video_hash}\n", encoding="utf-8")
    os.environ["PLAYTEST_BASE_URL"] = endpoint.url()
    os.environ["PLAYTEST_API_KEY"] = "fixture"
    os.environ["PLAYTEST_MODEL"] = "fixture-model"
    # The tool narrates a real run, which is right there and noise here.
    with contextlib.redirect_stdout(io.StringIO()):
        return table_run.main([str(idea_dir)] + extra)


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------

def check_parse() -> list:
    """The strict half of the contract, checked without a server at all."""
    bad = []
    good = table_run.parse_reply(
        "CHOICE 2\nWHY holding back keeps both tiers open\nDECISION real\n"
        "RULES QUESTION rules:turn[5] says nothing about ties\n"
        "NOTE fourth turn running with nothing to weigh", 5)
    if not good:
        return ["a well-formed reply did not parse"]
    for field, want in (("choice", 2), ("arbitrary", False),
                        ("decision", "real")):
        if good[field] != want:
            bad.append(f"{field} read as {good[field]!r}, wanted {want!r}")
    if good["question"] != ["rules:turn[5] says nothing about ties"]:
        bad.append(f"rules question read as {good['question']!r}")
    if good["note"] != ["fourth turn running with nothing to weigh"]:
        bad.append(f"note read as {good['note']!r}")
    # Every word but `real` means the seat did not have a decision, and the
    # three of them mean three different things that must stay distinguishable.
    for word in ("forced", "indifferent", "scripted"):
        got = table_run.parse_reply(f"CHOICE 1\nDECISION {word}", 5)
        if not got["arbitrary"] or got["decision"] != word:
            bad.append(f"DECISION {word} read as {got!r}")
    if table_run.parse_reply("CHOICE 1\nDECISION maybe", 5)["decision"] != "unstated":
        bad.append("a word outside the four was not recorded as unstated")

    # A reasoning model's scratch work turns up inside the reply on some
    # gateways. It has to be cut, not searched: a CHOICE the model wrote while
    # still weighing options is not the move it settled on.
    thought = table_run.parse_reply(
        "<mm:think>Maybe CHOICE 0, or CHOICE 1. Let me weigh both.</mm:think>\n"
        "CHOICE 4\nWHY it forces the reply I want\nDECISION real", 5)
    if not thought or thought["choice"] != 4:
        bad.append(f"a reply with a think block parsed as {thought!r}")
    tail = table_run.parse_reply(
        "still weighing this</think>\nCHOICE 2\nWHY settled\nDECISION real", 5)
    if not tail or tail["choice"] != 2:
        bad.append(f"a reply with a trimmed think block parsed as {tail!r}")
    if table_run.parse_reply(
            "<think>I could take CHOICE 1 here and then", 5) is not None:
        bad.append("read a move out of a thought the model never finished")

    for text, why in (
            ("I pick the second one", "prose with no CHOICE line"),
            ("CHOICE 9", "an index past the end of the list"),
            ("CHOICE two", "a spelled-out index"),
            ("the CHOICE 1 is inline", "CHOICE buried mid-line")):
        if table_run.parse_reply(text, 5) is not None:
            bad.append(f"accepted {why}")
    return bad


def check_full_run(idea_dir: Path) -> list:
    """A whole four-game max-player run, sessions, accounting, no leak."""
    endpoint = Endpoint()
    bad = []
    try:
        code = run_table(idea_dir, endpoint,
                          ["--schedule", "4:4", "--label-prefix", "f"])
    finally:
        endpoint.stop()
    if code != 0:
        return [f"table_run exited {code}"]

    summary = summary_of(idea_dir)
    if len(summary["games"]) != 4:
        bad.append(f"{len(summary['games'])} games recorded, wanted 4")
    modes = [game.get("knowledge_mode") for game in summary["games"]]
    if modes != ["fresh", "current-run-experienced",
                 "current-run-experienced",
                 "current-and-prior-iteration-experienced"]:
        bad.append(f"wrong four-game knowledge sequence: {modes}")
    if summary["leaks"]:
        bad.append(f"leak reported on a run that routes by code: {summary['leaks']}")
    if summary["usage"]["calls"] < 8:
        bad.append(f"only {summary['usage']['calls']} calls billed")
    if summary["usage"]["cached"] != summary["usage"]["calls"] * 7:
        bad.append("cached tokens do not add up over the calls made")
    site = idea_dir / "playtest" / "site"
    if not (site / "index.html").is_file():
        bad.append("the run did not create its replay website")
    elif not (site / "data.json").is_file():
        bad.append("the replay website has no generated run data")
    else:
        index = (site / "index.html").read_text(encoding="utf-8")
        if 'id="game-data"' not in index:
            bad.append("the replay website cannot load from a local file link")
        replay = json.loads((site / "data.json").read_text(encoding="utf-8"))
        if not replay.get("runs") or not replay["runs"][0].get("games"):
            bad.append("the replay website contains no LLM games")

    # Every seat gets a closing question, and every seat that played a game
    # gets a debrief for it, so a seat that sat out the 2p game still has to
    # be there at the end. That is the run keeping its players alive.
    ends = [d for d in summary["debriefs"] if d["game"] == "RUN END"]
    if len(ends) != 4:
        bad.append(f"{len(ends)} closing answers, wanted one per seat (4)")
    debrief_qs = [q for q in summary["rules_questions"]
                  if "breaks a tie" in q["text"]]
    if not debrief_qs:
        bad.append("a rules question raised in a debrief was not recorded")
    elif any(q["turn"] is not None for q in debrief_qs):
        bad.append("a debrief question was stamped with a turn number it "
                   "was not asked on")

    for record in summary["games"]:
        session = json.loads(Path(record["session"]).read_text(encoding="utf-8"))
        if any(m["by"] != "player" for m in session["moves"]):
            bad.append(f"{record['label']} has a move nobody played")
        eng = playtest.load_engine(Path(session["engine"]))
        state, _ = playtest.replay(eng, session)
        if not eng.is_over(state):
            bad.append(f"{record['label']} does not replay to a finished game")
        elif list(eng.winners(state)) != record["winners"]:
            bad.append(f"{record['label']} replays to different winners")
        if record["seed_blind"]:
            bad.append("a shuffling engine was called seed blind")
    return bad


def check_seat_isolation(idea_dir: Path) -> list:
    """No seat may ever be handed a block addressed to another seat."""
    endpoint = Endpoint()
    try:
        run_table(idea_dir, endpoint,
                   ["--schedule", "4:4", "--label-prefix", "iso"])
    finally:
        endpoint.stop()
    bad = []
    for text in endpoint.seen:
        addressed = set(re.findall(r"^YOU ARE seat (\d+)", text, re.M))
        if len(addressed) > 1:
            bad.append(f"one message addressed seats {sorted(addressed)}")
    return bad


def check_prior_iteration_arrives_only_before_game_four(idea_dir: Path) -> list:
    """Old playtest experience is delayed and remains seat-specific."""
    history = idea_dir / "history" / "reworks"
    history.mkdir(parents=True)
    (history / "iteration-1.json").write_text(json.dumps({
        "table_experience": {
            "source": "old/run.json",
            "debriefs": [
                {"game": "old1", "seat": seat,
                 "text": f"seat-{seat}-private-old-lesson"}
                for seat in range(4)
            ],
        },
    }), encoding="utf-8")
    endpoint = Endpoint()
    try:
        code = run_table(idea_dir, endpoint,
                         ["--schedule", "4:4", "--label-prefix", "prior"])
    finally:
        endpoint.stop()
    if code != 0:
        return [f"table_run exited {code}"]
    bad = []
    injections = [text for text in endpoint.seen
                  if text.startswith("PRIOR ITERATION EXPERIENCE")]
    if len(injections) != 4:
        bad.append(f"{len(injections)} experience injections, wanted 4")
    for seat in range(4):
        lesson = f"seat-{seat}-private-old-lesson"
        holders = [i for i, text in enumerate(injections) if lesson in text]
        if holders != [seat]:
            bad.append(f"{lesson} reached injection indexes {holders}")
    first_injection = next(
        (i for i, text in enumerate(endpoint.seen)
         if text.startswith("PRIOR ITERATION EXPERIENCE")), None)
    last_game_three = max(
        (i for i, text in enumerate(endpoint.seen)
         if "session prior3" in text), default=-1)
    if first_injection is None or first_injection <= last_game_three:
        bad.append("prior-iteration experience arrived before game 3 ended")
    summary = summary_of(idea_dir)
    if not all(item["available"] for item in summary["experience_injections"]):
        bad.append("the run summary did not mark archived experience available")
    return bad


def check_unreadable_stops(idea_dir: Path, mode: str) -> list:
    """A seat that cannot answer must stop the run, loudly.

    The tempting failure here is to let a scripted policy finish the game so
    the run produces something. It would produce a session file that reads
    exactly like a game players finished, which is the one outcome this whole
    stage exists to prevent.
    """
    endpoint = Endpoint(mode=mode)
    try:
        run_table(idea_dir, endpoint, ["--schedule", "4:4",
                                        "--label-prefix", f"{mode}_"])
    except SystemExit as exc:
        message = str(exc)
        bad = []
        if "TABLE ERROR" not in message:
            bad.append(f"stopped with an unhelpful message: {message!r}")
        # The message has to carry the rejected reply. Whoever reads it is
        # trying to tell an empty response from a refusal from a model
        # answering in prose, and only the text distinguishes those.
        if "What it actually sent" not in message:
            bad.append("the error does not show what the seat replied")
        elif mode == "unreadable" and "seems wise" not in message:
            bad.append("the error shows no trace of the actual reply text")
        # The abandoned game is the reproduction and must survive the failure.
        saved = list((idea_dir / "playtest" / "table").glob(f"{mode}_*.json"))
        if not saved:
            bad.append("the abandoned game was not written, so the position "
                       "that defeated the seat cannot be replayed")
        elif json.loads(saved[0].read_text(encoding="utf-8")
                        ).get("abandoned_at") is None:
            bad.append("the saved session does not record being abandoned")
        return bad
    finally:
        endpoint.stop()
    return [f"a {mode} reply did not stop the run"]


def check_a_dead_gateway_still_leaves_the_game(idea_dir: Path) -> list:
    """A transport that gives up must leave the position behind it.

    This is the same argument as an unreadable reply and it took a real run to
    notice the code only made it in one of the two places. Millbind died on a
    504 after 252 seconds and wrote nothing at all: no session, no turn
    number, no move count, just a traceback through `urlopen`. The position
    that caused it is the entire finding — a wide position is exactly what a
    gateway times out on — and the one case that most needed a reproduction
    was the one case that produced none.
    """
    endpoint = Endpoint(mode="gateway_dies")
    retries, backoff = table_run.GATEWAY_RETRIES, table_run.RETRY_BACKOFF
    table_run.GATEWAY_RETRIES, table_run.RETRY_BACKOFF = 1, 0.0
    try:
        run_table(idea_dir, endpoint, ["--schedule", "4:4",
                                       "--label-prefix", "dead_"])
    except SystemExit as exc:
        message = str(exc)
        bad = []
        if "504" not in message:
            bad.append(f"the error hides what the gateway said: {message!r}")
        # Turn and width are what tell a reader whether this was the wire or
        # the position, and a traceback carries neither.
        if " at turn " not in message or " moves" not in message:
            bad.append("the error names neither the turn nor how many moves "
                       "the position offered, so the run cannot be located")
        saved = list((idea_dir / "playtest" / "table").glob("dead_*.json"))
        if not saved:
            return bad + ["the partial game was not written, so the position "
                          "the gateway died on cannot be replayed"]
        session = json.loads(saved[0].read_text(encoding="utf-8"))
        if session.get("abandoned_at") is None:
            bad.append("the saved session does not record being abandoned")
        if "504" not in (session.get("abandoned_because") or ""):
            bad.append("the saved session does not say the gateway was why")
        # A reproduction is a seed and a list of choices. Zero moves would
        # still satisfy every check above and replay to nothing.
        if not session.get("moves"):
            bad.append("the saved session holds no moves, so it replays to "
                       "the opening rather than to the position")
        return bad
    finally:
        table_run.GATEWAY_RETRIES, table_run.RETRY_BACKOFF = retries, backoff
        endpoint.stop()
    return ["a dead gateway did not stop the run"]


def check_refuses_to_overwrite(idea_dir: Path) -> list:
    """A second run on the same labels must stop before spending anything.

    A session records what a player chose, and nothing re-derives it: the same
    seed and the same prompt do not give the same game back. This very check
    exists because a run was launched with the default prefix over five
    sessions another table had played, and only a `git checkout` got them
    back.
    """
    endpoint = Endpoint()
    bad = []
    try:
        if run_table(idea_dir, endpoint, ["--schedule", "4:4",
                                          "--label-prefix", "dup"]) != 0:
            return ["the first run failed"]
        if run_table(idea_dir, endpoint, ["--schedule", "4:4",
                                          "--label-prefix", "dup"]) == 0:
            bad.append("a second run on the same labels was allowed")
        before = (idea_dir / "playtest" / "table" / "dup1.json").read_text(
            encoding="utf-8")
        # A different seed, so the replacement is visibly a different game.
        # With the same seed this fixture answers identically and the file
        # would come back byte for byte, which proves nothing either way.
        if run_table(idea_dir, endpoint,
                     ["--schedule", "4:4", "--label-prefix", "dup",
                      "--seed", "99", "--overwrite"]) != 0:
            bad.append("--overwrite did not let the run through")
        after = (idea_dir / "playtest" / "table" / "dup1.json").read_text(
            encoding="utf-8")
        if before == after:
            bad.append("--overwrite ran but left the old session in place")
    finally:
        endpoint.stop()
    return bad


GAP_ENGINE = ENGINE.replace(
    "def apply_move(state, move, rng):",
    "def apply_move(state, move, rng):\n"
    "    if len(state['pile']) == 5:\n"
    "        raise Undefined(\"rules:turn[3]: the rules do not say what "
    "happens when the pile runs to five\")")


def check_rules_running_out(idea_dir: Path) -> list:
    """An engine refusing mid-game is the best thing this stage produces.

    It arrives as an exception, and the tempting thing is to let it end the
    run. That would throw away the game that reached the gap, and that game is
    the reproduction: a seed and a list of choices that walks anybody straight
    back to it. So it is caught, recorded on the session, put to the players as
    something to react to, and reported. What must never happen is the harness
    ruling on it, because the silence is the finding.
    """
    (idea_dir / "playtest" / "engine.py").write_text(GAP_ENGINE,
                                                     encoding="utf-8")
    endpoint = Endpoint()
    bad = []
    try:
        code = run_table(idea_dir, endpoint,
                         ["--schedule", "4:4", "--label-prefix", "gap"])
    finally:
        endpoint.stop()
    if code != 0:
        return [f"a rules gap ended the run with exit {code} instead of "
                f"being reported as the finding it is"]

    summary = summary_of(idea_dir)
    game = summary["games"][0]
    if not game["undefined"]:
        bad.append("the game was not marked as having hit a rules gap")
    elif "rules:turn[3]" not in game["undefined"]:
        bad.append(f"the gap lost its rule id: {game['undefined']!r}")
    if game["finished"]:
        bad.append("a game that stopped at a rules gap was recorded finished")
    if not any("ENGINE REFUSED" in q["text"]
               for q in summary["rules_questions"]):
        bad.append("the gap was not raised as a rules question")
    if not any("The rules do not cover the position it reached" in seen
               for seen in endpoint.seen):
        bad.append("the players were never told the game stopped on a gap")
    if not any("rules:turn[3]" in seen for seen in endpoint.seen):
        bad.append("the players were told it stopped but not on what")

    session = json.loads(Path(game["session"]).read_text(encoding="utf-8"))
    if not session["moves"]:
        bad.append("nothing was recorded, so the gap cannot be reproduced")
    return bad


def check_both_wires_count_alike(idea_dir: Path) -> list:
    """The same games on either wire must report the same prompt size.

    They do not report it the same way. `prompt_tokens` is the whole prompt
    with the cached part inside it; `input_tokens` counts only what was not
    served from cache. Add the cached figure to both and one wire appears to
    cost twice the other for identical work, which is exactly the false
    result this harness was built to produce comparisons for.
    """
    bad = []
    totals = {}
    # Both transports explicitly, so this stays a comparison of the two
    # rather than of the default against itself.
    for wire, extra, suffix in (("anthropic", ["--no-stream"], ""),
                                ("openai", ["--no-stream"], ""),
                                ("anthropic", ["--stream"], "_stream"),
                                ("openai", ["--stream"], "_stream")):
        endpoint = Endpoint()
        label = wire[:2] + suffix
        try:
            if run_table(idea_dir, endpoint,
                         ["--schedule", "4:4", "--wire", wire,
                          "--label-prefix", label] + extra) != 0:
                return [f"the {wire}{suffix} run failed"]
        finally:
            endpoint.stop()
        name = f"{wire}_cached{suffix}"
        use = json.loads((idea_dir / "playtest" / "table"
                          / f"run_{name}.json").read_text("utf-8"))["usage"]
        totals[wire + suffix] = (use["in"] + use["cached"], use["calls"])
    counts = {k: v for k, v in totals.items()}
    if len(set(c for _, c in counts.values())) != 1:
        bad.append(f"call counts differ across wires: {counts}")
    elif len(set(t for t, _ in counts.values())) != 1:
        bad.append(f"the same games counted different prompt totals "
                   f"depending on wire and streaming: {counts}")
    return bad


CASES = [
    ("reply_parsing_is_strict", lambda d: check_parse()),
    ("a_whole_run_end_to_end", check_full_run),
    ("no_seat_sees_another_seats_position", check_seat_isolation),
    ("prior_iteration_experience_arrives_only_before_game_four",
     check_prior_iteration_arrives_only_before_game_four),
    ("prose_instead_of_a_choice_stops_the_run",
     lambda d: check_unreadable_stops(d, "unreadable")),
    ("an_index_past_the_end_stops_the_run",
     lambda d: check_unreadable_stops(d, "out_of_range")),
    ("a_dead_gateway_still_leaves_the_game",
     check_a_dead_gateway_still_leaves_the_game),
    ("a_rerun_will_not_quietly_destroy_the_sessions",
     check_refuses_to_overwrite),
    ("rules_running_out_is_reported_not_raised", check_rules_running_out),
    ("both_wires_count_the_same_prompt_alike", check_both_wires_count_alike),
]


def main() -> int:
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        for name, case in CASES:
            idea_dir = make_idea(Path(tmp) / name)
            try:
                bad = case(idea_dir)
            except Exception as exc:  # a crash is a failure, not a stack trace
                bad = [f"raised {type(exc).__name__}: {exc}"]
            if bad:
                failures += 1
                print(f"  FAIL  table_run/{name}")
                for line in bad:
                    print(f"          {line}")
            else:
                print(f"  ok  table_run/{name}")
    if failures:
        print(f"\n{failures} FAILED of {len(CASES)} cases")
        return 1
    print(f"\nALL PASS ({len(CASES)} cases)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""ABO's model seats: a model decides each turn, and no part of this is an agent.

`agent-playtest` has to come from games in which each seat's decision is made by
an independent model. The loop that renders a position, asks the seat whose turn
it is, reads back one choice and applies it is deterministic code — this file —
and the model's only power is to name an index into the moves the engine already
enumerated. Anything else it says is refused rather than interpreted.

The boundary is the point. A seat is shown one rendering of what that seat is
permitted to see and the numbered list of its legal moves, and nothing else. It
holds no tools, reaches no file, cannot call the engine, cannot read the
evidence, and never sees another seat's messages — every byte a seat has been
shown is in its own transcript, so a reader can check that for themselves.

What a seat *says* about the game is a simulation finding, never a fun claim. A
seat reporting that a turn held no real decision, or that the game got smaller
once it worked it out, is recorded as exactly that. Whether people enjoy this
game is learned after delivery, through Reviews.
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

import config

EVALUATOR = "abo-model-seat-playtest"
EVALUATOR_VERSION = "1.0.0"

# Two seats, two briefs. The lane requires at least two distinct non-empty
# roles, and a role is a different way of approaching the game rather than a
# different label on the same one.
ROLES: Tuple[Dict[str, str], ...] = (
    {
        "role": "first-reading",
        "brief": (
            "You have just been handed this game and read the rules once. Play "
            "the move that looks right from the position in front of you. Do "
            "not assume a plan you have not been shown works."
        ),
    },
    {
        "role": "line-finder",
        "brief": (
            "You have played this game before and are looking for the line that "
            "wins it. Prefer a move that constrains what the other seat can do "
            "next over a move that only improves your own position."
        ),
    },
)

# What a seat is asked to say about the turn it just took. These are the words
# the imported reply parser already reads.
DECISION_KINDS = ("real", "forced", "arbitrary", "obvious")

MAX_REPLY_RETRIES = 2


class SeatBoundaryError(RuntimeError):
    """A seat tried to do something a seat is not permitted to do."""


class ModelSeatsUnavailable(RuntimeError):
    """No model-seat endpoint is configured."""


# ---------------------------------------------------------------------------
# Transports
# ---------------------------------------------------------------------------


class RecordedTransport:
    """Replay a recorded transcript. No network, ever.

    This is a transport substitution and not a policy fallback: the recorded
    replies are what a model actually said, and if the run asks a question the
    transcript does not answer, this raises rather than inventing a reply. A
    synthesized transcript would make `agent-playtest` a claim about a model
    that never played.
    """

    name = "recorded-transcript"
    live = False

    def __init__(self, transcript: Mapping[str, Any]) -> None:
        self.transcript = dict(transcript)
        self._replies: Dict[str, List[str]] = {
            key: list(value) for key, value in dict(transcript.get("replies", {})).items()
        }
        self._systems: Dict[str, str] = {}
        self.asked: List[Dict[str, str]] = []

    @classmethod
    def from_path(cls, path: Path) -> "RecordedTransport":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def open_seat(self, key: str, system: str) -> None:
        self._systems[key] = system

    def ask(self, key: str, text: str) -> str:
        self.asked.append({"key": key, "text": text})
        pending = self._replies.get(key)
        if not pending:
            raise ModelSeatsUnavailable(
                "the recorded transcript has no further reply for %s; a recorded "
                "run stops where the recording stops rather than inventing what "
                "the model would have said" % key
            )
        return pending.pop(0)


class HttpModelSeats:
    """One plain HTTPS call per decision, through the imported harness.

    The endpoint, key and model are read through the Workshop's own
    `load_dotenv` under ABO-scoped names. Nothing here holds a session open
    anywhere else: the whole state of the table is two dicts in this process,
    which is what makes the seat boundary auditable rather than promised.
    """

    live = True

    def __init__(self, seats) -> None:
        self._seats = seats
        self.name = seats.name

    @classmethod
    def from_env(cls, *, dotenv_path: Optional[str] = None, wire: str = "openai"):
        missing = config.missing_model_seat_settings(dotenv_path)
        if missing:
            raise ModelSeatsUnavailable(
                "no model-seat endpoint is configured (%s)" % ", ".join(missing)
            )
        settings = config.load_model_seat_environment(dotenv_path)
        harness = config.load_harness("table_run")
        return cls(
            harness.Seats(
                settings[config.ENV_MODEL_SEAT_BASE_URL],
                settings[config.ENV_MODEL_SEAT_API_KEY],
                settings[config.ENV_MODEL_SEAT_MODEL],
                wire,
                max_tokens=1024,
                cache=True,
            )
        )

    def open_seat(self, key: str, system: str) -> None:
        import asyncio

        asyncio.run(self._seats.open_seat(key, system))

    def ask(self, key: str, text: str) -> str:
        import asyncio

        reply, _usage = asyncio.run(self._seats.ask(key, text))
        return reply


# ---------------------------------------------------------------------------
# What a seat is shown
# ---------------------------------------------------------------------------


def seat_view(engine, state, seat: int) -> Any:
    """Exactly what this seat is permitted to see.

    A hidden-information engine is asked for the seat's own view and the full
    state is never rendered. A declared-open engine has nothing to hide, and
    that declaration was recorded by Make so play can check it.
    """

    observation = getattr(engine, "observation", None)
    if callable(observation):
        return observation(state, seat)
    if bool(getattr(engine, "HIDDEN_INFO", False)):
        raise SeatBoundaryError(
            "the engine declares hidden information but exposes no per-seat "
            "view, so a seat cannot be prompted without showing it everything"
        )
    return state


def render_position(engine, state, seat: int, moves: Sequence[Any]) -> str:
    """The position, the numbered moves, and nothing else.

    Deliberately plain text built here rather than handed over as a structure:
    a seat receives a rendering, not a handle on the game.
    """

    view = seat_view(engine, state, seat)
    listed = "\n".join(
        "  %d. %s" % (index, _describe(move)) for index, move in enumerate(moves)
    )
    return (
        "POSITION (seat %d)\n%s\n\nYOUR LEGAL MOVES\n%s\n\n"
        "Reply with exactly:\n"
        "CHOICE <n>            the index of the move you take\n"
        "DECISION <kind>       one of %s\n"
        "WHY <one sentence>    why you took it\n"
        "You may add RULES QUESTION <...> or NOTE <...> lines."
        % (
            seat,
            json.dumps(view, indent=2, sort_keys=True, default=str),
            listed,
            "/".join(DECISION_KINDS),
        )
    )


def _describe(move: Any) -> str:
    if isinstance(move, (list, tuple)):
        return " ".join(str(part) for part in move)
    return str(move)


def seat_system_prompt(record, role: Mapping[str, str], seat: int, seats: int) -> str:
    """One seat's immutable brief: the rules, its role, and the boundary."""

    rules = []
    for phase, index, step in record.steps:
        rules.append("%s[%d]: %s" % (phase, index, step.text))
    bill = "\n".join(
        "  %s x%d — %s" % (item.name, item.qty, item.desc) for item in record.components
    )
    return (
        "You are seat %d of %d in a game of %s.\n\n"
        "THE RULES\n%s\n\nTHE PIECES\n%s\n\n"
        "YOUR ROLE: %s\n%s\n\n"
        "You may only choose from the numbered moves you are shown. You cannot "
        "see any other seat's messages, you cannot read or write any file, and "
        "you cannot ask the game a question on your own behalf — if the rules "
        "do not cover something, say so with a RULES QUESTION line and take a "
        "move anyway. You may not replay a game because it was dull."
        % (
            seat,
            seats,
            record.title,
            "\n".join(rules),
            bill,
            role["role"],
            role["brief"],
        )
    )


# ---------------------------------------------------------------------------
# The loop
# ---------------------------------------------------------------------------


@dataclass
class SeatDecision:
    seat: int
    turn: int
    choice: int
    decision: str
    why: str
    questions: Sequence[str] = field(default_factory=tuple)
    notes: Sequence[str] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seat": self.seat,
            "turn": self.turn,
            "choice": self.choice,
            "decision": self.decision,
            "why": self.why,
            "questions": list(self.questions),
            "notes": list(self.notes),
        }


def _parse(harness, reply: str, move_count: int) -> Optional[Dict[str, Any]]:
    """The imported reply parser, which already bounds the index.

    A reply that is not an index into the moves the engine enumerated comes
    back as `None` and is refused. It is never interpreted into a move: a seat
    that cannot say `CHOICE <n>` is a broken configuration, not a bad turn, and
    a policy move substituted here would be read later as a player's.
    """

    return harness.parse_reply(reply, move_count)


def play_model_seat_game(
    engine,
    record,
    transport,
    *,
    seats: int,
    game_index: int,
    seed: int,
    turn_cap: int,
    roles: Sequence[Mapping[str, str]] = ROLES,
) -> Dict[str, Any]:
    """One game, one model decision per turn, all of it deterministic here."""

    harness = config.load_harness("table_run")
    if len(roles) < seats:
        raise SeatBoundaryError(
            "%d seats need %d roles and only %d were given" % (seats, seats, len(roles))
        )
    rng = random.Random(seed)
    state = engine.new_game(seats, rng)
    decisions: List[SeatDecision] = []
    questions: List[Dict[str, Any]] = []
    notes: List[Dict[str, Any]] = []
    sent: Dict[int, List[str]] = {seat: [] for seat in range(seats)}

    for seat in range(seats):
        transport.open_seat(
            "game%d-seat%d" % (game_index, seat),
            seat_system_prompt(record, roles[seat], seat, seats),
        )

    turns = 0
    undefined = None
    while turns < turn_cap and not engine.is_over(state):
        moves = engine.legal_moves(state)
        if not moves:
            break
        seat = int(engine.player_to_move(state))
        key = "game%d-seat%d" % (game_index, seat)
        prompt = render_position(engine, state, seat, moves)
        sent[seat].append(prompt)
        parsed = None
        for _attempt in range(MAX_REPLY_RETRIES + 1):
            reply = transport.ask(key, prompt)
            parsed = _parse(harness, reply, len(moves))
            if parsed is not None:
                break
        if parsed is None:
            raise SeatBoundaryError(
                "seat %d did not return an index into its %d enumerated moves "
                "after %d attempts; a reply that is not a choice is refused "
                "rather than interpreted" % (seat, len(moves), MAX_REPLY_RETRIES + 1)
            )
        decision = SeatDecision(
            seat=seat,
            turn=turns,
            choice=int(parsed["choice"]),
            decision=str(parsed.get("decision", "unstated")),
            why=str(parsed.get("why", "")),
            questions=tuple(parsed.get("question", ())),
            notes=tuple(parsed.get("note", ())),
        )
        decisions.append(decision)
        for text in decision.questions:
            questions.append({"seat": seat, "turn": turns, "text": text})
        for text in decision.notes:
            notes.append({"seat": seat, "turn": turns, "text": text})
        try:
            state = engine.apply_move(state, moves[decision.choice], rng)
        except Exception as exc:  # noqa: BLE001
            if any(cls.__name__ == "Undefined" for cls in type(exc).__mro__):
                undefined = str(exc)
                break
            raise
        turns += 1

    completed = undefined is None and engine.is_over(state)
    return {
        "game": game_index,
        "seed": seed,
        "turns": turns,
        "completed": completed,
        "undefined": undefined,
        "winners": list(engine.winners(state)) if completed else [],
        "scores": list(engine.scores(state)),
        "roles": [dict(roles[seat]) for seat in range(seats)],
        "decisions": [item.to_dict() for item in decisions],
        "questions": questions,
        "notes": notes,
        # Every byte each seat was shown, so the boundary is auditable rather
        # than asserted.
        "sent": {str(seat): list(value) for seat, value in sent.items()},
    }


def assert_no_cross_seat_leak(game: Mapping[str, Any]) -> None:
    """No seat was ever shown text addressed to another seat."""

    sent = dict(game.get("sent", {}))
    for seat, messages in sent.items():
        for other in sent:
            if other == seat:
                continue
            for message in messages:
                if ("POSITION (seat %s)" % other) in message:
                    raise SeatBoundaryError(
                        "seat %s was shown a position addressed to seat %s"
                        % (seat, other)
                    )


# ---------------------------------------------------------------------------
# The result
# ---------------------------------------------------------------------------


def summarize(games: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """What the seats did, and what they said, kept as findings.

    A seat's report is evidence about the *game* — that a turn held no real
    decision, that the game got smaller — and never evidence that anybody
    enjoyed it.
    """

    roles: List[str] = []
    for game in games:
        for entry in game.get("roles", ()):
            role = str(entry.get("role", "")).strip()
            if role and role not in roles:
                roles.append(role)

    decisions = [item for game in games for item in game.get("decisions", ())]
    kinds: Dict[str, int] = {}
    for item in decisions:
        kind = str(item.get("decision", "unstated"))
        kinds[kind] = kinds.get(kind, 0) + 1

    decision_free = sum(
        count for kind, count in kinds.items() if kind in ("forced", "arbitrary", "obvious")
    )
    findings = []
    if decisions and decision_free:
        findings.append(
            "decision-free turns: %d of %d turns were reported by the seat "
            "taking them as forced, arbitrary, or obvious"
            % (decision_free, len(decisions))
        )
    for game in games:
        for note in game.get("notes", ()):
            text = str(note.get("text", ""))
            if _reports_shrinking(text):
                findings.append(
                    "the game got smaller: seat %s reported at turn %s — %s"
                    % (note.get("seat"), note.get("turn"), text)
                )
    questions = [item for game in games for item in game.get("questions", ())]
    for question in questions:
        findings.append(
            "rules question raised in play: seat %s at turn %s — %s"
            % (question.get("seat"), question.get("turn"), question.get("text"))
        )
    gaps = [game for game in games if game.get("undefined")]
    for game in gaps:
        findings.append(
            "the rules ran out in game %s after %s turns: %s"
            % (game.get("game"), game.get("turns"), game.get("undefined"))
        )

    completed = [game for game in games if game.get("completed")]
    return {
        "evidence_class": "ai-simulation",
        "agent_roles": roles,
        "games": len(games),
        "completed_games": len(completed),
        "decisions": len(decisions),
        "decision_kinds": kinds,
        "seat_reports": findings,
        # Named for what it is. A model seat playing to win is not obviously a
        # social player, and the lane never defines the term; this is the style
        # whose decisions come from a model rather than from a script.
        "style": "social",
        "findings": findings,
        "claim": (
            "%d games were played in which every decision was made by an "
            "independent model choosing among the moves the engine enumerated."
            % len(games)
        ),
        "evaluator": EVALUATOR,
        "evaluator_version": EVALUATOR_VERSION,
    }


_SHRINKING = (
    "smaller",
    "shrink",
    "worked it out",
    "solved",
    "same every time",
    "no longer interesting",
    "always the same",
)


def _reports_shrinking(text: str) -> bool:
    lowered = text.casefold()
    return any(phrase in lowered for phrase in _SHRINKING)


def assert_roles_are_distinct(summary: Mapping[str, Any]) -> None:
    """Two or more distinct non-empty roles, or the result does not pass."""

    roles = list(summary.get("agent_roles", ()))
    if (
        len(roles) < 2
        or any(not str(role).strip() for role in roles)
        or len(set(roles)) != len(roles)
    ):
        raise SeatBoundaryError(
            "agent-playtest needs at least two distinct non-empty roles and got "
            "%r; one role, or one role repeated, is one perspective" % (roles,)
        )


def assert_can_be_evidence(transport) -> None:
    """A recording of a past run is not evidence about this revision.

    The recorded transport exists so the whole loop — the boundary, the reply
    parsing, the refusal of a non-index — can be checked with no network and no
    credential. What it cannot do is produce a passing `agent-playtest`: those
    replies were given about some other position in some other run, and
    evidence has to be bound to the exact bytes under test.
    """

    if not getattr(transport, "live", False):
        raise ModelSeatsUnavailable(
            "these games were replayed from a recorded transcript (%s), which "
            "checks the harness but cannot be evidence about this revision; a "
            "passing agent-playtest needs seats that played these exact bytes"
            % getattr(transport, "name", "recorded")
        )


def social_sample(summary: Mapping[str, Any]) -> Dict[str, Any]:
    """What `game-simulation` reads back as its `social` style.

    The two results stay separate with separate evidence files, because they
    answer different questions: the sample size and the measured properties for
    one, the distinct roles and their reports for the other. This is a
    reference to the model-seat games, not a merge of the two records.
    """

    return {
        "source": "model-seats",
        "completed_games": int(summary.get("completed_games", 0)),
        "decisions": int(summary.get("decisions", 0)),
        "agent_roles": list(summary.get("agent_roles", ())),
        "evaluator": EVALUATOR,
        "evaluator_version": EVALUATOR_VERSION,
    }


def transcript_digest(transcript: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(transcript, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


__all__ = [
    "DECISION_KINDS",
    "EVALUATOR",
    "EVALUATOR_VERSION",
    "HttpModelSeats",
    "MAX_REPLY_RETRIES",
    "ModelSeatsUnavailable",
    "ROLES",
    "RecordedTransport",
    "SeatBoundaryError",
    "SeatDecision",
    "assert_can_be_evidence",
    "assert_no_cross_seat_leak",
    "assert_roles_are_distinct",
    "play_model_seat_game",
    "render_position",
    "seat_system_prompt",
    "seat_view",
    "social_sample",
    "summarize",
    "transcript_digest",
]

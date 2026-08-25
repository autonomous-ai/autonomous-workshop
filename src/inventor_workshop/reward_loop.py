"""Content-addressed reward loops for self-improving Workshop stages."""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from .errors import ContractError
from .models import require_exact_version, require_json_mapping, require_sha256


_JOURNAL_SCHEMA_VERSION = 1
_MAX_JOURNAL_BYTES = 16 * 1024 * 1024
_LOOP_ID = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
_STEP_FILE = re.compile(r"^(\d{6})-([0-9a-f]{64})\.json$")
_PENDING_FILE = re.compile(r"^\.pending-[0-9a-f]{32}\.json$")


def _copy_mapping(value: Mapping[str, Any], label: str) -> Dict[str, Any]:
    require_json_mapping(value, label)
    try:
        copied = json.loads(
            json.dumps(
                dict(value),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )
        )
    except (TypeError, ValueError) as exc:
        raise ContractError("%s must be finite JSON" % label) from exc
    if not copied:
        raise ContractError("%s must not be empty" % label)
    return copied


def json_sha256(value: Mapping[str, Any]) -> str:
    copied = _copy_mapping(value, "reward-loop value")
    encoded = json.dumps(
        copied,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _canonical_json_bytes(value: Mapping[str, Any], label: str) -> bytes:
    copied = _copy_mapping(value, label)
    return json.dumps(
        copied,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _identity(
    identity: str, version: str, config_sha256: str, label: str
) -> Dict[str, str]:
    if not isinstance(identity, str) or not identity.strip() or len(identity) > 200:
        raise ContractError("%s identity must be bounded, non-empty text" % label)
    require_exact_version(version, "%s version" % label)
    require_sha256(config_sha256, "%s config_sha256" % label)
    return {
        "identity": identity,
        "version": version,
        "config_sha256": config_sha256,
    }


@dataclass(frozen=True)
class RewardLoopBinding:
    """Immutable identity for one resumable reward loop.

    ``max_steps`` is the bounded work allowance for each invocation. A later
    invocation may append another bounded batch, but only under this exact
    binding and after replaying the sealed prefix.
    """

    loop_id: str
    inputs_sha256: str
    initial_state_sha256: str
    goal: int
    max_steps: int
    max_total_steps: int
    creator_identity: str
    creator_version: str
    creator_config_sha256: str
    evaluator_identity: str
    evaluator_version: str
    evaluator_config_sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.loop_id, str) or not _LOOP_ID.fullmatch(self.loop_id):
            raise ContractError("reward-loop id must be a canonical slug")
        require_sha256(self.inputs_sha256, "reward-loop inputs_sha256")
        require_sha256(self.initial_state_sha256, "reward-loop initial_state_sha256")
        if type(self.goal) is not int or not 1 <= self.goal <= 100:
            raise ContractError("reward-loop goal must be an integer from 1 to 100")
        if type(self.max_steps) is not int or not 1 <= self.max_steps <= 20:
            raise ContractError("reward-loop max_steps must be an integer from 1 to 20")
        if (
            type(self.max_total_steps) is not int
            or not self.max_steps <= self.max_total_steps <= 1_000
        ):
            raise ContractError(
                "reward-loop max_total_steps must cover one batch and be at most 1,000"
            )
        _identity(
            self.creator_identity,
            self.creator_version,
            self.creator_config_sha256,
            "reward-loop creator",
        )
        _identity(
            self.evaluator_identity,
            self.evaluator_version,
            self.evaluator_config_sha256,
            "reward-loop evaluator",
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": _JOURNAL_SCHEMA_VERSION,
            "loop_id": self.loop_id,
            "inputs_sha256": self.inputs_sha256,
            "initial_state_sha256": self.initial_state_sha256,
            "goal": self.goal,
            "max_steps_per_invocation": self.max_steps,
            "max_total_steps": self.max_total_steps,
            "creator": _identity(
                self.creator_identity,
                self.creator_version,
                self.creator_config_sha256,
                "reward-loop creator",
            ),
            "evaluator": _identity(
                self.evaluator_identity,
                self.evaluator_version,
                self.evaluator_config_sha256,
                "reward-loop evaluator",
            ),
        }

    @property
    def sha256(self) -> str:
        return hashlib.sha256(
            _canonical_json_bytes(self.to_dict(), "reward-loop binding")
        ).hexdigest()


@dataclass(frozen=True)
class RewardSignal:
    """One independent environment verdict for an exact action."""

    value: int
    goal: int
    dimensions: Mapping[str, int]
    feedback: Sequence[str]
    evaluator: str
    evaluator_version: str
    config_sha256: str
    hard_tensions: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if type(self.value) is not int or not 0 <= self.value <= 100:
            raise ContractError("reward value must be an integer from 0 to 100")
        if type(self.goal) is not int or not 1 <= self.goal <= 100:
            raise ContractError("reward goal must be an integer from 1 to 100")
        dimensions = _copy_mapping(self.dimensions, "reward dimensions")
        if not all(
            isinstance(key, str)
            and key.strip()
            and type(score) is int
            and 0 <= score <= 100
            for key, score in dimensions.items()
        ):
            raise ContractError("reward dimensions must map names to scores from 0 to 100")
        feedback = tuple(self.feedback)
        tensions = tuple(self.hard_tensions)
        for values, label in ((feedback, "feedback"), (tensions, "hard tension")):
            if any(not isinstance(item, str) or not item.strip() for item in values):
                raise ContractError("reward %s must contain non-empty text" % label)
        if not isinstance(self.evaluator, str) or not self.evaluator.strip():
            raise ContractError("reward evaluator must be non-empty text")
        require_exact_version(self.evaluator_version, "reward evaluator_version")
        require_sha256(self.config_sha256, "reward config_sha256")
        object.__setattr__(self, "dimensions", dimensions)
        object.__setattr__(self, "feedback", feedback)
        object.__setattr__(self, "hard_tensions", tensions)

    @property
    def passed(self) -> bool:
        return self.value >= self.goal and not self.hard_tensions

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "goal": self.goal,
            "passed": self.passed,
            "dimensions": dict(self.dimensions),
            "feedback": list(self.feedback),
            "hard_tensions": list(self.hard_tensions),
            "evaluator": self.evaluator,
            "evaluator_version": self.evaluator_version,
            "config_sha256": self.config_sha256,
        }


@dataclass(frozen=True)
class RewardStep:
    step: int
    observation_sha256: str
    action_sha256: str
    next_state_sha256: str
    reward: RewardSignal

    def __post_init__(self) -> None:
        if type(self.step) is not int or self.step < 1:
            raise ContractError("reward-loop step must be positive")
        require_sha256(self.observation_sha256, "reward observation sha256")
        require_sha256(self.action_sha256, "reward action sha256")
        require_sha256(self.next_state_sha256, "reward next-state sha256")
        if not isinstance(self.reward, RewardSignal):
            raise ContractError("reward-loop step requires a RewardSignal")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "observation_sha256": self.observation_sha256,
            "action_sha256": self.action_sha256,
            "next_state_sha256": self.next_state_sha256,
            "reward": self.reward.to_dict(),
        }


@dataclass(frozen=True)
class RewardLoopResult:
    final_state: Mapping[str, Any]
    final_action: Mapping[str, Any]
    steps: Sequence[RewardStep]

    def __post_init__(self) -> None:
        state = _copy_mapping(self.final_state, "reward-loop final state")
        action = _copy_mapping(self.final_action, "reward-loop final action")
        steps = tuple(self.steps)
        if not steps or not all(isinstance(item, RewardStep) for item in steps):
            raise ContractError("reward loop must contain typed steps")
        object.__setattr__(self, "final_state", state)
        object.__setattr__(self, "final_action", action)
        object.__setattr__(self, "steps", steps)

    @property
    def reward(self) -> RewardSignal:
        return self.steps[-1].reward

    @property
    def reached_goal(self) -> bool:
        return self.reward.passed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reached_goal": self.reached_goal,
            "final_state_sha256": json_sha256(self.final_state),
            "final_action_sha256": json_sha256(self.final_action),
            "steps": [item.to_dict() for item in self.steps],
        }


def _reward_from_dict(value: Any) -> RewardSignal:
    if not isinstance(value, Mapping) or set(value) != {
        "value",
        "goal",
        "passed",
        "dimensions",
        "feedback",
        "hard_tensions",
        "evaluator",
        "evaluator_version",
        "config_sha256",
    }:
        raise ContractError("sealed reward signal is malformed")
    try:
        signal = RewardSignal(
            value["value"],
            value["goal"],
            value["dimensions"],
            value["feedback"],
            value["evaluator"],
            value["evaluator_version"],
            value["config_sha256"],
            value["hard_tensions"],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractError("sealed reward signal is malformed") from exc
    if value["passed"] is not signal.passed:
        raise ContractError("sealed reward signal has an invalid passed verdict")
    return signal


def _open_directory(path: Path, label: str) -> int:
    if path.is_symlink() or not path.is_dir():
        raise ContractError("%s must be a regular directory" % label)
    try:
        return os.open(
            path,
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0),
        )
    except OSError as exc:
        raise ContractError("cannot open %s safely" % label) from exc


def _fsync_directory(path: Path, label: str) -> None:
    descriptor = _open_directory(path, label)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _mkdir_durable(path: Path, label: str) -> None:
    if path.exists() or path.is_symlink():
        if path.is_symlink() or not path.is_dir():
            raise ContractError("%s must be a regular directory" % label)
        return
    parent = path.parent
    if parent.is_symlink() or not parent.is_dir():
        raise ContractError("%s parent must be a regular directory" % label)
    try:
        path.mkdir(mode=0o700)
    except FileExistsError:
        if path.is_symlink() or not path.is_dir():
            raise ContractError("%s raced with a non-directory" % label)
    os.chmod(path, 0o700, follow_symlinks=False)
    _fsync_directory(parent, "%s parent" % label)


def _write_all(descriptor: int, payload: bytes) -> None:
    offset = 0
    while offset < len(payload):
        written = os.write(descriptor, payload[offset:])
        if written <= 0:
            raise OSError("short write")
        offset += written


def _read_regular_at(directory: int, name: str, label: str) -> bytes:
    try:
        descriptor = os.open(
            name,
            os.O_RDONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0),
            dir_fd=directory,
        )
    except OSError as exc:
        raise ContractError("cannot open %s safely" % label) from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise ContractError("%s must be a regular file" % label)
        if metadata.st_size <= 0 or metadata.st_size > _MAX_JOURNAL_BYTES:
            raise ContractError("%s has invalid size" % label)
        chunks = []
        remaining = metadata.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            if not chunk:
                raise ContractError("%s changed while reading" % label)
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            raise ContractError("%s changed while reading" % label)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _write_once_at(directory: int, name: str, payload: bytes, label: str) -> None:
    """Durably link fully-fsynced bytes into an unused journal name."""

    pending = ".pending-%s.json" % secrets.token_hex(16)
    try:
        descriptor = os.open(
            pending,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0),
            0o600,
            dir_fd=directory,
        )
        try:
            _write_all(descriptor, payload)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        try:
            os.link(
                pending,
                name,
                src_dir_fd=directory,
                dst_dir_fd=directory,
                follow_symlinks=False,
            )
        except FileExistsError:
            current = _read_regular_at(directory, name, label)
            if current != payload:
                raise ContractError("%s already names different bytes" % label)
        os.unlink(pending, dir_fd=directory)
        os.fsync(directory)
    except ContractError:
        try:
            os.unlink(pending, dir_fd=directory)
        except OSError:
            pass
        raise
    except OSError as exc:
        try:
            os.unlink(pending, dir_fd=directory)
        except OSError:
            pass
        raise ContractError("could not durably seal %s" % label) from exc


class RewardLoopJournal:
    """Append-only, content-addressed storage for complete reward transitions."""

    @staticmethod
    def _manifest(
        binding: RewardLoopBinding, initial_state: Mapping[str, Any]
    ) -> Dict[str, Any]:
        state = _copy_mapping(initial_state, "reward-loop initial state")
        if json_sha256(state) != binding.initial_state_sha256:
            raise ContractError("reward-loop binding identifies another initial state")
        return {
            "schema_version": _JOURNAL_SCHEMA_VERSION,
            "binding": binding.to_dict(),
            "binding_sha256": binding.sha256,
            "initial_state": state,
            "initial_state_sha256": binding.initial_state_sha256,
        }

    @classmethod
    def peek_initial_state(
        cls, path: Path
    ) -> Optional[Tuple[Mapping[str, Any], Mapping[str, Any]]]:
        """Read an existing journal's binding and initial state without creating it."""

        requested = Path(path)
        if not requested.is_absolute():
            raise ContractError("reward journal path must be absolute")
        if not requested.exists() and not requested.is_symlink():
            return None
        descriptor = _open_directory(requested, "reward journal")
        try:
            try:
                raw = _read_regular_at(
                    descriptor, "binding.json", "reward journal binding"
                )
            except ContractError:
                try:
                    os.stat("binding.json", dir_fd=descriptor, follow_symlinks=False)
                except FileNotFoundError:
                    return None
                raise
        finally:
            os.close(descriptor)
        try:
            decoded = json.loads(raw.decode("utf-8"))
        except (UnicodeError, ValueError) as exc:
            raise ContractError("reward journal binding is not canonical JSON") from exc
        manifest = _copy_mapping(decoded, "reward journal binding")
        if raw != _canonical_json_bytes(manifest, "reward journal binding"):
            raise ContractError("reward journal binding is not canonical JSON")
        if set(manifest) != {
            "schema_version",
            "binding",
            "binding_sha256",
            "initial_state",
            "initial_state_sha256",
        } or manifest["schema_version"] != _JOURNAL_SCHEMA_VERSION:
            raise ContractError("reward journal binding fields are malformed")
        binding_value = _copy_mapping(
            manifest["binding"], "reward journal immutable binding"
        )
        initial_state = _copy_mapping(
            manifest["initial_state"], "reward journal initial state"
        )
        if (
            hashlib.sha256(
                _canonical_json_bytes(
                    binding_value, "reward journal immutable binding"
                )
            ).hexdigest()
            != manifest["binding_sha256"]
            or json_sha256(initial_state) != manifest["initial_state_sha256"]
        ):
            raise ContractError("reward journal binding digest is invalid")
        return binding_value, initial_state

    def __init__(
        self,
        path: Path,
        binding: RewardLoopBinding,
        initial_state: Mapping[str, Any],
    ) -> None:
        if not isinstance(binding, RewardLoopBinding):
            raise ContractError("reward journal requires a RewardLoopBinding")
        requested = Path(path)
        if not requested.is_absolute():
            raise ContractError("reward journal path must be absolute")
        _mkdir_durable(requested.parent, "reward journal parent")
        _mkdir_durable(requested, "reward journal")
        steps = requested / "steps"
        _mkdir_durable(steps, "reward journal steps")
        self.path = requested
        self.steps_path = steps
        self.binding = binding
        descriptor = _open_directory(requested, "reward journal")
        try:
            binding_bytes = _canonical_json_bytes(
                self._manifest(binding, initial_state), "reward-loop binding"
            )
            try:
                existing = _read_regular_at(
                    descriptor, "binding.json", "reward journal binding"
                )
            except ContractError:
                # Distinguish absence from an unsafe or malformed existing path.
                try:
                    os.stat("binding.json", dir_fd=descriptor, follow_symlinks=False)
                except FileNotFoundError:
                    _write_once_at(
                        descriptor,
                        "binding.json",
                        binding_bytes,
                        "reward journal binding",
                    )
                    existing = binding_bytes
                else:
                    raise
            if existing != binding_bytes:
                raise ContractError(
                    "reward journal belongs to different inputs, goal, budget, or workers"
                )
        finally:
            os.close(descriptor)

    @staticmethod
    def _record_mapping(value: Any, label: str) -> Dict[str, Any]:
        if not isinstance(value, Mapping):
            raise ContractError("%s is malformed" % label)
        return _copy_mapping(value, label)

    def replay(
        self, initial_state: Mapping[str, Any]
    ) -> Tuple[Mapping[str, Any], Mapping[str, Any], List[RewardStep], Optional[str]]:
        state: Mapping[str, Any] = _copy_mapping(
            initial_state, "reward-loop initial state"
        )
        if json_sha256(state) != self.binding.initial_state_sha256:
            raise ContractError("reward journal initial state changed")
        action: Mapping[str, Any] = {}
        steps: List[RewardStep] = []
        previous_sha256: Optional[str] = None
        descriptor = _open_directory(self.steps_path, "reward journal steps")
        try:
            names = os.listdir(descriptor)
            step_names = []
            for name in names:
                match = _STEP_FILE.fullmatch(name)
                if match:
                    step_names.append((int(match.group(1)), match.group(2), name))
                    continue
                if _PENDING_FILE.fullmatch(name):
                    metadata = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
                    if not stat.S_ISREG(metadata.st_mode):
                        raise ContractError(
                            "reward journal pending entry must be a regular file"
                        )
                    continue
                raise ContractError("reward journal contains an unknown entry")
            step_names.sort()
            for expected_step, (number, filename_sha256, name) in enumerate(
                step_names, start=1
            ):
                if number != expected_step:
                    raise ContractError("reward journal step sequence is incomplete")
                raw = _read_regular_at(
                    descriptor, name, "reward journal step %d" % number
                )
                if hashlib.sha256(raw).hexdigest() != filename_sha256:
                    raise ContractError("reward journal step content address changed")
                try:
                    decoded = json.loads(raw.decode("utf-8"))
                except (UnicodeError, ValueError) as exc:
                    raise ContractError("reward journal step is not canonical JSON") from exc
                record = self._record_mapping(decoded, "reward journal step")
                if raw != _canonical_json_bytes(record, "reward journal step"):
                    raise ContractError("reward journal step is not canonical JSON")
                if set(record) != {
                    "schema_version",
                    "binding_sha256",
                    "step",
                    "previous_step_sha256",
                    "observation",
                    "observation_sha256",
                    "action",
                    "action_sha256",
                    "next_state",
                    "next_state_sha256",
                    "reward",
                }:
                    raise ContractError("reward journal step fields are malformed")
                if (
                    record["schema_version"] != _JOURNAL_SCHEMA_VERSION
                    or record["binding_sha256"] != self.binding.sha256
                    or record["step"] != number
                    or record["previous_step_sha256"] != previous_sha256
                ):
                    raise ContractError("reward journal step chain is invalid")
                observation = self._record_mapping(
                    record["observation"], "reward journal observation"
                )
                action = self._record_mapping(
                    record["action"], "reward journal action"
                )
                next_state = self._record_mapping(
                    record["next_state"], "reward journal next state"
                )
                if (
                    record["observation_sha256"] != json_sha256(observation)
                    or record["action_sha256"] != json_sha256(action)
                    or record["next_state_sha256"] != json_sha256(next_state)
                ):
                    raise ContractError("reward journal step digest is invalid")
                reward = _reward_from_dict(record["reward"])
                if (
                    reward.goal != self.binding.goal
                    or reward.evaluator != self.binding.evaluator_identity
                    or reward.evaluator_version != self.binding.evaluator_version
                    or reward.config_sha256
                    != self.binding.evaluator_config_sha256
                ):
                    raise ContractError("reward journal evaluator binding changed")
                if steps and steps[-1].reward.passed:
                    raise ContractError("reward journal continued after reaching its goal")
                steps.append(
                    RewardStep(
                        number,
                        record["observation_sha256"],
                        record["action_sha256"],
                        record["next_state_sha256"],
                        reward,
                    )
                )
                state = next_state
                previous_sha256 = filename_sha256
        finally:
            os.close(descriptor)
        return state, action, steps, previous_sha256

    def append(
        self,
        *,
        step: int,
        previous_step_sha256: Optional[str],
        observation: Mapping[str, Any],
        action: Mapping[str, Any],
        next_state: Mapping[str, Any],
        reward: RewardSignal,
    ) -> Tuple[RewardStep, str]:
        if type(step) is not int or not 1 <= step <= 999_999:
            raise ContractError("reward journal step is outside its durable range")
        if previous_step_sha256 is not None:
            require_sha256(previous_step_sha256, "previous reward step sha256")
        observation_copy = _copy_mapping(observation, "reward-loop observation")
        action_copy = _copy_mapping(action, "reward-loop action")
        state_copy = _copy_mapping(next_state, "reward-loop next state")
        if not isinstance(reward, RewardSignal):
            raise ContractError("reward journal requires a RewardSignal")
        if (
            reward.goal != self.binding.goal
            or reward.evaluator != self.binding.evaluator_identity
            or reward.evaluator_version != self.binding.evaluator_version
            or reward.config_sha256 != self.binding.evaluator_config_sha256
        ):
            raise ContractError("reward signal differs from the journal evaluator")
        observation_sha256 = json_sha256(observation_copy)
        action_sha256 = json_sha256(action_copy)
        next_state_sha256 = json_sha256(state_copy)
        record = {
            "schema_version": _JOURNAL_SCHEMA_VERSION,
            "binding_sha256": self.binding.sha256,
            "step": step,
            "previous_step_sha256": previous_step_sha256,
            "observation": observation_copy,
            "observation_sha256": observation_sha256,
            "action": action_copy,
            "action_sha256": action_sha256,
            "next_state": state_copy,
            "next_state_sha256": next_state_sha256,
            "reward": reward.to_dict(),
        }
        payload = _canonical_json_bytes(record, "reward journal step")
        record_sha256 = hashlib.sha256(payload).hexdigest()
        name = "%06d-%s.json" % (step, record_sha256)
        descriptor = _open_directory(self.steps_path, "reward journal steps")
        try:
            _write_once_at(
                descriptor,
                name,
                payload,
                "reward journal step %d" % step,
            )
        finally:
            os.close(descriptor)
        return (
            RewardStep(
                step,
                observation_sha256,
                action_sha256,
                next_state_sha256,
                reward,
            ),
            record_sha256,
        )


Observer = Callable[[Mapping[str, Any], int], Mapping[str, Any]]
Agent = Callable[[Mapping[str, Any], int], Mapping[str, Any]]
Environment = Callable[
    [Mapping[str, Any], Mapping[str, Any], int],
    Tuple[Mapping[str, Any], RewardSignal],
]


def run_reward_loop(
    initial_state: Mapping[str, Any],
    *,
    observe: Observer,
    act: Agent,
    environment: Environment,
    goal: int,
    max_steps: int,
    journal_path: Optional[Path] = None,
    binding: Optional[RewardLoopBinding] = None,
) -> RewardLoopResult:
    """Run or resume transitions until the goal or this invocation's budget.

    With a journal, every completely evaluated transition is fsynced before it
    is accepted. Resume validates and reuses the sealed prefix, then appends at
    most ``max_steps`` new transitions. An action or verdict interrupted before
    that seal is deliberately the only work that may run again.
    """

    if type(goal) is not int or not 1 <= goal <= 100:
        raise ContractError("reward-loop goal must be an integer from 1 to 100")
    if type(max_steps) is not int or not 1 <= max_steps <= 20:
        raise ContractError("reward-loop max_steps must be an integer from 1 to 20")
    for function, label in (
        (observe, "observer"),
        (act, "agent"),
        (environment, "environment"),
    ):
        if not callable(function):
            raise ContractError("reward-loop %s must be callable" % label)
    state: Mapping[str, Any] = _copy_mapping(initial_state, "reward-loop initial state")
    if (journal_path is None) is not (binding is None):
        raise ContractError("durable reward loops require both path and binding")
    journal: Optional[RewardLoopJournal] = None
    steps: List[RewardStep] = []
    action: Mapping[str, Any] = {}
    previous_step_sha256: Optional[str] = None
    if journal_path is not None:
        assert binding is not None
        if binding.goal != goal or binding.max_steps != max_steps:
            raise ContractError("reward-loop call differs from its durable binding")
        if binding.initial_state_sha256 != json_sha256(state):
            raise ContractError("reward-loop binding identifies another initial state")
        journal = RewardLoopJournal(Path(journal_path), binding, state)
        state, action, steps, previous_step_sha256 = journal.replay(state)
        if steps and steps[-1].reward.passed:
            return RewardLoopResult(state, action, tuple(steps))
        if len(steps) >= binding.max_total_steps:
            return RewardLoopResult(state, action, tuple(steps))
    first_step = len(steps) + 1
    new_step_budget = max_steps
    if binding is not None:
        new_step_budget = min(
            new_step_budget, binding.max_total_steps - len(steps)
        )
    last_step = first_step + new_step_budget
    for step_number in range(first_step, last_step):
        observation = _copy_mapping(
            observe(state, step_number), "reward-loop observation"
        )
        action = _copy_mapping(act(observation, step_number), "reward-loop action")
        next_state, reward = environment(state, action, step_number)
        next_state = _copy_mapping(next_state, "reward-loop next state")
        if not isinstance(reward, RewardSignal):
            raise ContractError("reward-loop environment must return a RewardSignal")
        if reward.goal != goal:
            raise ContractError("reward-loop environment changed the goal")
        if journal is None:
            reward_step = RewardStep(
                step_number,
                json_sha256(observation),
                json_sha256(action),
                json_sha256(next_state),
                reward,
            )
        else:
            reward_step, previous_step_sha256 = journal.append(
                step=step_number,
                previous_step_sha256=previous_step_sha256,
                observation=observation,
                action=action,
                next_state=next_state,
                reward=reward,
            )
        steps.append(reward_step)
        state = next_state
        if reward.passed:
            break
    return RewardLoopResult(state, action, tuple(steps))


__all__ = [
    "Agent",
    "Environment",
    "Observer",
    "RewardLoopResult",
    "RewardLoopBinding",
    "RewardLoopJournal",
    "RewardSignal",
    "RewardStep",
    "json_sha256",
    "run_reward_loop",
]

"""The customer and operator CLI for Autonomous Workshop."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import secrets
import shlex
import shutil
import signal
import sqlite3
import stat
import subprocess
import sys
import unicodedata
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Mapping, Optional, Sequence

from ._package_data import (
    existing_bundled_catalog_roots,
    materialize_bundled_inventors,
    packaged_inventor_catalog_root,
    packaged_inventors_root,
)
from .artifacts import MAX_PACK_BYTES
from .clockwork import Clockwork
from .contribution import check_target, manifests_for_target
from .errors import AmbiguousEffectError, EffectError, WorkshopError
from .factory_agent import (
    FactoryAgentInstructionsWriter,
    FactoryAgentSession,
    FactoryPublicTransition,
    factory_credentials_from_environment,
)
from .handoff import (
    MAX_HANDOFF_BYTES,
    ManagerAssignmentHandoff,
    validate_manager_assignment_result,
)
from .instructions import sealed_instructions_manifest
from .jobs import Delivered, Feedback, Invented, Need, WaitingFor, WorkshopRun
from .execution_env import codex_subprocess_environment, minimal_tool_environment
from .agent_instructions import (
    DEFAULT_INSTRUCTIONS_CREATOR_MODEL,
    DEFAULT_INSTRUCTIONS_REWARD_MODEL,
    RewardedInstructions,
)
from .make import Wish, generate_wish_id
from .manifest import (
    discover_inventors,
    inventor_collection,
    load_manifest,
    validate_entrypoints,
)
from .models import Receipt, utc_now
from .pack import pack_artifact, plan_pack, seal_artifact
from .manager import WorkshopManager, discover_inventor_catalog
from .semantic_manager import CodexSemanticManager
from .scaffold import (
    create_inventor,
    prepare_inventor_collection,
    scaffold_inventor,
)
from .schemas import discover_schemas, resolve_schemas_root
from .skills import discover_skills, resolve_skills_root
from .store import InventorStore
from .shop import ShopDoor
from .taste import load_taste, load_taste_header
from .toys import PLAYTHING_LANES, ToyBlueprint
from .workshop import (
    CUSTOMIZATION_LEVELS,
    Workshop,
    WorkshopTools,
    _playtest_policy_needs,
    _read_instructions_checkpoint,
    _read_stage_checkpoint,
    _rebuild_checkpoint_results,
    _rebuild_made_value,
    _rebuild_playtested_value,
)


DEFAULT_WISH_PLAYTEST_ROUNDS = 4
_ASSIGNMENT_DIRECTORY = "manager-assignments"
_INVENTOR_ID_PART = re.compile(r"[^a-z0-9]+")
_SHARED_ENGINE_ENVIRONMENT_NAMES = frozenset(
    (
        "WORKSHOP_CODEX_BIN",
        "WORKSHOP_INVENT_MODEL",
        "WORKSHOP_REWARD_MODEL",
        "WORKSHOP_MAKE_MODEL",
        "WORKSHOP_MAKE_REWARD_MODEL",
        "WORKSHOP_PLAYTEST_MODEL",
        "WORKSHOP_INSTRUCTIONS_MODEL",
        "WORKSHOP_INSTRUCTIONS_REWARD_MODEL",
        "WORKSHOP_CAD_PYTHON",
        "WORKSHOP_HANDLING_FORCE_N",
        "WORKSHOP_HANDLING_SAFETY_FACTOR",
        "WORKSHOP_HANDLING_TORQUE_N_MM",
        "WORKSHOP_PRUSASLICER_BIN",
        "WORKSHOP_PRUSASLICER_PRINTER_PROFILE",
        "WORKSHOP_PRUSASLICER_FILAMENT_PROFILE",
        "WORKSHOP_PRUSASLICER_PROCESS_PROFILE",
        "WORKSHOP_PRUSASLICER_VERSION",
        "WORKSHOP_PRUSA_PROFILES",
    )
)


def _has_inventor_catalog(root: Path) -> bool:
    """Recognize a checkout/collection without loading contribution code."""

    try:
        resolved = Path(root).resolve(strict=True)
    except OSError:
        return False
    collection = resolved / "inventors" if (resolved / "inventors").is_dir() else resolved
    try:
        return any(
            child.is_dir()
            and not child.is_symlink()
            and (child / "inventor.json").is_file()
            and not (child / "inventor.json").is_symlink()
            and (child / "TASTE.md").is_file()
            and not (child / "TASTE.md").is_symlink()
            for child in collection.iterdir()
        )
    except OSError:
        return False


def _source_workshop_root() -> Optional[Path]:
    """Find a source/editable catalog without creating installed state."""

    current = Path.cwd().resolve()
    for candidate in (current, *current.parents):
        if _has_inventor_catalog(candidate):
            return candidate
    source_checkout = Path(__file__).resolve().parents[2]
    return source_checkout if _has_inventor_catalog(source_checkout) else None


def _catalog_roots(
    requested: Optional[Path], *, include_retained: bool = False
) -> tuple[Path, ...]:
    """Resolve catalog state lazily, materializing only an installed command run."""

    if requested is not None:
        return (Path(requested).resolve(),)
    source = _source_workshop_root()
    if source is not None:
        return (source,)
    if packaged_inventors_root() is not None:
        if include_retained:
            return _installed_retained_catalog_roots()
        return (materialize_bundled_inventors(),)
    # Keep the eventual discovery error grounded in the directory the customer
    # actually invoked the command from.
    return (Path.cwd().resolve(),)


def _default_workshop_root() -> Path:
    """Resolve the current catalog for a command that actually needs it."""

    return _catalog_roots(None)[0]


def _installed_retained_catalog_roots() -> tuple[Path, ...]:
    """Read installed catalog generations without creating WORKSHOP_HOME."""

    return existing_bundled_catalog_roots()


def _shell_command(*parts: Any) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def _inventor_id_from_taste(path: Path) -> str:
    """Derive a conservative CLI id from a validated TASTE header."""

    requested = Path(path)
    if requested.name != "TASTE.md":
        raise WorkshopError(
            "--taste must name a file called TASTE.md; rename the file so its identity is explicit"
        )
    header = load_taste_header(requested.parent)
    ascii_name = unicodedata.normalize("NFKD", header.name).encode(
        "ascii", "ignore"
    ).decode("ascii")
    inventor_id = _INVENTOR_ID_PART.sub("-", ascii_name.lower()).strip("-")[:63]
    inventor_id = inventor_id.rstrip("-")
    if len(inventor_id) < 2 or not inventor_id[0].isalpha():
        raise WorkshopError(
            "the Taste name cannot produce a safe inventor id; provide one explicitly after 'inventor'"
        )
    return inventor_id


class _ReadOnlyWorkshopStore:
    """The narrow, non-migrating status projection of one Workshop database."""

    _JSON_COLUMNS = (
        "metadata_json",
        "payload_json",
        "request_json",
        "live_request_json",
        "live_attempts_json",
        "response_json",
        "receipt_json",
        "stamp_json",
    )

    def __init__(self, database: Path) -> None:
        requested = Path(database)
        runtime_root = requested.parent
        if runtime_root.is_symlink() or not runtime_root.is_dir():
            raise WorkshopError(
                "Workshop status runtime must be a regular directory"
            )
        try:
            runtime_stat = runtime_root.lstat()
            database_stat = requested.lstat()
        except OSError as exc:
            raise WorkshopError("Workshop status database is missing") from exc
        if not stat.S_ISDIR(runtime_stat.st_mode):
            raise WorkshopError(
                "Workshop status runtime must be a regular directory"
            )
        if not stat.S_ISREG(database_stat.st_mode):
            raise WorkshopError("Workshop status database must be a regular file")
        resolved_runtime = runtime_root.resolve(strict=True)
        self.database = requested.resolve(strict=True)
        if self.database.parent != resolved_runtime:
            raise WorkshopError("Workshop status database escapes its runtime")
        self._runtime_identity = (runtime_stat.st_dev, runtime_stat.st_ino)
        self._database_identity = (database_stat.st_dev, database_stat.st_ino)

    def _assert_current_path(self) -> None:
        try:
            runtime_stat = self.database.parent.lstat()
            database_stat = self.database.lstat()
        except OSError as exc:
            raise WorkshopError(
                "Workshop status database changed while opening"
            ) from exc
        if (
            stat.S_ISLNK(runtime_stat.st_mode)
            or stat.S_ISLNK(database_stat.st_mode)
            or (runtime_stat.st_dev, runtime_stat.st_ino)
            != self._runtime_identity
            or (database_stat.st_dev, database_stat.st_ino)
            != self._database_identity
        ):
            raise WorkshopError("Workshop status database changed while opening")

    def _connect(self) -> sqlite3.Connection:
        self._assert_current_path()
        connection = sqlite3.connect(
            self.database.as_uri() + "?mode=ro",
            uri=True,
            timeout=5,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        try:
            self._assert_current_path()
        except Exception:
            connection.close()
            raise
        return connection

    @classmethod
    def _row(cls, row: sqlite3.Row) -> Mapping[str, Any]:
        value = dict(row)
        for key in cls._JSON_COLUMNS:
            if key in value:
                raw = value.pop(key)
                try:
                    value[key[:-5]] = json.loads(raw) if raw else None
                except (TypeError, json.JSONDecodeError) as exc:
                    raise WorkshopError(
                        "Workshop status database contains malformed JSON"
                    ) from exc
        return value

    def get_product(self, product_id: str) -> Mapping[str, Any]:
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT * FROM products WHERE id=?", (product_id,)
            ).fetchone()
        finally:
            connection.close()
        if row is None:
            raise KeyError("unknown product %r" % product_id)
        return self._row(row)

    def list_products(self) -> Sequence[Mapping[str, Any]]:
        connection = self._connect()
        try:
            rows = connection.execute("SELECT * FROM products ORDER BY id").fetchall()
        finally:
            connection.close()
        return tuple(self._row(row) for row in rows)

    def events(self, product_id: str) -> Sequence[Mapping[str, Any]]:
        connection = self._connect()
        try:
            rows = connection.execute(
                "SELECT * FROM events WHERE product_id=? ORDER BY sequence",
                (product_id,),
            ).fetchall()
        finally:
            connection.close()
        return tuple(self._row(row) for row in rows)

    def active_lease(self, product_id: str) -> Optional[Mapping[str, str]]:
        """Observe an unexpired product lease without deleting stale rows."""

        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT holder, expires_at FROM leases WHERE product_id=?",
                (product_id,),
            ).fetchone()
        finally:
            connection.close()
        if row is None or row["expires_at"] <= utc_now():
            return None
        return {"holder": row["holder"], "expires_at": row["expires_at"]}

    def latest_publish_intent(self, product_id: str) -> Optional[Mapping[str, Any]]:
        connection = self._connect()
        try:
            row = connection.execute(
                """SELECT * FROM publish_intents
                   WHERE product_id=?
                   ORDER BY created_at DESC, id DESC LIMIT 1""",
                (product_id,),
            ).fetchone()
        finally:
            connection.close()
        return self._row(row) if row is not None else None

    def verify_event_chain(self, product_id: str) -> bool:
        try:
            product = self.get_product(product_id)
            events = self.events(product_id)
        except (KeyError, WorkshopError, sqlite3.DatabaseError):
            return False
        if not events or not isinstance(product.get("metadata"), Mapping):
            return False
        previous = None
        stage = None
        artifact_sha256 = None
        revision = -1
        metadata = None
        for index, event in enumerate(events):
            if not isinstance(event.get("payload"), Mapping):
                return False
            document = {
                "product_id": event["product_id"],
                "kind": event["kind"],
                "from_stage": event["from_stage"],
                "to_stage": event["to_stage"],
                "artifact_sha256": event["artifact_sha256"],
                "payload": event["payload"],
                "created_at": event["created_at"],
                "previous_sha256": previous,
            }
            encoded = json.dumps(
                document,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
            expected = hashlib.sha256(encoded).hexdigest()
            if (
                event["previous_sha256"] != previous
                or event["event_sha256"] != expected
            ):
                return False
            if index == 0:
                if (
                    event["kind"] != "registered"
                    or event["from_stage"] is not None
                    or not event["to_stage"]
                ):
                    return False
                stage = event["to_stage"]
                artifact_sha256 = event["artifact_sha256"]
                metadata = event["payload"]
                revision = 0
            else:
                if (
                    event["kind"] != "transition"
                    or event["from_stage"] != stage
                    or not event["to_stage"]
                ):
                    return False
                stage = event["to_stage"]
                artifact_sha256 = event["artifact_sha256"]
                revision += 1
            previous = event["event_sha256"]
        return (
            product["stage"] == stage
            and product["revision"] == revision
            and product["artifact_sha256"] == artifact_sha256
            and product["metadata"] == metadata
            and product["created_at"] == events[0]["created_at"]
            and product["updated_at"] == events[-1]["created_at"]
        )


def _inventor_process_environment(inventor_id: str) -> Mapping[str, str]:
    """Build a strict worker environment with no Factory or unrelated secrets.

    An inventor entrypoint is contribution code. It receives the Codex runtime
    inputs needed by shared Invent/Make/Playtest workers, but Factory authority
    stays in the Workshop Manager process for the later Instructions handoff.
    """

    if not isinstance(inventor_id, str) or not inventor_id:
        raise WorkshopError("selected Inventor identity is malformed")
    environment = dict(codex_subprocess_environment(os.environ))
    environment.update(
        {
            name: value
            for name in _SHARED_ENGINE_ENVIRONMENT_NAMES
            if isinstance((value := os.environ.get(name)), str) and value
        }
    )
    environment["WORKSHOP_AGENT_WORKERS"] = "codex"
    environment["WORKSHOP_INVENT_WORKER"] = "codex"
    return environment


def _factory_credential_environment(
    inventor_id: str, source: Optional[Mapping[str, str]] = None
) -> Optional[Mapping[str, str]]:
    """Select one Factory account inside the trusted Manager process only."""

    values = os.environ if source is None else source
    password = values.get("FACTORY_PASSWORD")
    if not isinstance(password, str) or not password:
        return None
    return {"FACTORY_USERNAME": inventor_id, "FACTORY_PASSWORD": password}


def _manifest_workshop_shape(card: Any) -> tuple[str, str]:
    """Read one exact lane/contribution pair from the selected manifest."""

    card_current = getattr(card, "assert_manifest_current", None)
    if callable(card_current):
        card_current()
    manifest = load_manifest(Path(card.root) / "inventor.json")
    lanes = tuple(item for item in manifest.capabilities if item in PLAYTHING_LANES)
    levels = tuple(
        item for item in manifest.capabilities if item in CUSTOMIZATION_LEVELS
    )
    if (
        len(lanes) != 1
        or len(levels) != 1
        or set(manifest.capabilities) != {lanes[0], levels[0]}
    ):
        raise WorkshopError(
            "selected Inventor manifest must declare exactly one lane and one known contribution level"
        )
    return lanes[0], levels[0]


def _invented_from_event(value: Any) -> Invented:
    if not isinstance(value, Mapping) or set(value) != {
        "wish_sha256",
        "taste_sha256",
        "lane",
        "concept",
        "concept_sha256",
        "score",
        "target_score",
        "passed",
    }:
        raise WorkshopError("persisted Invent result is malformed")
    invented = Invented(
        wish_sha256=value["wish_sha256"],
        taste_sha256=value["taste_sha256"],
        lane=value["lane"],
        concept=value["concept"],
        score=value["score"],
        target_score=value["target_score"],
    )
    if invented.to_dict() != dict(value):
        raise WorkshopError("persisted Invent result identity is inconsistent")
    return invented


def _delivered_from_event(value: Any) -> Delivered:
    if not isinstance(value, Mapping) or set(value) != {
        "schema_version",
        "product_artifact_sha256",
        "instructions_sha256",
        "carrier",
        "service",
        "tracking_id",
        "status",
        "observed_at",
        "evidence",
    } or value.get("schema_version") != 1:
        raise WorkshopError("persisted Deliver result is malformed")
    return Delivered(
        product_artifact_sha256=value["product_artifact_sha256"],
        instructions_sha256=value["instructions_sha256"],
        carrier=value["carrier"],
        service=value["service"],
        tracking_id=value["tracking_id"],
        status=value["status"],
        observed_at=value["observed_at"],
        evidence=value["evidence"],
    )


def _validate_child_workshop_state(
    assignment: Any,
    child_result: Mapping[str, Any],
    *,
    allow_durable_factory_page: bool = False,
) -> Mapping[str, Any]:
    """Derive the child result from the trusted event chain, never stdout claims."""

    assert_current = getattr(assignment, "assert_current", None)
    if callable(assert_current):
        assert_current()
    card = assignment.decision.selected.card
    lane, level = _manifest_workshop_shape(card)
    database = Path(card.root) / ".workshop" / "workshop.sqlite3"
    if database.is_symlink() or not database.is_file():
        raise WorkshopError(
            "selected Inventor returned no durable Workshop event chain"
        )
    runtime = _ReadOnlyWorkshopStore(database)
    product_id = assignment.wish.product_id
    if not runtime.verify_event_chain(product_id):
        raise WorkshopError("selected Inventor Workshop event chain is not trustworthy")
    product = runtime.get_product(product_id)
    events = runtime.events(product_id)
    if not events:
        raise WorkshopError("selected Inventor Workshop event chain is empty")
    latest = events[-1]
    payload = latest.get("payload")
    if not isinstance(payload, Mapping):
        raise WorkshopError("latest Workshop event payload is malformed")
    taste = assignment.decision.selected.taste
    expected_metadata = {
        "wish": assignment.wish.to_dict(),
        "inventor_id": card.inventor_id,
        "taste_sha256": taste.sha256,
        "blueprint_sha256": ToyBlueprint.for_lane(lane).sha256,
        "lane": lane,
        "customization_level": level,
        "playtest_rounds": assignment.playtest_rounds,
    }
    if product.get("metadata") != expected_metadata:
        raise WorkshopError(
            "durable Workshop state differs from the exact Manager assignment"
        )
    job = product.get("stage")
    if latest.get("to_stage") != job:
        raise WorkshopError("latest Workshop event differs from product state")
    status = payload.get("status")
    if status not in ("waiting", "stopped", "delivered"):
        raise WorkshopError(
            "selected Inventor stopped without a terminal Workshop event"
        )
    round_number = payload.get("round")
    if type(round_number) is not int:
        raise WorkshopError("terminal Workshop event has no valid round")
    artifact_sha256 = product.get("artifact_sha256")
    if latest.get("artifact_sha256") != artifact_sha256:
        raise WorkshopError("terminal Workshop artifact identity is inconsistent")
    needs = ()
    if status == "waiting":
        raw_needs = payload.get("needs")
        if not isinstance(raw_needs, list) or not raw_needs:
            raise WorkshopError("waiting Workshop event has no typed needs")
        try:
            needs = tuple(Need(**dict(item)) for item in raw_needs)
        except (TypeError, WorkshopError) as exc:
            raise WorkshopError("waiting Workshop needs are malformed") from exc
    instructions_sha256 = next(
        (
            event["payload"].get("instructions_sha256")
            for event in reversed(events)
            if isinstance(event.get("payload"), Mapping)
            and isinstance(event["payload"].get("instructions_sha256"), str)
        ),
        None,
    )
    invented_value = next(
        (
            event["payload"].get("invented")
            for event in events
            if isinstance(event.get("payload"), Mapping)
            and "invented" in event["payload"]
        ),
        None,
    )
    invented = (
        _invented_from_event(invented_value)
        if invented_value is not None
        else None
    )
    delivery = None
    if status == "delivered":
        delivery = _delivered_from_event(payload.get("delivery"))
        if (
            delivery.product_artifact_sha256 != artifact_sha256
            or delivery.instructions_sha256 != instructions_sha256
        ):
            raise WorkshopError("persisted Deliver result has different exact inputs")
    page_url = None
    if allow_durable_factory_page:
        intent = runtime.latest_publish_intent(product_id)
        receipt_value = intent.get("receipt") if isinstance(intent, Mapping) else None
        try:
            receipt = Receipt.from_dict(receipt_value)
            receipt.assert_artifact(artifact_sha256)
        except (TypeError, WorkshopError) as exc:
            raise WorkshopError(
                "Manager-resumed Instructions lacks an exact durable Factory receipt"
            ) from exc
        if not (receipt.is_verified_draft or receipt.is_verified_public):
            raise WorkshopError(
                "Manager-resumed Instructions Factory receipt is not verified"
            )
        if receipt.details.get("instructions_sha256") != instructions_sha256:
            raise WorkshopError(
                "Manager-resumed Factory receipt identifies different Instructions"
            )
        page_url = receipt.details.get("page_url")
        if not isinstance(page_url, str) or not page_url:
            raise WorkshopError("Manager-resumed Factory receipt has no product page")
    trusted = WorkshopRun(
        product_id=product_id,
        status=status,
        job=job,
        round=round_number,
        artifact_sha256=artifact_sha256,
        instructions_sha256=instructions_sha256,
        needs=needs,
        delivery=delivery,
        playtest_rounds=assignment.playtest_rounds,
        page_url=page_url,
        invented=invented,
    ).to_dict()
    supplied = {
        key: value
        for key, value in child_result.items()
        if key != "manager_assignment"
    }
    if supplied != trusted:
        raise WorkshopError(
            "selected Inventor stdout differs from its durable Workshop state"
        )
    if callable(assert_current):
        assert_current()
    return {**trusted, "manager_assignment": child_result["manager_assignment"]}


class _ResumeOnlyStructuredRunner:
    """Identity-only runner; sealed Instructions resume must never invoke AI."""

    def __init__(self, model: str, reasoning_effort: str) -> None:
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.cli_version = "resume-only.1.0.0"

    def invoke(self, **kwargs):  # pragma: no cover - a resume invariant
        del kwargs
        raise WorkshopError("sealed Instructions resume attempted to rerun AI")


def _managed_child_run(
    command: Sequence[str],
    *,
    cwd: str,
    env: Mapping[str, str],
    input: str,
    capture_output: bool,
    text: bool,
    timeout: float,
    check: bool,
) -> subprocess.CompletedProcess:
    """Run one Inventor and reap its complete descendant process group."""

    if not capture_output or not text or check:
        raise WorkshopError("managed Inventor subprocess options are invalid")
    process = subprocess.Popen(
        list(command),
        cwd=cwd,
        env=dict(env),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(input=input, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except (AttributeError, ProcessLookupError, PermissionError):
            process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except (AttributeError, ProcessLookupError, PermissionError):
                process.kill()
            stdout, stderr = process.communicate()
        raise subprocess.TimeoutExpired(
            list(command), timeout, output=stdout, stderr=stderr
        ) from exc
    return subprocess.CompletedProcess(
        list(command), process.returncode, stdout=stdout, stderr=stderr
    )


def _resume_factory_instructions(
    assignment: Any,
    result: Mapping[str, Any],
    *,
    environment: Optional[Mapping[str, str]] = None,
    store_factory: Any = InventorStore,
    writer_factory: Any = FactoryAgentInstructionsWriter,
    workshop_factory: Any = Workshop,
    state_validator: Any = _validate_child_workshop_state,
) -> Mapping[str, Any]:
    """Resume only a sealed Factory handoff outside inventor-owned code.

    The selected profile runs without Factory credentials and therefore stops
    truthfully after scoring and sealing its manual/page facts. If the Manager
    owns a credential, this function gives it only to the shared site adapter,
    reconstructs the exact checkpoint, and resumes Instructions without
    executing the profile or any custom Invent/Make/Playtest hook.
    """

    if not isinstance(result, Mapping):
        raise WorkshopError("Workshop child result must be an object")
    needs = result.get("needs")
    is_factory_wait = (
        result.get("status") == "waiting"
        and result.get("job") == "instructions"
        and isinstance(needs, list)
        and any(
            isinstance(need, Mapping)
            and need.get("job") == "instructions"
            and need.get("capability") in ("site-page", "site-reconciliation")
            for need in needs
        )
    )
    if not is_factory_wait:
        return dict(result)
    inventor_id = assignment.decision.selected.card.inventor_id
    selected_environment = _factory_credential_environment(
        inventor_id, os.environ if environment is None else environment
    )
    if selected_environment is None:
        return dict(result)
    assert_current = getattr(assignment, "assert_current", None)
    if callable(assert_current):
        assert_current()
    card = assignment.decision.selected.card
    lane, level = _manifest_workshop_shape(card)
    credentials = factory_credentials_from_environment(
        inventor_id, selected_environment
    )
    runtime_root = Path(card.root) / ".workshop"
    writer = writer_factory(
        store_factory(runtime_root / "workshop.sqlite3"),
        inventor_id,
        credentials,
    )
    instructions = RewardedInstructions(
        writer,
        creator=_ResumeOnlyStructuredRunner(
            DEFAULT_INSTRUCTIONS_CREATOR_MODEL, "medium"
        ),
        evaluator=_ResumeOnlyStructuredRunner(
            DEFAULT_INSTRUCTIONS_REWARD_MODEL, "low"
        ),
    )

    def unavailable(context):  # pragma: no cover - resume must not call these
        del context
        raise WorkshopError("Instructions resume attempted an earlier Workshop stage")

    workshop_kwargs = {
        "inventor_id": inventor_id,
        "tools": WorkshopTools(
            invent=unavailable,
            make=unavailable,
            playtest=unavailable,
            instructions=instructions,
        ),
        "runtime_root": runtime_root,
    }
    # These inert seams reconstruct only the checkpoint-bound contribution
    # level. They are never called by resume_instructions and never import or
    # execute the inventor's custom implementation.
    if level in ("custom-make", "custom-playtest"):
        workshop_kwargs["make"] = unavailable
    if level == "custom-playtest":
        workshop_kwargs["playtest"] = unavailable
    workshop = workshop_factory(card.root, lane, **workshop_kwargs)
    resumed = workshop.resume_instructions(assignment.wish).to_dict()
    handoff = ManagerAssignmentHandoff.from_assignment(assignment)
    if result.get("manager_assignment") != handoff.result_binding():
        raise WorkshopError(
            "Manager-resumed Instructions lost its exact assignment binding"
        )
    rebound = {**resumed, "manager_assignment": handoff.result_binding()}
    if not callable(state_validator):
        raise WorkshopError("Workshop resumed-state validator must be callable")
    return state_validator(
        assignment,
        rebound,
        allow_durable_factory_page=True,
    )


def _run_inventor(
    assignment,
    *,
    action: str = "run",
    continuing: bool = False,
    runner: Any = _managed_child_run,
    state_validator: Any = _validate_child_workshop_state,
) -> Mapping[str, Any]:
    if action not in ("run", "resume"):
        raise WorkshopError("Inventor process action must be run or resume")
    handoff = ManagerAssignmentHandoff.from_assignment(assignment)
    command = list(assignment.entrypoint)
    if command[0] in ("python", "python3"):
        command[0] = sys.executable
    command.extend((action, "--assignment-stdin"))
    inventor_id = assignment.decision.selected.card.inventor_id
    try:
        completed = runner(
            command,
            cwd=str(assignment.decision.selected.card.root),
            env=_inventor_process_environment(inventor_id),
            input=json.dumps(
                handoff.to_dict(),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ),
            capture_output=True,
            text=True,
            timeout=3600,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        root = Path(assignment.decision.selected.card.root).parent
        if action == "resume" or continuing:
            raise WorkshopError(
                "the resumed Inventor did not finish within 60 minutes; do not "
                "start another worker yet. Inspect the exact durable run with: %s. "
                "After the active lease expires, continue it with: %s"
                % (
                    _status_command(assignment.wish.product_id, root),
                    _resume_command(assignment.wish.product_id, root),
                )
            ) from exc
        raise WorkshopError(
            "the selected Inventor did not finish within 60 minutes and may still "
            "own the Wish lease. Do not create a duplicate Wish. Inspect the exact "
            "saved run with: %s. If the worker stopped, wait for its lease to expire, "
            "then continue the same Wish with: %s"
            % (
                _status_command(assignment.wish.product_id, root),
                _resume_command(assignment.wish.product_id, root),
            )
        ) from exc
    except (OSError, subprocess.SubprocessError) as exc:
        root = Path(assignment.decision.selected.card.root).parent
        if action == "resume" or continuing:
            raise WorkshopError(
                "the selected Inventor continuation could not run; no unverified "
                "result was accepted. Inspect it with: %s, then retry the exact "
                "Wish with: %s"
                % (
                    _status_command(assignment.wish.product_id, root),
                    _resume_command(assignment.wish.product_id, root),
                )
            ) from exc
        raise WorkshopError(
            "the selected Inventor process could not run; its exact assignment is "
            "saved, but no verified result was accepted. Do not create a duplicate "
            "Wish. Inspect the same Wish with: %s, then continue it with: %s"
            % (
                _status_command(assignment.wish.product_id, root),
                _resume_command(assignment.wish.product_id, root),
            )
        ) from exc
    if completed.returncode != 0:
        root = Path(assignment.decision.selected.card.root).parent
        if action == "resume" or continuing:
            database = (
                Path(assignment.decision.selected.card.root)
                / ".workshop"
                / "workshop.sqlite3"
            )
            active = (
                _ReadOnlyWorkshopStore(database).active_lease(
                    assignment.wish.product_id
                )
                if database.is_file() and not database.is_symlink()
                else None
            )
            if active is not None:
                raise WorkshopError(
                    "another Workshop worker owns this Wish until %s; wait, then "
                    "inspect it with: %s"
                    % (
                        active["expires_at"],
                        _status_command(assignment.wish.product_id, root),
                    )
                )
            raise WorkshopError(
                "the selected Inventor could not continue this exact checkpoint; "
                "the durable run was not upgraded from child output. Inspect it "
                "with: %s" % _status_command(assignment.wish.product_id, root)
            )
        raise WorkshopError(
            "the selected Inventor stopped before returning a verified Workshop "
            "result. Do not create a duplicate Wish. Inspect the same Wish with: "
            "%s, then continue it with: %s"
            % (
                _status_command(assignment.wish.product_id, root),
                _resume_command(assignment.wish.product_id, root),
            )
        )
    try:
        payload = json.loads(completed.stdout)
    except (TypeError, ValueError) as exc:
        raise WorkshopError(
            "the selected Inventor returned an unreadable Workshop result"
        ) from exc
    if not isinstance(payload, dict):
        raise WorkshopError("the selected Inventor must return one Workshop result")
    try:
        bound = validate_manager_assignment_result(payload, handoff)
    except WorkshopError as exc:
        raise WorkshopError(
            "the selected Inventor returned a result for a different Manager assignment"
        ) from exc
    if not callable(state_validator):
        raise WorkshopError("Workshop child state validator must be callable")
    trusted = state_validator(assignment, bound)
    assert_current = getattr(assignment, "assert_current", None)
    if callable(assert_current):
        assert_current()
    return trusted


def _resume_inventor(
    assignment,
    *,
    runner: Any = _managed_child_run,
    state_validator: Any = _validate_child_workshop_state,
) -> Mapping[str, Any]:
    """Continue one sealed Manager assignment in its selected Inventor child."""

    return _run_inventor(
        assignment,
        action="resume",
        continuing=True,
        runner=runner,
        state_validator=state_validator,
    )


def _assignment_file(card_root: Path, product_id: str) -> Path:
    digest = hashlib.sha256(product_id.encode("utf-8")).hexdigest()
    return Path(card_root) / ".workshop" / _ASSIGNMENT_DIRECTORY / (digest + ".json")


def _read_saved_handoff(path: Path, inventor_id: str) -> ManagerAssignmentHandoff:
    """Read one bounded, non-symlink Manager handoff used only for resume."""

    requested = Path(path)
    runtime_root = requested.parent.parent
    if runtime_root.is_symlink() or not runtime_root.is_dir():
        raise WorkshopError("Manager assignment runtime must be a regular directory")
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        runtime_descriptor = os.open(str(runtime_root), directory_flags)
    except OSError as exc:
        raise WorkshopError("cannot safely open Manager assignment runtime") from exc
    try:
        try:
            expected_directory = os.stat(
                requested.parent.name,
                dir_fd=runtime_descriptor,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            raise WorkshopError("this Wish has no saved Manager assignment")
        if not stat.S_ISDIR(expected_directory.st_mode):
            raise WorkshopError(
                "Manager assignment storage must be a regular directory"
            )
        try:
            assignment_descriptor = os.open(
                requested.parent.name,
                directory_flags,
                dir_fd=runtime_descriptor,
            )
        except OSError as exc:
            raise WorkshopError(
                "cannot safely open Manager assignment storage"
            ) from exc
        try:
            opened_directory = os.fstat(assignment_descriptor)
            if (
                opened_directory.st_dev,
                opened_directory.st_ino,
            ) != (expected_directory.st_dev, expected_directory.st_ino):
                raise WorkshopError(
                    "Manager assignment storage changed while opening"
                )
            try:
                expected = os.stat(
                    requested.name,
                    dir_fd=assignment_descriptor,
                    follow_symlinks=False,
                )
            except FileNotFoundError:
                raise WorkshopError("this Wish has no saved Manager assignment")
            if not stat.S_ISREG(expected.st_mode):
                raise WorkshopError(
                    "saved Manager assignment must be a regular file"
                )
            if not 1 <= expected.st_size <= MAX_HANDOFF_BYTES:
                raise WorkshopError("saved Manager assignment is empty or too large")
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
            try:
                descriptor = os.open(
                    requested.name,
                    flags,
                    dir_fd=assignment_descriptor,
                )
            except OSError as exc:
                raise WorkshopError(
                    "cannot safely read the saved Manager assignment"
                ) from exc
            try:
                opened = os.fstat(descriptor)
                if not stat.S_ISREG(opened.st_mode) or (
                    opened.st_dev,
                    opened.st_ino,
                ) != (expected.st_dev, expected.st_ino):
                    raise WorkshopError(
                        "saved Manager assignment changed while opening"
                    )
                source = os.read(descriptor, MAX_HANDOFF_BYTES + 1)
                if len(source) > MAX_HANDOFF_BYTES or os.read(descriptor, 1):
                    raise WorkshopError("saved Manager assignment is too large")
                after = os.fstat(descriptor)
                if (
                    after.st_size != opened.st_size
                    or after.st_mtime_ns != opened.st_mtime_ns
                    or (after.st_dev, after.st_ino)
                    != (opened.st_dev, opened.st_ino)
                ):
                    raise WorkshopError(
                        "saved Manager assignment changed while reading"
                    )
            finally:
                os.close(descriptor)
        finally:
            os.close(assignment_descriptor)
    finally:
        os.close(runtime_descriptor)
    try:
        value = json.loads(source.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise WorkshopError("saved Manager assignment is not valid UTF-8 JSON") from exc
    if not isinstance(value, Mapping):
        raise WorkshopError("saved Manager assignment must be one object")
    return ManagerAssignmentHandoff.from_dict(
        value, expected_inventor_id=inventor_id
    )


def _save_manager_assignment(assignment: Any) -> Path:
    """Durably save the exact one-shot handoff before launching contribution code."""

    handoff = ManagerAssignmentHandoff.from_assignment(assignment)
    card_root = Path(assignment.decision.selected.card.root)
    runtime_root = card_root / ".workshop"
    assignment_root = runtime_root / _ASSIGNMENT_DIRECTORY
    for directory in (runtime_root, assignment_root):
        if directory.is_symlink():
            raise WorkshopError("Manager assignment storage must not be a symlink")
        directory.mkdir(mode=0o700, exist_ok=True)
        if not directory.is_dir():
            raise WorkshopError("Manager assignment storage must be a directory")
        try:
            os.chmod(directory, 0o700)
        except OSError as exc:
            raise WorkshopError("cannot secure Manager assignment storage") from exc
    path = _assignment_file(card_root, handoff.wish.product_id)
    source = (
        json.dumps(
            handoff.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(str(path), flags, 0o600)
    except FileExistsError:
        existing = _read_saved_handoff(path, handoff.inventor_id)
        if existing.to_dict() != handoff.to_dict():
            raise WorkshopError(
                "this Wish id is already bound to a different Manager assignment"
            )
        return path
    except OSError as exc:
        raise WorkshopError("cannot save the exact Manager assignment") from exc
    try:
        written = 0
        while written < len(source):
            written += os.write(descriptor, source[written:])
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    try:
        directory_descriptor = os.open(str(assignment_root), directory_flags)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except OSError as exc:
        raise WorkshopError("cannot durably seal the Manager assignment") from exc
    return path


def _find_durable_wish(
    root: Path, product_id: str, *, allow_missing: bool = False
) -> Optional[Mapping[str, Any]]:
    """Locate one product in Inventor-owned durable stores without mutation."""

    catalog = discover_inventor_catalog(root)
    matches = []
    for card in catalog.cards:
        assignment_path = _assignment_file(card.root, product_id)
        handoff = None
        if assignment_path.exists() or assignment_path.is_symlink():
            handoff = _read_saved_handoff(assignment_path, card.inventor_id)
            if handoff.wish.product_id != product_id:
                raise WorkshopError("saved Manager assignment belongs to another Wish")
        database = Path(card.root) / ".workshop" / "workshop.sqlite3"
        if database.is_symlink() or not database.is_file():
            if handoff is not None:
                matches.append(
                    {
                        "card": card,
                        "database": database,
                        "runtime": None,
                        "product": None,
                        "events": (),
                        "latest": None,
                        "handoff": handoff,
                    }
                )
            continue
        runtime = _ReadOnlyWorkshopStore(database)
        try:
            product = runtime.get_product(product_id)
        except KeyError:
            if handoff is not None:
                matches.append(
                    {
                        "card": card,
                        "database": database,
                        "runtime": runtime,
                        "product": None,
                        "events": (),
                        "latest": None,
                        "handoff": handoff,
                    }
                )
            continue
        if not runtime.verify_event_chain(product_id):
            raise WorkshopError(
                "saved Workshop event chain is invalid for %s" % product_id
            )
        events = runtime.events(product_id)
        if not events:
            raise WorkshopError("saved Workshop event chain is empty")
        matches.append(
            {
                "card": card,
                "database": database,
                "runtime": runtime,
                "product": product,
                "events": events,
                "latest": events[-1],
                "handoff": handoff,
            }
        )
    if not matches:
        if allow_missing:
            return None
        raise WorkshopError(
            "no saved Wish %r was found under %s; use the id printed by 'workshop wish'"
            % (product_id, Path(root))
        )
    if len(matches) != 1:
        raise WorkshopError(
            "Wish %r exists in more than one Inventor store; resolve the duplicate before continuing"
            % product_id
        )
    return matches[0]


def _root_for_durable_wish(
    roots: Sequence[Path], product_id: str
) -> tuple[Path, Mapping[str, Any]]:
    """Find an exact Wish across current and retained installed catalogs."""

    matches = []
    for root in roots:
        located = _find_durable_wish(root, product_id, allow_missing=True)
        if located is not None:
            matches.append((Path(root).resolve(), located))
    if not matches:
        searched = ", ".join(str(Path(root)) for root in roots)
        raise WorkshopError(
            "no saved Wish %r was found in the available catalog(s): %s; "
            "use the id printed by 'workshop wish'" % (product_id, searched)
        )
    if len(matches) != 1:
        raise WorkshopError(
            "Wish %r exists in more than one retained catalog; pass the exact "
            "--root printed when it started" % product_id
        )
    return matches[0]


def _valid_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _has_persisted_invented(events: Sequence[Mapping[str, Any]]) -> bool:
    for event in reversed(events):
        payload = event.get("payload")
        if (
            event.get("from_stage") != "invent"
            or event.get("to_stage") != "make"
            or not isinstance(payload, Mapping)
            or "invented" not in payload
        ):
            continue
        try:
            _invented_from_event(payload["invented"])
        except (TypeError, WorkshopError):
            return False
        return True
    return False


def _has_persisted_make_feedback(
    events: Sequence[Mapping[str, Any]], round_number: Any
) -> bool:
    if round_number == 1:
        return True
    if type(round_number) is not int or round_number < 2:
        return False
    for event in reversed(events):
        payload = event.get("payload")
        if (
            event.get("from_stage") != "playtest"
            or event.get("to_stage") != "make"
            or not isinstance(payload, Mapping)
            or payload.get("round") != round_number
        ):
            continue
        values = payload.get("feedback")
        if not isinstance(values, list) or not values:
            return False
        try:
            feedback = tuple(Feedback(**dict(value)) for value in values)
        except (TypeError, WorkshopError):
            return False
        return all(item.severity in ("improve", "block") for item in feedback)
    return False


def _resume_binding_problem(located: Mapping[str, Any]) -> Optional[str]:
    """Fail before a child effect when saved Manager and Workshop identities drift."""

    handoff = located.get("handoff")
    card = located.get("card")
    if not isinstance(handoff, ManagerAssignmentHandoff) or card is None:
        return "this durable product has no exact saved Manager assignment"
    if handoff.inventor_id != getattr(card, "inventor_id", None):
        return "the saved Manager assignment selected a different Inventor"
    if not handoff.has_exact_inventor_identity:
        return (
            "this legacy Manager assignment did not save the selected Inventor "
            "implementation identity, so contribution code cannot resume safely"
        )
    try:
        handoff.assert_inventor_current(card)
        lane, level = _manifest_workshop_shape(card)
        taste = load_taste(card.root)
    except (OSError, WorkshopError, ValueError) as exc:
        return "the selected Inventor identity changed: %s" % exc
    product = located.get("product")
    if product is None:
        return None
    metadata = product.get("metadata")
    expected = {
        "wish": handoff.wish.to_dict(),
        "inventor_id": handoff.inventor_id,
        "taste_sha256": taste.sha256,
        "blueprint_sha256": ToyBlueprint.for_lane(lane).sha256,
        "lane": lane,
        "customization_level": level,
        "playtest_rounds": handoff.playtest_rounds,
    }
    if metadata != expected:
        return (
            "durable Workshop bindings differ from the exact saved Manager assignment, "
            "Inventor identity, Taste, lane, customization, or Playtest allowance"
        )
    return None


def _accepted_invented_record(
    located: Mapping[str, Any]
) -> tuple[Optional[Mapping[str, Any]], Optional[Invented]]:
    metadata = located.get("product", {}).get("metadata")
    if not isinstance(metadata, Mapping):
        return None, None
    for event in reversed(located.get("events", ())):
        payload = event.get("payload")
        if (
            event.get("from_stage") != "invent"
            or event.get("to_stage") != "make"
            or not isinstance(payload, Mapping)
            or "invented" not in payload
        ):
            continue
        try:
            invented = _invented_from_event(payload["invented"])
        except (TypeError, WorkshopError):
            return event, None
        wish = metadata.get("wish")
        expected_wish_sha256 = (
            hashlib.sha256(
                json.dumps(
                    wish,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                    allow_nan=False,
                ).encode("utf-8")
            ).hexdigest()
            if isinstance(wish, Mapping)
            else None
        )
        if (
            not invented.passed
            or invented.wish_sha256 != expected_wish_sha256
            or invented.taste_sha256 != metadata.get("taste_sha256")
            or invented.lane != metadata.get("lane")
            or payload.get("round") != 1
            or payload.get("concept_sha256") != invented.concept_sha256
            or payload.get("invent_score") != invented.score
            or payload.get("invent_target_score") != invented.target_score
        ):
            return event, None
        return event, invented
    return None, None


def _exact_playtest_checkpoint_problem(
    located: Mapping[str, Any], run_root: Path, latest_payload: Mapping[str, Any]
) -> Optional[str]:
    round_number = latest_payload.get("round")
    made_event = next(
        (
            event
            for event in reversed(located.get("events", ()))
            if event.get("from_stage") == "make"
            and event.get("to_stage") == "playtest"
            and isinstance(event.get("payload"), Mapping)
            and event["payload"].get("round") == round_number
        ),
        None,
    )
    if made_event is None:
        return "Playtest has no authoritative Make-to-Playtest checkpoint event"
    made_event_payload = made_event["payload"]
    expected_refs = {
        key: made_event_payload.get(key)
        for key in (
            "made_checkpoint_path",
            "made_checkpoint_sha256",
            "made_checkpoint_round",
        )
    }
    if {key: latest_payload.get(key) for key in expected_refs} != expected_refs:
        return "latest Playtest state cites a different Made checkpoint"
    try:
        checkpoint, made_digest = _read_stage_checkpoint(
            run_root, made_event, "made"
        )
        metadata = located["product"]["metadata"]
        expected_keys = set(metadata) | {
            "product_id",
            "round",
            "invented",
            "input_feedback",
            "made",
        }
        # ``wish`` already lives in metadata; checkpoint bindings add product_id.
        if set(checkpoint) != expected_keys:
            return "Made checkpoint payload shape is not exact"
        if any(checkpoint.get(key) != value for key, value in metadata.items()):
            return "Made checkpoint bindings differ from the durable Workshop"
        if (
            checkpoint.get("product_id") != located["product"]["id"]
            or checkpoint.get("round") != round_number
        ):
            return "Made checkpoint belongs to a different Wish or round"
        _, accepted = _accepted_invented_record(located)
        if accepted is None or checkpoint.get("invented") != accepted.to_dict():
            return "Made checkpoint cites a different Invented record"
        made = _rebuild_made_value(run_root, checkpoint.get("made"))
        made.assert_current()
        if (
            made_event.get("artifact_sha256") != made.artifact_sha256
            or made_event_payload.get("artifact_sha256") != made.artifact_sha256
            or located["product"].get("artifact_sha256")
            != made.artifact_sha256
        ):
            return "Made checkpoint differs from the Playtest artifact identity"
        if "playtested_checkpoint_sha256" in latest_payload:
            completed, completed_digest = _read_stage_checkpoint(
                run_root, located["latest"], "playtested"
            )
            expected_completed_keys = set(metadata) | {
                "product_id",
                "round",
                "made_checkpoint_sha256",
                "made",
                "playtested",
            }
            if set(completed) != expected_completed_keys:
                return "Playtested checkpoint payload shape is not exact"
            if any(completed.get(key) != value for key, value in metadata.items()):
                return "Playtested checkpoint bindings differ from the durable Workshop"
            if (
                completed.get("product_id") != located["product"]["id"]
                or completed.get("round") != round_number
                or completed.get("made_checkpoint_sha256") != made_digest
                or completed_digest
                != latest_payload.get("playtested_checkpoint_sha256")
            ):
                return "Playtested checkpoint identity is inconsistent"
            completed_made = _rebuild_made_value(
                run_root, completed.get("made")
            )
            completed_made.assert_current()
            if (
                completed_made.artifact_manifest.to_dict()
                != made.artifact_manifest.to_dict()
                or completed_made.product != made.product
            ):
                return "Playtested checkpoint contains different Made bytes"
            _rebuild_playtested_value(
                run_root, completed.get("playtested"), completed_made
            )
    except (KeyError, OSError, TypeError, ValueError, WorkshopError) as exc:
        return "the exact Playtest checkpoint is unavailable: %s" % exc
    return None


def _exact_instructions_checkpoint_problem(
    located: Mapping[str, Any], run_root: Path, latest_payload: Mapping[str, Any]
) -> Optional[str]:
    try:
        latest = located["latest"]
        checkpoint, checkpoint_digest = _read_instructions_checkpoint(
            run_root, latest
        )
        metadata = located["product"]["metadata"]
        expected_keys = set(metadata) | {
            "product_id",
            "round",
            "made",
            "playtested",
        }
        if set(checkpoint) != expected_keys:
            return "Instructions checkpoint payload shape is not exact"
        if any(checkpoint.get(key) != value for key, value in metadata.items()):
            return "Instructions checkpoint bindings differ from the durable Workshop"
        round_number = latest_payload.get("round")
        if (
            checkpoint.get("product_id") != located["product"]["id"]
            or checkpoint.get("round") != round_number
            or latest_payload.get("resume_checkpoint_sha256")
            != checkpoint_digest
        ):
            return "Instructions checkpoint identity is inconsistent"
        approval = next(
            (
                event
                for event in reversed(located.get("events", ()))
                if event.get("from_stage") == "playtest"
                and event.get("to_stage") == "instructions"
                and isinstance(event.get("payload"), Mapping)
                and event["payload"].get("resume_checkpoint_sha256")
                == checkpoint_digest
            ),
            None,
        )
        if approval is None:
            return "Instructions checkpoint has no approved Playtest event"
        made, playtested, evidence_root = _rebuild_checkpoint_results(
            run_root, checkpoint
        )
        made.assert_current()
        blueprint = ToyBlueprint.for_lane(metadata["lane"])
        if not playtested.passed or _playtest_policy_needs(
            blueprint, made, playtested, evidence_root
        ):
            return "Instructions checkpoint no longer satisfies Playtest policy"
        if (
            located["product"].get("artifact_sha256") != made.artifact_sha256
            or latest.get("artifact_sha256") != made.artifact_sha256
            or approval.get("artifact_sha256") != made.artifact_sha256
            or approval["payload"].get("round") != round_number
            or approval["payload"].get("evidence_artifact_sha256")
            != playtested.evidence.evidence_artifact_sha256
        ):
            return "Instructions checkpoint identifies different Make or Playtest bytes"
    except (KeyError, OSError, TypeError, ValueError, WorkshopError) as exc:
        return "the exact Instructions checkpoint is unavailable: %s" % exc
    return None


def _resume_availability(
    located: Mapping[str, Any], page: Optional[Mapping[str, Any]] = None
) -> tuple[bool, str, str]:
    """Decide whether durable state supports an exact, non-overlapping resume."""

    product = located.get("product")
    runtime = located.get("runtime")
    binding_problem = _resume_binding_problem(located)
    if binding_problem is not None:
        return False, "identity-drift", binding_problem
    if product is None:
        if isinstance(located.get("handoff"), ManagerAssignmentHandoff):
            return (
                True,
                "assigned",
                "the exact saved Manager assignment can start its selected Inventor",
            )
        return (
            False,
            "not-started",
            "the selected Inventor has not created durable Workshop state yet",
        )
    if runtime is None or not callable(getattr(runtime, "active_lease", None)):
        return False, "malformed", "the durable Workshop store is unavailable"
    active = runtime.active_lease(product["id"])
    if active is not None:
        return (
            False,
            "active-worker",
            "another Workshop worker owns this Wish until %s; wait and check status before resuming"
            % active["expires_at"],
        )
    stage = product.get("stage")
    if stage == "wish":
        return (
            True,
            "wish",
            "the registered Wish can restart before Invent without changing identity",
        )
    if (
        stage != "instructions"
        and isinstance(page, Mapping)
        and page.get("status") in ("draft", "unknown")
    ):
        return True, "factory-page", "the exact Factory page can be continued"

    card = located.get("card")
    card_root = getattr(card, "root", None)
    run_root = (
        Path(card_root) / ".workshop" / "runs" / product["id"]
        if card_root is not None
        else None
    )
    if (
        run_root is None
        or run_root.is_symlink()
        or not run_root.is_dir()
    ):
        return (
            False,
            "missing-workspace",
            "the exact Workshop run workspace is missing or unsafe; this saved state cannot continue",
        )

    latest = located.get("latest")
    payload = latest.get("payload") if isinstance(latest, Mapping) else None
    if not isinstance(payload, Mapping):
        return False, "malformed", "the latest Workshop checkpoint is malformed"
    status = payload.get("status")
    if status not in ("working", "waiting"):
        return (
            False,
            "terminal",
            "this Workshop run is terminal and has no stage to continue",
        )
    if stage == "invent":
        return True, "invent", "Invent can restart from its exact saved boundary"
    if stage == "make":
        events = located.get("events", ())
        _, accepted = _accepted_invented_record(located)
        if accepted is not None and _has_persisted_make_feedback(
            events, payload.get("round")
        ):
            return True, "make", "Make can restart from its accepted Invented record"
        return (
            False,
            "legacy-make",
            "this legacy Make state has no full accepted Invented record; start a new Wish instead of guessing it",
        )
    if stage == "playtest":
        if (
            isinstance(payload.get("made_checkpoint_path"), str)
            and bool(payload["made_checkpoint_path"])
            and _valid_sha256(payload.get("made_checkpoint_sha256"))
            and payload.get("made_checkpoint_round") == payload.get("round")
        ):
            checkpoint_problem = _exact_playtest_checkpoint_problem(
                located, run_root.resolve(strict=True), payload
            )
            if checkpoint_problem is not None:
                return False, "invalid-playtest-checkpoint", checkpoint_problem
            return True, "playtest", "Playtest can restart from its exact Made checkpoint"
        return (
            False,
            "legacy-playtest",
            "this legacy Playtest state has no exact Made checkpoint; start a new Wish instead of rerunning Make implicitly",
        )
    if stage == "instructions":
        modern_checkpoint = (
            isinstance(payload.get("instructions_checkpoint_path"), str)
            and bool(payload["instructions_checkpoint_path"])
            and _valid_sha256(payload.get("instructions_checkpoint_sha256"))
            and payload.get("instructions_checkpoint_round")
            == payload.get("round")
            and payload.get("resume_checkpoint_sha256")
            == payload.get("instructions_checkpoint_sha256")
        )
        legacy_waiting_checkpoint = (
            status == "waiting"
            and _valid_sha256(payload.get("resume_checkpoint_sha256"))
            and payload.get("instructions_checkpoint_path") is None
        )
        if status in ("working", "waiting") and (
            modern_checkpoint or legacy_waiting_checkpoint
        ):
            checkpoint_problem = _exact_instructions_checkpoint_problem(
                located, run_root.resolve(strict=True), payload
            )
            if checkpoint_problem is not None:
                return False, "invalid-instructions-checkpoint", checkpoint_problem
            return (
                True,
                "instructions",
                "Instructions can continue from its approved Make and Playtest checkpoint",
            )
        return (
            False,
            "legacy-instructions",
            "Instructions has no exact waiting checkpoint that can be continued safely",
        )
    return (
        False,
        "unsupported-stage",
        "%s is not a resumable Workshop stage" % stage,
    )


def _status_receipt(root: Path, product_id: str) -> Mapping[str, Any]:
    located = _find_durable_wish(root, product_id)
    if located is None:  # ``allow_missing`` is false; keeps type narrowing explicit.
        raise WorkshopError("saved Wish disappeared while reading status")
    card = located["card"]
    product = located["product"]
    latest = located["latest"]
    if product is None:
        handoff = located.get("handoff")
        if not isinstance(handoff, ManagerAssignmentHandoff):
            raise WorkshopError("saved Wish has no durable state or Manager assignment")
        receipt = {
            "schema_version": 1,
            "catalog_root": str(Path(root).resolve()),
            "product_id": product_id,
            "status": "assigned",
            "job": "wish",
            "round": None,
            "inventor_id": card.inventor_id,
            "inventor_name": card.name,
            "artifact_sha256": None,
            "updated_at": None,
            "wish": handoff.wish.to_dict(),
            "needs": [],
            "event_chain": "not-started",
        }
        available, kind, _ = _resume_availability(located)
        if available:
            receipt["resume"] = {
                "status": "available",
                "kind": kind,
                "command": _resume_command(product_id, root),
            }
        return receipt
    payload = latest.get("payload")
    if not isinstance(payload, Mapping):
        raise WorkshopError("latest Workshop event payload is malformed")
    raw_needs = payload.get("needs", [])
    if not isinstance(raw_needs, list):
        raise WorkshopError("latest Workshop needs are malformed")
    try:
        needs = [Need(**dict(item)).to_dict() for item in raw_needs]
    except (TypeError, WorkshopError) as exc:
        raise WorkshopError("latest Workshop needs are malformed") from exc
    metadata = product.get("metadata")
    if not isinstance(metadata, Mapping):
        raise WorkshopError("saved Wish metadata is malformed")
    wish = metadata.get("wish")
    if not isinstance(wish, Mapping) or wish.get("product_id") != product_id:
        raise WorkshopError("saved Wish metadata has a different identity")
    if "status" in payload:
        status = payload["status"]
    elif (
        product.get("stage") == "wish"
        and latest.get("kind") == "registered"
        and latest.get("to_stage") == "wish"
    ):
        status = "working"
    else:
        raise WorkshopError("latest Workshop transition has no explicit status")
    if status not in ("working", "waiting", "stopped", "delivered"):
        raise WorkshopError("latest Workshop status is malformed")
    receipt = {
        "schema_version": 1,
        "catalog_root": str(Path(root).resolve()),
        "product_id": product_id,
        "status": status,
        "job": product.get("stage"),
        "round": payload.get("round"),
        "inventor_id": card.inventor_id,
        "inventor_name": card.name,
        "artifact_sha256": product.get("artifact_sha256"),
        "updated_at": product.get("updated_at"),
        "wish": dict(wish),
        "needs": needs,
        "event_chain": "valid",
    }
    active = located["runtime"].active_lease(product_id)
    if active is not None:
        receipt["worker"] = {
            "status": "active",
            "expires_at": active["expires_at"],
        }
    intent = _ReadOnlyWorkshopStore(located["database"]).latest_publish_intent(
        product_id
    )
    raw_receipt = intent.get("receipt") if isinstance(intent, Mapping) else None
    page = None
    if raw_receipt is not None:
        instructions_sha256 = next(
            (
                event["payload"].get("instructions_sha256")
                for event in reversed(located["events"])
                if isinstance(event.get("payload"), Mapping)
                and isinstance(event["payload"].get("instructions_sha256"), str)
            ),
            None,
        )
        if instructions_sha256 is None:
            instructions_root = (
                Path(card.root)
                / ".workshop"
                / "runs"
                / product_id
                / "instructions"
            )
            try:
                instructions_sha256 = sealed_instructions_manifest(
                    instructions_root
                ).artifact_sha256
            except WorkshopError as exc:
                raise WorkshopError(
                    "saved Factory draft has no exact sealed Instructions identity"
                ) from exc
        try:
            page = Receipt.from_dict(raw_receipt)
            page.assert_artifact(product.get("artifact_sha256"))
        except (TypeError, WorkshopError) as exc:
            raise WorkshopError(
                "saved Factory page receipt identifies different product bytes"
            ) from exc
        if (
            not isinstance(instructions_sha256, str)
            or page.details.get("instructions_sha256") != instructions_sha256
        ):
            raise WorkshopError(
                "saved Factory page receipt identifies different Instructions"
            )
    if page is not None and (page.is_verified_draft or page.is_verified_public):
        intent_state = intent.get("state") if isinstance(intent, Mapping) else None
        receipt["page"] = {
            "status": (
                "unknown"
                if intent_state in ("publishing", "live_unknown")
                else "public"
                if page.is_verified_public and intent_state == "live"
                else "draft"
            ),
            "page_url": page.details.get("page_url"),
        }
    available, kind, _ = _resume_availability(located, receipt.get("page"))
    if available:
        receipt["resume"] = {
            "status": "available",
            "kind": kind,
            "command": _resume_command(product_id, root),
        }
    return receipt


def _promote_factory_intent(
    store: Any,
    intent: Mapping[str, Any],
    draft: Receipt,
    credentials: Any,
    *,
    product_id: str,
    session_factory: Any,
    transition_factory: Any,
) -> Receipt:
    """Fence one public effect and reconcile crash ambiguity by GET only."""

    intent_id = intent.get("id")
    if not isinstance(intent_id, str) or not intent_id:
        raise WorkshopError("the selected Inventor Factory intent is malformed")
    if intent.get("state") == "live":
        public = Receipt.from_dict(intent.get("receipt"))
        if not public.is_verified_public:
            raise WorkshopError("durable Factory live receipt is not verified")
        public.assert_artifact(draft.artifact_sha256)
        return public

    holder = "workshop-cli-public-%s-%s" % (os.getpid(), secrets.token_hex(8))
    # Factory HTTP retries are bounded to minutes. Fifteen minutes fences one
    # complete transition without making a crash unrecoverable for hours.
    lease_token = store.acquire_lease(product_id, holder, ttl_seconds=900)
    try:
        intent = store.get_publish_intent(intent_id)
        if intent.get("state") == "publishing":
            # Acquiring the product lease proves the prior lease was released or
            # expired. Convert the stranded effect to ambiguity before any GET;
            # never resend the public transition from this state.
            store.recover_stranded_intent(
                intent_id,
                "previous public transition ended without a durable completion",
            )
            intent = store.get_publish_intent(intent_id)
        intent_state = intent.get("state")
        if intent_state == "live":
            public = Receipt.from_dict(intent.get("receipt"))
            if not public.is_verified_public:
                raise WorkshopError("durable Factory live receipt is not verified")
            public.assert_artifact(draft.artifact_sha256)
            return public

        session = session_factory(credentials)
        transition = transition_factory(session)
        if intent_state == "live_unknown":
            # Authenticated readback is the only effect allowed here. A draft
            # does not prove whether a prior publish crossed the boundary.
            identity = session.login()
            draft.assert_owner(identity.owner_id)
            door = ShopDoor(
                "manager-session",
                transport=session.authenticated_transport,
            )
            observed = transition._receipt(
                transition._design(door.get_design(draft.slug)),
                draft,
                identity.owner_id,
            )
            if not transition._is_current_public(observed):
                raise AmbiguousEffectError(
                    "Factory publication remains unknown: authenticated readback "
                    "does not prove the exact current history public; no retry was sent"
                )
            store.resolve_live_as_public(intent_id, observed)
            return observed

        if intent_state != "succeeded":
            raise WorkshopError(
                "Factory draft intent is %s, not a verified resumable draft"
                % intent_state
            )
        request = intent.get("request")
        if not isinstance(request, Mapping):
            raise WorkshopError("durable Factory draft request is malformed")
        origins = [
            request.get(name)
            for name in (
                "_workshop_api_origin",
                "_foundation_api_origin",
                "_core_api_origin",
            )
            if request.get(name) is not None
        ]
        if len(set(origins)) != 1 or not origins:
            raise WorkshopError("durable Factory draft has no unambiguous API origin")
        proof = {
            "instructions_sha256": draft.details.get("instructions_sha256"),
            "playtest_evidence_sha256": draft.details.get(
                "playtest_evidence_sha256"
            ),
            "page_url": draft.details.get("page_url"),
        }
        if any(not isinstance(value, str) or not value for value in proof.values()):
            raise WorkshopError(
                "authenticated Factory draft lacks exact Instructions, Playtest, or page proof"
            )
        publishing = store.begin_live(
            intent_id,
            {
                "api_origin": origins[0],
                "owner_id": draft.owner_id,
                "proof": proof,
            },
            lease_token=lease_token,
        )
        effect_token = publishing.get("effect_token")
        if not isinstance(effect_token, str) or not effect_token:
            raise WorkshopError("durable Factory publication fence is malformed")
        try:
            public = transition.publish(draft)
        except AmbiguousEffectError as exc:
            store.mark_live_unknown(
                intent_id, effect_token, "%s: %s" % (type(exc).__name__, exc)
            )
            raise
        except EffectError as exc:
            store.restore_draft_after_publish_rejection(
                intent_id, effect_token, "%s: %s" % (type(exc).__name__, exc)
            )
            raise
        except Exception as exc:
            store.mark_live_unknown(
                intent_id, effect_token, "%s: %s" % (type(exc).__name__, exc)
            )
            raise AmbiguousEffectError(
                "Factory publication outcome is unknown; reconcile before retry"
            ) from exc
        if not isinstance(public, Receipt) or not public.is_verified_public:
            store.mark_live_unknown(
                intent_id,
                effect_token,
                "Factory transition returned no verified public receipt",
            )
            raise AmbiguousEffectError(
                "Factory publication returned no verified public readback; reconcile before retry"
            )
        store.mark_publish_live(intent_id, effect_token, public)
        return public
    finally:
        store.release_lease(product_id, lease_token)


def _publish_inventor_draft(
    assignment,
    result: Mapping[str, Any],
    *,
    store_factory: Any = InventorStore,
    session_factory: Any = FactoryAgentSession,
    transition_factory: Any = FactoryPublicTransition,
) -> Mapping[str, Any]:
    """Durably promote the exact authenticated Instructions draft, then prove it."""

    product_id = assignment.wish.product_id
    inventor_id = assignment.decision.selected.card.inventor_id
    page_url = result.get("page_url")
    artifact_sha256 = result.get("artifact_sha256")
    if not isinstance(page_url, str) or not page_url:
        return {
            "status": "waiting",
            "reason": "Instructions has not produced an authenticated Factory draft yet.",
        }
    environment = _factory_credential_environment(inventor_id)
    if environment is None:
        catalog_root = Path(assignment.decision.selected.card.root).parent
        return {
            "status": "waiting",
            "reason": (
                "FACTORY_PASSWORD is not configured in the trusted Manager. Set it, "
                "then run: %s. The value is never printed or passed to Inventor code."
                % _resume_command(product_id, catalog_root)
            ),
        }
    try:
        credentials = factory_credentials_from_environment(inventor_id, environment)
        runtime_root = Path(assignment.decision.selected.card.root) / ".workshop"
        store = store_factory(runtime_root / "workshop.sqlite3")
        intent = store.latest_publish_intent(product_id)
        receipt_value = intent.get("receipt") if isinstance(intent, Mapping) else None
        draft = Receipt.from_dict(receipt_value)
        if draft.details.get("page_url") != page_url:
            raise WorkshopError(
                "the Factory draft URL differs from the Workshop Instructions receipt"
            )
        if isinstance(artifact_sha256, str):
            draft.assert_artifact(artifact_sha256)
        if not isinstance(intent, Mapping):
            raise WorkshopError("the selected Inventor has no durable Factory intent")
        public = _promote_factory_intent(
            store,
            intent,
            draft,
            credentials,
            product_id=product_id,
            session_factory=session_factory,
            transition_factory=transition_factory,
        )
    except WorkshopError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise WorkshopError(
            "the selected Inventor has no exact authenticated draft to publish"
        ) from exc
    return {
        "status": "public",
        "verified": True,
        "inventor_id": inventor_id,
        "design_id": public.design_id,
        "slug": public.slug,
        "current_history_id": public.current_history_id,
        "page_url": page_url,
    }


def _waiting_receipt(wish: Wish, waiting: WaitingFor) -> Mapping[str, Any]:
    return {
        "schema_version": 1,
        "status": "waiting",
        "wish": wish.to_dict(),
        "needs": [item.to_dict() for item in waiting.needs],
    }


def _status_command(product_id: str, root: Path) -> str:
    return _shell_command("workshop", "status", product_id, "--root", Path(root))


def _resume_command(product_id: str, root: Path, *, draft: bool = False) -> str:
    parts = ["workshop", "resume", product_id, "--root", Path(root)]
    if draft:
        parts.append("--draft")
    return _shell_command(*parts)


def _wish_command(objective: str, root: Path, *, draft: bool = False) -> str:
    parts = ["workshop", "wish", objective, "--root", Path(root)]
    if draft:
        parts.append("--draft")
    return _shell_command(*parts)


def _print_wish_receipt(
    receipt: Mapping[str, Any],
    *,
    root: Optional[Path] = None,
    show_wish: bool = True,
    show_match: bool = True,
) -> None:
    wish = receipt["wish"]
    if show_wish:
        print("Wish: %s" % wish["product_id"])
    match = receipt.get("match")
    if show_match and isinstance(match, dict):
        print("Matched with %s." % match["name"])
        print("Why: %s" % match["explanation"])
    result = receipt.get("result", receipt)
    invented = result.get("invented")
    if isinstance(invented, dict):
        concept = invented.get("concept")
        title = concept.get("title") if isinstance(concept, dict) else None
        if isinstance(title, str) and title:
            print(
                "Invented: %s (%s/%s)."
                % (title, invented.get("score"), invented.get("target_score"))
            )
    if result.get("status") == "waiting":
        job = result.get("job")
        print("Waiting%s." % (" at %s" % str(job).title() if job else ""))
        for need in result.get("needs", ()):
            print("Need: %s" % need["capability"])
            print("Why: %s" % need["reason"])
            instructions = need.get("instructions")
            if isinstance(instructions, str) and instructions:
                print("Next: %s" % instructions)
        if isinstance(result.get("next_command"), str):
            print("Retry: %s" % result["next_command"])
    else:
        print("Status: %s" % result.get("status", "started"))
    publication = result.get("publication")
    is_live = isinstance(publication, Mapping) and publication.get("status") == "public"
    page_url = result.get("page_url")
    if isinstance(page_url, str) and page_url and not is_live:
        print("Draft: %s" % page_url)
    if isinstance(publication, Mapping):
        if publication.get("status") == "public":
            print("Live: %s" % publication["page_url"])
        elif publication.get("reason"):
            print("Page: waiting — %s" % publication["reason"])
    if root is not None and match is not None:
        print("Saved: %s" % _status_command(wish["product_id"], root))
        if result.get("status") == "waiting":
            durable = _status_receipt(root, wish["product_id"])
            resume = durable.get("resume")
            if isinstance(resume, Mapping) and resume.get("status") == "available":
                print("Resume: %s" % resume["command"])


def _print_status_receipt(receipt: Mapping[str, Any], *, root: Path) -> None:
    print("Wish: %s" % receipt["product_id"])
    print("Inventor: %s" % receipt["inventor_name"])
    print(
        "Status: %s at %s%s"
        % (
            receipt["status"],
            str(receipt["job"]).title(),
            " (round %s)" % receipt["round"]
            if isinstance(receipt.get("round"), int)
            else "",
        )
    )
    for need in receipt.get("needs", ()):
        print("Need: %s" % need["capability"])
        print("Why: %s" % need["reason"])
        print("Next: %s" % need["instructions"])
    page = receipt.get("page")
    if isinstance(page, Mapping):
        label = {
            "public": "Live",
            "draft": "Draft",
            "unknown": "Page (publication unknown)",
        }.get(page.get("status"), "Page")
        if page.get("page_url"):
            print("%s: %s" % (label, page["page_url"]))
    worker = receipt.get("worker")
    if isinstance(worker, Mapping) and worker.get("status") == "active":
        print("Worker: active until %s" % worker["expires_at"])
    print("Event chain: %s" % receipt["event_chain"])
    resume = receipt.get("resume")
    if isinstance(resume, Mapping) and resume.get("status") == "available":
        print("Resume: %s" % resume["command"])


def _status(args: argparse.Namespace) -> int:
    roots = _catalog_roots(args.root, include_retained=args.root is None)
    if args.product_id is None:
        products: dict[str, Path] = {}
        for root in roots:
            catalog = discover_inventor_catalog(root)
            product_ids = []
            for card in catalog.cards:
                assignment_root = (
                    Path(card.root) / ".workshop" / _ASSIGNMENT_DIRECTORY
                )
                if assignment_root.is_symlink():
                    raise WorkshopError(
                        "Manager assignment storage must not be a symlink"
                    )
                if assignment_root.is_dir():
                    for path in sorted(assignment_root.glob("*.json")):
                        handoff = _read_saved_handoff(path, card.inventor_id)
                        product_ids.append(handoff.wish.product_id)
                database = Path(card.root) / ".workshop" / "workshop.sqlite3"
                if database.is_symlink() or not database.is_file():
                    continue
                product_ids.extend(
                    item["id"]
                    for item in _ReadOnlyWorkshopStore(database).list_products()
                )
            for product_id in set(product_ids):
                prior = products.get(product_id)
                resolved = Path(root).resolve()
                if prior is not None and prior != resolved:
                    raise WorkshopError(
                        "Wish %r exists in more than one retained catalog; pass "
                        "an exact --root" % product_id
                    )
                products[product_id] = resolved
        records = [
            _status_receipt(root, product_id)
            for product_id, root in sorted(products.items())
        ]
        receipt = {
            "schema_version": 1,
            "status": "ok",
            "count": len(records),
            "wishes": records,
        }
        if args.json:
            print(json.dumps(receipt, indent=2, sort_keys=True))
        elif not records:
            print("No durable Wishes yet. Start with: workshop wish \"what you wish existed\"")
        else:
            for item in records:
                print(
                    "%-38s %-12s %-14s %s"
                    % (
                        item["product_id"],
                        item["inventor_id"],
                        "%s/%s" % (item["job"], item["status"]),
                        item.get("updated_at") or "",
                    )
                )
        return 0
    selected_root, _ = _root_for_durable_wish(roots, args.product_id)
    receipt = _status_receipt(selected_root, args.product_id)
    if args.json:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    else:
        _print_status_receipt(receipt, root=selected_root)
    return 0


def _resume_assignment(root: Path, product_id: str) -> tuple[Any, Mapping[str, Any]]:
    located = _find_durable_wish(root, product_id)
    if located is None:  # ``allow_missing`` is false; keeps type narrowing explicit.
        raise WorkshopError("saved Wish disappeared while preparing resume")
    card = located["card"]
    handoff = _read_saved_handoff(
        _assignment_file(card.root, product_id), card.inventor_id
    )
    if handoff.wish.product_id != product_id:
        raise WorkshopError("saved Manager assignment belongs to another Wish")
    handoff.require_exact_inventor_identity()
    handoff.assert_inventor_current(card)
    if located["product"] is not None:
        metadata = located["product"].get("metadata")
        if (
            not isinstance(metadata, Mapping)
            or metadata.get("wish") != handoff.wish.to_dict()
        ):
            raise WorkshopError(
                "saved Manager assignment differs from durable Wish state"
            )
    taste = load_taste(card.root)
    def assert_current() -> None:
        handoff.assert_inventor_current(card)

    assignment = SimpleNamespace(
        wish=handoff.wish,
        inventor_id=handoff.inventor_id,
        playtest_rounds=handoff.playtest_rounds,
        assignment_sha256=handoff.assignment_sha256,
        entrypoint=tuple(handoff.entrypoint),
        assert_current=assert_current,
        decision=SimpleNamespace(
            decision_sha256=handoff.decision_sha256,
            selected=SimpleNamespace(card=card, taste=taste),
        ),
    )
    return assignment, located


def _is_site_wait(result: Mapping[str, Any]) -> bool:
    needs = result.get("needs")
    return (
        result.get("status") == "waiting"
        and result.get("job") == "instructions"
        and isinstance(needs, list)
        and any(
            isinstance(need, Mapping)
            and need.get("capability") in ("site-page", "site-reconciliation")
            for need in needs
        )
    )


def _factory_authentication_wait(
    assignment: Any,
    root: Path,
    prior: Mapping[str, Any],
    *,
    publish: bool,
) -> Mapping[str, Any]:
    return {
        **dict(prior),
        "product_id": assignment.wish.product_id,
        "status": "waiting",
        "job": "instructions",
        "playtest_rounds": assignment.playtest_rounds,
        "needs": [
            {
                "job": "instructions",
                "capability": "factory-authentication",
                "reason": "This Manager process has no Factory credential for the matched Inventor.",
                "instructions": (
                    "Set FACTORY_PASSWORD in the trusted Manager environment, then run: "
                    + _resume_command(
                        assignment.wish.product_id,
                        root,
                        draft=not publish,
                    )
                    + ". The value is never passed to Inventor code or printed."
                ),
            }
        ],
        "manager_assignment": ManagerAssignmentHandoff.from_assignment(
            assignment
        ).result_binding(),
    }


def _continue_instructions_as_manager(
    assignment: Any,
    result: Mapping[str, Any],
    root: Path,
    *,
    publish: bool,
) -> Mapping[str, Any]:
    if not _is_site_wait(result):
        return dict(result)
    if _factory_credential_environment(assignment.inventor_id) is None:
        return _factory_authentication_wait(
            assignment, root, result, publish=publish
        )
    return _resume_factory_instructions(assignment, result)


def _resume(args: argparse.Namespace) -> int:
    roots = _catalog_roots(args.root, include_retained=args.root is None)
    selected_root, _ = _root_for_durable_wish(roots, args.product_id)
    assignment, located = _resume_assignment(selected_root, args.product_id)
    status = _status_receipt(selected_root, args.product_id)
    needs = status.get("needs", [])
    available, kind, unavailable_reason = _resume_availability(
        located, status.get("page")
    )
    result: Mapping[str, Any]
    if not available:
        result = {
            "product_id": args.product_id,
            "status": status["status"],
            "job": status["job"],
            "needs": needs,
            "resume": "not-available",
            "reason": unavailable_reason,
        }
    elif kind == "factory-page":
        page = status.get("page")
        if not isinstance(page, Mapping):  # availability already proved this
            raise WorkshopError("resumable Factory page state disappeared")
        result = {
            "product_id": args.product_id,
            "status": status["status"],
            "job": status["job"],
            "artifact_sha256": status.get("artifact_sha256"),
            "page_url": page.get("page_url"),
            "needs": needs,
        }
    elif kind == "instructions" and _is_site_wait(
        {
            "status": status.get("status"),
            "job": status.get("job"),
            "needs": needs,
        }
    ):
        waiting = {
            "status": "waiting",
            "job": "instructions",
            "needs": needs,
            "manager_assignment": ManagerAssignmentHandoff.from_assignment(
                assignment
            ).result_binding(),
        }
        result = _continue_instructions_as_manager(
            assignment,
            waiting,
            selected_root,
            publish=args.publish,
        )
    elif kind == "assigned":
        result = _run_inventor(assignment, continuing=True)
        result = _continue_instructions_as_manager(
            assignment,
            result,
            selected_root,
            publish=args.publish,
        )
    elif kind == "wish":
        result = _resume_inventor(assignment)
        result = _continue_instructions_as_manager(
            assignment,
            result,
            selected_root,
            publish=args.publish,
        )
    else:
        result = _resume_inventor(assignment)
        result = _continue_instructions_as_manager(
            assignment,
            result,
            selected_root,
            publish=args.publish,
        )
    if args.publish and isinstance(result.get("page_url"), str):
        result = {
            **result,
            "publication": _publish_inventor_draft(assignment, result),
        }
    receipt = {
        "schema_version": 1,
        "status": result.get("status"),
        "wish": assignment.wish.to_dict(),
        "match": {
            "inventor_id": assignment.inventor_id,
            "name": assignment.decision.selected.card.name,
            "explanation": "Resuming the exact saved Manager assignment.",
        },
        "result": result,
    }
    if args.json:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    else:
        _print_wish_receipt(receipt, root=selected_root)
        if result.get("resume") == "not-available":
            print("Resume: unavailable — %s" % result["reason"])
    return 1 if result.get("resume") == "not-available" else 0


def _doctor(args: argparse.Namespace) -> int:
    root = _catalog_roots(args.root)[0]
    checks = []
    try:
        catalog = discover_inventor_catalog(root)
    except (WorkshopError, OSError, ValueError) as exc:
        checks.append(
            {
                "name": "inventor-catalog",
                "status": "needs-attention",
                "detail": str(exc),
                "next": _shell_command(
                    "workshop", "doctor", "--root", root
                ),
            }
        )
    else:
        checks.append(
            {
                "name": "inventor-catalog",
                "status": "ready",
                "detail": "%d discoverable Inventor(s)" % len(catalog.cards),
            }
        )

    binary = os.environ.get("WORKSHOP_CODEX_BIN") or shutil.which("codex")
    if not binary:
        checks.append(
            {
                "name": "codex",
                "status": "needs-attention",
                "detail": "Codex CLI is not installed or on PATH.",
                "next": "Install Codex CLI and sign in with 'codex login'.",
            }
        )
    else:
        try:
            completed = subprocess.run(
                [binary, "login", "status"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
                env=codex_subprocess_environment(),
            )
        except (OSError, subprocess.SubprocessError):
            completed = None
        if completed is None:
            checks.append(
                {
                    "name": "codex",
                    "status": "needs-attention",
                    "detail": "The configured Codex CLI command could not run.",
                    "next": (
                        "Check WORKSHOP_CODEX_BIN or install Codex CLI, then run "
                        "'codex login status'."
                    ),
                }
            )
        elif completed.returncode != 0:
            checks.append(
                {
                    "name": "codex",
                    "status": "needs-attention",
                    "detail": "Codex CLI is installed but not signed in.",
                    "next": "Run 'codex login'; credentials stay in Codex, not the Workshop repo.",
                }
            )
        else:
            checks.append(
                {
                    "name": "codex",
                    "status": "ready",
                    "detail": "Codex CLI is installed and signed in.",
                }
            )

    cad_ready = importlib.util.find_spec("build123d") is not None
    checks.append(
        {
            "name": "cad-runtime",
            "status": "ready" if cad_ready else "needs-attention",
            "detail": (
                "Shared parametric CAD runtime is installed."
                if cad_ready
                else "Shared parametric CAD runtime is not installed."
            ),
            **(
                {}
                if cad_ready
                else {"next": "Install the Workshop with its locked runtime dependencies."}
            ),
        }
    )
    try:
        from .agent_playtest import PRUSASLICER_VERSION, PrusaSlicerPrintCheck

        slicer = PrusaSlicerPrintCheck.from_environment()
        if slicer is not None:
            probe = subprocess.run(
                [slicer.binary, "--help"],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
                env=minimal_tool_environment(),
            )
            version = re.search(
                r"(?m)^PrusaSlicer(?:-|\s+(?:version\s+)?)"
                r"([0-9]+(?:\.[0-9]+){2})(?:\s|$)",
                "%s\n%s" % (probe.stdout, probe.stderr),
            )
            if (
                probe.returncode != 0
                or version is None
                or version.group(1) != PRUSASLICER_VERSION
            ):
                slicer = None
    except (
        WaitingFor,
        WorkshopError,
        OSError,
        ValueError,
        subprocess.SubprocessError,
    ):
        slicer = None
    checks.append(
        {
            "name": "printability",
            "status": "ready" if slicer is not None else "needs-attention",
            "detail": (
                "Pinned PrusaSlicer is available."
                if slicer is not None
                else "Pinned PrusaSlicer is not available for exact printability evidence."
            ),
            **(
                {}
                if slicer is not None
                else {
                    "next": "Install PrusaSlicer 2.9.6 in a standard location or set WORKSHOP_PRUSASLICER_BIN."
                }
            ),
        }
    )
    factory_ready = bool(os.environ.get("FACTORY_PASSWORD"))
    checks.append(
        {
            "name": "factory-page",
            "status": "ready" if factory_ready else "needs-attention",
            "detail": (
                "A Factory credential is supplied to this Manager; it is verified only during the exact handoff."
                if factory_ready
                else "FACTORY_PASSWORD is not configured; a verified page cannot go live."
            ),
            **(
                {}
                if factory_ready
                else {
                    "next": "Set FACTORY_PASSWORD only in the trusted Manager environment; never commit it."
                }
            ),
        }
    )
    receipt = {
        "schema_version": 1,
        "status": (
            "ready"
            if all(item["status"] == "ready" for item in checks)
            else "needs-attention"
        ),
        "root": str(root),
        "checks": checks,
    }
    if args.json:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    else:
        for item in checks:
            marker = "ready" if item["status"] == "ready" else "needs attention"
            print("%-18s %s — %s" % (item["name"], marker, item["detail"]))
            if item.get("next"):
                print("  Next: %s" % item["next"])
        print("Workshop: %s" % receipt["status"])
    return 0 if receipt["status"] == "ready" else 1


def _wish(args: argparse.Namespace) -> int:
    root = _catalog_roots(args.root)[0]
    objective = " ".join(args.objective)
    wish = Wish.create(
        generate_wish_id(),
        objective,
        context={"source": "workshop-cli"},
    )
    progress = sys.stderr if args.json else sys.stdout
    print("Wish: %s" % wish.product_id, file=progress, flush=True)
    print(
        "Page: will be public after exact verification (--draft keeps it private)."
        if args.publish
        else "Page: will remain a private authenticated draft.",
        file=progress,
        flush=True,
    )
    print("Matching your Wish with an Inventor...", file=progress, flush=True)
    semantic = CodexSemanticManager()
    manager = WorkshopManager(
        root=root,
        retriever=semantic.retrieve,
        judge=semantic.judge,
        judge_identity=semantic.judge_identity,
        judge_version=semantic.judge_version,
        judge_config_sha256=semantic.judge_config_sha256,
    )
    try:
        assignment = manager.assign(
            wish, playtest_rounds=DEFAULT_WISH_PLAYTEST_ROUNDS
        )
    except WaitingFor as waiting:
        receipt = {
            **_waiting_receipt(wish, waiting),
            "next_command": _wish_command(
                wish.objective, root, draft=not args.publish
            ),
        }
        showed_match = False
    else:
        _save_manager_assignment(assignment)
        print(
            "Matched with %s." % assignment.decision.selected.card.name,
            file=progress,
            flush=True,
        )
        print(
            "Track: %s" % _status_command(wish.product_id, root),
            file=progress,
            flush=True,
        )
        print(
            "Inventing, making, and playtesting (up to 60 minutes). "
            "Use Track in another terminal for durable status.",
            file=progress,
            flush=True,
        )
        result = _run_inventor(assignment)
        result = _resume_factory_instructions(assignment, result)
        if args.publish:
            result = {
                **result,
                "publication": _publish_inventor_draft(assignment, result),
            }
        decision = assignment.decision
        receipt = {
            "schema_version": 1,
            "status": result.get("status", "started"),
            "wish": wish.to_dict(),
            "match": {
                "inventor_id": assignment.inventor_id,
                "name": decision.selected.card.name,
                "score": decision.fit.score,
                "explanation": decision.fit.explanation,
                "decision_sha256": decision.decision_sha256,
            },
            "assignment_sha256": assignment.assignment_sha256,
            "result": result,
        }
        showed_match = True
    if args.json:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    else:
        _print_wish_receipt(
            receipt,
            root=root,
            show_wish=False,
            show_match=not showed_match,
        )
    return (
        1
        if getattr(args, "strict", False) and receipt.get("status") == "waiting"
        else 0
    )


def _registry(args: argparse.Namespace) -> int:
    if args.root is not None:
        root = Path(args.root).resolve()
    else:
        root = _source_workshop_root() or packaged_inventor_catalog_root()
        if root is None:
            root = Path.cwd().resolve()
    manifests = discover_inventors(root)
    problems = validate_entrypoints(manifests) if args.check_entrypoints else []
    records = []
    for manifest in manifests:
        header = load_taste_header(manifest.path.parent)
        records.append(
            {
                "id": manifest.inventor_id,
                "status": manifest.status,
                "name": header.name,
                "description": header.description,
            }
        )
    if args.json:
        print(json.dumps(records, indent=2, sort_keys=True))
    else:
        for item in records:
            print(
                "%-12s %-18s %-20s %s"
                % (item["id"], item["status"], item["name"], item["description"])
            )
        print("%d inventor manifests valid" % len(manifests))
    for problem in problems:
        print("error: %s" % problem, file=sys.stderr)
    return 1 if problems else 0


def _manifest(args: argparse.Namespace) -> int:
    manifest = seal_artifact(args.source, extra_excludes=args.exclude)
    if args.output:
        manifest.write(args.output)
    print(json.dumps(manifest.to_dict(), indent=2, sort_keys=True))
    return 0


def _pack(args: argparse.Namespace) -> int:
    packed = pack_artifact(
        args.source,
        args.output,
        extra_excludes=args.exclude,
        maximum_bytes=args.maximum_bytes,
    )
    print(
        json.dumps(
            {
                "artifact_sha256": packed.artifact_sha256,
                "bytes": packed.bytes,
                "entries": packed.entries,
                "pack_sha256": packed.pack_sha256,
                "path": str(packed.path),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _plan_pack(args: argparse.Namespace) -> int:
    plan = plan_pack(
        args.source,
        extra_excludes=args.exclude,
        maximum_bytes=args.maximum_bytes,
        largest=args.largest,
    )
    print(json.dumps(plan.to_dict(), indent=2, sort_keys=True))
    return 0 if plan.fits else 1


def _init_state(args: argparse.Namespace) -> int:
    Clockwork(args.database)
    print(str(args.database))
    return 0


def _audit_state(args: argparse.Namespace) -> int:
    if not args.database.is_file():
        raise FileNotFoundError("state database does not exist: %s" % args.database)
    store = Clockwork(args.database)
    valid = store.verify_event_chain(args.product_id)
    print("valid" if valid else "INVALID")
    return 0 if valid else 1


def _new_inventor(args: argparse.Namespace) -> int:
    destination = scaffold_inventor(
        inventor_collection(args.root),
        args.inventor_id,
        args.name,
        args.niche,
        lane=args.lane,
        level=args.level,
        template=args.template,
    )
    print(str(destination))
    return 0


def _default_inventor_name(inventor_id: str) -> str:
    return " ".join(part.capitalize() for part in inventor_id.split("-"))


def _create_inventor(args: argparse.Namespace) -> int:
    collection = prepare_inventor_collection(args.root)
    if args.taste is None and not args.inventor_id:
        raise WorkshopError(
            "inventor_id is required unless --taste supplies a TASTE.md name"
        )
    if args.taste is None and not args.description:
        raise WorkshopError("--description is required unless --taste is supplied")
    inventor_id = args.inventor_id or _inventor_id_from_taste(args.taste)
    name = (
        args.name
        if args.taste is not None
        else args.name or _default_inventor_name(inventor_id)
    )
    destination = create_inventor(
        collection,
        inventor_id,
        name,
        args.description,
        lane=args.lane,
        level=args.level,
        taste_path=args.taste,
        run_checks=True,
    )
    catalog = discover_inventor_catalog(collection)
    card = catalog.card(inventor_id)
    taste = load_taste(destination)
    receipt = {
        "schema_version": 1,
        "status": card.status,
        "id": inventor_id,
        "name": card.name,
        "description": card.description,
        "lane": args.lane,
        "level": args.level,
        "path": str(destination),
        "taste_sha256": taste.sha256,
        "manifest_sha256": card.manifest_sha256,
        "catalog_sha256": catalog.catalog_sha256,
        "catalog_size": len(catalog.cards),
        "validation": {"layout": "passed", "checks": "passed"},
    }
    if args.json:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    else:
        try:
            visible = destination.relative_to(Path.cwd())
        except ValueError:
            visible = destination
        print("%s joined the Workshop (experimental)." % card.name)
        print("Taste: %s" % (visible / "TASTE.md"))
        print("Checks: passed")
        print(
            "Start: %s"
            % _shell_command(
                "workshop",
                "wish",
                "I wish for a toy only this Inventor would make",
                "--root",
                Path(args.root).resolve(),
            )
        )
    return 0


def _check_inventor(args: argparse.Namespace) -> int:
    manifests = manifests_for_target(args.target)
    problems = check_target(args.target, run=args.run)
    for problem in problems:
        print("error: %s" % problem, file=sys.stderr)
    if not problems:
        action = "checks passed" if args.run else "layout valid"
        print("%d inventor(s): %s" % (len(manifests), action))
    return 1 if problems else 0


def _skills(args: argparse.Namespace) -> int:
    root = resolve_skills_root(args.root)
    if args.action == "path":
        print(str(root))
        return 0
    skills = discover_skills(root)
    if args.json:
        print(
            json.dumps(
                [skill.to_dict() for skill in skills],
                indent=2,
                sort_keys=True,
            )
        )
    else:
        for skill in skills:
            print("%-20s %s" % (skill.name, skill.sha256))
    return 0


def _schemas(args: argparse.Namespace) -> int:
    root = resolve_schemas_root(args.root)
    if args.action == "path":
        print(str(root))
        return 0
    for path in discover_schemas(root):
        print(path.name)
    return 0


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(
        prog="workshop",
        description=(
            "Make one Wish and let the Autonomous Workshop match an Inventor, "
            "invent the toy, make it, Playtest it, and publish its verified Factory page."
        ),
        epilog=(
            "Start here:\n"
            "  workshop doctor\n"
            "  workshop wish \"a wind-up moon that waddles across my desk\"\n"
            "  workshop create inventor --taste ./TASTE.md --lane moving-machines"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subcommands = command.add_subparsers(
        dest="command", required=True, metavar="COMMAND"
    )

    wish = subcommands.add_parser(
        "wish",
        help="wish for a toy; matching and a verified public page are automatic",
        description=(
            "Say what you wish existed. The Manager reads Inventor Tastes, chooses "
            "one exact match, and starts the shared Workshop. The run includes up to "
            "four AI Playtest-to-Make improvement passes. A verified Factory page goes public by "
            "default; this never claims the physical toy was printed or delivered."
        ),
        epilog=(
            "Prerequisites: a discoverable Inventor catalog, an installed and signed-in "
            "Codex CLI, the shared CAD/printability runtime, and FACTORY_PASSWORD for a "
            "live page. Run 'workshop doctor' first. A truthful waiting result exits 0; "
            "use --strict when automation should exit 1 on a wait."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    wish.add_argument(
        "objective",
        nargs="+",
        metavar="WISH",
        help="what you wish existed, in your own words (quotes are optional)",
    )
    wish.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Workshop checkout or inventor collection (default: auto-detected)",
    )
    wish.add_argument(
        "--json",
        action="store_true",
        help="emit one stable JSON receipt on stdout; progress goes to stderr",
    )
    wish.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 instead of 0 when the Workshop truthfully waits for a capability",
    )
    publication = wish.add_mutually_exclusive_group()
    publication.add_argument(
        "--publish",
        dest="publish",
        action="store_true",
        help=(
            "make the exact authenticated Instructions page public (default; "
            "kept for explicit scripts)"
        ),
    )
    publication.add_argument(
        "--draft",
        dest="publish",
        action="store_false",
        help="stop after the exact authenticated private draft; do not make it public",
    )
    wish.set_defaults(handler=_wish, publish=True)

    status = subcommands.add_parser(
        "status",
        help="inspect the durable status of one Wish",
        description=(
            "Find a Wish in the Inventors' durable event stores and verify its event "
            "chain. This command does not change Wish records and never calls a model "
            "or Factory."
        ),
    )
    status.add_argument(
        "product_id",
        nargs="?",
        help="Wish id printed by 'workshop wish' (omit to list durable Wishes)",
    )
    status.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Workshop checkout or inventor collection (default: auto-detected, including retained installed runs)",
    )
    status.add_argument("--json", action="store_true", help="emit one JSON status receipt")
    status.set_defaults(handler=_status)

    resume = subcommands.add_parser(
        "resume",
        help="continue an exact saved Workshop stage",
        description=(
            "Continue the exact Manager assignment saved by 'workshop wish'. Invent "
            "restarts from the Wish boundary; Make reuses the accepted Invented record; "
            "Playtest reuses the exact Made checkpoint; Instructions reuses its approved "
            "Make and Playtest checkpoint. Completed stages are never rerun. Legacy runs "
            "without the required checkpoint fail with a concrete next action."
        ),
    )
    resume.add_argument("product_id", help="saved Wish id")
    resume.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Workshop checkout or inventor collection (default: find the exact retained run)",
    )
    resume.add_argument("--json", action="store_true", help="emit one JSON receipt")
    resume_publication = resume.add_mutually_exclusive_group()
    resume_publication.add_argument(
        "--publish",
        dest="publish",
        action="store_true",
        help="make the verified page public (default)",
    )
    resume_publication.add_argument(
        "--draft",
        dest="publish",
        action="store_false",
        help="create/reconcile the authenticated draft without making it public",
    )
    resume.set_defaults(handler=_resume, publish=True)

    doctor = subcommands.add_parser(
        "doctor",
        help="check prerequisites without exposing credential values",
        description=(
            "Check the Inventor catalog, Codex sign-in, shared CAD/printability "
            "runtime, and whether Factory authentication is present. No model, "
            "product import, publication, or delivery action is performed."
        ),
    )
    doctor.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Workshop checkout or inventor collection (default: auto-detected)",
    )
    doctor.add_argument("--json", action="store_true", help="emit one JSON preflight receipt")
    doctor.set_defaults(handler=_doctor)

    registry = subcommands.add_parser(
        "inventors", aliases=("registry",), help="list and validate inventors"
    )
    registry.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Workshop checkout or inventor collection (default: auto-detected)",
    )
    registry.add_argument("--json", action="store_true", help="emit the catalog as JSON")
    registry.add_argument(
        "--check-entrypoints",
        action="store_true",
        help="also verify every declared profile command is executable",
    )
    registry.set_defaults(handler=_registry)

    artifact = subcommands.add_parser(
        "seal", aliases=("artifact",), help="seal a product artifact tree"
    )
    artifact.add_argument("source", type=Path, help="artifact directory to seal")
    artifact.add_argument("--output", type=Path, help="also write the manifest to this path")
    artifact.add_argument(
        "--exclude", action="append", default=[], help="exclude one relative path (repeatable)"
    )
    artifact.set_defaults(handler=_manifest)

    pack = subcommands.add_parser("pack", help="build a reproducible immutable Pack")
    pack.add_argument("source", type=Path, help="sealed artifact directory")
    pack.add_argument("output", type=Path, help="output Pack path")
    pack.add_argument(
        "--exclude", action="append", default=[], help="exclude one relative path (repeatable)"
    )
    pack.add_argument(
        "--maximum-bytes", type=int, default=MAX_PACK_BYTES, help="hard Pack byte limit"
    )
    pack.set_defaults(handler=_pack)

    plan = subcommands.add_parser(
        "plan-pack", help="preview exact Pack size and largest eligible files"
    )
    plan.add_argument("source", type=Path, help="artifact directory to inspect")
    plan.add_argument(
        "--exclude", action="append", default=[], help="exclude one relative path (repeatable)"
    )
    plan.add_argument(
        "--maximum-bytes", type=int, default=MAX_PACK_BYTES, help="planned Pack byte limit"
    )
    plan.add_argument("--largest", type=int, default=5, help="number of largest files to show")
    plan.set_defaults(handler=_plan_pack)

    clockwork = subcommands.add_parser(
        "clockwork", help="initialize or audit durable Workshop state"
    )
    clockwork_commands = clockwork.add_subparsers(dest="clockwork_action", required=True)
    state = clockwork_commands.add_parser("init", help="initialize the durable database")
    state.add_argument("database", type=Path, help="SQLite state database path")
    state.set_defaults(handler=_init_state)
    audit = clockwork_commands.add_parser("audit", help="verify a product event hash chain")
    audit.add_argument("database", type=Path, help="existing SQLite state database")
    audit.add_argument("product_id", help="product whose event chain to verify")
    audit.set_defaults(handler=_audit_state)

    # Compatibility commands for 0.2 automation.
    legacy_state = subcommands.add_parser("init-state")
    legacy_state.add_argument("database", type=Path)
    legacy_state.set_defaults(handler=_init_state)
    legacy_audit = subcommands.add_parser("audit-state")
    legacy_audit.add_argument("database", type=Path)
    legacy_audit.add_argument("product_id")
    legacy_audit.set_defaults(handler=_audit_state)

    create = subcommands.add_parser(
        "create", help="create a new inventor"
    )
    create_commands = create.add_subparsers(
        dest="create_kind", required=True, metavar="THING"
    )
    creator = create_commands.add_parser(
        "inventor",
        help="create a discoverable inventor powered by the Workshop",
        description=(
            "Bring an existing TASTE.md, or provide an id, description, and lane "
            "to generate a starter Taste. The Taste-only path inherits every shared "
            "Workshop engine component."
        ),
        epilog=(
            "Fastest path:\n"
            "  workshop create inventor --taste ./TASTE.md --lane moving-machines\n\n"
            "Starter path:\n"
            "  workshop create inventor mira --description \"kinetic desk toys, not games\" "
            "--lane moving-machines"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    creator.add_argument(
        "inventor_id",
        nargs="?",
        help="safe catalog id; omitted with --taste to derive it from the Taste name",
    )
    creator.add_argument(
        "--taste",
        type=Path,
        help="existing TASTE.md to preserve byte-for-byte and validate",
    )
    creator.add_argument(
        "--name",
        help="display name (starter path only; --taste already owns its name)",
    )
    creator.add_argument(
        "--description",
        help=(
            "Taste selection boundary: what should choose this inventor and "
            "the closest work that should not (required without --taste)"
        ),
    )
    creator.add_argument(
        "--lane",
        choices=PLAYTHING_LANES,
        required=True,
        help="kind of plaything this inventor makes",
    )
    creator.add_argument(
        "--level",
        choices=CUSTOMIZATION_LEVELS,
        default="taste-only",
        help="creative code owned by the inventor (default: taste-only)",
    )
    creator.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="workspace where inventors/ will be created (default: current directory)",
    )
    creator.add_argument(
        "--json",
        action="store_true",
        help="emit a stable creation receipt for an agent",
    )
    creator.set_defaults(handler=_create_inventor)

    # Read-only command compatibility through 0.x. It is intentionally absent
    # from help; new humans and agents should learn only ``create inventor``.
    new = subcommands.add_parser("new")
    new.add_argument("inventor_id")
    new.add_argument("--name", required=True)
    new.add_argument("--niche", required=True)
    new.add_argument(
        "--lane",
        choices=PLAYTHING_LANES,
        help="kind of plaything this inventor makes",
    )
    new.add_argument(
        "--level",
        choices=CUSTOMIZATION_LEVELS,
        default="taste-only",
        help="how much Make and Playtest code this inventor owns (default: taste-only)",
    )
    new.add_argument(
        "--template",
        choices=("board-game", "physical-product", "custom"),
        help=argparse.SUPPRESS,
    )
    new.add_argument("--root", type=Path, default=Path.cwd())
    new.set_defaults(handler=_new_inventor)

    check = subcommands.add_parser(
        "check", help="validate an inventor contribution"
    )
    check.add_argument(
        "target",
        type=Path,
        nargs="?",
        default=Path.cwd(),
        help="inventor folder, manifest, inventors/ collection, or repository",
    )
    check.add_argument(
        "--run",
        action="store_true",
        help="also execute the manifest's declared checks without a shell",
    )
    check.set_defaults(handler=_check_inventor)

    skills = subcommands.add_parser(
        "skills", help="discover the workshop's versioned agent skills"
    )
    skills.add_argument("action", choices=("list", "path"), nargs="?", default="list")
    skills.add_argument(
        "--root",
        type=Path,
        help="absolute skills root (auto-detected in a source checkout)",
    )
    skills.add_argument("--json", action="store_true")
    skills.set_defaults(handler=_skills)

    schemas = subcommands.add_parser(
        "schemas", help="discover the Workshop's installed JSON contracts"
    )
    schemas.add_argument("action", choices=("list", "path"), nargs="?", default="list")
    schemas.add_argument("--root", type=Path)
    schemas.set_defaults(handler=_schemas)
    return command


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        args = parser().parse_args(argv)
        return int(args.handler(args))
    except (WorkshopError, OSError, ValueError, KeyError) as exc:
        print("workshop: %s" % exc, file=sys.stderr)
        return 2

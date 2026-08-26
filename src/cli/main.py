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
import sqlite3
import stat
import subprocess
import sys
import unicodedata
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Mapping, Optional, Sequence

from cli.native_run import (
    native_run_exists,
    native_run_status,
    resume_native_run,
    start_native_run,
)
from workshop.runtime.package_data import (
    existing_bundled_catalog_roots,
    materialize_bundled_inventors,
    packaged_inventor_catalog_root,
    packaged_inventors_root,
)
from workshop.artifacts.core import MAX_PACK_BYTES
from workshop.workflow import Clockwork
from workshop.contributors import (
    CUSTOMIZATION_LEVELS,
    check_target,
    manifests_for_target,
)
from workshop.errors import AmbiguousEffectError, EffectError, WorkshopError
from workshop.integrations.factory_agent import (
    FactoryAgentReleaseWriter,
    FactoryAgentSession,
    FactoryPublicTransition,
    factory_credentials_from_environment,
)
from workshop.match import (
    MAX_HANDOFF_BYTES,
    ManagerAssignmentHandoff,
    validate_manager_assignment_result,
)
from workshop.deliver.contracts import Delivered
from workshop.invent.contracts import Invented
from workshop.outcomes import Need, WaitingFor
from workshop.workflow import WorkshopRun
from workshop.runtime.execution import codex_subprocess_environment, minimal_tool_environment
from workshop.release.agent import (
    DEFAULT_RELEASE_CREATOR_MODEL,
    DEFAULT_RELEASE_REWARD_MODEL,
    RewardedRelease,
)
from workshop.wish import Wish, generate_wish_id
from workshop.contributors import (
    discover_inventors,
    inventor_collection,
    load_manifest,
    validate_entrypoints,
)
from workshop.runtime import Receipt
from workshop.artifacts.pack import pack_artifact, plan_pack, seal_artifact
from workshop.match import CodexSemanticManager, WorkshopManager, discover_inventor_catalog
from workshop.contributors import (
    create_inventor,
    prepare_inventor_collection,
    scaffold_inventor,
)
from workshop.artifacts.schema_registry import discover_schemas, resolve_schemas_root
from workshop.make.skill_registry import discover_skills, resolve_skills_root
from workshop.runtime import InventorStore
from workshop.integrations.shop import ShopDoor
from workshop.contributors import load_taste, load_taste_header
from workshop.product import PLAYTHING_LANES, ToyBlueprint
from workshop.workflow import Workshop, WorkshopTools


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
        "WORKSHOP_RELEASE_MODEL",
        "WORKSHOP_RELEASE_REWARD_MODEL",
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
        if requested.is_symlink() or not requested.is_file():
            raise WorkshopError("Workshop status database must be a regular file")
        self.database = requested.resolve(strict=True)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database.as_uri() + "?mode=ro",
            uri=True,
            timeout=5,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
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
    stays in the Workshop Manager process for the later Release handoff.
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
        "release_sha256",
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
        release_sha256=value["release_sha256"],
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
    release_sha256 = next(
        (
            event["payload"].get("release_sha256")
            for event in reversed(events)
            if isinstance(event.get("payload"), Mapping)
            and isinstance(event["payload"].get("release_sha256"), str)
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
            or delivery.release_sha256 != release_sha256
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
                "Manager-resumed Release lacks an exact durable Factory receipt"
            ) from exc
        if not (receipt.is_verified_draft or receipt.is_verified_public):
            raise WorkshopError(
                "Manager-resumed Release Factory receipt is not verified"
            )
        if receipt.details.get("release_sha256") != release_sha256:
            raise WorkshopError(
                "Manager-resumed Factory receipt identifies a different Release"
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
        release_sha256=release_sha256,
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
    return {**trusted, "manager_assignment": child_result["manager_assignment"]}


class _ResumeOnlyStructuredRunner:
    """Identity-only runner; sealed Release resume must never invoke AI."""

    def __init__(self, model: str, reasoning_effort: str) -> None:
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.cli_version = "resume-only.1.0.0"

    def invoke(self, **kwargs):  # pragma: no cover - a resume invariant
        del kwargs
        raise WorkshopError("sealed Release resume attempted to rerun AI")


def _resume_factory_release(
    assignment: Any,
    result: Mapping[str, Any],
    *,
    environment: Optional[Mapping[str, str]] = None,
    store_factory: Any = InventorStore,
    writer_factory: Any = FactoryAgentReleaseWriter,
    workshop_factory: Any = Workshop,
    state_validator: Any = _validate_child_workshop_state,
) -> Mapping[str, Any]:
    """Resume only a sealed Factory handoff outside inventor-owned code.

    The selected profile runs without Factory credentials and therefore stops
    truthfully after scoring and sealing its manual/page facts. If the Manager
    owns a credential, this function gives it only to the shared site adapter,
    reconstructs the exact checkpoint, and resumes Release without
    executing the profile or any custom Invent/Make/Playtest hook.
    """

    if not isinstance(result, Mapping):
        raise WorkshopError("Workshop child result must be an object")
    needs = result.get("needs")
    is_factory_wait = (
        result.get("status") == "waiting"
        and result.get("job") == "release"
        and isinstance(needs, list)
        and any(
            isinstance(need, Mapping)
            and need.get("job") == "release"
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
    release_job = RewardedRelease(
        writer,
        creator=_ResumeOnlyStructuredRunner(
            DEFAULT_RELEASE_CREATOR_MODEL, "medium"
        ),
        evaluator=_ResumeOnlyStructuredRunner(
            DEFAULT_RELEASE_REWARD_MODEL, "low"
        ),
    )

    def unavailable(context):  # pragma: no cover - resume must not call these
        del context
        raise WorkshopError("Release resume attempted an earlier Workshop stage")

    workshop_kwargs = {
        "inventor_id": inventor_id,
        "tools": WorkshopTools(
            invent=unavailable,
            make=unavailable,
            playtest=unavailable,
            release=release_job,
        ),
        "runtime_root": runtime_root,
    }
    # These inert seams reconstruct only the checkpoint-bound contribution
    # level. They are never called by resume_release and never import or
    # execute the inventor's custom implementation.
    if level in ("custom-make", "custom-playtest"):
        workshop_kwargs["make"] = unavailable
    if level == "custom-playtest":
        workshop_kwargs["playtest"] = unavailable
    workshop = workshop_factory(card.root, lane, **workshop_kwargs)
    resumed = workshop.resume_release(assignment.wish).to_dict()
    handoff = ManagerAssignmentHandoff.from_assignment(assignment)
    if result.get("manager_assignment") != handoff.result_binding():
        raise WorkshopError(
            "Manager-resumed Release lost its exact assignment binding"
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
    runner: Any = subprocess.run,
    state_validator: Any = _validate_child_workshop_state,
) -> Mapping[str, Any]:
    handoff = ManagerAssignmentHandoff.from_assignment(assignment)
    command = list(assignment.entrypoint)
    if command[0] in ("python", "python3"):
        command[0] = sys.executable
    command.extend(("run", "--assignment-stdin"))
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
        raise WorkshopError(
            "the selected Inventor did not finish within 60 minutes; its exact "
            "assignment is saved, but this stage cannot resume automatically. "
            "Inspect it with: %s. If that process stopped, start a new Wish with: %s"
            % (
                _status_command(assignment.wish.product_id, root),
                _wish_command(assignment.wish.objective, root),
            )
        ) from exc
    except (OSError, subprocess.SubprocessError) as exc:
        root = Path(assignment.decision.selected.card.root).parent
        raise WorkshopError(
            "the selected Inventor process could not run; its exact assignment is "
            "saved, but no work is running. Inspect it with: %s. Retry as a new "
            "Wish with: %s"
            % (
                _status_command(assignment.wish.product_id, root),
                _wish_command(assignment.wish.objective, root),
            )
        ) from exc
    if completed.returncode != 0:
        raise WorkshopError(
            "the selected Inventor stopped before returning a Workshop result"
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
    return state_validator(assignment, bound)


def _assignment_file(card_root: Path, product_id: str) -> Path:
    digest = hashlib.sha256(product_id.encode("utf-8")).hexdigest()
    return Path(card_root) / ".workshop" / _ASSIGNMENT_DIRECTORY / (digest + ".json")


def _read_saved_handoff(path: Path, inventor_id: str) -> ManagerAssignmentHandoff:
    """Read one bounded, non-symlink Manager handoff used only for resume."""

    try:
        expected = path.lstat()
    except FileNotFoundError:
        raise WorkshopError("this Wish has no saved Manager assignment")
    if path.is_symlink() or not stat.S_ISREG(expected.st_mode):
        raise WorkshopError("saved Manager assignment must be a regular file")
    if not 1 <= expected.st_size <= MAX_HANDOFF_BYTES:
        raise WorkshopError("saved Manager assignment is empty or too large")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(str(path), flags)
    except OSError as exc:
        raise WorkshopError("cannot safely read the saved Manager assignment") from exc
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or (
            opened.st_dev,
            opened.st_ino,
        ) != (expected.st_dev, expected.st_ino):
            raise WorkshopError("saved Manager assignment changed while opening")
        source = os.read(descriptor, MAX_HANDOFF_BYTES + 1)
        if len(source) > MAX_HANDOFF_BYTES or os.read(descriptor, 1):
            raise WorkshopError("saved Manager assignment is too large")
        after = os.fstat(descriptor)
        if (
            after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
            or (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            raise WorkshopError("saved Manager assignment changed while reading")
    finally:
        os.close(descriptor)
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
        return {
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
    status = payload.get("status", "working")
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
    intent = _ReadOnlyWorkshopStore(located["database"]).latest_publish_intent(
        product_id
    )
    raw_receipt = intent.get("receipt") if isinstance(intent, Mapping) else None
    page = None
    if raw_receipt is not None:
        release_sha256 = next(
            (
                event["payload"].get("release_sha256")
                for event in reversed(located["events"])
                if isinstance(event.get("payload"), Mapping)
                and isinstance(event["payload"].get("release_sha256"), str)
            ),
            None,
        )
        try:
            page = Receipt.from_dict(raw_receipt)
            page.assert_artifact(product.get("artifact_sha256"))
        except (TypeError, WorkshopError) as exc:
            raise WorkshopError(
                "saved Factory page receipt identifies different product bytes"
            ) from exc
        if (
            not isinstance(release_sha256, str)
            or page.details.get("release_sha256") != release_sha256
        ):
            raise WorkshopError(
                "saved Factory page receipt identifies a different Release"
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
            "release_sha256": draft.details.get("release_sha256"),
            "playtest_evidence_sha256": draft.details.get(
                "playtest_evidence_sha256"
            ),
            "page_url": draft.details.get("page_url"),
        }
        if any(not isinstance(value, str) or not value for value in proof.values()):
            raise WorkshopError(
                "authenticated Factory draft lacks exact Release, Playtest, or page proof"
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
    """Durably promote the exact authenticated Release draft, then prove it."""

    product_id = assignment.wish.product_id
    inventor_id = assignment.decision.selected.card.inventor_id
    page_url = result.get("page_url")
    artifact_sha256 = result.get("artifact_sha256")
    if not isinstance(page_url, str) or not page_url:
        return {
            "status": "waiting",
            "reason": "Release has not produced an authenticated Factory draft yet.",
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
                "the Factory draft URL differs from the Workshop Release receipt"
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
        if result.get("status") == "waiting" and result.get("job") == "release":
            print("Resume: %s" % _resume_command(wish["product_id"], root))
        elif result.get("status") == "waiting":
            print("Resume: unavailable for this stage; the saved command is status only.")
            print("Restart: %s" % _wish_command(wish["objective"], root))


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
    print("Event chain: %s" % receipt["event_chain"])
    if receipt.get("status") == "waiting" and receipt.get("job") == "release":
        print("Resume: %s" % _resume_command(receipt["product_id"], root))
    elif receipt.get("status") in ("assigned", "working", "waiting"):
        print("Resume: unavailable for this stage; status does not restart its worker.")
        objective = receipt.get("wish", {}).get("objective")
        if isinstance(objective, str) and objective:
            print(
                "If the original process stopped, restart as a new Wish: %s"
                % _wish_command(objective, root)
            )


def _print_native_status_receipt(receipt: Mapping[str, Any]) -> None:
    print("Wish: %s" % receipt["product_id"])
    print(
        "Status: %s at %s (revision %s, round %s/%s)"
        % (
            receipt["status"],
            str(receipt["stage"]).title(),
            receipt["revision"],
            receipt["round"],
            receipt["max_rounds"],
        )
    )
    session_status = receipt.get("session_status")
    if isinstance(session_status, str):
        print("Native session: %s" % session_status)
    print("Checkpoint: %s" % receipt["checkpoint_sha256"])


def _status(args: argparse.Namespace) -> int:
    if args.product_id is not None and native_run_exists(args.product_id):
        receipt = native_run_status(args.product_id)
        if args.json:
            print(json.dumps(receipt, indent=2, sort_keys=True))
        else:
            _print_native_status_receipt(receipt)
        return 0
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
    if located["product"] is None:
        raise WorkshopError(
            "the Inventor has not created durable state yet; wait a moment and check status again"
        )
    metadata = located["product"].get("metadata")
    if not isinstance(metadata, Mapping) or metadata.get("wish") != handoff.wish.to_dict():
        raise WorkshopError("saved Manager assignment differs from durable Wish state")
    taste = load_taste(card.root)
    assignment = SimpleNamespace(
        wish=handoff.wish,
        inventor_id=handoff.inventor_id,
        playtest_rounds=handoff.playtest_rounds,
        assignment_sha256=handoff.assignment_sha256,
        entrypoint=tuple(card.entrypoint),
        decision=SimpleNamespace(
            decision_sha256=handoff.decision_sha256,
            selected=SimpleNamespace(card=card, taste=taste),
        ),
    )
    return assignment, located


def _resume(args: argparse.Namespace) -> int:
    if native_run_exists(args.product_id):
        receipt = resume_native_run(
            args.product_id,
            publish_requested=args.publish,
        )
        if args.json:
            print(json.dumps(receipt, indent=2, sort_keys=True))
        else:
            _print_native_status_receipt(receipt)
            print(
                "Track: %s"
                % _shell_command("workshop", "status", args.product_id)
            )
        return 0
    roots = _catalog_roots(args.root, include_retained=args.root is None)
    selected_root, _ = _root_for_durable_wish(roots, args.product_id)
    assignment, located = _resume_assignment(selected_root, args.product_id)
    status = _status_receipt(selected_root, args.product_id)
    needs = status.get("needs", [])
    site_wait = (
        status.get("status") == "waiting"
        and status.get("job") == "release"
        and any(
            need.get("capability") in ("site-page", "site-reconciliation")
            for need in needs
        )
    )
    result: Mapping[str, Any]
    if site_wait:
        if _factory_credential_environment(assignment.inventor_id) is None:
            result = {
                "product_id": args.product_id,
                "status": "waiting",
                "job": "release",
                "needs": [
                    {
                        "job": "release",
                        "capability": "factory-authentication",
                        "reason": "This Manager process has no Factory credential for the matched Inventor.",
                        "instructions": (
                            "Set FACTORY_PASSWORD in the trusted Manager environment, then run: "
                            + _resume_command(
                                args.product_id,
                                selected_root,
                                draft=not args.publish,
                            )
                            + ". The value is never passed to Inventor code or printed."
                        ),
                    }
                ],
                "manager_assignment": ManagerAssignmentHandoff.from_assignment(
                    assignment
                ).result_binding(),
            }
        else:
            waiting = {
                "status": "waiting",
                "job": "release",
                "needs": needs,
                "manager_assignment": ManagerAssignmentHandoff.from_assignment(
                    assignment
                ).result_binding(),
            }
            result = _resume_factory_release(assignment, waiting)
    else:
        page = status.get("page")
        if not isinstance(page, Mapping) or page.get("status") != "draft":
            result = {
                "product_id": args.product_id,
                "status": status["status"],
                "job": status["job"],
                "needs": needs,
                "resume": "not-available",
                "reason": (
                    "Only an exact sealed Release handoff can currently resume safely; "
                    "the durable run was not changed."
                ),
            }
        else:
            result = {
                "product_id": args.product_id,
                "status": status["status"],
                "job": status["job"],
                "artifact_sha256": status.get("artifact_sha256"),
                "page_url": page.get("page_url"),
                "needs": needs,
            }
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
        from workshop.playtest.agent import PRUSASLICER_VERSION, PrusaSlicerPrintCheck

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
    objective = " ".join(args.objective)
    wish = Wish.create(
        generate_wish_id(),
        objective,
        context={"source": "workshop-cli"},
    )
    progress = sys.stderr if args.json else sys.stdout
    print("Wish: %s" % wish.product_id, file=progress, flush=True)
    print(
        "Page: remains a private draft unless a later host-authorized effect publishes it.",
        file=progress,
        flush=True,
    )
    print(
        "Starting one native Codex session before Match...",
        file=progress,
        flush=True,
    )
    receipt = start_native_run(wish, publish_requested=args.publish)
    if args.json:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    else:
        print(
            "Status: %s at %s."
            % (receipt["status"], str(receipt["stage"]).title())
        )
        print("Track: %s" % _shell_command("workshop", "status", wish.product_id))
        print("Resume: %s" % _shell_command("workshop", "resume", wish.product_id))
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
        help="persist one Wish and start its native coding-agent session",
        description=(
            "Say what you wish existed. Workshop persists the exact Wish in a private "
            "run workspace, then starts one native Codex session before Match. Codex "
            "does the cognitive work; host checkpoints and deterministic gates retain "
            "authority. Publication is never automatic."
        ),
        epilog=(
            "Prerequisite: an installed and signed-in Codex CLI. Factory credentials "
            "are not passed to the native session. A truthful waiting result exits 0; "
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
        help="legacy catalog override; native run state always lives under WORKSHOP_HOME",
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
            "record a future publication request; never gives the native session credentials"
        ),
    )
    publication.add_argument(
        "--draft",
        dest="publish",
        action="store_false",
        help="keep all output private (default)",
    )
    wish.set_defaults(handler=_wish, publish=False)

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
        help="resume the exact native session for a saved Wish",
        description=(
            "Resume the exact native coding-agent session bound to the private Wish "
            "workspace. Legacy Release-only runs remain readable during migration."
        ),
    )
    resume.add_argument("product_id", help="saved Wish id")
    resume.add_argument(
        "--root",
        type=Path,
        default=None,
        help="legacy catalog override; native run state is found under WORKSHOP_HOME",
    )
    resume.add_argument("--json", action="store_true", help="emit one JSON receipt")
    resume_publication = resume.add_mutually_exclusive_group()
    resume_publication.add_argument(
        "--publish",
        dest="publish",
        action="store_true",
        help="record a future publication request; does not expose credentials to Codex",
    )
    resume_publication.add_argument(
        "--draft",
        dest="publish",
        action="store_false",
        help="keep all output private (default)",
    )
    resume.set_defaults(handler=_resume, publish=False)

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

"""The customer and operator CLI for Autonomous Workshop."""

from __future__ import annotations

import argparse
import concurrent.futures
from contextlib import contextmanager, nullcontext
import hashlib
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
import threading
import time
import unicodedata
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Mapping, Optional, Sequence

from ._package_data import (
    existing_bundled_catalog_roots,
    materialize_bundled_inventors,
    packaged_inventor_catalog_root,
    packaged_inventors_root,
)
from .artifacts import MAX_PACK_BYTES
from .batch import (
    BatchPlan,
    BatchPlanItem,
    BatchPlanStore,
    load_or_create_batch_manager_identity,
    parse_batch_file,
)
from .clockwork import Clockwork
from .codex_runtime import ALLOWED_WORKSHOP_MODELS
from .contribution import check_target, manifests_for_target
from .deliver import DefaultDeliver
from .engine_provenance import EngineProvenanceManifest
from .errors import AmbiguousEffectError, EffectError, WorkshopError
from .factory_agent import (
    FactoryAgentCredentials,
    FactoryAgentInstructionsWriter,
    FactoryAgentSession,
    FactoryPublicTransition,
    factory_credentials_from_environment,
)
from .handoff import (
    MAX_HANDOFF_BYTES,
    ManagerAssignmentHandoff,
    PublicationPolicy,
    validate_manager_assignment_result,
)
from .instructions import sealed_instructions_manifest
from .jobs import (
    Delivered,
    Feedback,
    Invented,
    Need,
    WaitingFor,
    WorkshopRun,
    deliver_wish_sha256,
)
from .execution_env import codex_subprocess_environment, minimal_tool_environment
from .agent_instructions import (
    DEFAULT_INSTRUCTIONS_CREATOR_MODEL,
    DEFAULT_INSTRUCTIONS_REWARD_MODEL,
    RewardedInstructions,
)
from .make import Wish, generate_wish_id
from .match_attempt import MatchAttemptEvent, MatchAttemptStore
from .manifest import (
    discover_inventors,
    inventor_collection,
    load_manifest,
    validate_entrypoints,
)
from .models import Receipt, utc_now
from .pack import pack_artifact, plan_pack, seal_artifact
from .pending_wish import PendingWish, PendingWishStore
from .manager import (
    WorkshopManager,
    discover_inventor_catalog,
    register_workshop_engine,
)
from .manager_services import (
    ManagerServices,
    configured_manager_services,
)
from .semantic_manager import CodexSemanticManager, DEFAULT_MANAGER_MODEL
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
    world_personalization_from_made,
)
from .world_reference_vault import (
    LOCAL_STORAGE_SECURITY_BOUNDARY,
    SUPPORTED_WORLD_CONSENT_METHODS,
    SUPPORTED_WORLD_MEDIA_TYPES,
    SUPPORTED_WORLD_SUBJECT_KINDS,
    WorldReferenceScope,
    WorldReferenceVault,
)
from .world_service import (
    WorldInventInputs,
    WorldPlaytestEvidence,
    WorldProviderIdentity,
    prepare_world_invent_inputs,
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


def _configured_world_reference_service(assignment: Any):
    """Production injection seam; return ``(service, public_identity)``.

    The default deliberately has no credential discovery. Deployments install
    this Manager-side adapter without placing its object or authority in the
    Inventor environment. Tests may replace this function deterministically.
    """

    del assignment
    services = _selected_manager_services()
    if services is None or services.world_reference_service is None:
        return None
    binding = services.binding("world_reference")
    if binding is None:  # pragma: no cover - property and binding are atomic
        raise WorkshopError("Manager world reference binding is inconsistent")
    return services.world_reference_service, binding.identity.world_identity()


def _configured_world_playtest_evidence(
    assignment: Any, result: Mapping[str, Any]
) -> Optional[WorldPlaytestEvidence]:
    """Production Manager seam for already verified raw-free evidence.

    A deployment normally builds the value with
    ``prepare_world_playtest_evidence`` and an isolated service. The default
    cannot measure private references and therefore returns no evidence.
    """

    services = _selected_manager_services()
    if services is None or services.world_playtest_service is None:
        return None
    personalization = _durable_world_personalization(assignment, result)
    world_inputs = getattr(assignment, "world_inputs", None)
    if not isinstance(world_inputs, WorldInventInputs):
        raise WorkshopError(
            "Manager world Playtest service requires exact Invent inputs"
        )
    return services.prepare_world_evidence(
        assignment.wish,
        result.get("artifact_sha256"),
        personalization,
        world_inputs,
    )


def _selected_manager_services(
    source: Optional[Mapping[str, str]] = None,
) -> Optional[ManagerServices]:
    """Load one explicitly selected trusted Manager composition."""

    values = os.environ if source is None else source
    selected = values.get("WORKSHOP_MANAGER_SERVICES")
    if selected is None:
        return None
    if not isinstance(selected, str) or not selected:
        return configured_manager_services(values)
    return _cached_manager_services(selected)


@lru_cache(maxsize=8)
def _cached_manager_services(configuration_id: str) -> ManagerServices:
    return configured_manager_services(
        {"WORKSHOP_MANAGER_SERVICES": configuration_id}
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
        explicit = Path(requested)
        if explicit.is_symlink():
            raise WorkshopError("Workshop catalog root must not be a symlink")
        return (explicit.resolve(),)
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


def _factory_credentials_for(
    inventor_id: str,
    source: Optional[Mapping[str, str]] = None,
):
    """Resolve one opaque Factory secret inside the Manager process only.

    An explicit ``source`` is the backward-compatible test/operator seam. In a
    normal command, a selected Manager service broker is authoritative; only
    installations without that capability use the legacy shared password.
    """

    if source is not None:
        environment = _factory_credential_environment(inventor_id, source)
        return (
            None
            if environment is None
            else factory_credentials_from_environment(inventor_id, environment)
        )
    services = _selected_manager_services()
    if services is not None and services.binding("factory_credentials") is not None:
        return services.factory_credentials_for(inventor_id)
    environment = _factory_credential_environment(inventor_id, os.environ)
    return (
        None
        if environment is None
        else factory_credentials_from_environment(inventor_id, environment)
    )


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
    try:
        delivered = Delivered.from_dict(value)
    except WorkshopError as exc:
        raise WorkshopError("persisted Deliver result is malformed") from exc
    if delivered.to_dict() != dict(value):
        raise WorkshopError("persisted Deliver result identity is inconsistent")
    return delivered


def _validate_child_workshop_state(
    assignment: Any,
    child_result: Mapping[str, Any],
    *,
    allow_durable_factory_page: bool = False,
    allow_ambiguous_deliver: bool = False,
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
    metadata = product.get("metadata")
    allowed_metadata_shapes = (
        set(expected_metadata),
        set(expected_metadata) | {"engine_provenance"},
    )
    if (
        not isinstance(metadata, Mapping)
        or set(metadata) not in allowed_metadata_shapes
        or any(metadata.get(key) != value for key, value in expected_metadata.items())
    ):
        raise WorkshopError(
            "durable Workshop state differs from the exact Manager assignment"
        )
    if "engine_provenance" in metadata:
        try:
            EngineProvenanceManifest.from_dict(metadata["engine_provenance"])
        except (KeyError, TypeError, ValueError, WorkshopError) as exc:
            raise WorkshopError(
                "durable Workshop engine provenance is malformed"
            ) from exc
    job = product.get("stage")
    if latest.get("to_stage") != job:
        raise WorkshopError("latest Workshop event differs from product state")
    status = payload.get("status")
    allowed_statuses = {"waiting", "stopped", "delivered"}
    if allow_ambiguous_deliver:
        allowed_statuses.add("working")
    if status not in allowed_statuses:
        raise WorkshopError(
            "selected Inventor stopped without a terminal Workshop event"
        )
    if status == "working" and (
        job != "deliver"
        or not isinstance(payload.get("deliver_provider_id"), str)
        or not payload.get("deliver_provider_id")
        or re.fullmatch(
            r"deliver-[0-9a-f]{64}",
            str(payload.get("deliver_attempt_id")),
        )
        is None
    ):
        raise WorkshopError(
            "ambiguous Deliver state has no exact provider attempt identity"
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
    world_inputs = getattr(assignment, "world_inputs", None)
    if world_inputs is not None:
        if lane != "little-worlds" or not isinstance(
            world_inputs, WorldInventInputs
        ):
            raise WorkshopError("Manager world inputs belong to another lane")
        world_inputs.assert_wish(assignment.wish)
        if invented is not None:
            world_inputs.assert_lane_contract(
                invented.concept.get("lane_contract")
            )
            accepted = next(
                (
                    event.get("payload")
                    for event in events
                    if event.get("from_stage") == "invent"
                    and event.get("to_stage") == "make"
                    and isinstance(event.get("payload"), Mapping)
                ),
                None,
            )
            if (
                not isinstance(accepted, Mapping)
                or accepted.get("world_inputs_sha256")
                != world_inputs.binding_sha256
            ):
                raise WorkshopError(
                    "durable Invent state is not bound to Manager world inputs"
                )
    delivery = None
    if status == "delivered":
        delivery = _delivered_from_event(payload.get("delivery"))
        if (
            delivery.product_artifact_sha256 != artifact_sha256
            or delivery.instructions_sha256 != instructions_sha256
            or delivery.product_id != product_id
            or delivery.wish_sha256 != deliver_wish_sha256(assignment.wish)
            or delivery.deliver_provider_id
            != payload.get("deliver_provider_id")
            or delivery.deliver_attempt_id != payload.get("deliver_attempt_id")
        ):
            raise WorkshopError(
                "persisted Deliver result has different exact Wish or inputs"
            )
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
    credentials: Optional[FactoryAgentCredentials] = None,
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
    if credentials is not None and environment is not None:
        raise WorkshopError(
            "Factory resume accepts credentials or an environment, not both"
        )
    selected_credentials = (
        credentials
        if credentials is not None
        else _factory_credentials_for(inventor_id, environment)
    )
    if selected_credentials is None:
        return dict(result)
    if not isinstance(selected_credentials, FactoryAgentCredentials):
        raise WorkshopError("Factory resume credentials are not typed")
    assert_current = getattr(assignment, "assert_current", None)
    if callable(assert_current):
        assert_current()
    card = assignment.decision.selected.card
    lane, level = _manifest_workshop_shape(card)
    assignment, world_need = _refresh_world_instructions_evidence(
        assignment, result
    )
    if world_need is not None:
        return {
            **dict(result),
            "status": "waiting",
            "job": "instructions",
            "needs": [world_need.to_dict()],
            "manager_assignment": ManagerAssignmentHandoff.from_assignment(
                assignment
            ).result_binding(),
        }
    runtime_root = Path(card.root) / ".workshop"
    writer = writer_factory(
        store_factory(runtime_root / "workshop.sqlite3"),
        inventor_id,
        selected_credentials,
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

    services = _selected_manager_services() if environment is None else None
    resume_tools = WorkshopTools(
        invent=unavailable,
        make=unavailable,
        playtest=unavailable,
        instructions=instructions,
        deliver=(
            None
            if services is None or services.deliver_fulfiller is None
            else DefaultDeliver(services.deliver_fulfiller)
        ),
    )
    provider_ids = {
        "invent": "workshop.resume-unavailable-invent-v1",
        "make": "workshop.resume-unavailable-make-v1",
        "playtest": "workshop.resume-unavailable-playtest-v1",
        "instructions": "workshop.factory-resume-instructions-v1",
    }
    if resume_tools.deliver is not None:
        provider_ids["deliver"] = services.stage_provider_id("deliver", "deliver")
    workshop_kwargs = {
        "inventor_id": inventor_id,
        "trusted_engine": register_workshop_engine(
            resume_tools, provider_ids=provider_ids
        ),
        "runtime_root": runtime_root,
    }
    if lane == "little-worlds":
        workshop_kwargs.update(
            {
                "world_inputs": getattr(assignment, "world_inputs", None),
                "world_evidence": getattr(assignment, "world_evidence", None),
            }
        )
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
    if runner is _managed_child_run:
        # The authoritative CLI executes every common stage in the trusted
        # Manager process. A manifested Inventor contributes inert Taste data;
        # its profile.py is never imported or spawned. Custom contribution
        # levels fail closed until their narrow stage-only RPC is available.
        from .manager_execution import execute_manager_workshop

        if not callable(state_validator):
            raise WorkshopError("Workshop state validator must be callable")
        services = _selected_manager_services()
        execution_options = {}
        if services is not None:
            execution_options["trusted_engine"] = (
                services.trusted_workshop_engine()
            )
        bound = execute_manager_workshop(
            assignment, action=action, **execution_options
        )
        return state_validator(assignment, bound)
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
    """Atomically and durably seal one exact handoff before child execution."""

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
    if not 1 <= len(source) <= MAX_HANDOFF_BYTES:
        raise WorkshopError("Manager assignment handoff is empty or too large")
    try:
        expected_directory = assignment_root.lstat()
    except OSError as exc:
        raise WorkshopError("cannot inspect Manager assignment storage") from exc
    if not stat.S_ISDIR(expected_directory.st_mode) or stat.S_ISLNK(
        expected_directory.st_mode
    ):
        raise WorkshopError("Manager assignment storage must be a regular directory")
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        directory_descriptor = os.open(str(assignment_root), directory_flags)
    except OSError as exc:
        raise WorkshopError("cannot safely open Manager assignment storage") from exc
    opened_directory = os.fstat(directory_descriptor)
    if (opened_directory.st_dev, opened_directory.st_ino) != (
        expected_directory.st_dev,
        expected_directory.st_ino,
    ):
        os.close(directory_descriptor)
        raise WorkshopError("Manager assignment storage changed while opening")
    temporary_name = ".%s-%s.tmp" % (path.name, secrets.token_hex(8))
    temporary_created = False
    try:
        flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0)
        )
        try:
            descriptor = os.open(
                temporary_name,
                flags,
                0o600,
                dir_fd=directory_descriptor,
            )
        except OSError as exc:
            raise WorkshopError("cannot stage the exact Manager assignment") from exc
        temporary_created = True
        try:
            os.fchmod(descriptor, 0o600)
            written = 0
            while written < len(source):
                count = os.write(descriptor, source[written:])
                if count <= 0:  # pragma: no cover - defensive short-write guard
                    raise WorkshopError("cannot completely stage Manager assignment")
                written += count
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        try:
            os.link(
                temporary_name,
                path.name,
                src_dir_fd=directory_descriptor,
                dst_dir_fd=directory_descriptor,
                follow_symlinks=False,
            )
        except FileExistsError:
            os.unlink(temporary_name, dir_fd=directory_descriptor)
            temporary_created = False
            os.fsync(directory_descriptor)
            existing = _read_saved_handoff(path, handoff.inventor_id)
            if existing.to_dict() != handoff.to_dict():
                raise WorkshopError(
                    "this Wish id is already bound to a different Manager assignment"
                )
        except OSError as exc:
            raise WorkshopError("cannot atomically seal Manager assignment") from exc
        else:
            # The final name appears only after all bytes are fsynced.  A crash
            # can therefore leave either no assignment (retry Match) or the
            # complete assignment, never a partial authoritative record.
            os.fsync(directory_descriptor)
            os.unlink(temporary_name, dir_fd=directory_descriptor)
            temporary_created = False
            os.fsync(directory_descriptor)
        current_directory = assignment_root.lstat()
        if (
            not stat.S_ISDIR(current_directory.st_mode)
            or (current_directory.st_dev, current_directory.st_ino)
            != (opened_directory.st_dev, opened_directory.st_ino)
        ):
            raise WorkshopError("Manager assignment storage changed while sealing")
    finally:
        if temporary_created:
            try:
                os.unlink(temporary_name, dir_fd=directory_descriptor)
                os.fsync(directory_descriptor)
            except OSError:
                pass
        os.close(directory_descriptor)
    return path


def _assignment_with_publication_policy(
    assignment: Any, policy: PublicationPolicy
) -> Any:
    """Attach Manager policy without changing the routed assignment identity."""

    if not isinstance(policy, PublicationPolicy):
        raise WorkshopError("Manager publication policy is not typed")
    values = {
        "wish": assignment.wish,
        "inventor_id": assignment.inventor_id,
        "playtest_rounds": assignment.playtest_rounds,
        "assignment_sha256": assignment.assignment_sha256,
        "entrypoint": tuple(assignment.entrypoint),
        "assert_current": assignment.assert_current,
        "decision": assignment.decision,
        "publication_policy": policy,
    }
    world_inputs = getattr(assignment, "world_inputs", None)
    world_evidence = getattr(assignment, "world_evidence", None)
    if world_inputs is not None:
        values["world_inputs"] = world_inputs
        values["world_evidence"] = world_evidence
    return SimpleNamespace(**values)


def _replace_manager_assignment_publication_policy(
    assignment: Any,
    saved: ManagerAssignmentHandoff,
    policy: PublicationPolicy,
) -> ManagerAssignmentHandoff:
    """Atomically seal a monotonic draft-to-public Manager authorization."""

    if not isinstance(saved, ManagerAssignmentHandoff):
        raise WorkshopError("saved Manager assignment is missing")
    current = saved.publication_policy or PublicationPolicy.legacy_fail_safe()
    if current.visibility == "public":
        if policy.visibility != "public":
            raise WorkshopError("a public Wish cannot be downgraded to draft")
        return saved
    if (
        policy.visibility != "public"
        or policy.authorization != "explicit-resume-publish"
    ):
        raise WorkshopError(
            "a saved draft can become public only through explicit --publish"
        )
    replacement = ManagerAssignmentHandoff(
        wish=saved.wish,
        inventor_id=saved.inventor_id,
        playtest_rounds=saved.playtest_rounds,
        decision_sha256=saved.decision_sha256,
        assignment_sha256=saved.assignment_sha256,
        manifest_sha256=saved.manifest_sha256,
        taste_sha256=saved.taste_sha256,
        implementation_sha256=saved.implementation_sha256,
        entrypoint=saved.entrypoint,
        world_inputs=saved.world_inputs,
        world_evidence=saved.world_evidence,
        publication_policy=policy,
        schema_version=4,
    )
    replacement.assert_inventor_current(assignment.decision.selected.card)
    card_root = Path(assignment.decision.selected.card.root)
    path = _assignment_file(card_root, saved.wish.product_id)
    if _read_saved_handoff(path, saved.inventor_id).to_dict() != saved.to_dict():
        raise WorkshopError(
            "saved Manager assignment changed before publication authorization"
        )
    source = (
        json.dumps(
            replacement.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")
    if len(source) > MAX_HANDOFF_BYTES:
        raise WorkshopError("updated Manager assignment is too large")
    assignment_root = path.parent
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        directory_descriptor = os.open(str(assignment_root), directory_flags)
    except OSError as exc:
        raise WorkshopError("cannot safely open Manager assignment storage") from exc
    temporary_name = ".%s.publication-%s" % (path.name, secrets.token_hex(8))
    temporary_created = False
    try:
        expected = os.stat(
            path.name,
            dir_fd=directory_descriptor,
            follow_symlinks=False,
        )
        if not stat.S_ISREG(expected.st_mode):
            raise WorkshopError("saved Manager assignment must be a regular file")
        descriptor = os.open(
            temporary_name,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0),
            0o600,
            dir_fd=directory_descriptor,
        )
        temporary_created = True
        try:
            written = 0
            while written < len(source):
                written += os.write(descriptor, source[written:])
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        before_replace = os.stat(
            path.name,
            dir_fd=directory_descriptor,
            follow_symlinks=False,
        )
        if (
            before_replace.st_dev,
            before_replace.st_ino,
            before_replace.st_size,
            before_replace.st_mtime_ns,
        ) != (
            expected.st_dev,
            expected.st_ino,
            expected.st_size,
            expected.st_mtime_ns,
        ):
            raise WorkshopError(
                "saved Manager assignment changed during publication authorization"
            )
        os.replace(
            temporary_name,
            path.name,
            src_dir_fd=directory_descriptor,
            dst_dir_fd=directory_descriptor,
        )
        temporary_created = False
        os.fsync(directory_descriptor)
    except OSError as exc:
        raise WorkshopError(
            "cannot durably update Manager publication authorization"
        ) from exc
    finally:
        if temporary_created:
            try:
                os.unlink(temporary_name, dir_fd=directory_descriptor)
            except OSError:
                pass
        os.close(directory_descriptor)
    verified = _read_saved_handoff(path, saved.inventor_id)
    if verified.to_dict() != replacement.to_dict():
        raise WorkshopError("Manager publication authorization did not persist exactly")
    return verified


def _find_durable_wish_once(
    root: Path, product_id: str, *, allow_missing: bool = False
) -> Optional[Mapping[str, Any]]:
    """Observe one Manager Wish or Inventor product without mutation."""

    catalog = discover_inventor_catalog(root)
    pending_store = PendingWishStore(catalog.collection)
    pending = pending_store.load(product_id, allow_missing=True)
    match_attempt = MatchAttemptStore(catalog.collection).load(
        product_id, allow_missing=True
    )
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
    if not matches and pending is not None:
        if pending.catalog_taste_identity_bound:
            pending.assert_catalog_current(catalog)
        return {
            "card": None,
            "database": None,
            "runtime": None,
            "product": None,
            "events": (),
            "latest": None,
            "handoff": None,
            "pending": pending,
            "pending_store": pending_store,
            "match_attempt": match_attempt,
        }
    if not matches:
        if match_attempt is not None:
            raise WorkshopError(
                "saved Match attempt has no PendingWish or Manager assignment"
            )
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
    located = matches[0]
    if pending is not None:
        # Once Match has sealed an assignment, that assignment is authoritative
        # even if the catalog later changes.  The stale pending record must still
        # agree byte-for-byte on every input it bound before Match.
        # ``match_attempt`` remains an immutable audit of the original Match
        # handoff.  Its handoff digest is deliberately not compared with the
        # current handoff here: a later explicit draft-to-public authorization
        # replaces only the saved handoff's publication policy and must not
        # rewrite or invalidate completed Match history.
        handoff = located.get("handoff")
        if not isinstance(handoff, ManagerAssignmentHandoff):
            raise WorkshopError(
                "a Manager pending Wish has Inventor state but no exact assignment"
            )
        if pending.catalog_collection != catalog.collection:
            raise WorkshopError("Manager pending Wish belongs to a different catalog root")
        if pending.wish.to_dict() != handoff.wish.to_dict():
            raise WorkshopError("Manager pending Wish differs from the saved assignment")
        if pending.playtest_rounds != handoff.playtest_rounds:
            raise WorkshopError("Manager pending Wish rounds differ from the saved assignment")
        saved_policy = handoff.publication_policy
        policy_matches = (
            isinstance(saved_policy, PublicationPolicy)
            and pending.publication_policy.to_dict() == saved_policy.to_dict()
        )
        legitimate_assignment_upgrade = (
            isinstance(saved_policy, PublicationPolicy)
            and pending.publication_policy.visibility == "draft"
            and saved_policy.visibility == "public"
            and saved_policy.authorization == "explicit-resume-publish"
        )
        if not (policy_matches or legitimate_assignment_upgrade):
            raise WorkshopError(
                "Manager pending Wish publication policy differs from the saved assignment"
            )
    return {
        **located,
        "pending": pending,
        "pending_store": pending_store,
        "match_attempt": match_attempt,
    }


def _find_durable_wish(
    root: Path, product_id: str, *, allow_missing: bool = False
) -> Optional[Mapping[str, Any]]:
    """Locate one stable Manager Wish snapshot without taking its write lock.

    PendingWish publication upgrades and append-only Match heads live in
    separate durable stores. Read both again after the broader assignment and
    runtime discovery so status can never combine an old policy with a newer
    attempt. Their heads are monotonic, making equal before/after digests a
    stable observation; a bounded retry handles a writer crossing the read.
    """

    for unused_attempt in range(3):
        located = _find_durable_wish_once(
            root, product_id, allow_missing=True
        )
        observed_pending = None if located is None else located.get("pending")
        observed_match = (
            None if located is None else located.get("match_attempt")
        )
        catalog = discover_inventor_catalog(root)
        current_pending = PendingWishStore(catalog.collection).load(
            product_id, allow_missing=True
        )
        current_match = MatchAttemptStore(catalog.collection).load(
            product_id, allow_missing=True
        )
        if (
            (
                None
                if observed_pending is None
                else observed_pending.record_sha256
            )
            == (
                None
                if current_pending is None
                else current_pending.record_sha256
            )
            and (
                None
                if observed_match is None
                else observed_match.event_sha256
            )
            == (
                None
                if current_match is None
                else current_match.event_sha256
            )
        ):
            if located is not None:
                return located
            if allow_missing:
                return None
            raise WorkshopError(
                "no saved Wish %r was found under %s; use the id printed by "
                "'workshop wish'" % (product_id, Path(root))
            )
    raise WorkshopError(
        "saved Manager Wish changed repeatedly during a read-only observation; "
        "retry status or resume"
    )


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
    allowed_metadata_shapes = (
        set(expected),
        set(expected) | {"engine_provenance"},
    )
    if (
        not isinstance(metadata, Mapping)
        or set(metadata) not in allowed_metadata_shapes
        or any(metadata.get(key) != value for key, value in expected.items())
    ):
        return (
            "durable Workshop bindings differ from the exact saved Manager assignment, "
            "Inventor identity, Taste, lane, customization, or Playtest allowance"
        )
    if "engine_provenance" in metadata:
        try:
            EngineProvenanceManifest.from_dict(metadata["engine_provenance"])
        except (KeyError, TypeError, ValueError, WorkshopError) as exc:
            return "durable Workshop engine provenance is invalid: %s" % exc
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
        business_metadata = {
            key: value
            for key, value in metadata.items()
            if key != "engine_provenance"
        }
        expected_keys = set(business_metadata) | {
            "product_id",
            "round",
            "invented",
            "input_feedback",
            "made",
        }
        # ``wish`` already lives in metadata; checkpoint bindings add product_id.
        if set(checkpoint) != expected_keys:
            return "Made checkpoint payload shape is not exact"
        if any(
            checkpoint.get(key) != value
            for key, value in business_metadata.items()
        ):
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
            expected_completed_keys = set(business_metadata) | {
                "product_id",
                "round",
                "made_checkpoint_sha256",
                "made",
                "playtested",
            }
            if set(completed) != expected_completed_keys:
                return "Playtested checkpoint payload shape is not exact"
            if any(
                completed.get(key) != value
                for key, value in business_metadata.items()
            ):
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
    located: Mapping[str, Any],
    run_root: Path,
    latest_payload: Mapping[str, Any],
    *,
    manager_assignment: Any = None,
) -> Optional[str]:
    try:
        latest = located["latest"]
        checkpoint, checkpoint_digest = _read_instructions_checkpoint(
            run_root, latest
        )
        metadata = located["product"]["metadata"]
        business_metadata = {
            key: value
            for key, value in metadata.items()
            if key != "engine_provenance"
        }
        expected_keys = set(business_metadata) | {
            "product_id",
            "round",
            "made",
            "playtested",
        }
        if set(checkpoint) != expected_keys:
            return "Instructions checkpoint payload shape is not exact"
        if any(
            checkpoint.get(key) != value
            for key, value in business_metadata.items()
        ):
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
        world_kwargs = {}
        if blueprint.lane == "little-worlds" and manager_assignment is not None:
            world_kwargs = {
                "wish": manager_assignment.wish,
                "world_inputs": getattr(
                    manager_assignment, "world_inputs", None
                ),
                "world_evidence": getattr(
                    manager_assignment, "world_evidence", None
                ),
            }
        if not playtested.passed or _playtest_policy_needs(
            blueprint, made, playtested, evidence_root, **world_kwargs
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
    located: Mapping[str, Any],
    page: Optional[Mapping[str, Any]] = None,
    *,
    manager_assignment: Any = None,
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
    if (
        stage == "deliver"
        and status == "delivered"
        and isinstance(page, Mapping)
        and page.get("status") in ("draft", "unknown")
    ):
        return (
            True,
            "factory-page",
            "the delivered toy's exact Factory page can be published or reconciled",
        )
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
                located,
                run_root.resolve(strict=True),
                payload,
                manager_assignment=manager_assignment,
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
    if stage == "deliver":
        if status == "working":
            return (
                False,
                "ambiguous-deliver",
                "Deliver has a working external effect with an unknown outcome; reconcile it instead of retrying",
            )
        exact = (
            status == "waiting"
            and isinstance(payload.get("deliver_checkpoint_path"), str)
            and bool(payload["deliver_checkpoint_path"])
            and _valid_sha256(payload.get("deliver_checkpoint_sha256"))
            and payload.get("deliver_checkpoint_round") == payload.get("round")
            and isinstance(payload.get("instructions_checkpoint_path"), str)
            and bool(payload["instructions_checkpoint_path"])
            and _valid_sha256(payload.get("instructions_checkpoint_sha256"))
            and payload.get("instructions_checkpoint_round") == payload.get("round")
        )
        if exact:
            return (
                True,
                "deliver",
                "Deliver can continue from its exact approved Instructions and no-effect wait",
            )
        return (
            False,
            "legacy-deliver",
            "Deliver has no exact no-effect checkpoint that can be continued safely",
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
    pending = located.get("pending")
    if (
        isinstance(pending, PendingWish)
        and located.get("handoff") is None
        and located.get("product") is None
    ):
        attempt = located.get("match_attempt")
        if attempt is not None and not isinstance(attempt, MatchAttemptEvent):
            raise WorkshopError("saved Match attempt is not typed")
        if isinstance(attempt, MatchAttemptEvent) and attempt.status == "assigned":
            raise WorkshopError(
                "Match attempt claims an assignment but its sealed handoff is missing"
            )
        status = (
            "waiting"
            if isinstance(attempt, MatchAttemptEvent)
            and attempt.status == "waiting"
            else "matching"
        )
        needs = (
            [item.to_dict() for item in attempt.needs]
            if isinstance(attempt, MatchAttemptEvent)
            and attempt.status == "waiting"
            else []
        )
        receipt = {
            "schema_version": 1,
            "catalog_root": str(Path(root).resolve()),
            "product_id": product_id,
            "status": status,
            "job": "match",
            "round": None,
            "inventor_id": None,
            "inventor_name": None,
            "artifact_sha256": None,
            "updated_at": (
                attempt.recorded_at
                if isinstance(attempt, MatchAttemptEvent)
                else None
            ),
            "wish": pending.wish.to_dict(),
            "needs": needs,
            "event_chain": "not-started",
            "publication_policy": pending.publication_policy.to_dict(),
            "catalog": {
                "collection": str(pending.catalog_collection),
                "catalog_sha256": pending.catalog_sha256,
                "total": pending.catalog_total,
                "full_taste_bound": pending.catalog_taste_identity_bound,
            },
        }
        if isinstance(attempt, MatchAttemptEvent):
            receipt["match_attempt"] = attempt.public_status()
        if pending.catalog_taste_identity_bound:
            receipt["resume"] = {
                "status": "available",
                "kind": "match",
                "command": _resume_command(product_id, root),
            }
        else:
            receipt["resume"] = {
                "status": "unavailable",
                "kind": "legacy-match",
                "reason": (
                    "this legacy pending Wish predates the full-TASTE catalog "
                    "snapshot; start a new Wish instead of rematching it under "
                    "changed creative constitutions"
                ),
            }
        return receipt
    card = located["card"]
    saved_handoff = located.get("handoff")
    match_attempt = located.get("match_attempt")
    if match_attempt is not None and not isinstance(
        match_attempt, MatchAttemptEvent
    ):
        raise WorkshopError("saved Match attempt is not typed")
    publication_policy = (
        saved_handoff.publication_policy
        if isinstance(saved_handoff, ManagerAssignmentHandoff)
        and saved_handoff.publication_policy is not None
        else PublicationPolicy.legacy_fail_safe()
    )
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
            "publication_policy": publication_policy.to_dict(),
            "manager_handoff_sha256": handoff.handoff_sha256,
        }
        if isinstance(match_attempt, MatchAttemptEvent):
            receipt["match_attempt"] = match_attempt.public_status()
        available, kind, reason = _resume_availability(located)
        if available:
            receipt["resume"] = {
                "status": "available",
                "kind": kind,
                "command": _resume_command(product_id, root),
            }
        else:
            receipt["resume"] = {
                "status": "unavailable",
                "kind": kind,
                "reason": reason,
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
        "publication_policy": publication_policy.to_dict(),
    }
    if isinstance(saved_handoff, ManagerAssignmentHandoff):
        # The Match event binds the handoff originally sealed at assignment.
        # This digest describes the current handoff, whose publication policy
        # may later be upgraded without rewriting that immutable Match audit.
        receipt["manager_handoff_sha256"] = saved_handoff.handoff_sha256
    if isinstance(match_attempt, MatchAttemptEvent):
        receipt["match_attempt"] = match_attempt.public_status()
    raw_engine_provenance = metadata.get("engine_provenance")
    if raw_engine_provenance is not None:
        try:
            engine_provenance = EngineProvenanceManifest.from_dict(
                raw_engine_provenance
            )
        except (KeyError, TypeError, ValueError, WorkshopError) as exc:
            raise WorkshopError(
                "saved Workshop engine provenance is malformed"
            ) from exc
        receipt["engine_provenance"] = engine_provenance.to_dict()
    if product.get("stage") == "deliver":
        deliver_provider_id = payload.get("deliver_provider_id")
        deliver_attempt_id = payload.get("deliver_attempt_id")
        if (
            not isinstance(deliver_provider_id, str)
            or not deliver_provider_id
            or len(deliver_provider_id) > 500
            or any(
                character.isspace()
                or ord(character) < 33
                or ord(character) == 127
                for character in deliver_provider_id
            )
            or not isinstance(deliver_attempt_id, str)
            or re.fullmatch(r"deliver-[0-9a-f]{64}", deliver_attempt_id) is None
        ):
            raise WorkshopError(
                "persisted Deliver state has no exact provider attempt identity"
            )
        receipt["deliver_provider_id"] = deliver_provider_id
        receipt["deliver_attempt_id"] = deliver_attempt_id
        if status == "working":
            receipt["reconcile"] = {
                "status": "required",
                "kind": "authenticated-deliver-readback",
                "command": _reconcile_command(product_id, root),
            }
    if status == "delivered":
        raw_delivery = next(
            (
                event_payload.get("delivery")
                for event in reversed(located["events"])
                if isinstance(
                    (event_payload := event.get("payload")), Mapping
                )
                and event_payload.get("status") == "delivered"
                and event_payload.get("delivery") is not None
            ),
            None,
        )
        delivered = _delivered_from_event(raw_delivery)
        try:
            persisted_wish = Wish(**dict(wish))
        except (TypeError, WorkshopError) as exc:
            raise WorkshopError("saved Deliver Wish is malformed") from exc
        if persisted_wish.to_dict() != dict(wish):
            raise WorkshopError("saved Deliver Wish identity is inconsistent")
        if (
            delivered.product_artifact_sha256 != product.get("artifact_sha256")
            or delivered.product_id != product_id
            or delivered.wish_sha256 != deliver_wish_sha256(persisted_wish)
            or delivered.deliver_provider_id
            != receipt.get("deliver_provider_id")
            or delivered.deliver_attempt_id != receipt.get("deliver_attempt_id")
        ):
            raise WorkshopError(
                "persisted Deliver result identifies another Wish or product"
            )
        receipt["delivery"] = delivered.to_dict()
    active = located["runtime"].active_lease(product_id)
    if active is not None:
        receipt["worker"] = {
            "status": "active",
            "expires_at": active["expires_at"],
        }
        reconciliation = receipt.get("reconcile")
        if isinstance(reconciliation, Mapping):
            receipt["reconcile"] = {
                **dict(reconciliation),
                "status": "blocked",
                "reason": (
                    "another Workshop worker owns this attempt until %s"
                    % active["expires_at"]
                ),
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
    available, kind, reason = _resume_availability(located, receipt.get("page"))
    if available:
        receipt["resume"] = {
            "status": "available",
            "kind": kind,
            "command": _resume_command(product_id, root),
        }
    else:
        receipt["resume"] = {
            "status": "unavailable",
            "kind": kind,
            "reason": reason,
        }
    return receipt


def _promote_factory_intent(
    store: Any,
    intent: Mapping[str, Any],
    draft: Receipt,
    credentials: Any,
    *,
    product_id: str,
    assert_current: Callable[[], None],
    session_factory: Any,
    transition_factory: Any,
) -> Receipt:
    """Fence one public effect and reconcile crash ambiguity by GET only."""

    if not callable(assert_current):
        raise WorkshopError(
            "Factory publication requires a current Manager assignment"
        )
    assert_current()

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
            assert_current()
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
            assert_current()
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
        assert_current()
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
            assert_current()
        except Exception:
            store.restore_draft_after_publish_rejection(
                intent_id,
                effect_token,
                "manager-assignment-changed-before-publication",
            )
            raise
        try:
            public = transition.publish(draft)
        except AmbiguousEffectError:
            store.mark_live_unknown(
                intent_id, effect_token, "ambiguous-factory-publication-effect"
            )
            raise
        except EffectError:
            store.restore_draft_after_publish_rejection(
                intent_id, effect_token, "factory-publication-rejected"
            )
            raise
        except Exception as exc:
            store.mark_live_unknown(
                intent_id, effect_token, "unexpected-factory-publication-error"
            )
            raise AmbiguousEffectError(
                "Factory publication outcome is unknown; reconcile before retry"
            ) from exc
        if not isinstance(public, Receipt) or not public.is_verified_public:
            store.mark_live_unknown(
                intent_id,
                effect_token,
                "unverified-factory-publication-receipt",
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
    if result.get("status") != "delivered" or not isinstance(
        result.get("delivery"), Mapping
    ):
        return {
            "status": "waiting",
            "reason": (
                "The authenticated Factory draft remains private until exact "
                "production, QA, packing, and carrier evidence proves this toy "
                "can be fulfilled. Factory publication may activate a sale listing."
            ),
        }
    delivered = _delivered_from_event(result["delivery"])
    if (
        not isinstance(artifact_sha256, str)
        or delivered.product_id != product_id
        or delivered.wish_sha256 != deliver_wish_sha256(assignment.wish)
        or delivered.product_artifact_sha256 != artifact_sha256
    ):
        raise WorkshopError(
            "the physical Deliver receipt belongs to another Wish or artifact"
        )
    credentials = _factory_credentials_for(inventor_id)
    if credentials is None:
        catalog_root = Path(assignment.decision.selected.card.root).parent
        return {
            "status": "waiting",
            "reason": (
                "The trusted Manager has no Factory credential for this Inventor. "
                "Configure its factory_credentials service (recommended), or the "
                "legacy FACTORY_PASSWORD, then run: %s. The secret is never printed "
                "or passed to Inventor code."
                % _resume_command(product_id, catalog_root)
            ),
        }
    try:
        runtime_root = Path(assignment.decision.selected.card.root) / ".workshop"
        store = store_factory(runtime_root / "workshop.sqlite3")
        intent = store.latest_publish_intent(product_id)
        receipt_value = intent.get("receipt") if isinstance(intent, Mapping) else None
        draft = Receipt.from_dict(receipt_value)
        if draft.details.get("page_url") != page_url:
            raise WorkshopError(
                "the Factory draft URL differs from the Workshop Instructions receipt"
            )
        draft.assert_artifact(artifact_sha256)
        if (
            draft.details.get("instructions_sha256")
            != delivered.instructions_sha256
        ):
            raise WorkshopError(
                "the physical Deliver receipt identifies different Instructions"
            )
        if not isinstance(intent, Mapping):
            raise WorkshopError("the selected Inventor has no durable Factory intent")
        assert_current = getattr(assignment, "assert_current", None)
        if not callable(assert_current):
            raise WorkshopError(
                "Factory publication requires a current Manager assignment"
            )
        assert_current()
        public = _promote_factory_intent(
            store,
            intent,
            draft,
            credentials,
            product_id=product_id,
            assert_current=assert_current,
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


def _pending_match_waiting_receipt(
    pending: PendingWish,
    waiting: WaitingFor,
    root: Path,
    attempt: MatchAttemptEvent,
) -> Mapping[str, Any]:
    """One retryable Match wait, bound to the already-printed Wish id."""

    if attempt.status != "waiting" or tuple(attempt.needs) != tuple(
        waiting.needs
    ):
        raise WorkshopError("durable Match attempt differs from its typed wait")

    return {
        **_waiting_receipt(pending.wish, waiting),
        "job": "match",
        "durable_status": "waiting",
        "match_attempt": attempt.public_status(),
        "publication_policy": pending.publication_policy.to_dict(),
        "next_command": _resume_command(pending.wish.product_id, root),
    }


def _match_pending_wish(root: Path, pending: PendingWish) -> Any:
    """Run semantic Match against exactly the catalog saved before the model call."""

    catalog = discover_inventor_catalog(root)
    pending.assert_catalog_current(catalog)
    semantic = CodexSemanticManager()
    manager = WorkshopManager(
        catalog_provider=lambda: catalog,
        retriever=semantic.retrieve,
        judge=semantic.judge,
        judge_identity=semantic.judge_identity,
        judge_version=semantic.judge_version,
        judge_config_sha256=semantic.judge_config_sha256,
    )
    assignment = manager.assign(
        pending.wish, playtest_rounds=pending.playtest_rounds
    )
    # Manager assignment construction binds the full Wish and catalog digest;
    # verify those public properties before adding publication authorization.
    try:
        assigned_wish = assignment.wish
        routing = assignment.decision.context.routing
        assigned_catalog = routing.catalog
        assert_current = assignment.assert_current
    except AttributeError as exc:
        raise WorkshopError("Match returned a malformed typed assignment") from exc
    if not isinstance(assigned_wish, Wish) or not callable(assert_current):
        raise WorkshopError("Match returned a malformed typed assignment")
    if assigned_wish.to_dict() != pending.wish.to_dict():
        raise WorkshopError("Match returned an assignment for a different Wish")
    if (
        getattr(assigned_catalog, "collection", None) != pending.catalog_collection
        or getattr(assigned_catalog, "catalog_sha256", None)
        != pending.catalog_sha256
    ):
        raise WorkshopError("Match returned an assignment from a different catalog")
    assert_current()
    return _assignment_with_publication_policy(
        assignment, pending.publication_policy
    )


def _start_matched_assignment(
    assignment: Any,
    root: Path,
    publication_policy: PublicationPolicy,
    *,
    progress: Any,
    allow_same_user_local_vault: bool = False,
) -> Mapping[str, Any]:
    """Run a newly sealed assignment while retaining Match's exact Why."""

    assignment = _prepare_assignment_world_inputs(
        assignment,
        allow_same_user_local_vault=allow_same_user_local_vault,
    )
    print(
        "Matched with %s." % assignment.decision.selected.card.name,
        file=progress,
        flush=True,
    )
    print(
        "Why: %s" % assignment.decision.fit.explanation,
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
    assignment, result = _continue_world_playtest_as_manager(assignment, result)
    result = _continue_instructions_as_manager(
        assignment,
        result,
        root,
        publication_policy=publication_policy,
    )
    if publication_policy.visibility == "public":
        result = {
            **result,
            "publication": _publish_inventor_draft(assignment, result),
        }
    decision = assignment.decision
    return {
        "schema_version": 1,
        "status": result.get("status", "started"),
        "wish": assignment.wish.to_dict(),
        "match": {
            "inventor_id": assignment.inventor_id,
            "name": decision.selected.card.name,
            "score": decision.fit.score,
            "explanation": decision.fit.explanation,
            "decision_sha256": decision.decision_sha256,
        },
        "assignment_sha256": assignment.assignment_sha256,
        "publication_policy": publication_policy.to_dict(),
        "result": result,
    }


def _status_command(product_id: str, root: Path) -> str:
    return _shell_command("workshop", "status", product_id, "--root", Path(root))


def _resume_command(product_id: str, root: Path) -> str:
    return _shell_command("workshop", "resume", product_id, "--root", Path(root))


def _reconcile_command(product_id: str, root: Path) -> str:
    return _shell_command(
        "workshop", "reconcile", product_id, "--root", Path(root)
    )


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
            elif isinstance(resume, Mapping) and resume.get("status") == "unavailable":
                print("Resume: unavailable — %s" % resume["reason"])


def _print_status_receipt(receipt: Mapping[str, Any], *, root: Path) -> None:
    print("Wish: %s" % receipt["product_id"])
    if receipt.get("job") == "match" and receipt.get("inventor_name") is None:
        print("Inventor: matching your Wish")
    else:
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
    match_attempt = receipt.get("match_attempt")
    if isinstance(match_attempt, Mapping):
        print(
            "Match attempt: %s (%s, event %s)"
            % (
                match_attempt.get("attempt_id"),
                match_attempt.get("status"),
                match_attempt.get("event_sequence"),
            )
        )
    if isinstance(receipt.get("manager_handoff_sha256"), str):
        print("Manager handoff: %s" % receipt["manager_handoff_sha256"])
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
    if isinstance(receipt.get("deliver_provider_id"), str):
        print("Deliver provider: %s" % receipt["deliver_provider_id"])
    if isinstance(receipt.get("deliver_attempt_id"), str):
        print("Deliver attempt: %s" % receipt["deliver_attempt_id"])
    reconciliation = receipt.get("reconcile")
    if (
        isinstance(reconciliation, Mapping)
        and reconciliation.get("status") == "required"
        and isinstance(reconciliation.get("command"), str)
    ):
        print("Reconcile: %s" % reconciliation["command"])
    elif (
        isinstance(reconciliation, Mapping)
        and reconciliation.get("status") == "blocked"
    ):
        print("Reconcile: unavailable — %s" % reconciliation.get("reason"))
        if isinstance(reconciliation.get("command"), str):
            print("After the worker stops: %s" % reconciliation["command"])
    provenance = receipt.get("engine_provenance")
    if isinstance(provenance, Mapping):
        print(
            "Engine provenance: %s (informational aggregate)"
            % provenance.get("informational_engine_sha256")
        )
        components = provenance.get("components")
        if isinstance(components, list):
            for component in components:
                if not isinstance(component, Mapping):
                    continue
                print(
                    "Engine %-12s %s  provider=%s  stage=%s"
                    % (
                        str(component.get("stage")).title() + ":",
                        component.get("state"),
                        component.get("provider_id") or "missing",
                        component.get("stage_sha256"),
                    )
                )
    print("Event chain: %s" % receipt["event_chain"])
    resume = receipt.get("resume")
    if isinstance(resume, Mapping) and resume.get("status") == "available":
        print("Resume: %s" % resume["command"])
    elif isinstance(resume, Mapping) and resume.get("status") == "unavailable":
        print("Resume: unavailable — %s" % resume["reason"])


def _status(args: argparse.Namespace) -> int:
    roots = _catalog_roots(args.root, include_retained=args.root is None)
    if args.product_id is None:
        products: dict[str, Path] = {}
        for root in roots:
            catalog = discover_inventor_catalog(root)
            product_ids = [
                record.wish.product_id
                for record in PendingWishStore(catalog.collection).list()
            ]
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
                        item["inventor_id"] or "matching",
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


def _reconcile(args: argparse.Namespace) -> int:
    """Read back one exact working Deliver attempt without fulfilling again."""

    roots = _catalog_roots(args.root, include_retained=args.root is None)
    selected_root, _ = _root_for_durable_wish(roots, args.product_id)
    assignment, located = _resume_assignment(selected_root, args.product_id)
    status = _status_receipt(selected_root, args.product_id)
    if status.get("job") != "deliver" or status.get("status") != "working":
        raise WorkshopError(
            "Deliver reconciliation requires an exact ambiguous working attempt"
        )
    reconciliation = status.get("reconcile")
    if (
        isinstance(reconciliation, Mapping)
        and reconciliation.get("status") == "blocked"
    ):
        raise WorkshopError(str(reconciliation.get("reason")))
    if located.get("product") is None:
        raise WorkshopError("Deliver reconciliation has no durable Workshop state")

    services = _selected_manager_services()
    if services is None or services.binding("deliver") is None:
        raise WorkshopError(
            "the exact Manager Deliver provider is not configured for authenticated readback"
        )
    selected_provider_id = services.stage_provider_id("deliver", "deliver")
    if selected_provider_id != status.get("deliver_provider_id"):
        raise AmbiguousEffectError(
            "The selected Manager Deliver provider differs from the working attempt; select its exact persisted provider before reconciliation."
        )

    from .manager_execution import execute_manager_workshop

    result = execute_manager_workshop(
        assignment,
        action="reconcile",
        trusted_engine=services.trusted_workshop_engine(),
    )
    result = _validate_child_workshop_state(
        assignment,
        result,
        allow_durable_factory_page=True,
        allow_ambiguous_deliver=True,
    )
    if result.get("status") == "working":
        result = {
            **result,
            "reconciliation": {
                "status": "still-unknown",
                "provider_id": status["deliver_provider_id"],
                "attempt_id": status["deliver_attempt_id"],
                "command": _reconcile_command(args.product_id, selected_root),
            },
        }
    publication_policy = getattr(assignment, "publication_policy", None)
    if not isinstance(publication_policy, PublicationPolicy):
        publication_policy = PublicationPolicy.legacy_fail_safe()
    receipt = {
        "schema_version": 1,
        "status": result.get("status"),
        "wish": assignment.wish.to_dict(),
        "match": {
            "inventor_id": assignment.inventor_id,
            "name": assignment.decision.selected.card.name,
            "explanation": (
                "Reconciling the exact persisted Manager Deliver attempt."
            ),
        },
        "publication_policy": publication_policy.to_dict(),
        "result": result,
    }
    if args.json:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    else:
        _print_wish_receipt(receipt, root=selected_root)
        reconciliation = result.get("reconciliation")
        if isinstance(reconciliation, Mapping):
            print(
                "Reconciliation: still unknown; no fulfillment retry was sent."
            )
            print("Read back again: %s" % reconciliation["command"])
    return 0 if result.get("status") == "delivered" else 1


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

    assignment_values = dict(
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
    if handoff.publication_policy is not None:
        assignment_values["publication_policy"] = handoff.publication_policy
    assignment = SimpleNamespace(**assignment_values)
    return assignment, located


def _world_assignment_view(
    assignment: Any,
    *,
    world_inputs: WorldInventInputs,
    world_evidence: Optional[WorldPlaytestEvidence] = None,
) -> Any:
    """Add raw-free world bindings without moving a service into child code."""

    world_inputs.assert_wish(assignment.wish)
    if world_evidence is not None and not isinstance(
        world_evidence, WorldPlaytestEvidence
    ):
        raise WorkshopError("configured world evidence is not typed")
    values = dict(
        wish=assignment.wish,
        inventor_id=assignment.inventor_id,
        playtest_rounds=assignment.playtest_rounds,
        assignment_sha256=assignment.assignment_sha256,
        entrypoint=tuple(assignment.entrypoint),
        assert_current=assignment.assert_current,
        decision=assignment.decision,
        world_inputs=world_inputs,
        world_evidence=world_evidence,
    )
    publication_policy = getattr(assignment, "publication_policy", None)
    if publication_policy is not None:
        values["publication_policy"] = publication_policy
    return SimpleNamespace(**values)


def _prepare_assignment_world_inputs(
    assignment: Any, *, allow_same_user_local_vault: bool
) -> Any:
    """Fetch exact descriptors in the Manager before contribution code runs."""

    card = assignment.decision.selected.card
    lane, unused_level = _manifest_workshop_shape(card)
    del unused_level
    if lane != "little-worlds":
        if allow_same_user_local_vault:
            raise WorkshopError(
                "--allow-same-user-local-vault belongs only to a little-worlds Wish"
            )
        return assignment
    configured = _configured_world_reference_service(assignment)
    if configured is None and allow_same_user_local_vault:
        vault = WorldReferenceVault(
            Path(card.root),
            trust_same_user_processes=True,
        )
        identity = WorldProviderIdentity(
            "workshop-local-world-reference-vault",
            "1.0.0",
            hashlib.sha256(
                b"world-reference-vault-v1:same-user-local-development"
            ).hexdigest(),
            LOCAL_STORAGE_SECURITY_BOUNDARY,
        )
        configured = (vault, identity)
    if configured is None:
        return assignment
    if (
        not isinstance(configured, tuple)
        or len(configured) != 2
        or not isinstance(configured[1], WorldProviderIdentity)
    ):
        raise WorkshopError(
            "configured world reference service must return (service, WorldProviderIdentity)"
        )
    services = _selected_manager_services()
    if services is not None and services.binding("world_reference") is not None:
        world_inputs = services.prepare_world_inputs(assignment.wish)
    else:
        world_inputs = prepare_world_invent_inputs(
            assignment.wish, configured[0], configured[1]
        )
    return _world_assignment_view(assignment, world_inputs=world_inputs)


def _world_instructions_evidence_need() -> Need:
    return Need(
        "instructions",
        "world-playtest-evidence",
        "The Manager cannot re-verify the exact private-reference Playtest "
        "envelope for this approved little world.",
        "Reconnect the isolated WorldPlaytestService and resume this exact Wish. "
        "Instructions and Factory publication remain blocked until its raw-free "
        "evidence matches the durable Wish, Invent scope, Make, and Playtest receipts.",
    )


def _durable_world_instructions_results(
    assignment: Any,
    result: Mapping[str, Any],
    located: Optional[Mapping[str, Any]] = None,
):
    """Rebuild exact approved bytes for Manager-side evidence re-verification."""

    if located is None:
        card = assignment.decision.selected.card
        database = Path(card.root) / ".workshop" / "workshop.sqlite3"
        if database.is_symlink() or not database.is_file():
            raise WorkshopError("world Instructions has no durable Workshop store")
        runtime = _ReadOnlyWorkshopStore(database)
        product = runtime.get_product(assignment.wish.product_id)
        if not runtime.verify_event_chain(assignment.wish.product_id):
            raise WorkshopError(
                "world Instructions event chain is not trustworthy"
            )
        events = runtime.events(assignment.wish.product_id)
        located = {
            "card": card,
            "runtime": runtime,
            "product": product,
            "events": events,
            "latest": events[-1] if events else None,
        }
    product = located.get("product")
    latest = located.get("latest")
    events = located.get("events")
    if (
        not isinstance(product, Mapping)
        or product.get("stage") != "instructions"
        or not isinstance(latest, Mapping)
        or not isinstance(events, Sequence)
    ):
        raise WorkshopError(
            "Manager world evidence re-verification requires durable Instructions state"
        )
    card = assignment.decision.selected.card
    run_root = (
        Path(card.root)
        / ".workshop"
        / "runs"
        / assignment.wish.product_id
    )
    checkpoint, unused_checkpoint_sha256 = _read_instructions_checkpoint(
        run_root.resolve(strict=True), latest
    )
    del unused_checkpoint_sha256
    made, playtested, evidence_root = _rebuild_checkpoint_results(
        run_root.resolve(strict=True), checkpoint
    )
    _, invented = _accepted_invented_record(located)
    if invented is None:
        raise WorkshopError(
            "world Instructions has no exact accepted Invented record"
        )
    world_inputs = getattr(assignment, "world_inputs", None)
    if not isinstance(world_inputs, WorldInventInputs):
        return None, None, None, None, _world_instructions_evidence_need()
    world_inputs.assert_wish(assignment.wish)
    lane_contract = invented.concept.get("lane_contract")
    world_inputs.assert_lane_contract(lane_contract)
    personalization = world_personalization_from_made(made)
    expected_personalization = {
        "consented_references": lane_contract.get("consented_references"),
        "feature_to_form_map": lane_contract.get("feature_to_form_map"),
    }
    if personalization != expected_personalization:
        raise WorkshopError(
            "durable Make personalization differs from its accepted Invent scope"
        )
    result_artifact = result.get("artifact_sha256")
    if result_artifact is not None and result_artifact != made.artifact_sha256:
        raise WorkshopError(
            "Manager Instructions result names different durable Make bytes"
        )
    return made, playtested, evidence_root, personalization, None


def _durable_world_personalization(
    assignment: Any, result: Mapping[str, Any]
) -> Mapping[str, Any]:
    """Reopen the exact Made checkpoint before an isolated World service call."""

    if not isinstance(result, Mapping):
        raise WorkshopError("world Playtest evidence request is malformed")
    if result.get("job") == "instructions":
        made, unused_playtested, unused_root, personalization, need = (
            _durable_world_instructions_results(assignment, result)
        )
        del unused_playtested, unused_root
        if need is not None or made is None or personalization is None:
            raise WorkshopError(
                "world Instructions lacks exact durable personalization"
            )
        return personalization

    card = assignment.decision.selected.card
    located = _find_durable_wish(Path(card.root).parent, assignment.wish.product_id)
    product = located.get("product")
    latest = located.get("latest")
    if result.get("job") == "deliver":
        if (
            not isinstance(product, Mapping)
            or product.get("stage") != "deliver"
            or not isinstance(latest, Mapping)
            or not isinstance(latest.get("payload"), Mapping)
        ):
            raise WorkshopError(
                "world evidence requires an exact durable Deliver wait"
            )
        run_root = (
            Path(card.root)
            / ".workshop"
            / "runs"
            / assignment.wish.product_id
        )
        if run_root.is_symlink() or not run_root.is_dir():
            raise WorkshopError("world Deliver workspace is missing or unsafe")
        resolved_root = run_root.resolve(strict=True)
        deliver_checkpoint, deliver_digest = _read_stage_checkpoint(
            resolved_root, latest, "deliver"
        )
        instructions_checkpoint, instructions_digest = (
            _read_instructions_checkpoint(resolved_root, latest)
        )
        made, playtested, unused_evidence_root = _rebuild_checkpoint_results(
            resolved_root, instructions_checkpoint
        )
        del unused_evidence_root
        payload = latest["payload"]
        if (
            payload.get("status") != "waiting"
            or payload.get("deliver_checkpoint_sha256") != deliver_digest
            or payload.get("instructions_checkpoint_sha256")
            != instructions_digest
            or deliver_checkpoint.get("instructions_checkpoint_sha256")
            != instructions_digest
            or deliver_checkpoint.get("made_artifact_sha256")
            != made.artifact_sha256
            or deliver_checkpoint.get("playtested_evidence_artifact_sha256")
            != playtested.evidence.evidence_artifact_sha256
            or result.get("artifact_sha256") != made.artifact_sha256
        ):
            raise WorkshopError(
                "world Deliver cites different approved checkpoint bytes"
            )
        return world_personalization_from_made(made)
    if (
        not isinstance(product, Mapping)
        or product.get("stage") != "playtest"
        or not isinstance(latest, Mapping)
        or not isinstance(latest.get("payload"), Mapping)
    ):
        raise WorkshopError(
            "world evidence requires an exact durable Playtest wait"
        )
    run_root = (
        Path(card.root)
        / ".workshop"
        / "runs"
        / assignment.wish.product_id
    )
    if run_root.is_symlink() or not run_root.is_dir():
        raise WorkshopError("world Playtest workspace is missing or unsafe")
    resolved_root = run_root.resolve(strict=True)
    checkpoint_problem = _exact_playtest_checkpoint_problem(
        located, resolved_root, latest["payload"]
    )
    if checkpoint_problem is not None:
        raise WorkshopError(checkpoint_problem)
    round_number = latest["payload"].get("round")
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
        raise WorkshopError("world Playtest has no exact Made checkpoint")
    checkpoint, unused_digest = _read_stage_checkpoint(
        resolved_root, made_event, "made"
    )
    del unused_digest
    made = _rebuild_made_value(resolved_root, checkpoint.get("made"))
    made.assert_current()
    if result.get("artifact_sha256") != made.artifact_sha256:
        raise WorkshopError(
            "world evidence request identifies different Made bytes"
        )
    return world_personalization_from_made(made)


def _refresh_world_instructions_evidence(
    assignment: Any,
    result: Mapping[str, Any],
    *,
    located: Optional[Mapping[str, Any]] = None,
) -> tuple[Any, Optional[Need]]:
    """Re-authorize a crash-resumed world release before any Factory effect."""

    card = assignment.decision.selected.card
    lane, unused_level = _manifest_workshop_shape(card)
    del unused_level
    if lane != "little-worlds" or result.get("job") != "instructions":
        return assignment, None
    made, playtested, evidence_root, personalization, need = (
        _durable_world_instructions_results(assignment, result, located)
    )
    if need is not None:
        return assignment, need
    world_inputs = getattr(assignment, "world_inputs", None)
    evidence = getattr(assignment, "world_evidence", None)
    if evidence is None:
        evidence_request = {
            **dict(result),
            "artifact_sha256": made.artifact_sha256,
            "world_inputs_sha256": world_inputs.binding_sha256,
        }
        evidence = _configured_world_playtest_evidence(
            assignment, evidence_request
        )
    if evidence is None:
        return assignment, _world_instructions_evidence_need()
    if not isinstance(evidence, WorldPlaytestEvidence):
        raise WorkshopError("configured world evidence is not typed")
    evidence.assert_context(
        assignment.wish,
        made.artifact_sha256,
        personalization,
        world_inputs,
    )
    needs = _playtest_policy_needs(
        ToyBlueprint.for_lane("little-worlds"),
        made,
        playtested,
        evidence_root,
        wish=assignment.wish,
        world_inputs=world_inputs,
        world_evidence=evidence,
    )
    if not playtested.passed or needs:
        raise WorkshopError(
            "durable world Playtest no longer satisfies exact Manager release policy"
        )
    return (
        _world_assignment_view(
            assignment,
            world_inputs=world_inputs,
            world_evidence=evidence,
        ),
        None,
    )


def _refresh_world_deliver_evidence(
    assignment: Any, result: Mapping[str, Any]
) -> tuple[Any, Optional[Need]]:
    """Restore exact raw-free World evidence before a Deliver continuation."""

    card = assignment.decision.selected.card
    lane, unused_level = _manifest_workshop_shape(card)
    del unused_level
    if lane != "little-worlds" or result.get("job") != "deliver":
        return assignment, None
    world_inputs = getattr(assignment, "world_inputs", None)
    if not isinstance(world_inputs, WorldInventInputs):
        return assignment, Need(
            "deliver",
            "world-playtest-evidence",
            "The Manager cannot reconstruct the exact admitted little-world reference scope for Deliver.",
            "Reconnect the Manager WorldReferenceService and resume this exact Wish.",
        )
    evidence = getattr(assignment, "world_evidence", None)
    if evidence is None:
        evidence = _configured_world_playtest_evidence(assignment, result)
    if evidence is None:
        return assignment, Need(
            "deliver",
            "world-playtest-evidence",
            "The Manager cannot re-verify the exact private-reference Playtest envelope before physical Deliver.",
            "Reconnect the isolated WorldPlaytestService and resume this exact Wish; no earlier Workshop stage will rerun.",
        )
    if not isinstance(evidence, WorldPlaytestEvidence):
        raise WorkshopError("configured world evidence is not typed")
    personalization = _durable_world_personalization(assignment, result)
    evidence.assert_context(
        assignment.wish,
        result.get("artifact_sha256"),
        personalization,
        world_inputs,
    )
    return (
        _world_assignment_view(
            assignment,
            world_inputs=world_inputs,
            world_evidence=evidence,
        ),
        None,
    )


def _continue_world_playtest_as_manager(
    assignment: Any, result: Mapping[str, Any]
) -> tuple[Any, Mapping[str, Any]]:
    """Resume once with independently verified evidence, when configured."""

    needs = result.get("needs")
    is_world_wait = (
        result.get("status") == "waiting"
        and result.get("job") == "playtest"
        and isinstance(needs, list)
        and any(
            isinstance(need, Mapping)
            and need.get("capability") == "world-test"
            for need in needs
        )
    )
    world_inputs = getattr(assignment, "world_inputs", None)
    if not is_world_wait or not isinstance(world_inputs, WorldInventInputs):
        return assignment, dict(result)
    evidence = _configured_world_playtest_evidence(assignment, result)
    if evidence is None:
        return assignment, dict(result)
    enhanced = _world_assignment_view(
        assignment,
        world_inputs=world_inputs,
        world_evidence=evidence,
    )
    return enhanced, _resume_inventor(enhanced)


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
    publication_policy: PublicationPolicy,
) -> Mapping[str, Any]:
    if not isinstance(publication_policy, PublicationPolicy):
        raise WorkshopError("Manager publication policy is not typed")
    visibility = publication_policy.visibility
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
                    "Configure the Manager factory_credentials service (recommended), "
                    "or set the legacy FACTORY_PASSWORD, then run: "
                    + _resume_command(assignment.wish.product_id, root)
                    + ". This Wish will inherit its saved %s policy. The value is "
                    "never passed to Inventor code or printed."
                    % visibility
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
    publication_policy: PublicationPolicy,
) -> Mapping[str, Any]:
    if not _is_site_wait(result):
        return dict(result)
    credentials = _factory_credentials_for(assignment.inventor_id)
    if credentials is None:
        return _factory_authentication_wait(
            assignment,
            root,
            result,
            publication_policy=publication_policy,
        )
    return _resume_factory_instructions(
        assignment, result, credentials=credentials
    )


def _resolve_resume_publication_policy(
    assignment: Any,
    located: Mapping[str, Any],
    requested_publish: Optional[bool],
) -> tuple[Any, Mapping[str, Any], PublicationPolicy, Optional[Mapping[str, str]]]:
    """Inherit saved visibility, or durably authorize one explicit upgrade."""

    if requested_publish is not None and type(requested_publish) is not bool:
        raise WorkshopError("resume publication choice is malformed")
    saved = located.get("handoff")
    if not isinstance(saved, ManagerAssignmentHandoff):
        raise WorkshopError("this Wish has no exact saved Manager assignment")
    current = saved.publication_policy or PublicationPolicy.legacy_fail_safe()
    if requested_publish is False:
        if current.visibility == "public":
            raise WorkshopError(
                "this Wish already authorizes public visibility; --draft cannot "
                "downgrade it or make an already-public page private"
            )
        return assignment, located, current, None
    if requested_publish is not True or current.visibility == "public":
        return assignment, located, current, None
    upgraded = current.authorize_public()
    replacement = _replace_manager_assignment_publication_policy(
        assignment, saved, upgraded
    )
    enhanced = _assignment_with_publication_policy(assignment, upgraded)
    rebound = {**dict(located), "handoff": replacement}
    return (
        enhanced,
        rebound,
        upgraded,
        {
            "from": "draft",
            "to": "public",
            "authorization": "explicit-resume-publish",
            "effect": (
                "the exact verified Factory page may now become visible to anyone"
            ),
        },
    )


def _resume_pending_match(
    args: argparse.Namespace,
    root: Path,
    initial: PendingWish,
) -> int:
    """Retry Match for the exact pre-Match Wish id, then start its assignment."""

    if not initial.catalog_taste_identity_bound:
        raise WorkshopError(
            "this legacy pending Wish predates the full-TASTE catalog snapshot; "
            "start a new Wish instead of rematching it under changed creative constitutions"
        )

    progress = sys.stderr if args.json else sys.stdout
    store = PendingWishStore(initial.catalog_collection)
    attempts = MatchAttemptStore(initial.catalog_collection)
    assignment = None
    receipt = None
    policy_change = None
    assignment_won_race = False
    with store.lock(initial.wish.product_id):
        located = _find_durable_wish(root, initial.wish.product_id)
        if isinstance(located.get("handoff"), ManagerAssignmentHandoff):
            # Another retry completed Match while this process waited for the
            # lock.  The exact sealed assignment is authoritative.
            assignment_won_race = True
        else:
            current = located.get("pending")
            if not isinstance(current, PendingWish):
                raise WorkshopError("saved pending Wish disappeared before Match resume")
            if args.publish is False and current.publication_policy.visibility == "public":
                raise WorkshopError(
                    "this Wish already authorizes public visibility; --draft cannot "
                    "downgrade it or make an already-public page private"
                )
            if args.publish is True and current.publication_policy.visibility == "draft":
                upgraded = current.publication_policy.authorize_public()
                replacement = current.with_publication_policy(upgraded)
                store.replace(current, replacement)
                current = replacement
                policy_change = {
                    "from": "draft",
                    "to": "public",
                    "authorization": "explicit-resume-publish",
                    "effect": (
                        "the exact verified Factory page may now become visible to anyone"
                    ),
                }
                print(
                    "Publication: this saved draft is now authorized to become public; "
                    "the exact verified Factory page may become visible to anyone.",
                    file=progress,
                    flush=True,
                )
            print(
                "Matching your saved Wish with an Inventor...",
                file=progress,
                flush=True,
            )
            working_attempt = attempts.begin(current)
            try:
                assignment = _match_pending_wish(root, current)
            except WaitingFor as waiting:
                waiting_attempt = attempts.record_waiting(
                    working_attempt, waiting.needs
                )
                receipt = _pending_match_waiting_receipt(
                    current, waiting, root, waiting_attempt
                )
            else:
                observed = store.load(current.wish.product_id)
                if not isinstance(observed, PendingWish) or (
                    observed.record_sha256 != current.record_sha256
                ):
                    raise WorkshopError("Manager pending Wish changed during Match resume")
                assignment_path = _save_manager_assignment(assignment)
                verified_handoff = _read_saved_handoff(
                    assignment_path, assignment.inventor_id
                )
                attempts.record_assigned(
                    working_attempt,
                    verified_handoff.handoff_sha256,
                )
    if assignment_won_race:
        return _resume(args)
    if assignment is not None:
        receipt = _start_matched_assignment(
            assignment,
            root,
            assignment.publication_policy,
            progress=progress,
            allow_same_user_local_vault=args.allow_same_user_local_vault,
        )
    if receipt is None:  # pragma: no cover - Match has exactly two typed outcomes
        raise WorkshopError("Match resume produced no durable outcome")
    if policy_change is not None:
        receipt = {**receipt, "publication_policy_change": policy_change}
    if args.json:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    else:
        _print_wish_receipt(
            receipt,
            root=root,
            show_match=assignment is not None,
        )
    return _wish_exit_code(receipt, strict=getattr(args, "strict", False))


def _resume(args: argparse.Namespace) -> int:
    roots = _catalog_roots(args.root, include_retained=args.root is None)
    selected_root, initial = _root_for_durable_wish(roots, args.product_id)
    pending = initial.get("pending")
    if isinstance(pending, PendingWish) and initial.get("handoff") is None:
        return _resume_pending_match(args, selected_root, pending)
    assignment, located = _resume_assignment(selected_root, args.product_id)
    assignment, located, publication_policy, policy_change = (
        _resolve_resume_publication_policy(assignment, located, args.publish)
    )
    if policy_change is not None:
        progress = sys.stderr if args.json else sys.stdout
        print(
            "Publication: this saved draft is now authorized to become public; "
            "the exact verified Factory page may become visible to anyone.",
            file=progress,
            flush=True,
        )
    status = _status_receipt(selected_root, args.product_id)
    needs = status.get("needs", [])
    terminal_or_ambiguous_deliver = (
        status.get("job") == "deliver"
        and status.get("status") in ("working", "delivered")
    )
    world_resume_need = None
    if terminal_or_ambiguous_deliver:
        # A completed Deliver needs only its exact durable receipt for a later
        # page transition. A working Deliver is effect-ambiguous. Neither case
        # may invoke World reference/comparison services merely to decide that.
        available, kind, unavailable_reason = _resume_availability(
            located,
            status.get("page"),
            manager_assignment=assignment,
        )
    else:
        assignment = _prepare_assignment_world_inputs(
            assignment,
            allow_same_user_local_vault=args.allow_same_user_local_vault,
        )
        evidence_probe = {
            "status": status.get("status"),
            "job": status.get("job"),
            "needs": needs,
            "artifact_sha256": status.get("artifact_sha256"),
        }
        assignment, world_instructions_need = _refresh_world_instructions_evidence(
            assignment,
            evidence_probe,
            located=located,
        )
        assignment, world_deliver_need = _refresh_world_deliver_evidence(
            assignment, evidence_probe
        )
        world_resume_need = world_instructions_need or world_deliver_need
        if world_resume_need is None:
            available, kind, unavailable_reason = _resume_availability(
                located,
                status.get("page"),
                manager_assignment=assignment,
            )
        else:
            available, kind, unavailable_reason = (
                False,
                "world-playtest-evidence",
                world_resume_need.reason,
            )
    result: Mapping[str, Any]
    if world_resume_need is not None:
        result = {
            "product_id": args.product_id,
            "status": "waiting",
            "job": world_resume_need.job,
            "playtest_rounds": assignment.playtest_rounds,
            "artifact_sha256": status.get("artifact_sha256"),
            "needs": [world_resume_need.to_dict()],
            "manager_assignment": ManagerAssignmentHandoff.from_assignment(
                assignment
            ).result_binding(),
        }
    elif not available:
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
            "delivery": status.get("delivery"),
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
            "artifact_sha256": status.get("artifact_sha256"),
            "needs": needs,
            "manager_assignment": ManagerAssignmentHandoff.from_assignment(
                assignment
            ).result_binding(),
        }
        result = _continue_instructions_as_manager(
            assignment,
            waiting,
            selected_root,
            publication_policy=publication_policy,
        )
    elif kind == "assigned":
        result = _run_inventor(assignment, continuing=True)
        result = _continue_instructions_as_manager(
            assignment,
            result,
            selected_root,
            publication_policy=publication_policy,
        )
    elif kind == "wish":
        result = _resume_inventor(assignment)
        result = _continue_instructions_as_manager(
            assignment,
            result,
            selected_root,
            publication_policy=publication_policy,
        )
    else:
        result = _resume_inventor(assignment)
        result = _continue_instructions_as_manager(
            assignment,
            result,
            selected_root,
            publication_policy=publication_policy,
        )
    assignment, result = _continue_world_playtest_as_manager(
        assignment, result
    )
    result = _continue_instructions_as_manager(
        assignment,
        result,
        selected_root,
        publication_policy=publication_policy,
    )
    if publication_policy.visibility == "public" and isinstance(
        result.get("page_url"), str
    ):
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
        "publication_policy": publication_policy.to_dict(),
        "result": result,
    }
    if policy_change is not None:
        receipt["publication_policy_change"] = dict(policy_change)
    if args.json:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    else:
        _print_wish_receipt(receipt, root=selected_root)
        if result.get("resume") == "not-available":
            print("Resume: unavailable — %s" % result["reason"])
    if result.get("resume") == "not-available":
        return 1
    return _wish_exit_code(receipt, strict=getattr(args, "strict", False))


def _batch_concurrency(value: str) -> int:
    try:
        selected = int(value)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("concurrency must be an integer from 1 to 8") from exc
    if not 1 <= selected <= 8:
        raise argparse.ArgumentTypeError("concurrency must be an integer from 1 to 8")
    return selected


def _batch_location(
    roots: Sequence[Path], batch_id: str
) -> tuple[Path, BatchPlanStore, BatchPlan]:
    matches = []
    for root in roots:
        catalog = discover_inventor_catalog(root)
        store = BatchPlanStore(catalog.collection)
        plan = store.load(batch_id, allow_missing=True)
        if plan is not None:
            matches.append((Path(root).resolve(), store, plan))
    if not matches:
        raise WorkshopError("this batch has no saved Manager plan")
    if len(matches) != 1:
        raise WorkshopError(
            "this batch id exists in more than one retained catalog; pass --root explicitly"
        )
    return matches[0]


def _batch_manager_scope(catalog_collection: Path) -> Path:
    """Return one stable Manager scope, including across installed generations."""

    collection = Path(catalog_collection).resolve(strict=True)
    parent = collection.parent
    if (
        collection.name == "inventors"
        and len(parent.name) == 64
        and all(character in "0123456789abcdef" for character in parent.name)
        and parent.parent.name == "bundled-catalogs"
    ):
        return parent.parent.parent.resolve(strict=True)
    return (parent if collection.name == "inventors" else collection).resolve(
        strict=True
    )


def _batch_policy_compatible(
    planned: PublicationPolicy, actual: PublicationPolicy
) -> bool:
    return planned.to_dict() == actual.to_dict() or (
        planned.visibility == "draft"
        and actual.visibility == "public"
        and actual.authorization == "explicit-resume-publish"
    )


def _batch_same_submission(existing: BatchPlan, proposed: BatchPlan) -> bool:
    """Compare every catalog-independent Wish and publication input exactly."""

    return (
        existing.batch_id == proposed.batch_id
        and existing.manager_scope_id == proposed.manager_scope_id
        and existing.submission_sha256 == proposed.submission_sha256
        and existing.playtest_rounds == proposed.playtest_rounds
        and len(existing.items) == len(proposed.items)
        and all(
            prior.wish.to_dict() == current.wish.to_dict()
            and prior.publication_policy.to_dict()
            == current.publication_policy.to_dict()
            for prior, current in zip(existing.items, proposed.items)
        )
    )


def _batch_item_status(
    root: Path, plan: BatchPlan, item: BatchPlanItem
) -> Mapping[str, Any]:
    product_id = item.wish.product_id
    try:
        receipt = _status_receipt(root, product_id)
    except WorkshopError as original:
        # Catalog drift is fatal only to Wishes that never completed Match.
        # Represent that item as unavailable so already-assigned siblings can
        # still continue under their sealed Manager handoffs.
        pending = PendingWishStore(plan.catalog_collection).load(
            product_id, allow_missing=True
        )
        if not isinstance(pending, PendingWish) or (
            pending.wish.to_dict() != item.wish.to_dict()
        ):
            raise
        catalog = discover_inventor_catalog(root)
        try:
            pending.assert_catalog_current(catalog)
        except WorkshopError as catalog_problem:
            if str(original) != str(catalog_problem):
                raise original
            return {
                "schema_version": 1,
                "catalog_root": str(Path(root).resolve()),
                "product_id": product_id,
                "status": "stopped",
                "job": "match",
                "round": None,
                "inventor_id": None,
                "inventor_name": None,
                "artifact_sha256": None,
                "updated_at": None,
                "wish": pending.wish.to_dict(),
                "needs": [
                    Need(
                        job="wish",
                        capability="exact-catalog-snapshot",
                        reason=(
                            "this Wish has not completed Match and its saved "
                            "Inventor catalog identity changed"
                        ),
                        instructions=(
                            "Restore the exact saved catalog snapshot, or start a "
                            "new Wish under the current catalog."
                        ),
                    ).to_dict()
                ],
                "event_chain": "not-started",
                "publication_policy": pending.publication_policy.to_dict(),
                "resume": {
                    "status": "unavailable",
                    "kind": "catalog-drift",
                    "reason": (
                        "Match cannot run after the exact saved catalog changed"
                    ),
                },
            }
        raise original
    if receipt.get("product_id") != product_id:
        raise WorkshopError("batch status returned another Wish identity")
    if receipt.get("wish") != item.wish.to_dict():
        raise WorkshopError("batch status returned different Wish content")
    raw_policy = receipt.get("publication_policy")
    if not isinstance(raw_policy, Mapping):
        raise WorkshopError("batch status has no exact publication policy")
    try:
        actual_policy = PublicationPolicy.from_dict(dict(raw_policy))
    except (TypeError, WorkshopError) as exc:
        raise WorkshopError("batch status publication policy is malformed") from exc
    if not _batch_policy_compatible(item.publication_policy, actual_policy):
        raise WorkshopError(
            "batch status publication policy conflicts with its immutable plan"
        )
    return receipt


def _terminate_batch_process(process: subprocess.Popen, *, force: bool = False) -> None:
    selected_signal = signal.SIGKILL if force else signal.SIGTERM
    try:
        os.killpg(process.pid, selected_signal)
    except (AttributeError, ProcessLookupError, PermissionError):
        try:
            process.kill() if force else process.terminate()
        except ProcessLookupError:
            pass


class _BatchInterrupted(RuntimeError):
    pass


class _BatchProcessSupervisor:
    """Own every batch child process group and cancel it as one unit."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._processes: dict[int, subprocess.Popen] = {}
        self._cancelled = threading.Event()

    def cancel(self) -> None:
        self._cancelled.set()
        with self._lock:
            processes = tuple(self._processes.values())
        for process in processes:
            _terminate_batch_process(process)

    def run(self, product_id: str, root: Path) -> subprocess.CompletedProcess:
        command = (
            sys.executable,
            "-m",
            "inventor_workshop",
            "resume",
            product_id,
            "--root",
            str(root),
            "--json",
        )
        # Executor shutdown drains tasks submitted before a signal.  Once
        # cancelled, those queued tasks must be inert rather than briefly
        # creating and then terminating fresh process groups.
        if self._cancelled.is_set():
            raise WorkshopError("batch process supervisor is already cancelled")
        process = subprocess.Popen(
            list(command),
            cwd=str(root),
            env=dict(os.environ),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        with self._lock:
            self._processes[process.pid] = process
        if self._cancelled.is_set():
            _terminate_batch_process(process)
        deadline = time.monotonic() + 4 * 60 * 60
        try:
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    _terminate_batch_process(process)
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        _terminate_batch_process(process, force=True)
                        process.wait()
                    raise subprocess.TimeoutExpired(
                        list(command), 4 * 60 * 60
                    )
                try:
                    process.wait(timeout=min(0.5, remaining))
                    break
                except subprocess.TimeoutExpired:
                    if self._cancelled.is_set():
                        _terminate_batch_process(process)
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            _terminate_batch_process(process, force=True)
                            process.wait()
                        break
            return subprocess.CompletedProcess(
                list(command), process.returncode, stdout=None, stderr=None
            )
        finally:
            with self._lock:
                self._processes.pop(process.pid, None)


@contextmanager
def _batch_signal_guard(supervisor: _BatchProcessSupervisor):
    if threading.current_thread() is not threading.main_thread():
        yield
        return
    installed = []

    def interrupt(signum, unused_frame):
        del unused_frame
        supervisor.cancel()
        raise _BatchInterrupted("signal %s" % signum)

    for selected in (signal.SIGINT, signal.SIGTERM):
        previous = signal.getsignal(selected)
        signal.signal(selected, interrupt)
        installed.append((selected, previous))
    try:
        yield
    finally:
        for selected, previous in reversed(installed):
            signal.signal(selected, previous)


def _run_batch_resume_child(
    product_id: str, root: Path
) -> subprocess.CompletedProcess:
    """Run one trusted Manager continuation in a separately reaped process."""

    command = (
        sys.executable,
        "-m",
        "inventor_workshop",
        "resume",
        product_id,
        "--root",
        str(root),
        "--json",
    )
    return _managed_child_run(
        command,
        cwd=str(root),
        env=os.environ,
        input="",
        capture_output=True,
        text=True,
        timeout=4 * 60 * 60,
        check=False,
    )


def _batch_status_payload(
    plan: BatchPlan,
    root: Path,
    *,
    launches: Optional[Mapping[str, Mapping[str, Any]]] = None,
) -> Mapping[str, Any]:
    launch_values = launches or {}
    items = []
    with PendingWishStore(plan.catalog_collection).validated_batch_reads():
        for position, item in enumerate(plan.items, 1):
            status = _batch_item_status(root, plan, item)
            entry = {
                "position": position,
                "product_id": item.wish.product_id,
                "batch_key": item.wish.context.get("batch_key"),
                "publication_policy": item.publication_policy.to_dict(),
                "status": status,
            }
            if item.wish.product_id in launch_values:
                entry["launch"] = dict(launch_values[item.wish.product_id])
            items.append(entry)
    def item_complete(entry: Mapping[str, Any]) -> bool:
        status = entry["status"]
        if status.get("status") != "delivered":
            return False
        raw_policy = status.get("publication_policy")
        if not isinstance(raw_policy, Mapping):
            return False
        actual = PublicationPolicy.from_dict(dict(raw_policy))
        if actual.visibility == "draft":
            return True
        page = status.get("page")
        return isinstance(page, Mapping) and page.get("status") == "public"

    complete = all(item_complete(item) for item in items)
    blocked = any(
        item["status"].get("status") in ("waiting", "stopped")
        or (
            isinstance(item["status"].get("resume"), Mapping)
            and item["status"]["resume"].get("status") == "unavailable"
            and item["status"].get("status") != "delivered"
        )
        or (
            isinstance(item.get("launch"), Mapping)
            and item["launch"].get("status") in ("failed", "timed-out")
        )
        or (
            item["status"].get("status") == "delivered"
            and isinstance(item["status"].get("page"), Mapping)
            and item["status"]["page"].get("status") == "unknown"
        )
        for item in items
    )
    return {
        "schema_version": 1,
        "batch_id": plan.batch_id,
        "plan_sha256": plan.plan_sha256,
        "catalog_root": str(root),
        "count": len(items),
        "status": "complete" if complete else "needs-attention" if blocked else "ready",
        "items": items,
    }


def _execute_batch(
    plan: BatchPlan,
    root: Path,
    store: BatchPlanStore,
    *,
    concurrency: int,
    runner: Any = None,
) -> Mapping[str, Any]:
    """Launch each currently resumable item once; derive truth from durable state."""

    selected_runner = _run_batch_resume_child if runner is None else runner
    if not callable(selected_runner):
        raise WorkshopError("batch worker runner must be callable")
    launches: dict[str, Mapping[str, Any]] = {}
    supervisor = _BatchProcessSupervisor() if runner is None else None
    if supervisor is not None:
        selected_runner = supervisor.run
    try:
        signal_guard = (
            _batch_signal_guard(supervisor)
            if supervisor is not None
            else nullcontext()
        )
        with signal_guard, store.supervise(plan):
            with PendingWishStore(
                plan.catalog_collection
            ).validated_batch_reads():
                initial = {
                    item.wish.product_id: _batch_item_status(root, plan, item)
                    for item in plan.items
                }
            scheduled = []
            for item in plan.items:
                product_id = item.wish.product_id
                resume = initial[product_id].get("resume")
                if (
                    isinstance(resume, Mapping)
                    and resume.get("status") == "available"
                ):
                    scheduled.append(item)
                else:
                    launches[product_id] = {
                        "status": "skipped",
                        "reason": (
                            resume.get("reason")
                            if isinstance(resume, Mapping)
                            else "this Wish has no resumable durable boundary"
                        ),
                    }

            def run_one(item):
                command = _resume_command(item.wish.product_id, root)
                try:
                    completed = selected_runner(item.wish.product_id, root)
                    if not isinstance(completed, subprocess.CompletedProcess):
                        raise WorkshopError(
                            "batch worker returned an untyped process result"
                        )
                    if type(completed.returncode) is not int:
                        raise WorkshopError("batch worker returned no exit status")
                    if completed.returncode == 0:
                        return {"status": "succeeded", "returncode": 0}
                    return {
                        "status": "failed",
                        "returncode": completed.returncode,
                        "reason": "the worker exited nonzero before this Wish completed",
                        "next": command,
                    }
                except subprocess.TimeoutExpired:
                    return {
                        "status": "timed-out",
                        "reason": "the worker exceeded four hours; inspect durable state before resuming",
                        "next": command,
                    }
                except (OSError, ValueError, WorkshopError):
                    return {
                        "status": "failed",
                        "reason": "the worker did not complete; inspect its durable state before resuming",
                        "next": command,
                    }

            with concurrent.futures.ThreadPoolExecutor(
                max_workers=concurrency,
                thread_name_prefix="workshop-batch",
            ) as pool:
                future_items = {
                    pool.submit(run_one, item): item for item in scheduled
                }
                for future in concurrent.futures.as_completed(future_items):
                    item = future_items[future]
                    launches[item.wish.product_id] = future.result()
    except _BatchInterrupted as exc:
        if supervisor is not None:
            supervisor.cancel()
        raise WorkshopError(
            "batch supervision was interrupted; every owned worker was terminated; inspect durable status before resuming"
        ) from exc
    return _batch_status_payload(plan, root, launches=launches)


def _print_batch_receipt(receipt: Mapping[str, Any]) -> None:
    print("Batch: %s" % receipt["batch_id"])
    print("Wishes: %s" % receipt["count"])
    print("Status: %s" % receipt["status"])
    for item in receipt["items"]:
        status = item["status"]
        print(
            "%-4s %-42s %s/%s  key=%s  visibility=%s"
            % (
                item["position"],
                item["product_id"],
                status.get("job"),
                status.get("status"),
                item.get("batch_key"),
                (
                    status.get("publication_policy", {}).get("visibility")
                    if isinstance(status.get("publication_policy"), Mapping)
                    else "unknown"
                ),
            )
        )
        launch = item.get("launch")
        if isinstance(launch, Mapping) and launch.get("status") != "succeeded":
            print(
                "     Launch: %s%s"
                % (
                    launch.get("status"),
                    " — %s" % launch["reason"]
                    if isinstance(launch.get("reason"), str)
                    else "",
                )
            )
            if isinstance(launch.get("next"), str):
                print("     Next: %s" % launch["next"])
        needs = status.get("needs")
        if isinstance(needs, list):
            for need in needs:
                if isinstance(need, Mapping):
                    print(
                        "     Need: %s — %s"
                        % (need.get("capability"), need.get("reason"))
                    )
                    if isinstance(need.get("instructions"), str):
                        print("     Next: %s" % need["instructions"])
        resume = status.get("resume")
        if (
            isinstance(resume, Mapping)
            and resume.get("status") == "unavailable"
            and not needs
            and isinstance(resume.get("reason"), str)
        ):
            print("     Next: %s" % resume["reason"])
        elif (
            isinstance(resume, Mapping)
            and resume.get("status") == "available"
            and status.get("status") == "delivered"
            and isinstance(resume.get("command"), str)
        ):
            print("     Next: %s" % resume["command"])


def _batch_submit(args: argparse.Namespace) -> int:
    root = _catalog_roots(args.root)[0]
    catalog = discover_inventor_catalog(root)
    visibility = "public" if args.publish else "draft"
    requests = parse_batch_file(
        args.file,
        input_format=args.format,
        default_visibility=visibility,
    )
    identity = load_or_create_batch_manager_identity(
        _batch_manager_scope(catalog.collection)
    )
    proposed = BatchPlan.from_requests(
        catalog,
        requests,
        playtest_rounds=args.playtest_rounds,
        manager_identity=identity,
    )
    search_roots = _catalog_roots(
        args.root, include_retained=args.root is None
    )
    existing = []
    for candidate in search_roots:
        candidate_catalog = discover_inventor_catalog(candidate)
        candidate_store = BatchPlanStore(candidate_catalog.collection)
        candidate_plan = candidate_store.load(
            proposed.batch_id, allow_missing=True
        )
        if candidate_plan is not None:
            existing.append(
                (Path(candidate).resolve(), candidate_store, candidate_plan)
            )
    if len(existing) > 1:
        raise WorkshopError(
            "this exact submission exists in more than one retained catalog; pass --root explicitly"
        )
    if existing:
        root, store, plan = existing[0]
        if not _batch_same_submission(plan, proposed):
            raise WorkshopError(
                "Manager batch id is already bound to different exact Wishes or publication policies"
            )
    else:
        plan = proposed
        store = BatchPlanStore(catalog.collection)
    store.stage(plan)
    if args.run:
        receipt = _execute_batch(
            plan, root, store, concurrency=args.concurrency
        )
    else:
        receipt = _batch_status_payload(plan, root)
    if args.json:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    else:
        _print_batch_receipt(receipt)
        if not args.run:
            print(
                "Run: %s"
                % _shell_command(
                    "workshop", "batch", "resume", plan.batch_id, "--root", root
                )
            )
    return 0


def _batch_status(args: argparse.Namespace) -> int:
    roots = _catalog_roots(args.root, include_retained=args.root is None)
    root, unused_store, plan = _batch_location(roots, args.batch_id)
    del unused_store
    receipt = _batch_status_payload(plan, root)
    if args.json:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    else:
        _print_batch_receipt(receipt)
    return 0


def _batch_resume(args: argparse.Namespace) -> int:
    roots = _catalog_roots(args.root, include_retained=args.root is None)
    root, store, plan = _batch_location(roots, args.batch_id)
    receipt = _execute_batch(
        plan, root, store, concurrency=args.concurrency
    )
    if args.json:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    else:
        _print_batch_receipt(receipt)
    return 1 if args.strict and receipt["status"] != "complete" else 0


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
    codex_authenticated = False
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
        selected_probe_model = os.environ.get(
            "WORKSHOP_MANAGER_MODEL", DEFAULT_MANAGER_MODEL
        )
        probe_nonce = secrets.token_hex(16)
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
            codex_authenticated = True
            checks.append(
                {
                    "name": "codex",
                    "status": "ready",
                    "detail": "Codex CLI is installed and signed in.",
                }
            )

    if not getattr(args, "deep", False):
        checks.append(
            {
                "name": "codex-structured-call",
                "status": "not-probed",
                "detail": (
                    "Codex authentication was checked, but the exact tool-free "
                    "structured runtime was not invoked."
                ),
                "next": (
                    "Run 'workshop doctor --deep' to spend one small selected-model call "
                    "and prove the actual Workshop model boundary."
                ),
            }
        )
    elif not codex_authenticated:
        checks.append(
            {
                "name": "codex-structured-call",
                "status": "needs-attention",
                "detail": "The structured runtime cannot be probed until Codex is signed in.",
                "next": "Repair the Codex check, then rerun 'workshop doctor --deep'.",
            }
        )
    else:
        try:
            from .codex_runtime import CodexStructuredRunner

            probe = CodexStructuredRunner(
                model=selected_probe_model,
                reasoning_effort="low",
                binary=binary,
                timeout_seconds=90,
            ).invoke(
                prompt=(
                    "Autonomous Workshop readiness probe. Return exactly one "
                    "JSON object with ok=true and nonce=%s." % probe_nonce
                ),
                schema={
                    "type": "object",
                    "properties": {
                        "ok": {"type": "boolean", "const": True},
                        "nonce": {"type": "string", "const": probe_nonce},
                    },
                    "required": ["ok", "nonce"],
                    "additionalProperties": False,
                },
            )
            structured_ready = probe == {"ok": True, "nonce": probe_nonce}
        except Exception:
            structured_ready = False
        checks.append(
            {
                "name": "codex-structured-call",
                "status": "ready" if structured_ready else "needs-attention",
                "detail": (
                    "The exact tool-free structured model call completed."
                    if structured_ready
                    else "The exact tool-free structured model call did not complete."
                ),
                "model": selected_probe_model,
                "reasoning_effort": "low",
                **(
                    {}
                    if structured_ready
                    else {
                        "next": (
                            "Run the configured Codex CLI outside a nested sandbox, "
                            "verify its version/config compatibility, and retry "
                            "'workshop doctor --deep'."
                        )
                    }
                ),
            }
        )

    model_variables = (
        "WORKSHOP_MANAGER_MODEL",
        "WORKSHOP_INVENT_MODEL",
        "WORKSHOP_REWARD_MODEL",
        "WORKSHOP_MAKE_MODEL",
        "WORKSHOP_MAKE_REWARD_MODEL",
        "WORKSHOP_PLAYTEST_MODEL",
        "WORKSHOP_INSTRUCTIONS_MODEL",
        "WORKSHOP_INSTRUCTIONS_REWARD_MODEL",
    )
    invalid_model_overrides = tuple(
        name
        for name in model_variables
        if os.environ.get(name) is not None
        and os.environ[name] not in ALLOWED_WORKSHOP_MODELS
    )
    checks.append(
        {
            "name": "model-policy",
            "status": (
                "needs-attention" if invalid_model_overrides else "ready"
            ),
            "detail": (
                "One or more Workshop model overrides are not permitted."
                if invalid_model_overrides
                else "Every configured Workshop model is Terra or Luna."
            ),
            **(
                {}
                if not invalid_model_overrides
                else {
                    "next": (
                        "Set %s to gpt-5.6-terra or gpt-5.6-luna."
                        % ", ".join(invalid_model_overrides)
                    )
                }
            ),
        }
    )

    try:
        from .agent_make import LockedCadSkillBuilder

        LockedCadSkillBuilder().ensure_available()
        cad_ready = True
    except (WaitingFor, WorkshopError, OSError, ValueError):
        cad_ready = False
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
                else {
                    "next": (
                        "Install the Workshop with its locked runtime dependencies, "
                        "or point WORKSHOP_CAD_PYTHON at that exact Python runtime."
                    )
                }
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
    try:
        services = _selected_manager_services()
        service_error = None
    except WorkshopError as exc:
        services = None
        service_error = str(exc)
    if service_error is not None:
        checks.append(
            {
                "name": "manager-services",
                "status": "needs-attention",
                "detail": "The selected Manager service configuration could not load.",
                "next": (
                    "Install or repair the named autonomous_workshop.manager_services "
                    "entry point, then rerun Doctor."
                ),
            }
        )
    elif services is None:
        checks.append(
            {
                "name": "manager-services",
                "status": "needs-attention",
                "detail": (
                    "No production service composition is selected; only the "
                    "Workshop's bounded built-in providers are available."
                ),
                "next": (
                    "Install a trusted Manager service package and set "
                    "WORKSHOP_MANAGER_SERVICES to its entry-point name."
                ),
            }
        )
    else:
        checks.append(
            {
                "name": "manager-services",
                "status": "ready",
                "detail": (
                    "Loaded trusted Manager service configuration '%s'."
                    % services.configuration_id
                ),
                "providers": services.public_summary()["capabilities"],
            }
        )

    engine_scope = "manager-common-defaults-before-inventor-selection"
    engine_provenance = None
    if service_error is None:
        try:
            if services is None:
                from .manager_execution import default_trusted_workshop_engine

                selected_engine = default_trusted_workshop_engine()
            else:
                selected_engine = services.trusted_workshop_engine()
            if not isinstance(
                selected_engine.provenance, EngineProvenanceManifest
            ):
                raise WorkshopError(
                    "selected Manager engine has no public provenance"
                )
            engine_provenance = selected_engine.provenance
        except Exception:
            engine_provenance = None
    checks.append(
        {
            "name": "engine-provenance",
            "status": "ready" if engine_provenance is not None else "needs-attention",
            "detail": (
                "All five prospective Manager-owned shared stages have a public, secret-free component manifest."
                if engine_provenance is not None
                else "The prospective Manager engine provenance could not be materialized."
            ),
            "scope": engine_scope,
            **(
                {
                    "informational_engine_sha256": (
                        engine_provenance.informational_engine_sha256
                    ),
                    "stage_sha256": engine_provenance.stage_sha256,
                }
                if engine_provenance is not None
                else {
                    "next": (
                        "Repair the selected Manager service composition, then rerun Doctor."
                    )
                }
            ),
        }
    )

    research_ready = services is not None and services.binding("research") is not None
    checks.append(
        {
            "name": "wish-aware-research",
            "status": "ready" if research_ready else "needs-attention",
            "detail": (
                "A versioned Wish-aware research provider is configured."
                if research_ready
                else (
                    "Only the privacy-preserving lane baseline is available; "
                    "specific science and prior-art Wishes may wait for relevant sources."
                )
            ),
            **(
                {}
                if research_ready
                else {
                    "next": "Configure the Manager research capability for broad, source-backed Wishes."
                }
            ),
        }
    )
    classic_ready = (
        services is not None and services.binding("classic_rules") is not None
    )
    checks.append(
        {
            "name": "classic-rules",
            "status": "ready" if classic_ready else "needs-attention",
            "detail": (
                "A versioned classic-rules registry is configured."
                if classic_ready
                else "The built-in conformance provider covers checkers only."
            ),
            **(
                {}
                if classic_ready
                else {
                    "next": "Configure independent rules/conformance providers for every classic Alice may select."
                }
            ),
        }
    )
    world_ready = (
        services is not None
        and services.binding("world_reference") is not None
        and services.binding("world_playtest") is not None
    )
    checks.append(
        {
            "name": "little-worlds",
            "status": "ready" if world_ready else "needs-attention",
            "detail": (
                "External isolated World reference and Playtest services are configured."
                if world_ready
                else "Little worlds lack the complete external isolated reference-and-comparison service pair."
            ),
            **(
                {}
                if world_ready
                else {
                    "next": "Configure both world_reference and world_playtest Manager capabilities; local same-user storage is development-only."
                }
            ),
        }
    )

    broker_ready = (
        services is not None
        and services.binding("factory_credentials") is not None
    )
    legacy_factory_ready = bool(os.environ.get("FACTORY_PASSWORD"))
    factory_ready = broker_ready or legacy_factory_ready
    checks.append(
        {
            "name": "factory-page",
            "status": "ready" if factory_ready else "needs-attention",
            "detail": (
                (
                    "A per-inventor Factory credential broker is configured; each account is verified only during its exact handoff."
                    if broker_ready
                    else "A legacy shared Factory password is supplied; it is verified only during the exact handoff."
                )
                if factory_ready
                else "No Manager Factory credential provider is configured; a verified page cannot be created."
            ),
            **(
                {}
                if factory_ready
                else {
                    "next": (
                        "Configure the Manager factory_credentials broker (recommended), "
                        "or set the legacy FACTORY_PASSWORD only in the trusted Manager environment."
                    )
                }
            ),
        }
    )
    delivery_ready = services is not None and services.binding("deliver") is not None
    checks.append(
        {
            "name": "physical-delivery",
            "status": "ready" if delivery_ready else "needs-attention",
            "detail": (
                "A Manager-owned production, QA, packing, and carrier provider is configured."
                if delivery_ready
                else (
                    "No Workshop production, hands-on QA, packing, and carrier "
                    "provider is configured."
                )
            ),
            **(
                {}
                if delivery_ready
                else {
                    "next": (
                        "Connect a Manager-owned Deliver provider before treating a public "
                        "Factory listing as fulfillable."
                    )
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
        "engine_scope": engine_scope,
        "engine_customization_note": (
            "A selected Inventor may replace only its declared custom Make or Playtest after Match."
        ),
        "engine_provenance": (
            engine_provenance.to_dict()
            if engine_provenance is not None
            else None
        ),
    }
    if args.json:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    else:
        for item in checks:
            marker = {
                "ready": "ready",
                "not-probed": "not probed",
                "needs-attention": "needs attention",
            }[item["status"]]
            print("%-18s %s — %s" % (item["name"], marker, item["detail"]))
            if item.get("next"):
                print("  Next: %s" % item["next"])
        if engine_provenance is not None:
            print(
                "Engine provenance: %s (informational aggregate; %s)"
                % (
                    engine_provenance.informational_engine_sha256,
                    engine_scope,
                )
            )
            for component in engine_provenance.components:
                print(
                    "  %-12s %s  provider=%s  stage=%s"
                    % (
                        component.stage.title() + ":",
                        component.state,
                        component.provider_id or "missing",
                        component.stage_sha256,
                    )
                )
        print("Workshop: %s" % receipt["status"])
    return 0 if receipt["status"] == "ready" else 1


def _references(args: argparse.Namespace) -> int:
    """Continue one exact little-worlds Wish with private customer inputs."""

    roots = _catalog_roots(args.root, include_retained=True)
    _, located = _root_for_durable_wish(roots, args.product_id)
    handoff = located.get("handoff")
    if not isinstance(handoff, ManagerAssignmentHandoff):
        raise WorkshopError(
            "private references require the exact saved Manager assignment"
        )
    wish = handoff.wish
    if wish.product_id != args.product_id:
        raise WorkshopError("saved Manager assignment belongs to another Wish")
    card = located["card"]
    if args.references_action == "add":
        if not args.allow_same_user_local_vault:
            raise WorkshopError(
                "the local vault is not isolated from Inventor code running as "
                "the same OS user; use a production reference service, or pass "
                "--allow-same-user-local-vault only for trusted development"
            )
        runtime = located.get("runtime")
        if runtime is None or located.get("product") is None:
            raise WorkshopError(
                "private references can be added after the Wish has a durable Workshop run"
            )
        lease = runtime.active_lease(wish.product_id)
        if lease is not None:
            raise WorkshopError(
                "the Wish is still running; wait for its durable waiting result before adding private references"
            )
        scope = WorldReferenceScope(
            reference_id=args.reference_id,
            subject_kind=args.subject_kind,
            subject=args.subject,
            rights_basis=args.rights_basis,
            allowed_features=tuple(args.allowed_feature),
            excluded_features=tuple(args.excluded_feature),
            reviewer_id=args.reviewer_id,
            verification_method=args.verification_method,
        )
        vault = WorldReferenceVault(
            Path(card.root),
            create=True,
            trust_same_user_processes=True,
        )
        receipt = vault.add(
            wish,
            scope=scope,
            reference_path=args.reference_file,
            consent_path=args.consent_file,
            media_type=args.media_type,
        )
        document = {
            "schema_version": 1,
            "status": "staged-local-development",
            "wish": wish.product_id,
            "reference": receipt.to_dict(),
            "integration_status": {
                "invent": "ready-on-explicit-manager-resume",
                "playtest": "external-isolated-service-required",
            },
        }
        if args.json:
            print(json.dumps(document, indent=2, sort_keys=True))
        else:
            print(
                "Reference %s is staged in the same-user local development vault for %s."
                % (receipt.reference_id, wish.product_id)
            )
            print(
                "Resume with 'workshop resume %s --allow-same-user-local-vault' "
                "to pass only raw-free scope and hashes to shared Invent."
                % wish.product_id
            )
            print(
                "This vault remains readable by same-user Inventor code, and World "
                "Playtest still requires an external isolated service."
            )
        return 0

    if WorldReferenceVault.exists(Path(card.root)):
        receipts = WorldReferenceVault(
            Path(card.root), trust_same_user_processes=True
        ).list(wish)
    else:
        receipts = ()
    document = {
        "schema_version": 1,
        "wish": wish.product_id,
        "references": [receipt.to_dict() for receipt in receipts],
    }
    if args.json:
        print(json.dumps(document, indent=2, sort_keys=True))
    elif receipts:
        for receipt in receipts:
            print(
                "%s  %s  %d bytes  reviewer %s"
                % (
                    receipt.reference_id,
                    receipt.content_sha256,
                    receipt.content_bytes,
                    receipt.reviewer_id,
                )
            )
    else:
        print("No private references are sealed for %s." % wish.product_id)
    return 0


def _wish(args: argparse.Namespace) -> int:
    root = _catalog_roots(args.root)[0]
    objective = " ".join(args.objective)
    wish = Wish.create(
        generate_wish_id(),
        objective,
        context={"source": "workshop-cli"},
    )
    progress = sys.stderr if args.json else sys.stdout
    publication_policy = PublicationPolicy.for_wish(publish=args.publish)
    catalog = discover_inventor_catalog(root)
    pending = PendingWish.create(
        wish,
        publication_policy,
        catalog,
        playtest_rounds=DEFAULT_WISH_PLAYTEST_ROUNDS,
    )
    pending_store = PendingWishStore(catalog.collection)
    match_attempts = MatchAttemptStore(catalog.collection)
    # This fsynced record is the point at which the id becomes customer-visible.
    # No semantic Manager object exists, and therefore no model can be called,
    # until the exact Wish, policy, and catalog identity are durable.
    pending_store.save(pending)
    print("Wish: %s" % wish.product_id, file=progress, flush=True)
    print(
        "Page: after exact verification and physical Deliver, Factory will make "
        "it public and may list it for sale (--draft keeps it private)."
        if args.publish
        else "Page: will remain a private authenticated draft.",
        file=progress,
        flush=True,
    )
    print(
        "Track: %s" % _status_command(wish.product_id, root),
        file=progress,
        flush=True,
    )
    print("Matching your Wish with an Inventor...", file=progress, flush=True)
    assignment = None
    receipt = None
    showed_match = False
    with pending_store.lock(wish.product_id):
        current = pending_store.load(wish.product_id)
        if not isinstance(current, PendingWish) or (
            current.record_sha256 != pending.record_sha256
        ):
            raise WorkshopError("Manager pending Wish changed before Match")
        # An id collision or a non-cooperating writer cannot cause assignment
        # fan-out: recheck the whole catalog while holding the per-Wish lock.
        located = _find_durable_wish(root, wish.product_id)
        if located.get("handoff") is not None:
            raise WorkshopError("this Wish id already has a Manager assignment")
        working_attempt = match_attempts.begin(current)
        try:
            assignment = _match_pending_wish(root, current)
        except WaitingFor as waiting:
            waiting_attempt = match_attempts.record_waiting(
                working_attempt, waiting.needs
            )
            receipt = _pending_match_waiting_receipt(
                current, waiting, root, waiting_attempt
            )
        else:
            # Revalidate the immutable pre-Match bytes after the model returns,
            # then fsync the one selected Inventor handoff before launching it.
            observed = pending_store.load(wish.product_id)
            if not isinstance(observed, PendingWish) or (
                observed.record_sha256 != current.record_sha256
            ):
                raise WorkshopError("Manager pending Wish changed during Match")
            assignment_path = _save_manager_assignment(assignment)
            verified_handoff = _read_saved_handoff(
                assignment_path, assignment.inventor_id
            )
            match_attempts.record_assigned(
                working_attempt,
                verified_handoff.handoff_sha256,
            )
    if assignment is not None:
        # Keep Invent/Make outside the Match lock so read-only status and a later
        # exact resume are never blocked by a long-running child.
        receipt = _start_matched_assignment(
            assignment,
            root,
            publication_policy,
            progress=progress,
        )
        showed_match = True
    if receipt is None:  # pragma: no cover - Match has exactly two typed outcomes
        raise WorkshopError("Match produced no durable outcome")
    if args.json:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    else:
        _print_wish_receipt(
            receipt,
            root=root,
            show_wish=False,
            show_match=not showed_match,
        )
    return _wish_exit_code(receipt, strict=getattr(args, "strict", False))


def _wish_exit_code(receipt: Mapping[str, Any], *, strict: bool) -> int:
    """Translate one truthful Wish terminal state into automation semantics."""

    if not isinstance(receipt, Mapping) or type(strict) is not bool:
        raise WorkshopError("Wish exit status requires a typed receipt and strict flag")
    return int(strict and receipt.get("status") in ("waiting", "stopped"))


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
            "invent the toy, make it, Playtest it, physically Deliver it, and only "
            "then publish its verified Factory page when authorized."
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
        help="wish for a toy; matching and the Deliver-gated page flow are automatic",
        description=(
            "Say what you wish existed. The Manager reads Inventor Tastes, chooses "
            "one exact match, and starts the shared Workshop. The run includes up to "
            "four AI Playtest-to-Make improvement passes. Public visibility is authorized "
            "by default, but the verified Factory draft remains private until exact "
            "production, QA, packing, and carrier evidence completes physical Deliver."
        ),
        epilog=(
            "Prerequisites: a discoverable Inventor catalog, an installed and signed-in "
            "Codex CLI, the shared CAD/printability runtime, and Manager Factory "
            "credential and physical Deliver providers. Run 'workshop doctor' first. A "
            "truthful waiting or stopped "
            "result exits 0; use --strict when automation should exit 1 unless the "
            "Workshop reaches its successful terminal state."
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
        help="exit 1 instead of 0 when the Workshop truthfully waits or stops",
    )
    publication = wish.add_mutually_exclusive_group()
    publication.add_argument(
        "--publish",
        dest="publish",
        action="store_true",
        help=(
            "authorize the exact authenticated page to become public after Deliver "
            "(default); Factory may then list it at a platform-estimated price"
        ),
    )
    publication.add_argument(
        "--draft",
        dest="publish",
        action="store_false",
        help=(
            "keep the exact authenticated page private, including after physical "
            "Deliver; do not make it public"
        ),
    )
    wish.set_defaults(handler=_wish, publish=True)

    batch = subcommands.add_parser(
        "batch",
        help="durably stage and run a bounded file of Wishes",
        description=(
            "Save every Wish and its full-TASTE catalog snapshot before any model "
            "runs, then supervise bounded parallel continuations. Mass visibility "
            "must be chosen explicitly."
        ),
    )
    batch_commands = batch.add_subparsers(
        dest="batch_command", required=True, metavar="ACTION"
    )
    batch_submit = batch_commands.add_parser(
        "submit",
        help="stage every Wish before optionally starting workers",
    )
    batch_submit.add_argument("file", type=Path, metavar="WISHES")
    batch_submit.add_argument(
        "--format",
        choices=("lines", "jsonl"),
        default="lines",
        help="one Wish per line, or strict key/wish/visibility JSONL",
    )
    batch_visibility = batch_submit.add_mutually_exclusive_group(required=True)
    batch_visibility.add_argument(
        "--draft",
        dest="publish",
        action="store_false",
        help="bind every row to private-draft visibility",
    )
    batch_visibility.add_argument(
        "--publish",
        dest="publish",
        action="store_true",
        help=(
            "authorize every row for public visibility after physical Deliver; "
            "Factory may then list it for sale"
        ),
    )
    batch_submit.add_argument(
        "--run",
        action="store_true",
        help="start resumable items after all plans and PendingWishes are durable",
    )
    batch_submit.add_argument(
        "--concurrency",
        type=_batch_concurrency,
        default=1,
        metavar="N",
        help="maximum trusted Manager workers, from 1 to 8 (default: 1)",
    )
    batch_submit.add_argument(
        "--playtest-rounds",
        type=int,
        choices=range(1, 101),
        default=4,
        metavar="N",
        help="maximum Make/Playtest rounds per Wish (default: 4)",
    )
    batch_submit.add_argument("--root", type=Path)
    batch_submit.add_argument("--json", action="store_true")
    batch_submit.set_defaults(handler=_batch_submit)

    batch_status = batch_commands.add_parser(
        "status", help="read every item from durable Workshop state"
    )
    batch_status.add_argument("batch_id", metavar="BATCH_ID")
    batch_status.add_argument("--root", type=Path)
    batch_status.add_argument("--json", action="store_true")
    batch_status.set_defaults(handler=_batch_status)

    batch_resume = batch_commands.add_parser(
        "resume",
        help="run each currently resumable item at most once in this invocation",
    )
    batch_resume.add_argument("batch_id", metavar="BATCH_ID")
    batch_resume.add_argument(
        "--concurrency",
        type=_batch_concurrency,
        default=1,
        metavar="N",
        help="maximum trusted Manager workers, from 1 to 8 (default: 1)",
    )
    batch_resume.add_argument(
        "--strict",
        action="store_true",
        help=(
            "exit 1 unless every Wish is physically delivered and every "
            "public-authorized page is live"
        ),
    )
    batch_resume.add_argument("--root", type=Path)
    batch_resume.add_argument("--json", action="store_true")
    batch_resume.set_defaults(handler=_batch_resume)

    status = subcommands.add_parser(
        "status",
        help="inspect the durable status of one Wish",
        description=(
            "Find a Manager-owned Wish while it is matching, or its exact Inventor "
            "assignment and durable event chain afterward. This command does not "
            "change Wish records and never calls a model or Factory."
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

    reconcile = subcommands.add_parser(
        "reconcile",
        help="read back one ambiguous Deliver attempt without retrying it",
        description=(
            "Use the exact persisted Manager fulfillment provider and attempt id "
            "to perform authenticated GET-only readback. This command never calls "
            "Deliver preflight or fulfillment, never rotates providers, and never "
            "reruns an earlier Workshop stage."
        ),
    )
    reconcile.add_argument("product_id", help="Wish id working at Deliver")
    reconcile.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Workshop checkout or inventor collection (default: find the exact retained run)",
    )
    reconcile.add_argument(
        "--json", action="store_true", help="emit one JSON reconciliation receipt"
    )
    reconcile.set_defaults(handler=_reconcile)

    resume = subcommands.add_parser(
        "resume",
        help="continue an exact saved Workshop stage",
        description=(
            "Retry Match for the same id when a Wish is still matching, or continue the "
            "exact Manager assignment saved afterward. Invent restarts from the Wish "
            "boundary; Make reuses the accepted Invented record; Playtest reuses the "
            "exact Made checkpoint; Instructions reuses its approved Make and Playtest "
            "checkpoint. Completed stages are never rerun. Legacy runs without the "
            "required checkpoint fail with a concrete next action. A bare resume "
            "inherits the Wish's saved draft/public policy; only explicit --publish can "
            "upgrade a saved draft. --strict changes only the process exit code: a "
            "truthful waiting or stopped continuation exits 1."
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
    resume.add_argument(
        "--strict",
        action="store_true",
        help=(
            "exit 1 instead of 0 when the resumed Workshop truthfully waits or stops"
        ),
    )
    resume.add_argument(
        "--allow-same-user-local-vault",
        action="store_true",
        help=(
            "development only: let the Manager read the local reference vault; "
            "same-user Inventor code can also read those files"
        ),
    )
    resume_publication = resume.add_mutually_exclusive_group()
    resume_publication.add_argument(
        "--publish",
        dest="publish",
        action="store_true",
        help=(
            "explicitly and durably upgrade a saved draft to public; the exact "
            "verified Factory page may become visible to anyone"
        ),
    )
    resume_publication.add_argument(
        "--draft",
        dest="publish",
        action="store_false",
        help=(
            "confirm draft-only visibility; cannot downgrade a Wish that already "
            "authorizes public visibility"
        ),
    )
    resume.set_defaults(handler=_resume, publish=None)

    references = subcommands.add_parser(
        "references",
        help="stage Wish-bound little-world reference inputs",
        description=(
            "Stage or inspect reference material for a saved little-worlds Wish. "
            "The current 0600 local backend is development-only and is not isolated "
            "from Inventor code running as the same OS user."
        ),
    )
    reference_commands = references.add_subparsers(
        dest="references_action", required=True, metavar="ACTION"
    )
    reference_add = reference_commands.add_parser(
        "add",
        help="stage one reference and customer-supplied attestation record",
        description=(
            "Seal one immutable reference id for an exact, already-started "
            "little-worlds Wish. This stages the customer's declaration; it does "
            "not independently prove legal rights or likeness recognition."
        ),
    )
    reference_add.add_argument("product_id", help="Wish id printed by 'workshop wish'")
    reference_add.add_argument("reference_id", help="stable lowercase id for this attachment")
    reference_add.add_argument("reference_file", type=Path, help="private JPEG, PNG, or WebP file")
    reference_add.add_argument(
        "--consent-file",
        type=Path,
        required=True,
        help="customer-created attestation/rights record (never generated by the Workshop)",
    )
    reference_add.add_argument(
        "--media-type",
        choices=tuple(sorted(SUPPORTED_WORLD_MEDIA_TYPES)),
        required=True,
        help="declared media type of the reference bytes",
    )
    reference_add.add_argument(
        "--subject-kind",
        choices=tuple(sorted(SUPPORTED_WORLD_SUBJECT_KINDS)),
        required=True,
        help="supported declared subject class; celebrity, franchise, and third-party likenesses are rejected",
    )
    reference_add.add_argument(
        "--subject", required=True, help="bounded subject description used by Invent"
    )
    reference_add.add_argument(
        "--rights-basis",
        required=True,
        help="customer's declared ownership or authorization basis; not independently verified",
    )
    reference_add.add_argument(
        "--allow",
        dest="allowed_feature",
        action="append",
        required=True,
        metavar="FEATURE",
        help="one feature allowed by the customer-supplied scope record (repeatable)",
    )
    reference_add.add_argument(
        "--exclude",
        dest="excluded_feature",
        action="append",
        default=[],
        metavar="FEATURE",
        help="one feature excluded by the customer-supplied scope record (repeatable)",
    )
    reference_add.add_argument(
        "--reviewer-id",
        required=True,
        help="claimed stable customer/order reviewer id for this exact scope",
    )
    reference_add.add_argument(
        "--verification-method",
        choices=tuple(sorted(SUPPORTED_WORLD_CONSENT_METHODS)),
        default="customer-supplied-attestation-record",
        help="declared record type; the local vault does not authenticate the customer or legal rights",
    )
    reference_add.add_argument(
        "--allow-same-user-local-vault",
        action="store_true",
        help=(
            "development only: acknowledge that local 0600 files are readable "
            "by Inventor code running as the same OS user"
        ),
    )
    reference_add.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Workshop checkout or retained run containing the exact Wish",
    )
    reference_add.add_argument("--json", action="store_true", help="emit a raw-free JSON receipt")
    reference_add.set_defaults(handler=_references)

    reference_list = reference_commands.add_parser(
        "list", help="list raw-free receipts for one exact Wish"
    )
    reference_list.add_argument("product_id", help="Wish id printed by 'workshop wish'")
    reference_list.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Workshop checkout or retained run containing the exact Wish",
    )
    reference_list.add_argument("--json", action="store_true", help="emit raw-free JSON")
    reference_list.set_defaults(handler=_references)

    doctor = subcommands.add_parser(
        "doctor",
        help="check prerequisites without exposing credential values",
        description=(
            "Check the Inventor catalog, Codex sign-in and model policy, shared "
            "CAD/printability runtime, Factory authentication, and physical Deliver "
            "readiness. By default no model, product import, publication, or delivery "
            "action is performed. --deep spends one small selected Manager-model call to prove the exact "
            "tool-free structured runtime; it still creates no product or external effect."
        ),
    )
    doctor.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Workshop checkout or inventor collection (default: auto-detected)",
    )
    doctor.add_argument("--json", action="store_true", help="emit one JSON preflight receipt")
    doctor.add_argument(
        "--deep",
        action="store_true",
        help=(
            "spend one small selected Manager-model call to prove the exact structured-model boundary; "
            "does not create, import, publish, or deliver a product"
        ),
    )
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
    finally:
        # A normal CLI process executes one command. Tests and embedded callers
        # may execute several; never retain live provider objects across those
        # command boundaries or silently miss a rotated configuration.
        _cached_manager_services.cache_clear()

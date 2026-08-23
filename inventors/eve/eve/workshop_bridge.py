"""Eve's deliberately small bridge into the Inventor Workshop.

Eve remains the authority for her creative queue, checks, and reward ledger.
The Workshop owns two facts that must not be reinvented here:

* content-addressed artifact seals and canonical Packs; and
* the durable Sender that fences a Shop Door's non-idempotent import.

The SQLite product in this module is therefore only a send identity. It
is not a second copy of Eve's game lifecycle and it never advances Eve's queue.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional

import inventor_workshop.artifacts as workshop_artifacts
from inventor_workshop import (
    Clockwork,
    HttpResponse,
    Sender,
    ShopDoor,
    inspect_pack,
    pack_artifact,
    seal_artifact,
)
from inventor_workshop.errors import AmbiguousSendError, ContractError


Transport = Callable[
    [str, str, Mapping[str, str], Optional[bytes], int], HttpResponse
]


ARTIFACT_MANIFEST_NAME = "_inventor-artifact.json"
SEND_PROJECTION_NAME = "_send.json"
CLOCKWORK_STATE_NAME = "clockwork.sqlite3"
PACK_DIRECTORY = "packs"

# Durable compatibility names. They continue an existing effect history in
# place; all fresh Eve work emits only the canonical names above.
LEGACY_SEND_PROJECTION_NAMES = (
    "_workshop-launch.json",
    "_foundation-launch.json",
    "_core-publication.json",
)
LEGACY_STATE_NAMES = (
    "inventor-workshop.sqlite3",
    "inventor-foundation.sqlite3",
    "inventor-core.sqlite3",
)
LEGACY_PACK_DIRECTORIES = ("launch-packets", "publication-packets")

# Compatibility constants for existing Eve extensions. Canonical code below
# uses SEND/CLOCKWORK/PACK exclusively.
LAUNCH_PROJECTION_NAME = SEND_PROJECTION_NAME
WORKSHOP_STATE_NAME = CLOCKWORK_STATE_NAME
LAUNCH_PACKET_DIRECTORY = PACK_DIRECTORY
LEGACY_LAUNCH_PROJECTION_NAME = "_core-publication.json"
LEGACY_STATE_NAME = "inventor-core.sqlite3"
LEGACY_PACKET_DIRECTORY = "publication-packets"
_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,99}$")


def validate_slug(slug: str) -> str:
    if not isinstance(slug, str) or not _SLUG.fullmatch(slug):
        raise ContractError(
            "Eve send slug must be 1..100 lowercase letters, digits, or hyphens"
        )
    return slug


def _project_payload(slug: str, title: Optional[str] = None) -> str:
    return (
        json.dumps(
            {
                "id": "eve-%s"
                % hashlib.sha256(slug.encode("utf-8")).hexdigest()[:16],
                "name": str(title or slug.replace("-", " ").title())[:120],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def _ensure_project_manifest(
    game_dir: Path, slug: str, title: Optional[str] = None
) -> Path:
    """Create the deterministic Shop Door project manifest when absent."""
    project = game_dir / "project.json"
    if os.path.lexists(str(project)):
        metadata = project.lstat()
        if project.is_symlink() or not stat.S_ISREG(metadata.st_mode):
            raise ContractError("Eve project.json must be a non-symlink regular file")
        return project
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(str(project), flags, 0o644)
    except OSError as exc:
        raise ContractError("cannot create Eve project.json safely") from exc
    try:
        payload = _project_payload(slug, title).encode("utf-8")
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("short write while creating Eve project.json")
            view = view[written:]
        os.fsync(descriptor)
    except OSError as exc:
        raise ContractError("cannot write Eve project.json safely") from exc
    finally:
        os.close(descriptor)
    return project


def snapshot_built_game(
    game_dir: Path, *, title: Optional[str] = None
) -> Dict[str, Any]:
    """Seal exact artifact bytes after Eve's Make stage finishes.

    The manifest filename is reserved by Workshop and excluded from later hashes,
    so taking the snapshot repeatedly does not create a self-referential tree.
    This is evidence for Eve's existing print-stage workflow; it does not move
    the game in either Eve's queue or Workshop's lifecycle graph. Make
    also writes the deterministic ``project.json`` required by the current
    Shop Door, so this identity is the same one Sender later sends.
    """
    game_dir = Path(game_dir)
    if not game_dir.is_dir() or game_dir.is_symlink():
        raise ContractError("Eve game directory must be a non-symlink directory")
    slug = validate_slug(game_dir.name)
    _ensure_project_manifest(game_dir, slug, title)
    manifest = seal_artifact(
        game_dir,
        extra_excludes=(
            "sent.json",
            "published.json",
            SEND_PROJECTION_NAME,
            *LEGACY_SEND_PROJECTION_NAMES,
        ),
        created_at="content-addressed",
    )
    manifest.write(game_dir / ARTIFACT_MANIFEST_NAME)
    return manifest.to_dict()


def _api_base(configured_base: str) -> str:
    base = str(configured_base or "").rstrip("/")
    if base.endswith("/api/v1"):
        return base
    return base + "/api/v1"


def _single_durable_path(
    root: Path, canonical_name: str, legacy_names, label: str
) -> Path:
    candidates = [root / canonical_name] + [root / name for name in legacy_names]
    existing = [path for path in candidates if os.path.lexists(str(path))]
    if len(existing) > 1:
        raise ContractError(
            "multiple Eve %s paths exist (%s); reconcile them before Eve can send"
            % (label, ", ".join(path.name for path in existing))
        )
    return existing[0] if existing else candidates[0]


def clockwork_path(cfg) -> Path:
    """Choose one durable Clockwork database without splitting send history."""

    return _single_durable_path(
        Path(cfg.root) / "state",
        CLOCKWORK_STATE_NAME,
        LEGACY_STATE_NAMES,
        "Clockwork state",
    )


def workshop_state_path(cfg) -> Path:
    """Compatibility spelling for :func:`clockwork_path`."""

    return clockwork_path(cfg)


def _clockwork(cfg) -> Clockwork:
    return Clockwork(clockwork_path(cfg))


def _pack_root(cfg) -> Path:
    """Continue one existing Pack directory or select the canonical directory."""

    return _single_durable_path(
        Path(cfg.root) / "state",
        PACK_DIRECTORY,
        LEGACY_PACK_DIRECTORIES,
        "Pack directory",
    )


def _product_id(slug: str) -> str:
    """One stable, bounded send identity per logical Eve game."""
    slug = validate_slug(slug)
    slug_identity = hashlib.sha256(slug.encode("utf-8")).hexdigest()[:16]
    return "eve:%s" % slug_identity


def _ensure_send_product(
    clockwork: Clockwork, slug: str, artifact_sha256: str
) -> str:
    """Bind one Eve game to exact bytes without mirroring Eve's stages.

    Product ids are stable across artifact changes. Until Workshop exposes an
    atomic logical-product artifact revision API, changed bytes require a new
    Eve slug; this prevents an unresolved import from being bypassed by merely
    editing the source tree.
    """
    product_id = _product_id(slug)
    try:
        product = clockwork.get_product(product_id)
    except KeyError:
        clockwork.register_product(
            product_id,
            "send-ready",
            metadata={"inventor": "eve", "slug": slug},
            artifact_sha256=artifact_sha256,
        )
        return product_id
    if product.get("artifact_sha256") != artifact_sha256:
        prior = clockwork.latest_publish_intent(product_id)
        if prior is not None and prior.get("state") in (
            "planned",
            "sending",
            "unknown",
            "publishing",
            "live_unknown",
        ):
            raise AmbiguousSendError(
                "Eve game %s has unresolved Workshop send intent %s in state %s; changed "
                "bytes cannot bypass it"
                % (slug, prior.get("id"), prior.get("state"))
            )
        raise ContractError(
            "Eve game %s is already bound to different artifact bytes; use a "
            "new slug for a corrected send" % slug
        )
    return product_id


def _copy_pack_tree(game_dir: Path, destination: Path) -> None:
    """Stage regular files through no-follow, nonblocking descriptors.

    ``shutil.copytree`` can follow a raced path or block forever when an agent
    leaves a FIFO behind. This walk holds each source directory by descriptor,
    rejects every symlink/special node before reading, and verifies each inode
    and size after the copy.
    """
    try:
        root_identity = game_dir.lstat()
    except OSError as exc:
        raise ContractError("Eve game directory is unavailable") from exc
    if not stat.S_ISDIR(root_identity.st_mode) or game_dir.is_symlink():
        raise ContractError("Eve game directory must be a non-symlink directory")
    if not hasattr(os, "O_DIRECTORY") or os.open not in getattr(os, "supports_dir_fd", set()):
        raise ContractError("this platform cannot safely stage Eve Pack files")
    read_flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    directory_flags = read_flags | os.O_DIRECTORY
    try:
        root_descriptor = os.open(str(game_dir), directory_flags)
    except OSError as exc:
        raise ContractError("cannot safely open Eve game directory") from exc
    destination.mkdir(mode=0o700)
    counters = {"files": 0, "bytes": 0}

    def safe_name(name: str, relative: str) -> None:
        if (
            not name
            or name in (".", "..")
            or "/" in name
            or "\\" in name
            or any(ord(character) < 32 or ord(character) == 127 for character in name)
        ):
            raise ContractError("unsafe Eve Pack path: %s" % relative)

    def copy_directory(source_descriptor: int, target: Path, prefix: str, depth: int) -> None:
        if depth > 64:
            raise ContractError("Eve Pack tree exceeds 64 directory levels")
        try:
            with os.scandir(source_descriptor) as iterator:
                entries = sorted(iterator, key=lambda item: item.name)
        except OSError as exc:
            raise ContractError("cannot enumerate Eve Pack tree") from exc
        names_before = [entry.name for entry in entries]
        for entry in entries:
            relative = "%s/%s" % (prefix, entry.name) if prefix else entry.name
            safe_name(entry.name, relative)
            try:
                expected = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise ContractError("cannot inspect Eve Pack path %s" % relative) from exc
            if stat.S_ISLNK(expected.st_mode):
                raise ContractError("Eve Pack tree contains symlink: %s" % relative)
            if stat.S_ISDIR(expected.st_mode):
                try:
                    child_descriptor = os.open(
                        entry.name, directory_flags, dir_fd=source_descriptor
                    )
                except OSError as exc:
                    raise ContractError(
                        "cannot safely open Eve Pack directory %s" % relative
                    ) from exc
                try:
                    opened = os.fstat(child_descriptor)
                    if (
                        not stat.S_ISDIR(opened.st_mode)
                        or (opened.st_dev, opened.st_ino)
                        != (expected.st_dev, expected.st_ino)
                    ):
                        raise ContractError(
                            "Eve Pack directory changed while staging: %s" % relative
                        )
                    child_target = target / entry.name
                    child_target.mkdir(mode=0o700)
                    copy_directory(child_descriptor, child_target, relative, depth + 1)
                finally:
                    os.close(child_descriptor)
                continue
            if not stat.S_ISREG(expected.st_mode):
                raise ContractError(
                    "Eve Pack tree contains a special file: %s" % relative
                )
            counters["files"] += 1
            if counters["files"] > workshop_artifacts.MAX_ENTRIES:
                raise ContractError("Eve Pack tree has too many files")
            if expected.st_size > workshop_artifacts.MAX_FILE_BYTES:
                raise ContractError("Eve Pack file is too large: %s" % relative)
            source_file = None
            target_file = None
            try:
                source_file = os.open(entry.name, read_flags, dir_fd=source_descriptor)
                opened = os.fstat(source_file)
                if (
                    not stat.S_ISREG(opened.st_mode)
                    or (opened.st_dev, opened.st_ino)
                    != (expected.st_dev, expected.st_ino)
                ):
                    raise ContractError(
                        "Eve Pack file changed while opening: %s" % relative
                    )
                target_file = os.open(
                    str(target / entry.name),
                    os.O_WRONLY
                    | os.O_CREAT
                    | os.O_EXCL
                    | getattr(os, "O_NOFOLLOW", 0),
                    0o600,
                )
                copied = 0
                while True:
                    chunk = os.read(source_file, 1024 * 1024)
                    if not chunk:
                        break
                    copied += len(chunk)
                    if copied > workshop_artifacts.MAX_FILE_BYTES:
                        raise ContractError(
                            "Eve Pack file grew past its limit: %s" % relative
                        )
                    view = memoryview(chunk)
                    while view:
                        written = os.write(target_file, view)
                        if written <= 0:
                            raise OSError("short write while staging Pack")
                        view = view[written:]
                after = os.fstat(source_file)
                if (
                    copied != opened.st_size
                    or after.st_size != opened.st_size
                    or after.st_mtime_ns != opened.st_mtime_ns
                    or (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino)
                ):
                    raise ContractError(
                        "Eve Pack file changed while staging: %s" % relative
                    )
                counters["bytes"] += copied
                if counters["bytes"] > workshop_artifacts.MAX_EXPANDED_BYTES:
                    raise ContractError("Eve Pack tree is too large")
                os.fchmod(target_file, 0o755 if opened.st_mode & stat.S_IXUSR else 0o644)
            except OSError as exc:
                raise ContractError(
                    "cannot safely stage Eve Pack file %s" % relative
                ) from exc
            finally:
                if target_file is not None:
                    os.close(target_file)
                if source_file is not None:
                    os.close(source_file)
        try:
            with os.scandir(source_descriptor) as iterator:
                names_after = sorted(entry.name for entry in iterator)
        except OSError as exc:
            raise ContractError("cannot recheck Eve Pack tree") from exc
        if names_before != names_after:
            raise ContractError("Eve Pack tree changed while staging")

    try:
        opened_root = os.fstat(root_descriptor)
        if (opened_root.st_dev, opened_root.st_ino) != (
            root_identity.st_dev,
            root_identity.st_ino,
        ):
            raise ContractError("Eve game directory changed while opening")
        copy_directory(root_descriptor, destination, "", 0)
    finally:
        os.close(root_descriptor)


def build_pack(
    cfg, game_dir: Path, slug: str, title: Optional[str] = None
) -> Dict[str, Any]:
    """Build and retain one immutable canonical Pack from safe staged bytes.

    The current Shop Door needs a root ``project.json``. Eve's Make stage
    writes it into new selected artifacts; this staging guard also supplies it
    for a historical source that has not yet crossed the Workshop boundary.
    Eve's queue is never rewritten here.
    """
    slug = validate_slug(slug)
    game_dir = Path(game_dir)
    pack_root = _pack_root(cfg)
    pack_root.mkdir(parents=True, mode=0o700, exist_ok=True)
    pack_root_metadata = pack_root.lstat()
    if not stat.S_ISDIR(pack_root_metadata.st_mode) or pack_root.is_symlink():
        raise ContractError("Eve Pack root must be a non-symlink directory")
    os.chmod(str(pack_root), 0o700)
    with tempfile.TemporaryDirectory(prefix=".eve-pack-", dir=str(pack_root)) as temporary:
        workspace = Path(temporary)
        staged_game = workspace / "game"
        _copy_pack_tree(game_dir, staged_game)
        _ensure_project_manifest(staged_game, slug, title)
        candidate = workspace / "pack.zip"
        packed = pack_artifact(
            staged_game,
            candidate,
            extra_excludes=(
                "sent.json",
                "published.json",
                SEND_PROJECTION_NAME,
                *LEGACY_SEND_PROJECTION_NAMES,
            ),
        )
        destination = pack_root / (
            "eve-%s-%s.zip"
            % (
                hashlib.sha256(slug.encode("utf-8")).hexdigest()[:16],
                packed.pack_sha256,
            )
        )
        if os.path.lexists(str(destination)):
            inspection = inspect_pack(destination)
            if (
                inspection.pack_sha256 != packed.pack_sha256
                or inspection.artifact_sha256 != packed.artifact_sha256
            ):
                raise ContractError("retained Eve Pack has changed bytes")
        else:
            os.replace(candidate, destination)
            os.chmod(str(destination), 0o600)
        inspection = inspect_pack(destination)
        if (
            inspection.pack_sha256 != packed.pack_sha256
            or inspection.artifact_sha256 != packed.artifact_sha256
        ):
            raise ContractError("retained Eve Pack identity is inconsistent")
        return {
            "path": str(destination),
            "bytes": inspection.bytes,
            "entries": inspection.entries,
            "pack_sha256": inspection.pack_sha256,
            "artifact_sha256": inspection.artifact_sha256,
            # Workshop 0.2 compatibility spelling.
            "packet_sha256": inspection.pack_sha256,
        }


def send_draft(
    cfg,
    game,
    metadata: Mapping[str, Any],
    *,
    transport: Optional[Transport] = None,
) -> Dict[str, Any]:
    """Send one exact Eve Pack through Workshop's durable Sender."""
    game_dir = Path(cfg.games_dir) / game.slug
    # Panel and playtest add evidence after the CAD build. Refresh the Make
    # snapshot at the final selection point, then require the safely staged
    # Pack to carry those exact bytes. A raced source tree fails locally before
    # a durable intent or Shop Door effect can exist.
    selected = snapshot_built_game(
        game_dir, title=game.title or game.slug
    )
    packed = build_pack(
        cfg, game_dir, game.slug, title=game.title or game.slug
    )
    if packed["artifact_sha256"] != selected["artifact_sha256"]:
        raise ContractError(
            "Eve artifact changed between Make selection and Pack staging"
        )
    clockwork = _clockwork(cfg)
    product_id = _ensure_send_product(
        clockwork, game.slug, packed["artifact_sha256"]
    )
    api_base = _api_base(cfg.shop_api)
    client_options: Dict[str, Any] = {
        "api_base": api_base,
        # The configured deployment is pinned as the sole allowed origin.
        "allowed_origins": (api_base,),
    }
    if transport is not None:
        client_options["transport"] = transport
    shop = ShopDoor(cfg.shop_token, **client_options)
    sender = Sender(clockwork, shop, cfg.shop_owner_id)
    outcome = sender.send_draft(
        product_id, Path(packed["path"]), metadata
    )
    intent = clockwork.get_publish_intent(outcome.intent_id)
    stamp = outcome.stamp.to_dict()
    return {
        "product_id": product_id,
        "send_id": outcome.intent_id,
        "stamp": stamp,
        "send_state": intent["state"],
        "pack": packed,
        "clockwork_state": str(clockwork.path),
        # Compatibility keys for older Eve callers and durable projections.
        "intent_id": outcome.intent_id,
        "receipt": stamp,
        "intent_state": intent["state"],
        "packet": packed,
        "workshop_state": str(clockwork.path),
    }


def send_state(cfg, slug: str) -> Optional[Dict[str, Any]]:
    """Return Eve's current Sender state for an operator-facing error."""
    path = clockwork_path(cfg)
    if not os.path.lexists(str(path)):
        return None
    clockwork = Clockwork(path)
    return clockwork.latest_publish_intent(_product_id(slug))


# Tiny source-compatibility wrappers. New Eve code uses Pack and Send names.
def build_launch_packet(
    cfg, game_dir: Path, slug: str, title: Optional[str] = None
) -> Dict[str, Any]:
    return build_pack(cfg, game_dir, slug, title)


def launch_draft(
    cfg,
    game,
    metadata: Mapping[str, Any],
    *,
    transport: Optional[Transport] = None,
) -> Dict[str, Any]:
    return send_draft(cfg, game, metadata, transport=transport)


def launch_state(cfg, slug: str) -> Optional[Dict[str, Any]]:
    return send_state(cfg, slug)

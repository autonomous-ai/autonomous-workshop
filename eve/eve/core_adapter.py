"""Eve's deliberately small boundary to the shared inventor core.

Eve remains the authority for her creative queue, gates, and reward ledger.
The shared core owns two infrastructure facts that must not be reinvented here:

* content-addressed artifact manifests / canonical Panda upload packets; and
* the durable publication outbox that fences Panda's non-idempotent import.

The SQLite product in this module is therefore only a publication identity. It
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
from typing import Any, Dict, Mapping, Optional

import inventor_core.artifacts as core_artifacts
from inventor_core.errors import AmbiguousPublishError, ContractError
from inventor_core.panda import (
    PandaClient,
    PandaPublicationCoordinator,
    Transport,
    inspect_publish_packet,
)
from inventor_core.store import InventorStore


CORE_MANIFEST_NAME = "_inventor-artifact.json"
CORE_PUBLICATION_PROJECTION = "_core-publication.json"
CORE_STATE_NAME = "inventor-core.sqlite3"
_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,99}$")


def validate_slug(slug: str) -> str:
    if not isinstance(slug, str) or not _SLUG.fullmatch(slug):
        raise ContractError(
            "Eve publication slug must be 1..100 lowercase letters, digits, or hyphens"
        )
    return slug


def snapshot_built_game(game_dir: Path) -> Dict[str, Any]:
    """Write a core artifact manifest after Eve's CAD builder finishes.

    The manifest filename is reserved by core and excluded from later hashes,
    so taking the snapshot repeatedly does not create a self-referential tree.
    This is evidence for Eve's existing print-stage workflow; it does not move
    the game in either Eve's queue or core's lifecycle graph.
    """
    game_dir = Path(game_dir)
    if not game_dir.is_dir() or game_dir.is_symlink():
        raise ContractError("Eve game directory must be a non-symlink directory")
    manifest = core_artifacts.build_artifact_manifest(
        game_dir, created_at="content-addressed"
    )
    manifest.write(game_dir / CORE_MANIFEST_NAME)
    return manifest.to_dict()


def _api_base(configured_base: str) -> str:
    base = str(configured_base or "").rstrip("/")
    if base.endswith("/api/v1"):
        return base
    return base + "/api/v1"


def _publication_store(cfg) -> InventorStore:
    return InventorStore(Path(cfg.root) / "state" / CORE_STATE_NAME)


def _product_id(slug: str) -> str:
    """One stable, bounded publication identity per logical Eve game."""
    slug = validate_slug(slug)
    slug_identity = hashlib.sha256(slug.encode("utf-8")).hexdigest()[:16]
    return "eve:%s" % slug_identity


def _ensure_publication_product(
    store: InventorStore, slug: str, artifact_sha256: str
) -> str:
    """Bind one Eve game to exact bytes without mirroring Eve's stages.

    Product ids are stable across artifact changes. Until core exposes an
    atomic logical-product artifact revision API, changed bytes require a new
    Eve slug; this prevents an unresolved import from being bypassed by merely
    editing the source tree.
    """
    product_id = _product_id(slug)
    try:
        product = store.get_product(product_id)
    except KeyError:
        store.register_product(
            product_id,
            "publication-ready",
            metadata={"inventor": "eve", "slug": slug},
            artifact_sha256=artifact_sha256,
        )
        return product_id
    if product.get("artifact_sha256") != artifact_sha256:
        prior = store.latest_publish_intent(product_id)
        if prior is not None and prior.get("state") in (
            "planned",
            "sending",
            "unknown",
            "publishing",
            "live_unknown",
        ):
            raise AmbiguousPublishError(
                "Eve game %s has unresolved core intent %s in state %s; changed "
                "bytes cannot bypass it"
                % (slug, prior.get("id"), prior.get("state"))
            )
        raise ContractError(
            "Eve game %s is already bound to different artifact bytes; use a "
            "new slug for a corrected publication version" % slug
        )
    return product_id


def _copy_publication_tree(game_dir: Path, destination: Path) -> None:
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
        raise ContractError("this platform cannot safely stage Eve publication files")
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
            raise ContractError("unsafe Eve publication path: %s" % relative)

    def copy_directory(source_descriptor: int, target: Path, prefix: str, depth: int) -> None:
        if depth > 64:
            raise ContractError("Eve publication tree exceeds 64 directory levels")
        try:
            with os.scandir(source_descriptor) as iterator:
                entries = sorted(iterator, key=lambda item: item.name)
        except OSError as exc:
            raise ContractError("cannot enumerate Eve publication tree") from exc
        names_before = [entry.name for entry in entries]
        for entry in entries:
            relative = "%s/%s" % (prefix, entry.name) if prefix else entry.name
            safe_name(entry.name, relative)
            try:
                expected = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise ContractError("cannot inspect Eve publication path %s" % relative) from exc
            if stat.S_ISLNK(expected.st_mode):
                raise ContractError("Eve publication tree contains symlink: %s" % relative)
            if stat.S_ISDIR(expected.st_mode):
                try:
                    child_descriptor = os.open(
                        entry.name, directory_flags, dir_fd=source_descriptor
                    )
                except OSError as exc:
                    raise ContractError(
                        "cannot safely open Eve publication directory %s" % relative
                    ) from exc
                try:
                    opened = os.fstat(child_descriptor)
                    if (
                        not stat.S_ISDIR(opened.st_mode)
                        or (opened.st_dev, opened.st_ino)
                        != (expected.st_dev, expected.st_ino)
                    ):
                        raise ContractError(
                            "Eve publication directory changed while staging: %s" % relative
                        )
                    child_target = target / entry.name
                    child_target.mkdir(mode=0o700)
                    copy_directory(child_descriptor, child_target, relative, depth + 1)
                finally:
                    os.close(child_descriptor)
                continue
            if not stat.S_ISREG(expected.st_mode):
                raise ContractError(
                    "Eve publication tree contains a special file: %s" % relative
                )
            counters["files"] += 1
            if counters["files"] > core_artifacts.MAX_ENTRIES:
                raise ContractError("Eve publication tree has too many files")
            if expected.st_size > core_artifacts.MAX_FILE_BYTES:
                raise ContractError("Eve publication file is too large: %s" % relative)
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
                        "Eve publication file changed while opening: %s" % relative
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
                    if copied > core_artifacts.MAX_FILE_BYTES:
                        raise ContractError(
                            "Eve publication file grew past its limit: %s" % relative
                        )
                    view = memoryview(chunk)
                    while view:
                        written = os.write(target_file, view)
                        if written <= 0:
                            raise OSError("short write while staging publication")
                        view = view[written:]
                after = os.fstat(source_file)
                if (
                    copied != opened.st_size
                    or after.st_size != opened.st_size
                    or after.st_mtime_ns != opened.st_mtime_ns
                    or (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino)
                ):
                    raise ContractError(
                        "Eve publication file changed while staging: %s" % relative
                    )
                counters["bytes"] += copied
                if counters["bytes"] > core_artifacts.MAX_EXPANDED_BYTES:
                    raise ContractError("Eve publication tree is too large")
                os.fchmod(target_file, 0o755 if opened.st_mode & stat.S_IXUSR else 0o644)
            except OSError as exc:
                raise ContractError(
                    "cannot safely stage Eve publication file %s" % relative
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
            raise ContractError("cannot recheck Eve publication tree") from exc
        if names_before != names_after:
            raise ContractError("Eve publication tree changed while staging")

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


def build_publication_packet(
    cfg, game_dir: Path, slug: str, title: Optional[str] = None
) -> Dict[str, Any]:
    """Build and retain an immutable canonical packet from a safe staging tree.

    Panda needs a root ``project.json``. Historical Eve projects do not all
    carry one, so it is injected only into an isolated staging copy. Neither
    the source game nor Eve's queue is rewritten.
    """
    slug = validate_slug(slug)
    game_dir = Path(game_dir)
    packet_root = Path(cfg.root) / "state" / "publication-packets"
    packet_root.mkdir(parents=True, mode=0o700, exist_ok=True)
    packet_root_metadata = packet_root.lstat()
    if not stat.S_ISDIR(packet_root_metadata.st_mode) or packet_root.is_symlink():
        raise ContractError("Eve publication packet root must be a non-symlink directory")
    os.chmod(str(packet_root), 0o700)
    with tempfile.TemporaryDirectory(prefix=".eve-packet-", dir=str(packet_root)) as temporary:
        workspace = Path(temporary)
        staged_game = workspace / "game"
        _copy_publication_tree(game_dir, staged_game)
        project = staged_game / "project.json"
        if not os.path.lexists(str(project)):
            project.write_text(
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
                + "\n",
                encoding="utf-8",
            )
        candidate = workspace / "packet.zip"
        built = core_artifacts.build_publish_packet(
            staged_game,
            candidate,
            extra_excludes=("published.json", CORE_PUBLICATION_PROJECTION),
        )
        packet_sha256 = built["packet_sha256"]
        destination = packet_root / (
            "eve-%s-%s.zip"
            % (hashlib.sha256(slug.encode("utf-8")).hexdigest()[:16], packet_sha256)
        )
        if os.path.lexists(str(destination)):
            inspection = inspect_publish_packet(destination)
            if (
                inspection["packet_sha256"] != packet_sha256
                or inspection["artifact_sha256"] != built["artifact_sha256"]
            ):
                raise ContractError("retained Eve publication packet has changed bytes")
        else:
            os.replace(candidate, destination)
            os.chmod(str(destination), 0o600)
        inspection = inspect_publish_packet(destination)
        if (
            inspection["packet_sha256"] != packet_sha256
            or inspection["artifact_sha256"] != built["artifact_sha256"]
        ):
            raise ContractError("retained Eve publication packet identity is inconsistent")
        return {**built, "path": str(destination)}


def import_panda_draft(
    cfg,
    game,
    metadata: Mapping[str, Any],
    *,
    transport: Optional[Transport] = None,
) -> Dict[str, Any]:
    """Import one exact Eve artifact through core's durable Panda outbox."""
    game_dir = Path(cfg.games_dir) / game.slug
    packet = build_publication_packet(
        cfg, game_dir, game.slug, title=game.title or game.slug
    )
    store = _publication_store(cfg)
    product_id = _ensure_publication_product(
        store, game.slug, packet["artifact_sha256"]
    )
    api_base = _api_base(cfg.store_base_url)
    client_options: Dict[str, Any] = {
        "api_base": api_base,
        # The configured deployment is pinned as the sole allowed origin.
        "allowed_origins": (api_base,),
    }
    if transport is not None:
        client_options["transport"] = transport
    client = PandaClient(cfg.store_bearer, **client_options)
    coordinator = PandaPublicationCoordinator(store, client, cfg.panda_owner_id)
    outcome = coordinator.import_draft(
        product_id, Path(packet["path"]), metadata
    )
    intent = store.get_publish_intent(outcome.intent_id)
    return {
        "product_id": product_id,
        "intent_id": outcome.intent_id,
        "receipt": outcome.receipt.to_dict(),
        "intent_state": intent["state"],
        "packet": packet,
        "core_store": str(store.path),
    }


def publication_state(cfg, slug: str) -> Optional[Dict[str, Any]]:
    """Return Eve's current core outbox state for an operator-facing error."""
    store = _publication_store(cfg)
    return store.latest_publish_intent(_product_id(slug))

"""Bob's narrow adapter to the repository-wide :mod:`inventor_core` runtime.

Bob remains runnable from ``bob/`` without installing a wheel: the adapter
prefers an installed package, then resolves ``../core/src`` from this file.
Publication operations call :func:`require_core` and fail closed when neither
is available.  Keeping that bootstrap here prevents every Bob module from
growing its own path assumptions.
"""

from __future__ import annotations

import importlib
import os
import stat
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Optional, Sequence, Tuple


class CoreUnavailable(RuntimeError):
    """The shared runtime required by a safety-sensitive operation is absent."""


@dataclass(frozen=True)
class CoreRuntime:
    build_publish_packet: Any
    inspect_publish_packet: Any
    InventorStore: Any
    PandaClient: Any
    PandaPublicationCoordinator: Any
    HttpResponse: Any
    PublicationReceipt: Any
    AmbiguousPublishError: Any
    ContractError: Any
    CorePublishError: Any
    StateConflict: Any


def _configured_source() -> Optional[Path]:
    configured = os.environ.get("BOB_CORE_SRC")
    if configured is None:
        return None
    source = Path(configured).expanduser().resolve()
    if not (source / "inventor_core" / "__init__.py").is_file():
        raise CoreUnavailable(
            "BOB_CORE_SRC does not contain inventor_core: %s" % source
        )
    return source


def _repository_source() -> Path:
    return Path(__file__).resolve().parents[2] / "core" / "src"


def _module_paths(module: Any) -> Tuple[Path, ...]:
    """Return every filesystem location advertised by an imported module."""

    values = []
    module_file = getattr(module, "__file__", None)
    if module_file:
        values.append(module_file)
    module_path = getattr(module, "__path__", None)
    if module_path:
        values.extend(module_path)
    spec = getattr(module, "__spec__", None)
    if spec is not None:
        origin = getattr(spec, "origin", None)
        if origin and origin not in ("built-in", "frozen"):
            values.append(origin)
        locations = getattr(spec, "submodule_search_locations", None)
        if locations:
            values.extend(locations)

    paths = []
    for value in values:
        try:
            candidate = Path(value).expanduser().resolve()
        except (OSError, TypeError, ValueError):
            continue
        if candidate not in paths:
            paths.append(candidate)
    return tuple(paths)


def _require_loaded_core_from(source: Path) -> None:
    """Fail if a cached core module cannot be proven to come from ``source``.

    An explicit ``BOB_CORE_SRC`` is a deployment pin, not merely a sys.path
    preference.  Python returns objects from ``sys.modules`` before consulting
    sys.path, so accepting an already-imported site-package here would bypass
    that pin.  We deliberately reject the process instead of evicting/reloading
    modules: mixed old/new core objects are unsafe at a publication boundary.
    """

    package_root = (source / "inventor_core").resolve()
    for name, module in tuple(sys.modules.items()):
        if name != "inventor_core" and not name.startswith("inventor_core."):
            continue
        if module is None:
            raise CoreUnavailable(
                "BOB_CORE_SRC pin cannot verify partially loaded module %s" % name
            )
        locations = _module_paths(module)
        if not locations:
            raise CoreUnavailable(
                "BOB_CORE_SRC pin cannot verify loaded module %s" % name
            )
        for location in locations:
            try:
                location.relative_to(package_root)
            except ValueError:
                raise CoreUnavailable(
                    "loaded %s resolves outside BOB_CORE_SRC: %s (expected %s)"
                    % (name, location, package_root)
                )


def require_core() -> CoreRuntime:
    """Load core, with an explicit override acting as a strict deployment pin."""

    source = _configured_source()
    if source is not None:
        _require_loaded_core_from(source)
        source_text = str(source)
        if source_text not in sys.path:
            sys.path.insert(0, source_text)
    else:
        try:
            importlib.import_module("inventor_core")
        except ImportError:
            source = _repository_source()
            if not (source / "inventor_core" / "__init__.py").is_file():
                raise CoreUnavailable(
                    "shared core is unavailable; expected %s or set BOB_CORE_SRC"
                    % source
                )
            source_text = str(source)
            if source_text not in sys.path:
                sys.path.insert(0, source_text)
    try:
        core = importlib.import_module("inventor_core")
        errors = importlib.import_module("inventor_core.errors")
        models = importlib.import_module("inventor_core.models")
    except ImportError as exc:
        raise CoreUnavailable(
            "shared core could not be imported: %s" % exc
        ) from exc
    if source is not None:
        _require_loaded_core_from(source)
    return CoreRuntime(
        build_publish_packet=core.build_publish_packet,
        inspect_publish_packet=core.inspect_publish_packet,
        InventorStore=core.InventorStore,
        PandaClient=core.PandaClient,
        PandaPublicationCoordinator=core.PandaPublicationCoordinator,
        HttpResponse=core.HttpResponse,
        PublicationReceipt=models.PublicationReceipt,
        AmbiguousPublishError=errors.AmbiguousPublishError,
        ContractError=errors.ContractError,
        CorePublishError=errors.PublishError,
        StateConflict=errors.StateConflict,
    )


def _safe_relative(value: str) -> Path:
    candidate = PurePosixPath(value)
    if (
        not value
        or candidate.is_absolute()
        or "\\" in value
        or ".." in candidate.parts
        or candidate.as_posix() != value
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ValueError("unsafe Bob artifact path: %r" % value)
    return Path(*candidate.parts)


def _copy_regular(source: Path, destination: Path) -> None:
    """Copy one held regular-file descriptor into private staging.

    The packet is built from the staging bytes, never by reopening Bob's
    mutable game tree, so a generator cannot swap a symlink or FIFO between
    discovery and the core packet read.
    """

    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor = None
    try:
        expected = source.lstat()
        if not stat.S_ISREG(expected.st_mode):
            raise ValueError("Bob artifact is not a regular file: %s" % source)
        descriptor = os.open(str(source), flags)
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or (opened.st_dev, opened.st_ino) != (expected.st_dev, expected.st_ino)
        ):
            raise ValueError("Bob artifact changed while opening: %s" % source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with open(destination, "xb") as output:
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                output.write(chunk)
            output.flush()
            os.fsync(output.fileno())
        after = os.fstat(descriptor)
        if after.st_size != opened.st_size or after.st_mtime_ns != opened.st_mtime_ns:
            raise ValueError("Bob artifact changed while staging: %s" % source)
        os.chmod(destination, 0o644)
    finally:
        if descriptor is not None:
            os.close(descriptor)


def build_game_packet(
    entries: Sequence[Tuple[Path, str]], destination: Path, maximum_bytes: int
) -> dict:
    """Build Bob's selected product bytes with core's canonical ZIP contract."""

    runtime = require_core()
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bob-core-packet-") as temporary:
        product = Path(temporary) / "product"
        product.mkdir(mode=0o700)
        seen = set()
        for source, relative_text in sorted(entries, key=lambda pair: pair[1]):
            relative = _safe_relative(relative_text)
            normalized = relative.as_posix()
            if normalized in seen:
                raise ValueError("duplicate Bob artifact path: %s" % normalized)
            seen.add(normalized)
            _copy_regular(Path(source), product / relative)
        if not seen:
            raise ValueError("Bob artifact has no publishable files")
        return runtime.build_publish_packet(
            product, destination, maximum_bytes=maximum_bytes
        )

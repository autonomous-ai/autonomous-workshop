"""Bob's narrow adapter to the repository-wide :mod:`inventor_workshop`.

Bob remains runnable from ``inventors/bob/`` without installing a wheel: the
adapter prefers an installed package, then resolves ``../../workshop/src``
from this file.
Send operations call :func:`require_workshop` and fail closed when neither
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


class WorkshopUnavailable(RuntimeError):
    """The shared runtime required by a safety-sensitive operation is absent."""


@dataclass(frozen=True)
class WorkshopRuntime:
    pack_artifact: Any
    inspect_pack: Any
    Clockwork: Any
    ShopDoor: Any
    Sender: Any
    HttpResponse: Any
    Stamp: Any
    AmbiguousSendError: Any
    ContractError: Any
    WorkshopSendError: Any
    StateConflict: Any
    load_taste: Any


def _configured_source() -> Optional[Path]:
    names = ("BOB_WORKSHOP_SRC", "BOB_FOUNDATION_SRC", "BOB_CORE_SRC")
    values = [(name, os.environ[name]) for name in names if os.environ.get(name)]
    resolved = [
        (name, Path(value).expanduser().resolve()) for name, value in values
    ]
    if resolved and any(path != resolved[0][1] for _, path in resolved[1:]):
        raise WorkshopUnavailable(
            "%s disagree" % " and ".join(
                name if name == "BOB_WORKSHOP_SRC" else "legacy %s" % name
                for name, _ in resolved
            )
        )
    configured = values[0][1] if values else None
    if configured is None:
        return None
    source = Path(configured).expanduser().resolve()
    if not (source / "inventor_workshop" / "__init__.py").is_file():
        raise WorkshopUnavailable(
            "BOB_WORKSHOP_SRC does not contain inventor_workshop: %s" % source
        )
    return source


def _symbol(module: Any, canonical: str, *legacy: str) -> Any:
    """Resolve one v0.3 symbol, accepting older names only at this adapter."""

    for name in (canonical,) + legacy:
        value = getattr(module, name, None)
        if value is not None:
            return value
    raise WorkshopUnavailable(
        "Workshop does not expose %s (compatibility names checked: %s)"
        % (canonical, ", ".join(legacy) or "none")
    )


def _repository_source() -> Path:
    return Path(__file__).resolve().parents[3] / "workshop" / "src"


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


def _require_loaded_workshop_from(source: Path) -> None:
    """Fail if a cached Workshop module cannot be proven to come from ``source``.

    An explicit ``BOB_WORKSHOP_SRC`` is a deployment pin, not merely a sys.path
    preference.  Python returns objects from ``sys.modules`` before consulting
    sys.path, so accepting an already-imported site-package here would bypass
    that pin.  We deliberately reject the process instead of evicting/reloading
    modules: mixed old/new Workshop objects are unsafe at a send boundary.
    """

    package_root = (source / "inventor_workshop").resolve()
    for name, module in tuple(sys.modules.items()):
        if name != "inventor_workshop" and not name.startswith(
            "inventor_workshop."
        ):
            continue
        if module is None:
            raise WorkshopUnavailable(
                "BOB_WORKSHOP_SRC pin cannot verify partially loaded module %s"
                % name
            )
        locations = _module_paths(module)
        if not locations:
            raise WorkshopUnavailable(
                "BOB_WORKSHOP_SRC pin cannot verify loaded module %s" % name
            )
        for location in locations:
            try:
                location.relative_to(package_root)
            except ValueError:
                raise WorkshopUnavailable(
                    "loaded %s resolves outside BOB_WORKSHOP_SRC: %s (expected %s)"
                    % (name, location, package_root)
                )


def require_workshop() -> WorkshopRuntime:
    """Load Workshop with an explicit override as a strict deployment pin."""

    source = _configured_source()
    if source is not None:
        _require_loaded_workshop_from(source)
        source_text = str(source)
        if source_text not in sys.path:
            sys.path.insert(0, source_text)
    else:
        try:
            importlib.import_module("inventor_workshop")
        except ImportError:
            source = _repository_source()
            if not (source / "inventor_workshop" / "__init__.py").is_file():
                raise WorkshopUnavailable(
                    "Workshop is unavailable; expected %s or set BOB_WORKSHOP_SRC"
                    % source
                )
            source_text = str(source)
            if source_text not in sys.path:
                sys.path.insert(0, source_text)
    try:
        workshop = importlib.import_module("inventor_workshop")
        errors = importlib.import_module("inventor_workshop.errors")
        models = importlib.import_module("inventor_workshop.models")
    except ImportError as exc:
        raise WorkshopUnavailable(
            "Workshop could not be imported: %s" % exc
        ) from exc
    if source is not None:
        _require_loaded_workshop_from(source)
    return WorkshopRuntime(
        pack_artifact=_symbol(workshop, "pack_artifact", "build_publish_packet"),
        inspect_pack=_symbol(workshop, "inspect_pack", "inspect_publish_packet"),
        Clockwork=_symbol(workshop, "Clockwork", "InventorStore"),
        ShopDoor=_symbol(workshop, "ShopDoor", "Portal"),
        Sender=_symbol(workshop, "Sender", "Launchpad"),
        HttpResponse=workshop.HttpResponse,
        Stamp=_symbol(workshop, "Stamp")
        if getattr(workshop, "Stamp", None) is not None
        else _symbol(models, "Stamp", "PublicationReceipt"),
        AmbiguousSendError=_symbol(
            errors, "AmbiguousSendError", "AmbiguousPublishError"
        ),
        ContractError=errors.ContractError,
        WorkshopSendError=_symbol(errors, "SendError", "PublishError"),
        StateConflict=errors.StateConflict,
        load_taste=_symbol(workshop, "load_taste", "load_taste_profile"),
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
    discovery and the Workshop packet read.
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
) -> Any:
    """Pack Bob's selected product bytes with Workshop's canonical contract."""

    runtime = require_workshop()
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bob-workshop-packet-") as temporary:
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
        packed = runtime.pack_artifact(product, destination)
        if destination.stat().st_size > maximum_bytes:
            raise ValueError(
                "Bob pack is %d bytes; configured limit is %d"
                % (destination.stat().st_size, maximum_bytes)
            )
        return packed


def send_draft(sender: Any, product_id: str, packed: Path, listing: Any) -> Any:
    """Use Workshop v0.3 Send, with the v0.2 method isolated here."""

    canonical = getattr(sender, "send_draft", None)
    if canonical is not None:
        return canonical(product_id, packed, listing)
    return sender.import_draft(product_id, packed, listing)


def send_live(sender: Any, intent_id: str, price_cents: int) -> Any:
    """Use Workshop v0.3 Send, with the v0.2 method isolated here."""

    canonical = getattr(sender, "send_live", None)
    if canonical is not None:
        return canonical(intent_id, price_cents)
    return sender.publish_live(intent_id, price_cents)

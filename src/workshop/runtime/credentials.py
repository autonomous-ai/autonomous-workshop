"""Host-only credential loading outside every product-run workspace.

The preferred local source is ``$WORKSHOP_HOME/credentials/factory.env``.
It is read lazily by the trusted host after a native coding-agent turn exits;
the file path and values are never passed to that subprocess.
"""

from __future__ import annotations

import os
import re
import stat
from pathlib import Path
from typing import Mapping, Optional

from workshop.errors import ContractError
from workshop.runtime.package_data import default_workshop_home


MAX_FACTORY_CREDENTIAL_FILE_BYTES = 32 * 1024
_FACTORY_CREDENTIAL_NAME = re.compile(
    r"^FACTORY_(?:PASSWORD|USERNAME|[A-Z][A-Z0-9_]{0,63}_USERNAME)$"
)


def factory_credential_file(
    environment: Optional[Mapping[str, str]] = None,
) -> Path:
    """Return the supported host-only Factory credential file path."""

    return default_workshop_home(environment) / "credentials" / "factory.env"


def _credential_environment_values(values: Mapping[str, str]) -> dict[str, str]:
    return {
        name: value
        for name, value in values.items()
        if isinstance(name, str)
        and _FACTORY_CREDENTIAL_NAME.fullmatch(name) is not None
        and isinstance(value, str)
        and value
    }


def _read_private_credential_file(path: Path) -> bytes:
    try:
        parent_identity = path.parent.lstat()
        identity = path.lstat()
    except OSError as exc:
        raise ContractError("Factory credential file is unavailable") from exc
    if (
        path.parent.is_symlink()
        or not stat.S_ISDIR(parent_identity.st_mode)
        or stat.S_IMODE(parent_identity.st_mode) != 0o700
    ):
        raise ContractError("Factory credential directory permissions must be 0700")
    if (
        path.is_symlink()
        or not stat.S_ISREG(identity.st_mode)
        or stat.S_IMODE(identity.st_mode) != 0o600
    ):
        raise ContractError("Factory credential file permissions must be 0600")
    if not 1 <= identity.st_size <= MAX_FACTORY_CREDENTIAL_FILE_BYTES:
        raise ContractError("Factory credential file size is invalid")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(str(path), flags)
    except OSError as exc:
        raise ContractError("Factory credential file cannot be opened safely") from exc
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or (opened.st_dev, opened.st_ino) != (identity.st_dev, identity.st_ino)
            or stat.S_IMODE(opened.st_mode) != 0o600
        ):
            raise ContractError("Factory credential file changed while opening")
        source = os.read(descriptor, MAX_FACTORY_CREDENTIAL_FILE_BYTES + 1)
        if len(source) > MAX_FACTORY_CREDENTIAL_FILE_BYTES or os.read(descriptor, 1):
            raise ContractError("Factory credential file size is invalid")
        after = os.fstat(descriptor)
        if (
            (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino)
            or after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
        ):
            raise ContractError("Factory credential file changed while reading")
        return source
    finally:
        os.close(descriptor)


def _parse_factory_credential_file(source: bytes) -> dict[str, str]:
    try:
        text = source.decode("utf-8")
    except UnicodeError as exc:
        raise ContractError("Factory credential file must be UTF-8") from exc
    if "\x00" in text:
        raise ContractError("Factory credential file contains invalid data")
    result: dict[str, str] = {}
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ContractError(
                "Factory credential file line %d is malformed" % line_number
            )
        name, value = line.split("=", 1)
        if _FACTORY_CREDENTIAL_NAME.fullmatch(name) is None:
            raise ContractError(
                "Factory credential file line %d has an unsupported name"
                % line_number
            )
        if name in result:
            raise ContractError("Factory credential file contains a duplicate name")
        if (
            not value
            or value != value.strip()
            or len(value.encode("utf-8")) > 4096
            or any(ord(character) < 32 or ord(character) == 127 for character in value)
        ):
            raise ContractError(
                "Factory credential file line %d has an invalid value" % line_number
            )
        result[name] = value
    if not result:
        raise ContractError("Factory credential file contains no credentials")
    return result


def factory_credential_environment(
    environment: Optional[Mapping[str, str]] = None,
) -> Mapping[str, str]:
    """Load bounded Factory values without exposing unrelated environment data.

    Explicit process environment values override the private local file for
    compatibility with ephemeral and CI hosts. Product-run Codex receives
    neither source through :func:`codex_subprocess_environment`.
    """

    values = os.environ if environment is None else environment
    path = factory_credential_file(values)
    loaded: dict[str, str] = {}
    if path.exists() or path.is_symlink():
        loaded.update(_parse_factory_credential_file(_read_private_credential_file(path)))
    loaded.update(_credential_environment_values(values))
    return loaded


__all__ = [
    "MAX_FACTORY_CREDENTIAL_FILE_BYTES",
    "factory_credential_environment",
    "factory_credential_file",
]

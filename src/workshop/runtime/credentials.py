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


def _read_private_credential_file(
    path: Path,
    *,
    label: str = "Factory",
    max_bytes: int = MAX_FACTORY_CREDENTIAL_FILE_BYTES,
) -> bytes:
    try:
        parent_identity = path.parent.lstat()
        identity = path.lstat()
    except OSError as exc:
        raise ContractError("%s credential file is unavailable" % label) from exc
    if (
        path.parent.is_symlink()
        or not stat.S_ISDIR(parent_identity.st_mode)
        or stat.S_IMODE(parent_identity.st_mode) != 0o700
    ):
        raise ContractError(
            "%s credential directory permissions must be 0700" % label
        )
    if (
        path.is_symlink()
        or not stat.S_ISREG(identity.st_mode)
        or stat.S_IMODE(identity.st_mode) != 0o600
    ):
        raise ContractError("%s credential file permissions must be 0600" % label)
    if not 1 <= identity.st_size <= max_bytes:
        raise ContractError("%s credential file size is invalid" % label)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(str(path), flags)
    except OSError as exc:
        raise ContractError(
            "%s credential file cannot be opened safely" % label
        ) from exc
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or (opened.st_dev, opened.st_ino) != (identity.st_dev, identity.st_ino)
            or stat.S_IMODE(opened.st_mode) != 0o600
        ):
            raise ContractError("%s credential file changed while opening" % label)
        source = os.read(descriptor, max_bytes + 1)
        if len(source) > max_bytes or os.read(descriptor, 1):
            raise ContractError("%s credential file size is invalid" % label)
        after = os.fstat(descriptor)
        if (
            (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino)
            or after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
        ):
            raise ContractError("%s credential file changed while reading" % label)
        return source
    finally:
        os.close(descriptor)


def _parse_credential_file(
    source: bytes, name_pattern: "re.Pattern[str]", *, label: str
) -> dict[str, str]:
    try:
        text = source.decode("utf-8")
    except UnicodeError as exc:
        raise ContractError("%s credential file must be UTF-8" % label) from exc
    if "\x00" in text:
        raise ContractError("%s credential file contains invalid data" % label)
    result: dict[str, str] = {}
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ContractError(
                "%s credential file line %d is malformed" % (label, line_number)
            )
        name, value = line.split("=", 1)
        if name_pattern.fullmatch(name) is None:
            raise ContractError(
                "%s credential file line %d has an unsupported name"
                % (label, line_number)
            )
        if name in result:
            raise ContractError(
                "%s credential file contains a duplicate name" % label
            )
        if (
            not value
            or value != value.strip()
            or len(value.encode("utf-8")) > 4096
            or any(ord(character) < 32 or ord(character) == 127 for character in value)
        ):
            raise ContractError(
                "%s credential file line %d has an invalid value" % (label, line_number)
            )
        result[name] = value
    if not result:
        raise ContractError("%s credential file contains no credentials" % label)
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
        loaded.update(
            _parse_credential_file(
                _read_private_credential_file(path),
                _FACTORY_CREDENTIAL_NAME,
                label="Factory",
            )
        )
    loaded.update(_credential_environment_values(values))
    return loaded


__all__ = [
    "MAX_FACTORY_CREDENTIAL_FILE_BYTES",
    "factory_credential_environment",
    "factory_credential_file",
]

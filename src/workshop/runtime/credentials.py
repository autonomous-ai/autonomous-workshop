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
_FACTORY_SCOPED_USERNAME_NAME = re.compile(
    r"^FACTORY_([A-Z][A-Z0-9_]{0,63})_USERNAME$"
)
_FACTORY_INVENTOR_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def factory_credential_file(
    environment: Optional[Mapping[str, str]] = None,
) -> Path:
    """Return the supported host-only Factory credential file path."""

    return default_workshop_home(environment) / "credentials" / "factory.env"


def _is_quote_wrapped(value: str) -> bool:
    return (
        len(value) >= 2
        and value[0] in ("'", '"')
        and value[-1] == value[0]
    )


def _credential_environment_values(values: Mapping[str, str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for name, value in values.items():
        if (
            not isinstance(name, str)
            or _FACTORY_CREDENTIAL_NAME.fullmatch(name) is None
            or not isinstance(value, str)
            or not value
        ):
            continue
        if _is_quote_wrapped(value):
            raise ContractError(
                "Factory credential environment variable %s must not contain "
                "literal surrounding quotes" % name
            )
        result[name] = value
    return result


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
        if _is_quote_wrapped(value):
            raise ContractError(
                "%s credential file line %d must not use surrounding quotes; "
                "write the raw value after '='" % (label, line_number)
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
    environment_values = _credential_environment_values(values)
    environment_usernames = {
        name
        for name in environment_values
        if name == "FACTORY_USERNAME"
        or _FACTORY_SCOPED_USERNAME_NAME.fullmatch(name) is not None
    }
    if environment_usernames:
        # A process-level username overrides the file's service-account
        # username even when an older file used the scoped compatibility form.
        # Password-only overrides continue to pair with the file username.
        for name in tuple(loaded):
            if name == "FACTORY_USERNAME" or (
                _FACTORY_SCOPED_USERNAME_NAME.fullmatch(name) is not None
            ):
                loaded.pop(name)
    loaded.update(environment_values)
    return loaded


def validate_factory_credential_configuration(values: Mapping[str, str]) -> None:
    """Validate one host credential set without returning or exposing secrets.

    The canonical configuration is one Workshop-owned service account under
    ``FACTORY_USERNAME`` and ``FACTORY_PASSWORD``. Exactly one legacy scoped
    username is accepted temporarily as an unambiguous compatibility alias;
    it is normalized to the same single service account and never binds
    publication authority to the selected Inventor.
    """

    if not isinstance(values, Mapping):
        raise ContractError("Factory credential configuration must be a mapping")

    usernames_present = False
    generic_username = values.get("FACTORY_USERNAME")
    if generic_username is not None:
        if (
            not isinstance(generic_username, str)
            or not generic_username
            or generic_username != generic_username.strip()
            or len(generic_username.encode("utf-8")) > 512
            or any(
                ord(character) < 33 or ord(character) == 127
                for character in generic_username
            )
        ):
            raise ContractError("Factory generic username is malformed")
        if _is_quote_wrapped(generic_username):
            raise ContractError(
                "Factory generic username must not contain literal surrounding quotes"
            )
        usernames_present = True

    scoped_usernames: list[tuple[str, str]] = []
    for name, username in values.items():
        if not isinstance(name, str):
            continue
        match = _FACTORY_SCOPED_USERNAME_NAME.fullmatch(name)
        if match is None:
            continue
        if not isinstance(username, str) or not username:
            raise ContractError("Factory scoped username is malformed")
        if _is_quote_wrapped(username):
            raise ContractError(
                "Factory scoped username must not contain literal surrounding quotes"
            )
        inventor_id = match.group(1).lower().replace("_", "-")
        if _FACTORY_INVENTOR_ID.fullmatch(inventor_id) is None:
            raise ContractError(
                "Factory scoped username name must encode a canonical inventor_id"
            )
        if username.casefold() != inventor_id.casefold():
            raise ContractError(
                "Factory scoped username must exactly match the inventor_id "
                "encoded by its variable name"
            )
        scoped_usernames.append((name, username))
        usernames_present = True

    if generic_username is not None and scoped_usernames:
        raise ContractError(
            "Factory credentials must define only one Workshop service account; "
            "remove legacy scoped username variables"
        )
    if len(scoped_usernames) > 1:
        raise ContractError(
            "Factory credentials must define only one Workshop service account; "
            "replace legacy scoped username variables with FACTORY_USERNAME"
        )

    password = values.get("FACTORY_PASSWORD")
    password_present = password is not None
    if password_present:
        if (
            not isinstance(password, str)
            or not password
            or password != password.strip()
            or len(password.encode("utf-8")) > 4096
            or any(
                ord(character) < 33 or ord(character) == 127
                for character in password
            )
        ):
            raise ContractError("Factory password is malformed")
        if _is_quote_wrapped(password):
            raise ContractError(
                "Factory password must not contain literal surrounding quotes"
            )

    if usernames_present != password_present:
        raise ContractError(
            "Factory username and FACTORY_PASSWORD must be configured together"
        )


def factory_service_credential_environment(
    values: Mapping[str, str],
) -> Mapping[str, str]:
    """Normalize one validated Workshop Factory service-account pair.

    A single legacy ``FACTORY_<INVENTOR>_USERNAME`` value is accepted only so
    existing private hosts can migrate without interrupting Release. Its
    variable name grants no Inventor-scoped authority.
    """

    validate_factory_credential_configuration(values)
    username = values.get("FACTORY_USERNAME")
    if username is None:
        scoped = [
            value
            for name, value in values.items()
            if isinstance(name, str)
            and _FACTORY_SCOPED_USERNAME_NAME.fullmatch(name) is not None
        ]
        username = scoped[0] if scoped else None
    password = values.get("FACTORY_PASSWORD")
    if username is None and password is None:
        return {}
    assert isinstance(username, str)
    assert isinstance(password, str)
    return {
        "FACTORY_USERNAME": username,
        "FACTORY_PASSWORD": password,
    }


__all__ = [
    "MAX_FACTORY_CREDENTIAL_FILE_BYTES",
    "factory_credential_environment",
    "factory_credential_file",
    "factory_service_credential_environment",
    "validate_factory_credential_configuration",
]

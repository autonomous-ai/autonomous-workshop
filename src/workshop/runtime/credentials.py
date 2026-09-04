"""Host-only credential loading outside every product-run workspace.

Browser-issued credentials are stored per Inventor under
``$WORKSHOP_HOME/credentials/inventors/``.
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
    r"^FACTORY_(?:INVENTOR_ID|PASSWORD|USERNAME|"
    r"[A-Z][A-Z0-9_]{0,63}_USERNAME)$"
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
            or len(value.encode("utf-8")) > 16_384
            or any(ord(character) < 32 or ord(character) == 127 for character in value)
        ):
            raise ContractError(
                "%s credential file line %d has an invalid value" % (label, line_number)
            )
        result[name] = value
    if not result:
        raise ContractError("%s credential file contains no credentials" % label)
    return result


def private_credential_values(
    path: Path,
    name_pattern: "re.Pattern[str]",
    *,
    label: str,
    max_bytes: int = MAX_FACTORY_CREDENTIAL_FILE_BYTES,
) -> dict[str, str]:
    """Read one private ``NAME=value`` file under the Factory file's rules."""

    return _parse_credential_file(
        _read_private_credential_file(path, label=label, max_bytes=max_bytes),
        name_pattern,
        label=label,
    )


def inventor_credential_file(
    inventor_id: str,
    environment: Optional[Mapping[str, str]] = None,
) -> Path:
    """Return one per-Inventor publishing-account file."""

    if not isinstance(inventor_id, str) or _FACTORY_INVENTOR_ID.fullmatch(inventor_id) is None:
        raise ContractError("Inventor id must be a canonical slug")
    values = os.environ if environment is None else environment
    return default_workshop_home(values) / "credentials" / "inventors" / (
        "%s.env" % inventor_id
    )


def factory_credential_environment(
    environment: Optional[Mapping[str, str]] = None,
    *,
    inventor_id: Optional[str] = None,
) -> Mapping[str, str]:
    """Load bounded Factory values without exposing unrelated environment data.

    ``inventor_id`` selects that Inventor's credential file when it exists and
    falls back to the legacy host-wide username/password pair. Explicit process
    environment values override disk for ephemeral and CI hosts. Product-run
    Codex receives none of these sources through
    :func:`codex_subprocess_environment`.
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
    if inventor_id is not None:
        scoped = inventor_credential_file(inventor_id, values)
        if scoped.exists() or scoped.is_symlink():
            loaded = _parse_credential_file(
                _read_private_credential_file(scoped),
                _FACTORY_CREDENTIAL_NAME,
                label="Factory",
            )
            if loaded.get("FACTORY_INVENTOR_ID") != inventor_id:
                raise ContractError(
                    "Factory credential is not bound to Inventor %s" % inventor_id
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
    bound_inventor_id = loaded.get("FACTORY_INVENTOR_ID")
    if (
        inventor_id is not None
        and bound_inventor_id is not None
        and bound_inventor_id != inventor_id
    ):
        raise ContractError(
            "Factory credential is not bound to Inventor %s" % inventor_id
        )
    return loaded


def validate_factory_credential_configuration(values: Mapping[str, str]) -> None:
    """Validate one host credential set without returning or exposing secrets.

    Browser authorization stores one generated Factory username/password pair
    plus its Inventor binding. One scoped username alias remains accepted for
    legacy hosts.
    """

    if not isinstance(values, Mapping):
        raise ContractError("Factory credential configuration must be a mapping")

    bound_inventor_id = values.get("FACTORY_INVENTOR_ID")
    if bound_inventor_id is not None and (
        not isinstance(bound_inventor_id, str)
        or _FACTORY_INVENTOR_ID.fullmatch(bound_inventor_id) is None
    ):
        raise ContractError("Factory credential inventor id is malformed")

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
    if bound_inventor_id is not None and generic_username is None:
        raise ContractError(
            "Factory credential inventor id requires FACTORY_USERNAME"
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


def _store_factory_values(values: Mapping[str, str], path: Path) -> Path:
    validate_factory_credential_configuration(values)
    directory = path.parent
    try:
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(directory, 0o700)
    except OSError as exc:
        raise ContractError(
            "Factory credential directory could not be created: %s" % directory
        ) from exc
    document = "".join("%s=%s\n" % (name, values[name]) for name in sorted(values))
    temporary = path.with_name(path.name + ".tmp")
    try:
        descriptor = os.open(
            str(temporary), os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600
        )
        try:
            os.fchmod(descriptor, 0o600)
            os.write(descriptor, document.encode("utf-8"))
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.replace(temporary, path)
    except OSError as exc:
        raise ContractError("Factory credentials could not be stored") from exc
    return path


def store_factory_credentials(
    username: str,
    password: str,
    *,
    inventor_id: Optional[str] = None,
    environment: Optional[Mapping[str, str]] = None,
) -> Path:
    """Write one validated Factory service-account pair to the private file.

    The file is the operator's own credential store: 0600 inside a 0700
    directory, never inside a run workspace and never given to an agent.  An
    existing file is replaced atomically so a failed write cannot leave a
    half-written credential behind.
    """

    values = {"FACTORY_USERNAME": username, "FACTORY_PASSWORD": password}
    if inventor_id is not None:
        values["FACTORY_INVENTOR_ID"] = inventor_id
    path = (
        factory_credential_file(environment)
        if inventor_id is None
        else inventor_credential_file(inventor_id, environment)
    )
    return _store_factory_values(values, path)


def factory_service_credential_environment(
    values: Mapping[str, str],
) -> Mapping[str, str]:
    """Normalize one validated Workshop Factory username/password pair.

    The Inventor binding is validated at the file boundary and deliberately
    omitted from the service mapping consumed by the unchanged Factory login
    integration. A single legacy ``FACTORY_<INVENTOR>_USERNAME`` value remains
    accepted for migration.
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
    "private_credential_values",
    "MAX_FACTORY_CREDENTIAL_FILE_BYTES",
    "factory_credential_environment",
    "inventor_credential_file",
    "factory_credential_file",
    "factory_service_credential_environment",
    "store_factory_credentials",
    "validate_factory_credential_configuration",
]

#!/usr/bin/env python3
"""Render one launchd plist template without shell text substitution."""

from __future__ import annotations

import argparse
import os
import plistlib
import re
import stat
import tempfile
from pathlib import Path
from typing import Any, Mapping


_PLACEHOLDER = re.compile(r"__[A-Z][A-Z0-9_]*__")


class RenderError(ValueError):
    """The template or one of its path bindings is unsafe."""


def _plain_directory(value: str, label: str) -> str:
    path = Path(value)
    if not path.is_absolute():
        raise RenderError(f"{label} must be absolute")
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise RenderError(f"{label} is unavailable") from exc
    if not stat.S_ISDIR(metadata.st_mode) or path.is_symlink():
        raise RenderError(f"{label} must be a non-symlink directory")
    return str(path.resolve(strict=True))


def _replace(value: Any, bindings: Mapping[str, str]) -> Any:
    if isinstance(value, str):
        for token, replacement in bindings.items():
            value = value.replace(token, replacement)
        unresolved = _PLACEHOLDER.search(value)
        if unresolved:
            raise RenderError(f"unresolved plist placeholder {unresolved.group(0)}")
        return value
    if isinstance(value, list):
        return [_replace(item, bindings) for item in value]
    if isinstance(value, dict):
        return {
            _replace(key, bindings): _replace(item, bindings)
            for key, item in value.items()
        }
    return value


def render_plist(
    *,
    template: Path,
    output: Path,
    repository: str,
    user_home: str,
    core_source: str,
) -> None:
    repository = _plain_directory(repository, "repository")
    user_home = _plain_directory(user_home, "user home")
    core_source = _plain_directory(core_source, "core source")
    if not template.is_absolute() or not output.is_absolute():
        raise RenderError("template and output paths must be absolute")
    try:
        template_metadata = template.lstat()
    except OSError as exc:
        raise RenderError("plist template is unavailable") from exc
    if not stat.S_ISREG(template_metadata.st_mode) or template.is_symlink():
        raise RenderError("plist template must be a non-symlink regular file")
    if not output.parent.is_dir() or output.parent.is_symlink():
        raise RenderError("plist output parent must be a non-symlink directory")

    with template.open("rb") as handle:
        document = plistlib.load(handle)
    rendered = _replace(
        document,
        {
            "__REPO__": repository,
            "__USER_HOME__": user_home,
            "__CORE_SRC__": core_source,
        },
    )
    payload = plistlib.dumps(rendered, fmt=plistlib.FMT_XML, sort_keys=False)

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.", suffix=".tmp", dir=output.parent
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            descriptor = -1
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, output)
        os.chmod(output, 0o600, follow_symlinks=False)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--home", required=True)
    parser.add_argument("--core-src", required=True)
    args = parser.parse_args()
    try:
        render_plist(
            template=args.template,
            output=args.output,
            repository=args.repo,
            user_home=args.home,
            core_source=args.core_src,
        )
    except (OSError, plistlib.InvalidFileException, RenderError) as exc:
        parser.exit(1, f"render_launchd: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

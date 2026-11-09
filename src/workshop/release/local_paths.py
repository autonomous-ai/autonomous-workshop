"""Publication hygiene: host-local path prefixes never leave the machine.

Release writes every public byte through this one redaction: the toy archive
it projects into the repository and the Factory handoff it uploads (a create
and a Listing Update alike). Make's own round records, logs and reports name
the run workspace and the builder's home directory; publishing them would
publish both.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

# Any user's home directory, as the direct-publish dry run also reports it.
HOST_HOME_PATH = re.compile(rb"(?:/Users|/home)/[^/\s\"'<>`)]+/")
WORKSHOP_RUN_PLACEHOLDER = b"<WORKSHOP_RUN>"
HOME_PLACEHOLDER = b"<HOME>"


def redact_local_paths(
    content: bytes,
    *,
    run_root: Optional[Path] = None,
) -> tuple[bytes, tuple[str, ...]]:
    """Replace host-local absolute prefixes without interpreting artifact prose.

    The run root and this user's home are replaced exactly. Any other home
    directory left in UTF-8 text (a project built under another account or
    copied from another run) is replaced too; binary content is never
    pattern-matched, so image and model bytes keep their exact values unless
    they literally contain this machine's own prefixes.
    """

    replacements = []
    candidates = []
    if run_root is not None:
        candidates.append((
            str(Path(run_root).resolve(strict=True)).encode("utf-8"),
            WORKSHOP_RUN_PLACEHOLDER,
            "workshop-run-root",
        ))
    candidates.append((
        str(Path.home().resolve()).encode("utf-8"),
        HOME_PLACEHOLDER,
        "home-directory",
    ))
    public = content
    for private, placeholder, label in candidates:
        if private and len(private) > 1 and private in public:
            public = public.replace(private, placeholder)
            replacements.append(label)
    if HOST_HOME_PATH.search(public):
        try:
            public.decode("utf-8")
        except UnicodeDecodeError:
            pass
        else:
            public = HOST_HOME_PATH.sub(HOME_PLACEHOLDER + b"/", public)
            if "home-directory" not in replacements:
                replacements.append("home-directory")
    return public, tuple(replacements)


def names_host_path(content: bytes) -> bool:
    """Whether ``content`` still names any home directory."""

    return HOST_HOME_PATH.search(content) is not None

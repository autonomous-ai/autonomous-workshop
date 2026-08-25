"""A tiny, dependency-free ``.env`` loader.

Matches the convention already used by ``inventors/bob/bob.py``'s
``_load_dotenv``: a real environment variable always wins over one loaded
from the file, comments and blank lines are skipped, and a missing file is
not an error — config may legitimately come from the real environment
instead. No third-party dependency is added; the core Workshop package
ships with none.
"""

from __future__ import annotations

import os
from typing import Optional


def load_dotenv(path: Optional[str] = None) -> None:
    """Populate ``os.environ`` from a ``.env`` file.

    Defaults to ``.env`` in the current working directory. An existing
    environment variable is never overwritten by the file, and a missing
    file is silently ignored.
    """

    target = path or ".env"
    try:
        with open(target, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key:
                    os.environ.setdefault(key, value)
    except OSError:
        pass


__all__ = ["load_dotenv"]

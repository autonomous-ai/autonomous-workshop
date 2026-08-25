#!/usr/bin/env python3
"""Publish one checked-in sealed Workshop product as a private Shop draft.

The descriptor contains only repository-relative paths and immutable hashes.
Credentials are read exclusively from ``WORKSHOP_SHOP_TOKEN`` and
``WORKSHOP_SHOP_OWNER_ID``; this command has no credential arguments and never
prints either value.  It can create or verify a private draft, but it cannot
make a product public.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Mapping, Optional, Sequence, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from inventor_workshop.sealed_draft import publish_sealed_draft


def _credentials(environ: Mapping[str, str]) -> Tuple[str, str]:
    token = environ.get("WORKSHOP_SHOP_TOKEN")
    owner_id = environ.get("WORKSHOP_SHOP_OWNER_ID")
    if not token or not token.strip() or not owner_id or not owner_id.strip():
        raise SystemExit(
            "WORKSHOP_SHOP_TOKEN and WORKSHOP_SHOP_OWNER_ID are both required"
        )
    return token, owner_id


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "descriptor",
        type=Path,
        help="checked-in sealed private-draft descriptor (relative to this repository)",
    )
    parser.add_argument(
        "--verify-draft",
        action="store_true",
        help="perform one additional authenticated fresh private-draft readback",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    token, owner_id = _credentials(os.environ)
    result = publish_sealed_draft(
        args.descriptor,
        token=token,
        owner_id=owner_id,
        repo_root=REPO_ROOT,
        verify_draft=args.verify_draft,
    )
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

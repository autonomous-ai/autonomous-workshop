"""Descriptor-level freshness primitives shared by BOTH freshness authorities.

A render package's currency is decided twice, by design: the viewer's validator
(``viewer/server_py/artifact.py``) decides what a status GET answers, and the producer's
per-kind ``is_current`` callable — re-evaluated under the generation lock — decides
whether a build no-ops. When the two disagree the failure is SILENT rather than loud: the
producer reports ``skipped``, the request settles ``ready``, and the stale package
renders. So a check added to one side must be added to the other.

These primitives live here, and not in either caller, because this module is stdlib-only:
a long-lived reader process can import it without dragging OCP/build123d into itself.
Sharing the code is what makes the two sides agree by construction instead of by review.

No tolerant reads. A descriptor either records what the current producer records, or the
package is stale and gets rebuilt (``__cadgen__/`` is a gitignored per-machine cache, so
invalidation costs one lazy rebuild per entry actually reopened).
"""

from __future__ import annotations

from typing import Any, Mapping

# One number covers everything about how a STEP package was produced: the descriptor's
# layout AND the bytes inside the payloads it references. Bumping it both makes a validator
# refuse existing packages and (via the component cid salt in _internal.component_package)
# forces the payloads to be re-emitted rather than reused by geometry. Splitting those two
# into separate numbers is how a fix ships half applied: the descriptor advances while
# content-addressed payloads are reused unchanged.
#
# 3: the topology extractor's curveType/continuity names were corrupted by a memoization
#    collision between the numerically overlapping GeomAbs_* enum families (see
#    _internal.step_scene._enum_name), so every package built before that fix records
#    surface names on its edges.
STEP_PACKAGE_VERSION = 3

SCHEMA_VERSION_FIELD = "packageSchemaVersion"
BAKE_HASH_FIELD = "bakeHash"


def descriptor_bake_hash(descriptor: Mapping[str, Any]) -> str | None:
    """The ``bakeHash`` a descriptor records, or None when it records none.

    A STEP package bakes no format settings into its payload, so a descriptor that records
    one was not written by this producer and is stale.
    """
    recorded = descriptor.get(BAKE_HASH_FIELD)
    if not isinstance(recorded, str):
        return None
    return recorded.strip() or None


def schema_version_matches(descriptor: Mapping[str, Any], expected: int) -> bool:
    """True when the descriptor records exactly ``expected`` as its schema version.

    Strict equality with no tolerance branch: a missing, non-integer, or older version
    is stale, not "probably fine".
    """
    recorded = descriptor.get(SCHEMA_VERSION_FIELD)
    if isinstance(recorded, bool) or not isinstance(recorded, int):
        return False
    return recorded == expected

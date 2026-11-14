"""Which cadfits fit table an Approved Proof was approved with (ADR 0105).

The vendored ``cadfits`` reads ``WORKSHOP_FIT_TABLE`` at import and builds
with that named table. A seeded run builds its Approved Proof's sources, so
every process that builds them must name the table the owner approved them
under, or the same sources become another geometry (the 2026-11-13 resync
halved ``slip`` and ``snug``).

An approval names its table in ``fit_table``. One sealed before that field
existed is placed by the skills ``LOCK.json`` it recorded: the one LOCK the
resync wrote means the current table, any earlier LOCK the legacy one.
"""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping

FIT_TABLE_ENV = "WORKSHOP_FIT_TABLE"
LEGACY = "fits-legacy"
CURRENT = "fits-2026-11-13"
# Keep equal to cadfits.FIT_TABLES' names (a test holds them together).
NAMES = (LEGACY, CURRENT)

# sha256 of src/workshop/make/skills/LOCK.json from the resync that changed
# the table (ea8b2fcc) until seal_proof began recording ``fit_table``.
CURRENT_TABLE_LOCKS = frozenset({
    "6cc66a4a370ad265c6e0ccda1ee44d99da6487adfac52a69f60b610adb43d62f",
})


def approval_fit_table(approval: Mapping[str, Any]) -> str:
    """The fit table one Approved Proof's APPROVAL.json was approved with."""

    if "fit_table" in approval:
        name = approval["fit_table"]
        if name not in NAMES:
            raise ValueError("APPROVAL.json fit_table %r names no fit table; known: %s"
                             % (name, ", ".join(NAMES)))
        return name
    return CURRENT if approval.get("skills_lock_sha256") in CURRENT_TABLE_LOCKS else LEGACY


def pin(environment: MutableMapping[str, str], approval: Mapping[str, Any]) -> str:
    """Set ``WORKSHOP_FIT_TABLE`` in ``environment`` to the approval's table.

    The sealed approval decides; a different name already there is replaced,
    since a seeded run builds only what the owner approved."""

    name = approval_fit_table(approval)
    environment[FIT_TABLE_ENV] = name
    return name


def sealing_fit_table(environment: Mapping[str, str]) -> str:
    """The table a Proof being sealed now was built and gated with."""

    name = environment.get(FIT_TABLE_ENV) or CURRENT
    if name not in NAMES:
        raise ValueError("%s=%r names no fit table; known: %s" % (FIT_TABLE_ENV, name, ", ".join(NAMES)))
    return name


__all__ = ["CURRENT", "CURRENT_TABLE_LOCKS", "FIT_TABLE_ENV", "LEGACY", "NAMES",
           "approval_fit_table", "pin", "sealing_fit_table"]

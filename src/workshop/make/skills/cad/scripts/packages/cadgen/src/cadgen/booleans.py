"""Serial OCCT Booleans, so one source always builds one B-rep.

build123d asks OCCT for its parallel Boolean before every fuse, cut,
intersection and section (``SetRunParallel(True)``). Thread timing then
settles near-tolerance contacts differently from run to run: the same
unchanged source can give a different B-rep identity, or a print detail that
joins in one build and is refused in the next (Workshop issue #102, Broken
God's spine-housing: 1 of 8 identical builds refused a rivet).

:func:`serial_booleans` makes every Boolean in this process run serially,
whatever build123d asks for. Every loader in the Make toolchain that runs a
``gen_step()`` source calls it first, so a Component file needs no wrapper of
its own. It is process-wide and idempotent; it never changes geometry a serial
build would make, only removes the run-to-run variation.
"""

from __future__ import annotations

# Set on the replacement so a second call, or a reload of this module, does
# not wrap the replacement again.
_SERIAL_MARK = "_cadgen_serial_boolean"


def _serial_setter(original):
    def set_run_parallel(self, flag=False):  # noqa: ARG001 - the request is overridden
        original(self, False)

    setattr(set_run_parallel, _SERIAL_MARK, True)
    set_run_parallel.__doc__ = "Serial whatever the caller asks for (cadgen.booleans, Workshop #102)."
    return set_run_parallel


def _owners():
    from OCP.BOPAlgo import BOPAlgo_Options
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Algo

    # Both bind SetRunParallel themselves: every BRepAlgoAPI operation
    # (Fuse, Cut, Common, Section, Splitter) inherits BRepAlgoAPI_Algo's, and
    # the BOPAlgo builders inherit BOPAlgo_Options'.
    return BOPAlgo_Options, BRepAlgoAPI_Algo


def serial_booleans() -> None:
    """Run every OCCT Boolean in this process serially, from now on."""
    owners = _owners()
    # The default for an operation nobody configures.
    owners[0].SetParallelMode_s(False)
    for owner in owners:
        current = owner.__dict__.get("SetRunParallel")
        if current is None or getattr(current, _SERIAL_MARK, False):
            continue
        owner.SetRunParallel = _serial_setter(current)


def booleans_are_serial() -> bool:
    """Whether :func:`serial_booleans` is in force in this process."""
    owners = _owners()
    return not owners[0].GetParallelMode_s() and all(
        getattr(owner.__dict__.get("SetRunParallel"), _SERIAL_MARK, False) for owner in owners
    )


__all__ = ["booleans_are_serial", "serial_booleans"]

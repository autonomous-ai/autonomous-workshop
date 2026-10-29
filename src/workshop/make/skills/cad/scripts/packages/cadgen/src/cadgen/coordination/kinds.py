"""What an artifact kind has to supply to get coordination for free.

Adding a coordinated artifact format should be a constant here, not another hand-placed
lock. Independent producers that each decided for themselves whether to lock are how a
cold ``cad inspect`` build once became invisible to the viewer and raced a viewer-started
build in the same directory.

A kind carries only what the coordination layer itself needs: a name for the status record
and the phase set its progress bar is weighted over. Freshness is deliberately NOT here --
``artifact_build`` takes ``is_current`` as a callable, so coordination calls freshness and
never decides what fresh means.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from cadgen.coordination.phases import (
    PHASE_COMPONENTS,
    PHASE_FINALIZE,
    PHASE_GENERATE,
    PHASE_PACKAGE,
)


@dataclass(frozen=True)
class ArtifactKind:
    """One coordinated output format.

    ``name``   identifies the kind in status records.
    ``phases`` the phases this kind actually has, in order. The progress bar is weighted
               over exactly these, so a kind with no meshing stage does not reserve half
               its bar for one.
    ``labels`` human text for phases this kind introduces. PHASE_LABELS covers the shared
               ones; a kind with novel phases supplies its own here rather than growing
               that global dict, so an unrelated kind's vocabulary never leaks into
               another's bar. Merged OVER the shared labels, so a kind may also override.
    """

    name: str
    phases: tuple[str, ...] = (PHASE_GENERATE, PHASE_PACKAGE, PHASE_COMPONENTS, PHASE_FINALIZE)
    labels: Mapping[str, str] = field(default_factory=dict)


# A component-GLB render package: assembly.json + content-addressed components/<cid>.glb.
STEP_PACKAGE = ArtifactKind(name="step-package")

# The only coordinated kind. A run that merely occupies a model's GENERATOR (inspect validate
# and interfere build the scene in memory) writes no package, so it is coordinated with
# generator_busy() against this kind rather than being a kind of its own. Add one here when
# something needs to coordinate a directory this one does not cover.

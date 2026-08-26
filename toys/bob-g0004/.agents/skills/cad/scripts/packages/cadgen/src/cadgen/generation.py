"""Public artifact-generation entry points.

The generation engine lives in :mod:`cadgen._internal.generation`; this module
re-exports the supported surface consumed by skill CLIs. Anything not exported
here is private and may change between releases.
"""

from cadgen._internal.generation import (
    generate_step_targets,
    targets_include_output_pairs,
)

__all__ = [
    "generate_step_targets",
    "targets_include_output_pairs",
]

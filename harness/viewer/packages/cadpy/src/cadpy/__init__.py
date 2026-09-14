"""Shared CAD artifact generation runtime."""

__all__ = ["ensure_step_glb_artifact", "validate_step_glb_artifact"]


def __getattr__(name: str):
    if name in __all__:
        from cadpy.api import ensure_step_glb_artifact, validate_step_glb_artifact

        return {
            "ensure_step_glb_artifact": ensure_step_glb_artifact,
            "validate_step_glb_artifact": validate_step_glb_artifact,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

"""Shared CAD artifact generation runtime."""

from typing import TYPE_CHECKING

__all__ = [
    "AssemblyHelper",
    "srgb",
    "srgb_to_linear",
    "linear_to_srgb",
    "is_legacy_linear",
    "display_channels",
    "linear_channels",
    "MateRelation",
    "MateTarget",
    "label_text",
    "label_shape",
    "target",
]


def __getattr__(name: str):
    if name in {"AssemblyHelper", "MateRelation", "MateTarget", "label_shape", "label_text", "target"}:
        from cadgen.assembly import AssemblyHelper, MateRelation, MateTarget, label_shape, label_text, target

        return {
            "AssemblyHelper": AssemblyHelper,
            "MateRelation": MateRelation,
            "MateTarget": MateTarget,
            "label_text": label_text,
            "label_shape": label_shape,
            "target": target,
        }[name]
    if name in {"srgb", "srgb_to_linear", "linear_to_srgb", "is_legacy_linear", "display_channels", "linear_channels"}:
        from cadgen import color

        return getattr(color, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


if TYPE_CHECKING:
    from cadgen.assembly import AssemblyHelper, MateRelation, MateTarget, label_shape, label_text, target
    from cadgen.color import display_channels, is_legacy_linear, linear_channels, linear_to_srgb, srgb, srgb_to_linear

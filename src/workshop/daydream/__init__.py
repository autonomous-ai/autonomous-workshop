"""Daydream: one Inventor dreams one brand-new toy idea before any Wish exists."""

from workshop.daydream.catalog import PriorWork, lint_novelty
from workshop.daydream.contracts import (
    DAYDREAM_IDEA_KIND,
    DAYDREAM_SEAL_KIND,
    DaydreamError,
    Idea,
    NoveltyReport,
    PriorArt,
    SealedDaydream,
    TasteFit,
    generate_daydream_id,
    render_brief,
)
from workshop.daydream.native import (
    DAYDREAM_TURN_TIMEOUT_SECONDS,
    DaydreamPaths,
    daydream_paths,
    list_daydreams,
    load_sealed_daydream,
    run_daydream,
    wish_from_daydream,
)
from workshop.daydream.loop import (
    DEFAULT_MAX_CONSECUTIVE_FAILURES,
    LoopLease,
    LoopState,
    acquire_loop,
    read_loop_state,
    request_stop,
)
from workshop.daydream.notebook import NotebookEntry
from workshop.daydream.prompt import DAYDREAM_CONSTITUTION, build_daydream_prompt
from workshop.daydream.seeds import DaydreamSeed, draw_seed

__all__ = [
    "DAYDREAM_CONSTITUTION",
    "DAYDREAM_IDEA_KIND",
    "DAYDREAM_SEAL_KIND",
    "DAYDREAM_TURN_TIMEOUT_SECONDS",
    "DEFAULT_MAX_CONSECUTIVE_FAILURES",
    "DaydreamError",
    "DaydreamPaths",
    "DaydreamSeed",
    "Idea",
    "LoopLease",
    "LoopState",
    "NotebookEntry",
    "NoveltyReport",
    "PriorArt",
    "PriorWork",
    "SealedDaydream",
    "TasteFit",
    "acquire_loop",
    "build_daydream_prompt",
    "daydream_paths",
    "draw_seed",
    "generate_daydream_id",
    "lint_novelty",
    "list_daydreams",
    "load_sealed_daydream",
    "read_loop_state",
    "render_brief",
    "request_stop",
    "run_daydream",
    "wish_from_daydream",
]

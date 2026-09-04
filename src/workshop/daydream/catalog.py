"""Prior work discovery and the deterministic novelty lint."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

from workshop.daydream._files import read_regular_bytes
from workshop.daydream.contracts import (
    DaydreamError,
    Idea,
    MAX_NOVELTY_NEIGHBORS,
    NoveltyNeighbor,
    NoveltyReport,
    bounded_line,
    bounded_paragraph,
)
from workshop.errors import ContractError


MAX_PRIOR_WORK_SOURCE_CHARS = 200
MAX_PRIOR_WORK_TITLE_CHARS = 200
MAX_PRIOR_WORK_SUMMARY_CHARS = 2_000
MAX_CATALOG_FILE_BYTES = 64 * 1024
MAX_BUNDLED_CATALOG_BYTES = 256 * 1024
MAX_BUNDLED_CATALOG_ENTRIES = 2_000
PRIOR_WORK_CATALOG_KIND = "autonomous-workshop.prior-work-catalog"
NOVELTY_MAX_SIMILARITY = 0.5
MIN_TOKEN_CHARS = 3
STOPWORDS = frozenset(
    (
        "the", "and", "for", "with", "that", "this", "from", "into", "onto",
        "your", "you", "one", "two", "when", "then", "than", "its", "it's",
        "are", "was", "were", "has", "have", "but", "not", "out", "over",
        "under", "on", "in", "of", "to", "a", "an", "is", "be", "by", "as",
        "at", "or", "so", "up", "down", "off", "all", "any", "each", "every",
        "very", "just", "also", "toy", "toys", "game", "games", "play",
        "piece", "pieces", "part", "parts", "print", "printed", "desk",
        "tiny", "small",
    )
)


@dataclass(frozen=True)
class PriorWork:
    """One thing that already exists, bounded for prompts and the lint."""

    source: str
    title: str
    summary: str

    def __post_init__(self) -> None:
        bounded_line(self.source, "prior work source", MAX_PRIOR_WORK_SOURCE_CHARS)
        bounded_line(self.title, "prior work title", MAX_PRIOR_WORK_TITLE_CHARS)
        bounded_paragraph(self.summary, "prior work summary", MAX_PRIOR_WORK_SUMMARY_CHARS)

    def to_dict(self) -> Dict[str, Any]:
        return {"source": self.source, "title": self.title, "summary": self.summary}


def _prior_work_or_none(source: str, title: Any, summary: Any) -> Optional[PriorWork]:
    if not isinstance(title, str) or not isinstance(summary, str):
        return None
    try:
        return PriorWork(
            source=source,
            title=title.strip()[:MAX_PRIOR_WORK_TITLE_CHARS],
            summary=" ".join(summary.split())[:MAX_PRIOR_WORK_SUMMARY_CHARS],
        )
    except ContractError:
        return None


def _read_catalog_text(path: Path) -> Optional[str]:
    try:
        return read_regular_bytes(
            path, maximum=MAX_CATALOG_FILE_BYTES, label="catalog file"
        ).decode("utf-8")
    except (OSError, DaydreamError, UnicodeDecodeError):
        return None


def _wish_prior_work(source: str, path: Path) -> Optional[PriorWork]:
    text = _read_catalog_text(path)
    if text is None:
        return None
    try:
        raw = json.loads(text)
    except (ValueError, RecursionError):
        return None
    if not isinstance(raw, Mapping):
        return None
    summary = raw.get("public_summary")
    if not isinstance(summary, str) or not summary.strip():
        summary = raw.get("objective")
    return _prior_work_or_none(source, raw.get("public_title"), summary)


def _readme_prior_work(source: str, path: Path) -> Optional[PriorWork]:
    text = _read_catalog_text(path)
    if text is None:
        return None
    lines = text.splitlines()
    if not lines or not lines[0].startswith("# "):
        return None
    title = lines[0][2:].strip()
    paragraph: list[str] = []
    for line in lines[1:]:
        stripped = line.strip()
        if not stripped:
            if paragraph:
                break
            continue
        if stripped.startswith(("![", "<", "#", "[", "|")):
            if paragraph:
                break
            continue
        paragraph.append(stripped)
    if not paragraph:
        return None
    return _prior_work_or_none(source, title, " ".join(paragraph))


def load_repository_prior_work(
    repository_root: Optional[Path],
) -> tuple[PriorWork, ...]:
    """Read the public toy catalog of a source checkout; malformed toys are skipped."""

    if repository_root is None:
        return ()
    toys = Path(repository_root) / "toys"
    if toys.is_symlink() or not toys.is_dir():
        return ()
    try:
        children = sorted(toys.iterdir(), key=lambda item: item.name)
    except OSError:
        return ()
    entries: list[PriorWork] = []
    for child in children:
        if child.is_symlink() or not child.is_dir():
            continue
        source = "toys/%s" % child.name
        entry = _wish_prior_work(source, child / "wish" / "wish.json")
        if entry is None:
            entry = _readme_prior_work(source, child / "README.md")
        if entry is not None:
            entries.append(entry)
    return tuple(entries)


def load_bundled_prior_work() -> tuple[PriorWork, ...]:
    """Load the release-bundled public portfolio used outside a source checkout."""

    try:
        payload = resources.files("workshop.daydream").joinpath("prior_work.json").read_bytes()
    except (OSError, TypeError) as exc:
        raise DaydreamError("bundled prior-work catalog is unavailable") from exc
    if not 1 <= len(payload) <= MAX_BUNDLED_CATALOG_BYTES:
        raise DaydreamError("bundled prior-work catalog exceeds its byte bound")
    try:
        raw = json.loads(payload.decode("utf-8"))
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise DaydreamError("bundled prior-work catalog is not valid UTF-8 JSON") from exc
    if (
        not isinstance(raw, Mapping)
        or set(raw) != {"schema_version", "kind", "entries"}
        or type(raw["schema_version"]) is not int
        or raw["schema_version"] != 1
        or raw["kind"] != PRIOR_WORK_CATALOG_KIND
        or not isinstance(raw["entries"], list)
        or not 1 <= len(raw["entries"]) <= MAX_BUNDLED_CATALOG_ENTRIES
    ):
        raise DaydreamError("bundled prior-work catalog contract is invalid")
    entries: list[PriorWork] = []
    for index, value in enumerate(raw["entries"]):
        if not isinstance(value, Mapping) or set(value) != {"source", "title", "summary"}:
            raise DaydreamError("bundled prior-work entry %d is invalid" % index)
        try:
            entries.append(PriorWork(**value))
        except (TypeError, ContractError) as exc:
            raise DaydreamError("bundled prior-work entry %d is invalid" % index) from exc
    if len({entry.source for entry in entries}) != len(entries):
        raise DaydreamError("bundled prior-work catalog repeats a source")
    return tuple(entries)


def load_prior_work(repository_root: Optional[Path]) -> tuple[PriorWork, ...]:
    """Merge the bundled release view with newer source-checkout entries."""

    merged = {entry.source: entry for entry in load_bundled_prior_work()}
    for entry in load_repository_prior_work(repository_root):
        merged[entry.source] = entry
    return tuple(merged[source] for source in sorted(merged))


def source_checkout_root() -> Optional[Path]:
    """Return the repository root when this module runs from a source checkout."""

    module = Path(__file__).resolve()
    if len(module.parents) < 4:
        return None
    candidate = module.parents[3]
    if (
        (candidate / "src" / "workshop" / "daydream" / "catalog.py").resolve() != module
        or not (candidate / "toys").is_dir()
        or not (candidate / ".agents" / "product-run" / "AGENTS.md").is_file()
    ):
        return None
    return candidate


def _words(text: str) -> list[str]:
    folded = "".join(
        character if character.isalnum() else " " for character in text.casefold()
    )
    return folded.split()


def normalize_title(text: str) -> str:
    """Lowercase a title and collapse every non-alphanumeric run to one space."""

    return " ".join(_words(text))


def content_tokens(text: str) -> frozenset[str]:
    """Return the distinctive lowercase words of a text for the novelty lint."""

    return frozenset(
        word
        for word in _words(text)
        if len(word) >= MIN_TOKEN_CHARS and word not in STOPWORDS
    )


def _jaccard(left: frozenset[str], right: frozenset[str]) -> float:
    union = left | right
    if not union:
        return 0.0
    return round(len(left & right) / len(union), 4)


def lint_novelty(idea: Idea, prior: Sequence[PriorWork]) -> NoveltyReport:
    """Reject an idea that repeats a title or re-tells an existing toy."""

    if not isinstance(idea, Idea):
        raise ContractError("lint_novelty requires an Idea")
    idea_title = normalize_title(idea.title)
    idea_tokens = content_tokens(
        " ".join((idea.title, idea.one_liner, idea.what_you_do, idea.what_happens))
    )
    # A catalog summary is one or two sentences; compare at that granularity
    # too, or a long idea could never score high against a short entry.
    headline_tokens = content_tokens("%s %s" % (idea.title, idea.one_liner))
    scored: list[tuple[float, PriorWork]] = []
    for entry in prior:
        if not isinstance(entry, PriorWork):
            raise ContractError("lint_novelty prior work must be PriorWork entries")
        if idea_title == normalize_title(entry.title):
            similarity = 1.0
        else:
            entry_tokens = content_tokens("%s %s" % (entry.title, entry.summary))
            similarity = max(
                _jaccard(idea_tokens, entry_tokens),
                _jaccard(headline_tokens, entry_tokens),
            )
        scored.append((similarity, entry))
    scored.sort(key=lambda item: (-item[0], item[1].title, item[1].source))
    nearest = tuple(
        NoveltyNeighbor(source=entry.source, title=entry.title, similarity=similarity)
        for similarity, entry in scored[:MAX_NOVELTY_NEIGHBORS]
    )
    if not nearest:
        return NoveltyReport(
            status="new",
            max_similarity=0.0,
            nearest=(),
            reason="no prior work to compare against",
        )
    top = nearest[0]
    if top.similarity >= NOVELTY_MAX_SIMILARITY:
        return NoveltyReport(
            status="too-close",
            max_similarity=top.similarity,
            nearest=nearest,
            reason="too close to %s (%s): similarity %.2f is at or above %.2f"
            % (top.title, top.source, top.similarity, NOVELTY_MAX_SIMILARITY),
        )
    return NoveltyReport(
        status="new",
        max_similarity=top.similarity,
        nearest=nearest,
        reason="nearest prior work is %s (%s) at similarity %.2f"
        % (top.title, top.source, top.similarity),
    )


def render_prior_work_markdown(prior: Sequence[PriorWork]) -> str:
    """Render the prior-work file the Inventor reads before dreaming."""

    lines = ["# Prior work (already exists — do not repeat)", ""]
    if not prior:
        lines.append("(none recorded yet)")
    for entry in prior:
        if not isinstance(entry, PriorWork):
            raise ContractError("render_prior_work_markdown requires PriorWork entries")
        lines.append(
            "- **%s** (%s): %s"
            % (entry.title, entry.source, " ".join(entry.summary.split()))
        )
    return "\n".join(lines) + "\n"


__all__ = [
    "MAX_CATALOG_FILE_BYTES",
    "NOVELTY_MAX_SIMILARITY",
    "PriorWork",
    "STOPWORDS",
    "content_tokens",
    "lint_novelty",
    "load_bundled_prior_work",
    "load_prior_work",
    "load_repository_prior_work",
    "normalize_title",
    "render_prior_work_markdown",
    "source_checkout_root",
]

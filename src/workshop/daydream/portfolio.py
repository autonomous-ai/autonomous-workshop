"""Cross-Inventor portfolio projection over the durable owner notebooks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from workshop.daydream.catalog import PriorWork
from workshop.daydream.contracts import require_inventor_id
from workshop.daydream.notebook import NotebookEntry, read_notebook
from workshop.errors import ContractError


MAX_PORTFOLIO_INVENTORS = 256
MAX_PORTFOLIO_ENTRIES = 2_000


@dataclass(frozen=True)
class PortfolioEntry:
    """One Inventor-owned memory viewed in the Workshop-wide portfolio."""

    inventor_id: str
    memory: NotebookEntry

    def __post_init__(self) -> None:
        require_inventor_id(self.inventor_id, "portfolio inventor_id")
        if not isinstance(self.memory, NotebookEntry):
            raise ContractError("portfolio memory must be a NotebookEntry")


def load_portfolio(
    daydreams_root: Path, *, exclude_inventor: str | None = None
) -> tuple[PortfolioEntry, ...]:
    """Project every real Inventor notebook into one bounded cross-owner view."""

    if exclude_inventor is not None:
        require_inventor_id(exclude_inventor, "excluded portfolio inventor_id")
    root = Path(daydreams_root)
    if not root.exists() and not root.is_symlink():
        return ()
    if root.is_symlink() or not root.is_dir():
        raise ContractError("portfolio root must be a real directory")
    children = sorted(root.iterdir(), key=lambda item: item.name)
    if len(children) > MAX_PORTFOLIO_INVENTORS:
        raise ContractError("portfolio exceeds its Inventor bound")
    entries: list[PortfolioEntry] = []
    for child in children:
        if child.is_symlink() or not child.is_dir() or child.name == exclude_inventor:
            continue
        try:
            inventor_id = require_inventor_id(child.name, "portfolio inventor_id")
        except ContractError:
            continue
        for memory in read_notebook(child / "NOTEBOOK.jsonl", limit=MAX_PORTFOLIO_ENTRIES):
            entries.append(PortfolioEntry(inventor_id=inventor_id, memory=memory))
            if len(entries) > MAX_PORTFOLIO_ENTRIES:
                raise ContractError("portfolio exceeds its entry bound")
    entries.sort(key=lambda entry: (entry.memory.created_at, entry.memory.daydream_id))
    return tuple(entries)


def render_portfolio_markdown(entries: Sequence[PortfolioEntry]) -> str:
    """Render structure and status so native judgment can reject reskins."""

    lines = ["# Workshop portfolio (all Inventors — do not repeat or reskin)", ""]
    if not entries:
        lines.append("(none recorded yet)")
    for entry in entries:
        if not isinstance(entry, PortfolioEntry):
            raise ContractError("render_portfolio_markdown requires PortfolioEntry items")
        memory = entry.memory
        lines.append(
            "- **%s** (%s, %s, %s): %s"
            % (
                memory.title,
                entry.inventor_id,
                memory.daydream_id,
                memory.status,
                memory.one_liner,
            )
        )
        if memory.structure is not None:
            lines.append(
                "  - Structure `%s`: %s -> %s -> %s"
                % (
                    memory.structure.sha256[:12],
                    " ".join(memory.structure.action.split()),
                    " ".join(memory.structure.response.split()),
                    " ".join(memory.structure.payoff.split()),
                )
            )
            lines.append(
                "  - Physical opportunity: %s"
                % " ".join(memory.structure.physical_opportunity.split())
            )
            lines.append(
                "  - Anti-generic signature: %s"
                % " ".join(memory.structure.anti_generic_signature.split())
            )
    return "\n".join(lines) + "\n"


def prior_work_from_portfolio(entries: Sequence[PortfolioEntry]) -> tuple[PriorWork, ...]:
    """Project portfolio traces into the conservative lexical novelty floor."""

    prior: list[PriorWork] = []
    for entry in entries:
        if not isinstance(entry, PortfolioEntry):
            raise ContractError("portfolio prior work requires PortfolioEntry items")
        memory = entry.memory
        fragments = [memory.one_liner]
        if memory.structure is not None:
            fragments.extend(
                (
                    memory.structure.physical_opportunity,
                    memory.structure.action,
                    memory.structure.response,
                    memory.structure.payoff,
                    memory.structure.anti_generic_signature,
                )
            )
        summary = " ".join(" ".join(fragment.split()) for fragment in fragments)
        prior.append(
            PriorWork(
                source="portfolio:%s:%s" % (entry.inventor_id, memory.daydream_id),
                title=memory.title,
                summary=summary[:2_000],
            )
        )
    return tuple(prior)


__all__ = [
    "MAX_PORTFOLIO_ENTRIES",
    "MAX_PORTFOLIO_INVENTORS",
    "PortfolioEntry",
    "load_portfolio",
    "prior_work_from_portfolio",
    "render_portfolio_markdown",
]

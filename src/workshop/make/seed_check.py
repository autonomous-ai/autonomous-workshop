"""The host's check of a seeded Make against its Approved Proof (ADR 0096).

Before Make is accepted in a run seeded with ``--seed-source``, the host runs
``proof_diff`` itself on each Component's sealed approved STEP
(``seed/approved/part_<id>.step``) and the STEP Make delivered. It is a
comparison of exact bytes, not a gate rerun (ADR 0061). It refuses:

- a Component whose latest round has no summary;
- a round locked by the approval as exact (``review.seed == "exact"``) whose
  B-rep identity is not the approved one, or whose delivered STEP is not
  within tolerance of the approved STEP;
- a round locked by the approval whose delivered STEP is over tolerance:
  a deviation over tolerance needs its Component Review;
- an assembly review carried from the Approved Proof
  (``make_round --carry-assembly-review``) when a Component deviated and the
  review does not name it with a basis that covers it: schema 10 covers no
  deviation; schema 11 (the partial carry) covers one within tolerance as
  ``within-tolerance`` or ``component-review``, and one over tolerance only
  as ``component-review``. A Component the review calls ``exact`` must be
  the approved B-rep.

Every Component whose identity is not the approved one is returned as a
seed deviation, for the receipt and ``workshop status --json``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Mapping

from workshop.errors import ContractError

SEED_APPROVAL = "seed-approval"
_ROUNDS = ("measure", "component-rounds")
_PART_KEYS = ("part", "passed", "volume_delta", "bbox_side_delta_mm", "two_way", "surface_deviation_mm")


def _default_compare(approved: Path, built: Path) -> dict[str, Any]:
    from workshop.make import proof_diff

    return proof_diff.compare(approved, built)


def latest_component_summary(project: Path, role: str) -> dict[str, Any]:
    """The summary of a Component's latest round; ContractError when none."""

    root = Path(project).joinpath(*_ROUNDS, role)
    try:
        state = json.loads((root / "make-round-state.json").read_text(encoding="utf-8"))
        round_index = int(state["round"])
        summary = json.loads((root / ("r%04d" % round_index) / "summary.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        raise ContractError("seed: %s has no readable latest component round" % role) from exc
    if not isinstance(summary, dict):
        raise ContractError("seed: %s's latest round summary is not an object" % role)
    return summary


def verify_made_seed(
    project: Path,
    run_root: Path,
    components: Mapping[str, Any],
    *,
    compare: Callable[[Path, Path], Mapping[str, Any]] = _default_compare,
) -> list[dict[str, Any]]:
    """Every seed deviation of the made Components, or ContractError."""

    deviations: list[dict[str, Any]] = []
    for role, approved in sorted(components.items()):
        if not isinstance(approved, Mapping) or not isinstance(approved.get("approved_step"), str):
            raise ContractError("seed: the approval holds no approved STEP for %s" % role)
        made = Path(project) / ("part_%s.step" % role)
        if not made.is_file():
            raise ContractError("seed: part_%s.step was not made" % role)
        summary = latest_component_summary(project, role)
        review = summary.get("review") if isinstance(summary.get("review"), dict) else {}
        by_seed = review.get("carried_from") == SEED_APPROVAL
        exact = summary.get("identity") == approved.get("identity")
        try:
            report = dict(compare(Path(run_root) / "seed" / approved["approved_step"], made))
        except Exception as exc:  # noqa: BLE001 - an unmeasured Component is over tolerance
            report = {"passed": None, "error": "%s: %s" % (type(exc).__name__, exc)}
        within = report.get("passed") is True
        if by_seed and review.get("seed") == "exact" and not exact:
            raise ContractError(
                "seed: %s's round claims the Approved Proof's Component, but its B-rep "
                "identity is not the approved one" % role
            )
        if exact and not within:
            raise ContractError(
                "seed: part_%s.step is not within tolerance of the approved STEP, though its "
                "round reports the approved B-rep" % role
            )
        if by_seed and not within:
            raise ContractError(
                "seed: %s deviates from the Approved Proof over tolerance and was locked "
                "without its Component Review" % role
            )
        if exact:
            continue
        deviation = {
            "component": role,
            "within_tolerance": within,
            "locked_by": SEED_APPROVAL if by_seed else "component-review",
            "parts": [{key: part.get(key) for key in _PART_KEYS}
                      for part in report.get("parts") or () if isinstance(part, Mapping)],
            "missing": list(report.get("missing") or ()),
            "extra": list(report.get("extra") or ()),
        }
        if "error" in report:
            deviation["error"] = report["error"]
        deviations.append(deviation)
    carried = _carried_assembly_review(Path(project))
    if carried is not None:
        _check_carried_bases(carried, deviations)
    return deviations


def _check_carried_bases(review: Mapping[str, Any], deviations: list[dict[str, Any]]) -> None:
    """Refuse a carried assembly review whose bases do not cover the
    deviations the host measured itself (ADR 0096 partial carry)."""

    bases = review.get("components") if review.get("schema_version") == 11 else None
    bases = bases if isinstance(bases, Mapping) else {}
    uncovered = []
    deviated = {item["component"]: item for item in deviations}
    for role, item in sorted(deviated.items()):
        basis = bases.get(role, {}).get("basis") if isinstance(bases.get(role), Mapping) else None
        allowed = ("within-tolerance", "component-review") if item["within_tolerance"] else ("component-review",)
        if basis not in allowed:
            uncovered.append(role)
    if uncovered:
        raise ContractError(
            "seed: the assembly review is carried from the Approved Proof, but %s deviated "
            "with no basis that carries it; the assembly needs the blind review" % ", ".join(uncovered)
        )


def _carried_assembly_review(project: Path) -> Mapping[str, Any] | None:
    """snap/SIGNATURE-REVIEW.json when it is carried from the Approved Proof."""

    try:
        review = json.loads((project / "snap" / "SIGNATURE-REVIEW.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return None
    return review if isinstance(review, dict) and review.get("carried_from") == SEED_APPROVAL else None


__all__ = ["SEED_APPROVAL", "latest_component_summary", "verify_made_seed"]

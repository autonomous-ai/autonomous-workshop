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

In a run that froze ADR 0102's review (``review_basis="approved-proof"``,
MAKE-OPTIONS schema 5) it also refuses a deviation locked by a Component
Review whose review was not taken against the Approved Proof: the review
must name ``basis: "approved-proof"`` and bind, by sha256, its round's
visual packet, which must compare with this Component's sealed approved
STEP and show no Reference Image. A run seeded before keeps its review
against the references.

In such a run whose seal carries the Approved Proof's assembly renders
(APPROVAL schema 3, ``assembly_renders``; ADR 0102's 2026-11-11 amendment)
it also refuses the last assembly round's look unless the Approved Proof's
assembly review carried to it (``carried_from: "seed-approval"``), or the
look that stands for it (that round's, or the earlier one it carried from)
was taken beside those sealed renders: its packet names
``basis: "approved-proof"``, binds exactly the sealed renders by sha256 and
no Reference Image, and its recorded feedback answers ``matches_approved``,
never ``matches_reference``. A seal without assembly renders keeps the
reference look.

ADR 0103: a schema 4 seal records ``contract_images``, the contract's
Reference and Guide Images replaced by renders of the approved Proof, and
the run seals exactly those bytes. Both checks above then read them as the
approved side: a deviation's packet must bind, as ``contract_images``,
exactly the seal's renders of its Component and show no other image, and
the assembly look exactly the seal's assembly renders.

Every Component whose identity is not the approved one is returned as a
seed deviation, for the receipt and ``workshop status --json``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Mapping

from workshop.errors import ContractError

SEED_APPROVAL = "seed-approval"
APPROVED_PROOF = "approved-proof"
_ROUNDS = ("measure", "component-rounds")
_ASSEMBLY_ROUNDS = ("measure", "rounds")
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
    review_basis: str | None = None,
    assembly_renders: Any = None,
    contract_images: Any = None,
) -> list[dict[str, Any]]:
    """Every seed deviation of the made Components, or ContractError.
    ``review_basis`` is what the run froze a deviation's review against:
    ``"approved-proof"`` (ADR 0102) or None (the Reference Images).
    ``assembly_renders`` is the seal's ``assembly_renders`` (APPROVAL schema
    3), or None for a seal that carries none. ``contract_images`` is a
    schema 4 seal's (ADR 0103), or None."""

    if review_basis not in (None, APPROVED_PROOF):
        raise ContractError("seed: unknown review basis %r" % (review_basis,))
    if review_basis == APPROVED_PROOF and contract_images is not None:
        check_assembly_look(Path(project), _images_of(contract_images, "assembly"), key="contract_images")
    elif review_basis == APPROVED_PROOF and assembly_renders is not None:
        check_assembly_look(Path(project), assembly_renders)

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
        # Issue #231: a comparison that could not run (a host environment
        # that cannot import the CAD kernel, say) is named, not reported as
        # a shape over tolerance.
        unmeasured = (
            "; the host could not compare them (%s)" % str(report["error"])[:300]
            if report.get("passed") is None and report.get("error") else ""
        )
        if by_seed and review.get("seed") == "exact" and not exact:
            raise ContractError(
                "seed: %s's round claims the Approved Proof's Component, but its B-rep "
                "identity is not the approved one" % role
            )
        if exact and not within:
            raise ContractError(
                "seed: part_%s.step is not within tolerance of the approved STEP, though its "
                "round reports the approved B-rep%s" % (role, unmeasured)
            )
        if by_seed and not within:
            raise ContractError(
                "seed: %s deviates from the Approved Proof over tolerance and was locked "
                "without its Component Review%s" % (role, unmeasured)
            )
        if exact:
            continue
        if review_basis == APPROVED_PROOF and not by_seed:
            _check_approved_proof_review(
                Path(project), role, review, approved,
                None if contract_images is None else _images_of(contract_images, "geometry:%s" % role))
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


def _images_of(contract_images: Any, shows: str) -> list[dict[str, Any]]:
    """The seal's Reference Image renders of ``shows`` (ADR 0103)."""

    if not isinstance(contract_images, list):
        raise ContractError("seed: the approval's contract_images is not a list")
    return [item for item in contract_images if isinstance(item, Mapping)
            and item.get("kind") == "reference" and item.get("shows") == shows]


def _check_approved_proof_review(project: Path, role: str, review: Mapping[str, Any],
                                 approved: Mapping[str, Any], images: Any = None) -> None:
    """Refuse a deviation's Component Review that was not taken against the
    Approved Proof (ADR 0102): the review names the basis and the packet it
    judged, and that packet, read from its round, compares with this
    Component's sealed approved STEP and binds no Reference Image."""

    where = "seed: %s deviates from the Approved Proof, and " % role
    if review.get("basis") != APPROVED_PROOF:
        raise ContractError(where + "its Component Review was not taken against the Approved Proof's render; "
                            "a seeded run reviews a visible deviation against the approved Component, never a "
                            "Reference Image")
    round_index = review.get("round")
    digest = review.get("packet_sha256")
    if type(round_index) is not int or round_index < 1 or not isinstance(digest, str):
        raise ContractError(where + "its Component Review names no round and packet")
    packet_path = project.joinpath(*_ROUNDS, role, "r%04d" % round_index, "visual-packet.json")
    try:
        content = packet_path.read_bytes()
        packet = json.loads(content)
    except (OSError, ValueError) as exc:
        raise ContractError(where + "the packet its Component Review judged is missing") from exc
    if hashlib.sha256(content).hexdigest() != digest:
        raise ContractError(where + "the packet its Component Review judged changed")
    shown = packet.get("approved") if isinstance(packet, dict) else None
    if (packet.get("basis") != APPROVED_PROOF or not isinstance(shown, dict)
            or not packet.get("comparisons")):
        raise ContractError(where + "the packet its Component Review judged does not compare it with the "
                            "Approved Proof's render")
    if packet.get("references"):
        raise ContractError(where + "the packet its Component Review judged shows a Reference Image")
    if images is not None:
        sealed = _sealed_render_hashes(images)
        if not sealed or shown.get("contract_images") != sealed:
            raise ContractError(where + "the packet its Component Review judged does not compare it with the "
                                "approved Proof renders the seal recorded")
        if not set(dict(shown.get("renders") or {}).values()) <= set(sealed.values()):
            raise ContractError(where + "the packet its Component Review judged shows renders that are not "
                                "the sealed ones")
        return
    if not isinstance(approved.get("step_sha256"), str) or shown.get("step_sha256") != approved["step_sha256"]:
        raise ContractError(where + "the packet its Component Review judged is not of the sealed approved STEP")

def _sealed_render_hashes(assembly_renders: Any) -> dict[str, str]:
    if not isinstance(assembly_renders, list):
        raise ContractError("seed: the approval's assembly_renders is not a list")
    hashes = {}
    for item in assembly_renders:
        if (not isinstance(item, Mapping) or not isinstance(item.get("file"), str)
                or not isinstance(item.get("sha256"), str)):
            raise ContractError("seed: the approval names an invalid assembly render")
        hashes[item["file"]] = item["sha256"]
    return hashes


def check_assembly_look(project: Path, assembly_renders: Any, key: str = "assembly_renders") -> None:
    """Refuse the last assembly round's look in a run that froze ADR 0102's
    review when it was not taken beside the Approved Proof's sealed assembly
    renders (the 2026-11-11 amendment); see the module docstring."""

    sealed = _sealed_render_hashes(assembly_renders)
    rounds = Path(project).joinpath(*_ASSEMBLY_ROUNDS)
    try:
        state = json.loads((Path(project) / "measure" / "make-round-state.json").read_text(encoding="utf-8"))
        latest = "r%04d" % int(state["round"])
        summary = json.loads((rounds / latest / "summary.json").read_text(encoding="utf-8"))
        visual = summary["visual"]
        status = visual["status"]
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        raise ContractError("seed: the Make has no readable last assembly round with a look") from exc
    if status == "carried" and visual.get("carried_from") == SEED_APPROVAL:
        return
    where = "seed: the last assembly round's look (%s) " % latest
    look = latest
    if status == "carried":
        look = visual.get("carried_from")
        if not isinstance(look, str) or not (rounds / look).is_dir() or "/" in look or look.startswith("."):
            raise ContractError(where + "carries from no assembly round")
        try:
            summary = json.loads((rounds / look / "summary.json").read_text(encoding="utf-8"))
            visual = summary["visual"]
        except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
            raise ContractError(where + "carries from %s, which has no readable look" % look) from exc
        where = "seed: the assembly look carried from %s " % look
    packet_path = rounds / look / "visual-packet.json"
    try:
        content = packet_path.read_bytes()
        packet = json.loads(content)
        feedback = json.loads((rounds / look / "visual-feedback.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise ContractError(where + "has no recorded look at a packet") from exc
    digest = hashlib.sha256(content).hexdigest()
    if visual.get("packet_sha256") != digest or feedback.get("packet_sha256") != digest:
        raise ContractError(where + "is of a packet that changed")
    shown = packet.get("approved") if isinstance(packet, dict) else None
    if packet.get("basis") != APPROVED_PROOF or not isinstance(shown, dict):
        raise ContractError(where + "was taken against the Reference Images; a seeded run that froze the "
                            "Approved Proof review looks at the assembly beside the Approved Proof's own "
                            "assembly renders, never a Reference Image (ADR 0102)")
    if packet.get("references"):
        raise ContractError(where + "shows a Reference Image")
    if shown.get(key) != sealed:
        raise ContractError(where + "does not compare with the Approved Proof's sealed assembly renders")
    if sorted(dict(shown.get("renders") or {}).values()) != sorted(sealed.values()):
        raise ContractError(where + "shows renders that are not the sealed ones")
    if "matches_reference" in feedback or "matches_approved" not in feedback:
        raise ContractError(where + "was not recorded against the Approved Proof (matches_approved)")


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


__all__ = ["APPROVED_PROOF", "SEED_APPROVAL", "check_assembly_look", "latest_component_summary",
           "verify_made_seed"]

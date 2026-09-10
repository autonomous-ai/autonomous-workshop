#!/usr/bin/env python3
"""Construct and reconcile motion review from the checker's declared poses.

States are tessellated in memory and bound by hash; no mesh reaches disk,
because STEP is the only geometry format this toolchain writes.

This validates the presented geometry, not physical dynamics or Wish fidelity.
The independent motion review and check_motion remain required.
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import io
import json
import runpy
import stat
from pathlib import Path, PurePosixPath

EVIDENCE = "snap/MOTION-EVIDENCE.json"
REVIEW = "snap/MOTION-REVIEW.json"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def read_file(project, relative, maximum=20 * 1024 * 1024):
    path = PurePosixPath(relative)
    if path.is_absolute() or not path.parts or any(p in (".", "..") for p in path.parts) or "\\" in relative:
        raise ValueError("unsafe motion evidence path")
    target = project
    for part in path.parts:
        target = target / part
        if target.is_symlink():
            raise ValueError("linked motion evidence is forbidden")
    info = target.stat()
    if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= maximum:
        raise ValueError("invalid motion evidence file")
    return target.read_bytes()


def digest(project, relative):
    return hashlib.sha256(read_file(project, relative)).hexdigest()


def sources(project):
    return {
        p.relative_to(project).as_posix(): digest(project, p.relative_to(project).as_posix())
        for p in sorted(project.rglob("*.py"))
        if not any(part in ("__cadgen__", "__pycache__", ".venv", ".git") for part in p.relative_to(project).parts)
    }


@functools.lru_cache(maxsize=1)
def state_tool():
    return runpy.run_path(str(Path(__file__).with_name("motion_states.py")))


def requires_motion_presentation(project):
    path = project / "measure/motion.json"
    if not path.exists() and not path.is_symlink():
        return False
    manifest = json.loads(read_file(project, "measure/motion.json"))
    def coupled(conditions):
        return any(c.get("check") == "coupled_motion_collision" or
                   (c.get("check") == "assembly_sequence" and coupled((c.get("inputs") or {}).get("steps", [])))
                   for c in conditions if isinstance(c, dict))
    return coupled(manifest.get("conditions", []))


def _check_animation(raw):
    from PIL import Image
    with Image.open(io.BytesIO(raw)) as im:
        if im.format != "GIF" or not 8 <= im.n_frames <= 48 or not 256 <= min(im.size) <= max(im.size) <= 1024:
            raise ValueError("motion presentation must be a bounded animated GIF")
        frames = set()
        for index in range(im.n_frames):
            im.seek(index)
            frames.add(hashlib.sha256(im.convert("RGB").tobytes()).hexdigest())
        if len(frames) < 3:
            raise ValueError("motion animation is static; choose a view that shows the declared action")


def _check_review(project, signature, evidence_raw):
    raw = read_file(project, REVIEW, 64 * 1024)
    review = json.loads(raw)
    expected = {"schema_version", "evidence_sha256", "concept_sha256", "reviewer", "review_rounds", "blind_motion_read", "motion_matches_wish", "simulation_not_physical_test"}
    if raw != canonical(review) or set(review) != expected or review["schema_version"] != 1:
        raise ValueError("invalid independent motion review")
    for key in ("concept_sha256", "reviewer", "review_rounds"):
        if review[key] != signature[key]:
            raise ValueError("motion review differs from the signature review")
    if review["evidence_sha256"] != hashlib.sha256(evidence_raw).hexdigest():
        raise ValueError("motion review has stale evidence")
    if review["motion_matches_wish"] is not True or review["simulation_not_physical_test"] is not True:
        raise ValueError("motion review must affirm the simulated motion, not physical testing")
    if not isinstance(review["blind_motion_read"], str) or not 1 <= len(review["blind_motion_read"].strip()) <= 2000:
        raise ValueError("motion review needs an independent motion observation")


def _bound_state_evidence(project):
    """Check source, manifest and state-byte bindings without CAD reconstruction."""
    raw = read_file(project, EVIDENCE, 64 * 1024)
    evidence = json.loads(raw)
    fields = {"schema_version", "kind", "sources", "assembly_entry", "states", "render", "animation_sha256", "motion_sha256"}
    if raw != canonical(evidence) or set(evidence) != fields or evidence["schema_version"] != 2 or evidence["kind"] != "declared-cad-motion-animation":
        raise ValueError("motion evidence must be schema 2; regenerate with motion_presentation.py from measure/motion.json")
    if not evidence["sources"] or evidence["sources"] != sources(project):
        raise ValueError("motion animation has stale CAD sources")
    if evidence["assembly_entry"] not in evidence["sources"]:
        raise ValueError("motion assembly entry must be a bound project source")
    if evidence["motion_sha256"] != digest(project, "measure/motion.json"):
        raise ValueError("motion animation has stale motion conditions")
    states = evidence["states"]
    if not isinstance(states, list) or not 8 <= len(states) <= 48:
        raise ValueError("motion presentation needs 8 to 48 ordered declared states")
    for row in states:
        if (not isinstance(row, dict) or set(row) != {"condition_id", "sample_index", "sha256"}
                or not isinstance(row["condition_id"], str) or type(row["sample_index"]) is not int
                or not isinstance(row["sha256"], str) or len(row["sha256"]) != 64):
            raise ValueError("motion animation has invalid or stale state geometry")
    identities = [(s["condition_id"], s["sample_index"]) for s in states]
    if len(set(identities)) != len(states) or len({s["sha256"] for s in states}) < 3:
        raise ValueError("motion animation needs distinct samples and geometry states")
    return raw, evidence


def describe_states(project):
    """Return caption data from declared samples, without approving geometry."""
    raw, evidence = _bound_state_evidence(project)
    manifest_raw = read_file(project, "measure/motion.json")
    if hashlib.sha256(manifest_raw).hexdigest() != evidence["motion_sha256"]:
        raise ValueError("motion conditions changed while describing states")
    identities = [{key: row[key] for key in ("condition_id", "sample_index")} for row in evidence["states"]]
    annotations = state_tool()["sample_annotations"](json.loads(manifest_raw), identities)
    rows = [{**state, "steps": annotation["steps"], "movers": annotation["movers"]}
            for state, annotation in zip(evidence["states"], annotations, strict=True)]
    final_raw, _ = _bound_state_evidence(project)
    if final_raw != raw:
        raise ValueError("motion evidence changed while describing states")
    return {"schema_version": 1, "kind": "declared-motion-sample-annotations",
            "evidence_sha256": hashlib.sha256(raw).hexdigest(),
            "motion_sha256": evidence["motion_sha256"], "assembly_entry": evidence["assembly_entry"],
            "geometry_reconciled_by_this_command": False,
            "scope": "Caption values from bound declarations; full motion presentation, mechanical checks and independent review remain required.",
            "states": rows}


def validate(project, signature_review):
    if not requires_motion_presentation(project) and not (project / REVIEW).exists():
        return
    raw, evidence = _bound_state_evidence(project)
    states = evidence["states"]
    animation = read_file(project, "snap/motion.gif")
    if evidence["animation_sha256"] != hashlib.sha256(animation).hexdigest():
        raise ValueError("motion animation hash mismatch")
    _check_animation(animation)
    _check_review(project, signature_review, raw)

    # Recompute after cheap provenance and review checks. A rehashed wrong state
    # or unrelated animation must not pass just because its metadata is current.
    tool = state_tool()
    tool["validate_render"](evidence["render"])
    manifest = json.loads(read_file(project, "measure/motion.json"))
    selected = {}
    for row in states:
        selected.setdefault(row["condition_id"], []).append(row["sample_index"])
    entry, expected = tool["construct"](project, manifest, selected)
    if entry != evidence["assembly_entry"] or len(expected) != len(states):
        raise ValueError("motion states differ from the declared assembly or conditions")
    for row, (identity, occurrences) in zip(states, expected):
        if any(row[key] != value for key, value in identity.items()):
            raise ValueError("motion states are not in declared condition/sample order")
        if row["sha256"] != hashlib.sha256(tool["state_bytes"](occurrences)).hexdigest():
            raise ValueError(f"motion state {row['condition_id']}[{row['sample_index']}] differs from the checked poses; regenerate the presentation")
    if evidence["animation_sha256"] != hashlib.sha256(tool["animation_bytes"](expected, evidence["render"])).hexdigest():
        raise ValueError("motion animation differs from its reconciled geometry and camera")
    if sources(project) != evidence["sources"] or digest(project, "measure/motion.json") != evidence["motion_sha256"]:
        raise ValueError("motion inputs changed during reconciliation")


def _write(project, relative, data):
    path = project
    for component in PurePosixPath(relative).parts:
        path = path / component
        if path.is_symlink():
            raise ValueError("linked motion output is forbidden")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not path.is_file():
        raise ValueError("motion output must be a regular file")
    path.write_bytes(data)


def generate(project, *, selections=None, frames=8, view="iso", size=600):
    tool = state_tool()
    manifest = json.loads(read_file(project, "measure/motion.json"))
    conditions = tool["coupled_conditions"](manifest)
    selections = dict(selections or {})
    if set(selections) - {c["id"] for c in conditions}:
        raise ValueError("sample selection names an unknown coupled condition")
    for condition in conditions:
        selections[condition["id"]] = tool["sample_indices"](condition, selections.get(condition["id"]), frames)
    source_hashes = sources(project)
    motion_hash = digest(project, "measure/motion.json")
    entry, states = tool["construct"](project, manifest, selections)
    _, azimuth, elevation = tool["helpers"]()[1]["parse_view"](view)
    render = {"azimuth": azimuth, "elevation": elevation, "size": size}
    animation = tool["animation_bytes"](states, render)
    _check_animation(animation)
    if source_hashes != sources(project) or motion_hash != digest(project, "measure/motion.json"):
        raise ValueError("motion inputs changed during generation")
    rows = []
    for identity, occurrences in states:
        # Bound by hash only: the state never reaches disk, and validation
        # rebuilds it from the same declared poses.
        data = tool["state_bytes"](occurrences)
        if len(data) > 20 * 1024 * 1024:
            raise ValueError("motion state exceeds the 20 MiB reconciliation limit")
        rows.append({**identity, "sha256": hashlib.sha256(data).hexdigest()})
    evidence = {"schema_version": 2, "kind": "declared-cad-motion-animation", "sources": source_hashes,
                "assembly_entry": entry, "states": rows, "render": render,
                "animation_sha256": hashlib.sha256(animation).hexdigest(), "motion_sha256": motion_hash}
    _write(project, "snap/motion.gif", animation)
    _write(project, EVIDENCE, canonical(evidence))
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--describe-states", action="store_true", help="print bound state identities and per-mover caption values without generating or verifying geometry")
    parser.add_argument("--frames", type=int, default=8, help="default sampled states per coupled condition (8 to 48)")
    parser.add_argument("--samples", action="append", default=[], metavar="CONDITION=0,1,...", help="explicit increasing indices from a condition's motion table")
    parser.add_argument("--view", default="iso", help="named view or AZ,EL")
    parser.add_argument("--size", type=int, default=600)
    args = parser.parse_args()
    try:
        if args.describe_states:
            if args.samples or args.frames != 8 or args.view != "iso" or args.size != 600:
                raise ValueError("--describe-states reads existing states; generation options do not apply")
            print(json.dumps(describe_states(args.project.resolve()), sort_keys=True, allow_nan=False))
            return
        if not 8 <= args.frames <= 48:
            raise ValueError("--frames must be 8 to 48")
        selected = {}
        for text in args.samples:
            ident, indices = text.split("=", 1)
            if ident in selected:
                raise ValueError("duplicate --samples condition")
            selected[ident] = [int(i) for i in indices.split(",")]
        generate(args.project.resolve(), selections=selected, frames=args.frames, view=args.view, size=args.size)
    except (OSError, ValueError, TypeError, KeyError, argparse.ArgumentTypeError) as exc:
        parser.error(str(exc))
    print("Wrote snap/motion.gif and snap/MOTION-EVIDENCE.json from reconciled declared poses; independent review and check_motion are still required.")


if __name__ == "__main__":
    main()

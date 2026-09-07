#!/usr/bin/env python3
"""Render exact state STLs and validate their bounded review provenance.

No dynamics or physical performance is inferred. The existing check_motion
gate remains responsible for the declared rigid-body conditions.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import runpy
import stat
from pathlib import Path, PurePosixPath

EVIDENCE = "snap/MOTION-EVIDENCE.json"
REVIEW = "snap/MOTION-REVIEW.json"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


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


def requires_motion_presentation(project):
    path = project / "measure/motion.json"
    if not path.exists() and not path.is_symlink():
        return False
    manifest = json.loads(read_file(project, "measure/motion.json"))
    # Typed declaration, not interpretation of Wish prose. Assembly-only
    # insertion/retention checks do not demand a running-product animation.
    return any(c.get("check") == "coupled_motion_collision" for c in manifest.get("conditions", []))


def validate(project, signature_review):
    if not requires_motion_presentation(project) and not (project / REVIEW).exists():
        return
    from PIL import Image

    raw = read_file(project, EVIDENCE, 64 * 1024)
    evidence = json.loads(raw)
    if raw != canonical(evidence) or set(evidence) != {"schema_version", "kind", "sources", "states", "animation_sha256", "motion_sha256"}:
        raise ValueError("invalid motion presentation evidence")
    if evidence["schema_version"] != 1 or evidence["kind"] != "exact-cad-state-animation":
        raise ValueError("invalid motion presentation identity")
    if not evidence["sources"] or evidence["sources"] != sources(project):
        raise ValueError("motion animation has stale CAD sources")
    states = evidence["states"]
    if not isinstance(states, list) or not 8 <= len(states) <= 48:
        raise ValueError("motion presentation needs 8 to 48 ordered exact STL states")
    for state in states:
        if set(state) != {"path", "sha256"} or not state["path"].endswith(".stl") or state["sha256"] != digest(project, state["path"]):
            raise ValueError("motion animation has stale state geometry")
    if len({s["sha256"] for s in states}) < 3:
        raise ValueError("motion animation needs distinct geometry states")
    if evidence["motion_sha256"] != digest(project, "measure/motion.json"):
        raise ValueError("motion animation has stale motion conditions")
    animation = read_file(project, "snap/motion.gif")
    if evidence["animation_sha256"] != hashlib.sha256(animation).hexdigest():
        raise ValueError("motion animation hash mismatch")
    with Image.open(io.BytesIO(animation)) as im:
        if im.format != "GIF" or not 8 <= im.n_frames <= 48 or not 256 <= min(im.size) <= max(im.size) <= 1024:
            raise ValueError("motion presentation must be a bounded animated GIF")
        frame_hashes = set()
        for index in range(im.n_frames):
            im.seek(index)
            frame_hashes.add(hashlib.sha256(im.convert("RGB").tobytes()).hexdigest())
        if len(frame_hashes) < 3:
            raise ValueError("motion animation is static")
    review_raw = read_file(project, REVIEW, 64 * 1024)
    review = json.loads(review_raw)
    expected = {"schema_version", "evidence_sha256", "concept_sha256", "reviewer", "review_rounds", "blind_motion_read", "motion_matches_wish", "simulation_not_physical_test"}
    if review_raw != canonical(review) or set(review) != expected or review["schema_version"] != 1:
        raise ValueError("invalid independent motion review")
    for key in ("concept_sha256", "reviewer", "review_rounds"):
        if review[key] != signature_review[key]:
            raise ValueError("motion review differs from the signature review")
    if review["evidence_sha256"] != hashlib.sha256(raw).hexdigest():
        raise ValueError("motion review has stale evidence")
    if review["motion_matches_wish"] is not True or review["simulation_not_physical_test"] is not True:
        raise ValueError("motion review must affirm the simulated motion, not physical testing")
    if not isinstance(review["blind_motion_read"], str) or not 1 <= len(review["blind_motion_read"].strip()) <= 2000:
        raise ValueError("motion review needs an independent motion observation")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--state-stl", action="append", required=True)
    args = parser.parse_args()
    project = args.project.resolve()
    if not 8 <= len(args.state_stl) <= 48:
        parser.error("supply 8 to 48 project-relative state STLs in cycle order")
    renderer = runpy.run_path(str(Path(__file__).with_name("render_product")))
    import numpy as np

    meshlib = renderer["_load_meshlib"]()
    states = []
    meshes = []
    for path in args.state_stl:
        states.append({"path": path, "sha256": digest(project, path)})
        meshes.append(meshlib.load_stl(project / path))
    framing = np.concatenate([m.reshape(-1, 3) for m in meshes])
    frames = [renderer["render"](m, size=600, view="iso", base=(45, 143, 145), accent=(227, 177, 73), background=(248, 245, 234), framing=framing) for m in meshes]
    (project / "snap").mkdir(exist_ok=True)
    frames[0].save(project / "snap/motion.gif", save_all=True, append_images=frames[1:], duration=120, loop=0, disposal=2)
    evidence = {"schema_version": 1, "kind": "exact-cad-state-animation", "sources": sources(project), "states": states, "animation_sha256": digest(project, "snap/motion.gif"), "motion_sha256": digest(project, "measure/motion.json")}
    (project / EVIDENCE).write_bytes(canonical(evidence))
    print("Wrote snap/motion.gif and snap/MOTION-EVIDENCE.json; simulation only. Independent review and check_motion are still required.")


if __name__ == "__main__":
    main()

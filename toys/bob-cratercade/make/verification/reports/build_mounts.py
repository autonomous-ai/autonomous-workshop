"""Build an exact catalog-hardware mount manifest from the recursive assembly.

No geometry is authored or changed. Run once again after final assembly edits;
an earlier probe cannot bind later canopy/apron geometry. Both output paths are
explicit so a documentation probe cannot overwrite measure/mounts.json.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps

PROJECT = Path(__file__).resolve().parents[1]
QUALIFIED = {
    "countersunk_socket_screw_m4_l0016_simple.step":
        ("bolt", "618c3cc10eebf249c53021abc0b8a5dd3bf8d297c8e64f13601952a47b924c73"),
    "iso4762_socket_head_cap_screw_m4x25.step":
        ("bolt", "fe23a5ff4ad2498848424d5e6f92d960099f99fbc093ff66ed5dae5cae74426e"),
    "thin_jam_nut_m4_simple.step":
        ("nut", "aeb7ae1544c06508860f1e4c29d4bf17944adbf12a0110a1ee12b7497008722b"),
}
FLEXIBLE_LABELS = {
    "flipper_left_rubber_band", "flipper_right_rubber_band", "launcher_rubber_band",
}
MIN_CLEARANCE_MM = 0.0  # Heads/nuts intentionally contact their bearing lands.
NEAR_DISTANCE_MM = 2.0
BOUNDS_PAD_MM = 1e-5
POSE_TOL = 1e-8
REL_VOLUME_TOL = 1e-8


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def shape_volume(shape):
    """OCC intersections may be a ShapeList rather than one Shape."""
    if shape is None:
        return 0.0
    if hasattr(shape, "wrapped"):
        # Adaptive integration keeps analytic supplier and equivalent NURBS
        # representations comparable without changing identity tolerances.
        props = GProp_GProps()
        BRepGProp.VolumeProperties_s(shape.wrapped, props, 1e-12, False, False)
        return float(props.Mass())
    return sum(shape_volume(item) for item in shape)


def source_hashes():
    return {str(path.relative_to(PROJECT)): sha256(path)
            for path in sorted(PROJECT.rglob("*.py"))
            if path.relative_to(PROJECT).parts[0] not in ("measure", "__cadgen__")
            and "__pycache__" not in path.parts}


def write_json(path, data):
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def matrix(location):
    transform = location.wrapped.Transformation()
    return [[transform.Value(r, c) for c in range(1, 5)] for r in range(1, 4)]


def matrix_error(a, b):
    return max(abs(x-y) for ar, br in zip(matrix(a), matrix(b))
               for x, y in zip(ar, br))


def pose_dict(location):
    position, rotation = tuple(location)
    return {"position": list(position), "rotation": list(rotation)}


def bounds(shape):
    box = shape.bounding_box()
    return [list(box.min), list(box.max)]


def lower_bound(a, b):
    """Euclidean distance between expanded containing AABBs, hence a lower bound."""
    gaps = [max(a[0][i]-b[1][i]-2*BOUNDS_PAD_MM,
                b[0][i]-a[1][i]-2*BOUNDS_PAD_MM, 0.0) for i in range(3)]
    return math.sqrt(sum(gap*gap for gap in gaps))


def recursive_leaves(root):
    """Keep assembly leaves, including actual hardware inside the rocker group."""
    found = []

    def walk(node, trail):
        label = getattr(node, "label", "") or ""
        path = trail + ([label] if label else [])
        children = list(getattr(node, "children", ()) or ())
        if children:
            for child in children:
                walk(child, path)
            return
        if not label or not list(node.solids()):
            raise ValueError(f"Unlabelled or non-solid assembly leaf: {path}")
        # check_mount indexes original leaf shapes. A nonidentity parent pose
        # would make that gate's obstacles local rather than world geometry.
        error = matrix_error(node.location, node.global_location)
        if error > POSE_TOL:
            raise ValueError(f"Gate-indexed leaf {label} is not in world pose: {error}")
        from build123d import Compound
        world = Compound.cast(node.wrapped).located(node.global_location)
        world.label = label
        world.color = node.color
        found.append({"label": label, "path": ".".join(path), "shape": world,
                      "pose": node.global_location, "bbox": bounds(world),
                      "color": list(node.color) if node.color is not None else None,
                      "gate_pose_error": error})

    walk(root, [])
    counts = Counter(row["label"] for row in found)
    if duplicate := sorted(label for label, count in counts.items() if count != 1):
        raise ValueError(f"Assembly leaf labels are not unique: {duplicate}")
    return sorted(found, key=lambda row: row["label"])


def catalog():
    import cadmount
    actual = {p.name for p in (PROJECT / "ref").iterdir()
              if p.is_file() and p.suffix.lower() in (".step", ".stp")}
    if actual != set(QUALIFIED):
        raise ValueError(f"Qualified ref STEP set changed: {sorted(actual)}")
    result = []
    for filename, (kind, expected) in sorted(QUALIFIED.items()):
        path = PROJECT / "ref" / filename
        digest = sha256(path)
        if digest != expected:
            raise ValueError(f"Unqualified changed catalog bytes: {filename}: {digest}")
        shape = cadmount.load(str(path))
        if kind == "nut":
            # Match the qualified supplier representation used by the product.
            # Mixed analytic/NURBS coincident Booleans can fail on mirrored
            # inclined placements. Supplier bytes and identity tolerances stay
            # unchanged; all 199 converted installed nuts passed native validity.
            from build123d import Solid
            from OCP.BRepBuilderAPI import BRepBuilderAPI_NurbsConvert
            shape = Solid.cast(BRepBuilderAPI_NurbsConvert(shape.wrapped, True).Shape())
        result.append({"path": str(path.relative_to(PROJECT)), "sha256": digest,
                       "kind": kind, "shape": shape, "volume": shape_volume(shape)})
    return result


def identify(leaf, references):
    label, actual = leaf["label"], leaf["shape"]
    kind = "bolt" if label.endswith("_bolt") else "nut" if label.endswith("_nut") else None
    volume = shape_volume(actual)
    candidates = [row for row in references
                  if abs(volume-row["volume"]) <= max(1e-7, REL_VOLUME_TOL*row["volume"])]
    if kind is None:
        if candidates:
            raise ValueError(f"Catalog-volume leaf lacks a bolt/nut label: {label}")
        return None
    candidates = [row for row in candidates if row["kind"] == kind]
    if len(candidates) != 1:
        raise ValueError(f"Cannot uniquely qualify hardware {label}, volume {volume}")
    reference = candidates[0]
    pose = leaf["pose"] * reference["shape"].location.inverse()
    # Verify the serialized pose with the same Location constructor as the gate.
    from build123d import Location, Pos, Rot
    at = pose_dict(pose)
    replay = Location(at["position"], at["rotation"])
    replay_error = matrix_error(pose, replay)
    placed = replay * reference["shape"]
    common = placed.intersect(actual)
    common_volume = shape_volume(common)
    residual = abs(shape_volume(placed)+volume-2*common_volume)
    bbox_error = max(abs(x-y) for a, b in zip(bounds(placed), leaf["bbox"])
                     for x, y in zip(a, b))
    tolerance = max(1e-7, REL_VOLUME_TOL*reference["volume"])
    recovery = None
    if bbox_error > 1e-5 or residual > tolerance:
        # A mirrored source shape can bake its reflection into its BRep while
        # keeping only a translation in Location. Catalog hardware is achiral;
        # recover a proper rigid pose, never substitute the mirrored shape.
        # Each candidate must pass the same full BRep identity test below.
        for tilt in ((0,0,0),(180,0,0),(0,180,0),(90,0,0),(-90,0,0),(0,90,0),(0,-90,0)):
            for spin in range(0,360,30):
                candidate = pose * Rot(*tilt) * Rot(0,0,spin)
                trial = candidate * reference["shape"]
                trial_bounds = bounds(trial)
                delta = [(leaf["bbox"][0][i]+leaf["bbox"][1][i]
                          -trial_bounds[0][i]-trial_bounds[1][i])/2 for i in range(3)]
                candidate = Pos(*delta) * candidate
                trial = candidate * reference["shape"]
                error = max(abs(x-y) for a,b in zip(bounds(trial),leaf["bbox"]) for x,y in zip(a,b))
                if error > 1e-5:
                    continue
                difference = abs(shape_volume(trial)+volume-2*shape_volume(trial.intersect(actual)))
                if difference <= tolerance:
                    pose = candidate
                    at = pose_dict(pose)
                    replay = Location(at["position"], at["rotation"])
                    replay_error = matrix_error(pose,replay)
                    placed = replay * reference["shape"]
                    residual = abs(shape_volume(placed)+volume-2*shape_volume(placed.intersect(actual)))
                    bbox_error = max(abs(x-y) for a,b in zip(bounds(placed),leaf["bbox"]) for x,y in zip(a,b))
                    recovery = {"tilt_degrees": list(tilt), "spin_degrees": spin,
                                "translation_mm": delta}
                    break
            if recovery is not None:
                break
    if replay_error > POSE_TOL or bbox_error > 1e-5 or residual > tolerance:
        raise ValueError(f"Catalog pose geometry mismatch for {label}: "
                         f"pose={replay_error}, bbox={bbox_error}, volume={residual}")
    return reference, at, {"catalog_volume_mm3": reference["volume"],
                           "leaf_volume_mm3": volume,
                           "symmetric_difference_volume_mm3": residual,
                           "volume_tolerance_mm3": tolerance,
                           "bbox_max_delta_mm": bbox_error,
                           "serialized_pose_max_delta": replay_error,
                           "baked_geometry_pose_recovery": recovery}


def build(output, evidence_path):
    before = source_hashes()
    references = catalog()
    entry = PROJECT / "cratercade.step.py"
    spec = importlib.util.spec_from_file_location("_mount_manifest_entry", entry)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    print("Building current recursive assembly", file=sys.stderr, flush=True)
    root = module.gen_step()
    leaves = recursive_leaves(root)
    print(f"Qualifying catalog poses across {len(leaves)} recursive leaves",
          file=sys.stderr, flush=True)
    write_json(evidence_path, {"status": "checking-catalog-poses", "source_sha256": before,
                              "assembly_leaf_count": len(leaves), "manifest_written": False})
    rigid = [leaf for leaf in leaves if leaf["label"] not in FLEXIBLE_LABELS]
    rows, proofs = [], []
    for leaf in leaves:
        match = identify(leaf, references)
        if match is None:
            continue
        reference, at, identity = match
        nearby, omitted = [], []
        for other in rigid:
            if other["label"] == leaf["label"]:
                continue
            distance = lower_bound(leaf["bbox"], other["bbox"])
            if distance <= NEAR_DISTANCE_MM:
                nearby.append(other["label"])
            else:
                assert distance > MIN_CLEARANCE_MM
                omitted.append({"label": other["label"], "aabb_lower_bound_mm": distance})
        if not nearby:
            raise ValueError(f"No nearby rigid seat for {leaf['label']}")
        rows.append({"id": leaf["label"], "component": reference["path"],
                     "sha256": reference["sha256"], "at": at, "parts": nearby,
                     "bolts": False, "min_clearance": MIN_CLEARANCE_MM})
        proofs.append({"label": leaf["label"], "path": leaf["path"],
                       "color_rgba": leaf["color"], "at": at, "identity": identity,
                       "included_rigid_obstacles": nearby,
                       "omitted_rigid_obstacles": omitted,
                       "omitted_min_lower_bound_mm": min((r["aabb_lower_bound_mm"]
                                                           for r in omitted), default=None)})
    if {row["component"] for row in rows} != {r["path"] for r in references}:
        raise ValueError("Not every qualified reference occurs in the assembly")
    after = source_hashes()
    if before != after or any(sha256(PROJECT/r["path"]) != r["sha256"] for r in references):
        write_json(evidence_path, {"status": "failed-source-changed", "source_before": before,
                                  "source_after": after, "candidate_mount_count": len(rows),
                                  "mount_proofs": proofs, "manifest_written": False})
        raise ValueError("CAD source/reference bytes changed during manifest build; rerun")
    manifest = {"assembly": "cratercade.step.py", "mounts": rows}
    evidence = {"schema": 1, "builder_sha256": sha256(__file__),
                "source_sha256": before, "catalog_sha256": {r["path"]: r["sha256"] for r in references},
                "assembly_leaf_count": len(leaves), "mount_count": len(rows),
                "canopy_leaf_count": sum(r["label"].startswith("canopy_") for r in leaves),
                "apron_leaf_count": sum(r["label"] in ("apron_left", "apron_right") for r in leaves),
                "mount_counts_by_component": dict(Counter(row["component"] for row in rows)),
                "excluded_flexible_leaves": sorted(set(FLEXIBLE_LABELS) & {r["label"] for r in leaves}),
                "min_clearance_mm": MIN_CLEARANCE_MM, "near_distance_mm": NEAR_DISTANCE_MM,
                "aabb_padding_per_coordinate_mm": BOUNDS_PAD_MM,
                "pruning_proof": "Expanded AABBs contain each BRep. Their Euclidean distance "
                                 "is a lower bound on solid distance. Every omitted rigid leaf "
                                 "has that bound > near_distance_mm > min_clearance_mm.",
                "leaves": [{"label": r["label"], "path": r["path"], "bbox_mm": r["bbox"],
                            "color_rgba": r["color"], "at": pose_dict(r["pose"]),
                            "gate_local_world_pose_error": r["gate_pose_error"]} for r in leaves],
                "mount_proofs": proofs,
                "limitations": ["Static catalog pose/identity and conservative obstacle coverage only; "
                                "this builder does not run check_mount or prove access, motion, printing or physical fit.",
                                "Regenerate after final assembly changes, including canopy/apron integration."]}
    payload = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    evidence["manifest_sha256"] = hashlib.sha256(payload.encode()).hexdigest()
    write_json(evidence_path, evidence)
    write_json(output, manifest)
    return {"mounts": len(rows), "leaves": len(leaves), "manifest": str(Path(output).resolve()),
            "manifest_sha256": evidence["manifest_sha256"], "evidence": str(Path(evidence_path).resolve())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--evidence", required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(PROJECT))
    skill_scripts = PROJECT.parents[4] / ".agents" / "skills" / "cad" / "scripts"
    sys.path.insert(0, str(skill_scripts))
    try:
        result = build(args.output, args.evidence)
    except Exception as error:
        report = Path(args.evidence)
        partial = json.loads(report.read_text()) if report.is_file() else {}
        partial.update({"status": "failed", "error": f"{type(error).__name__}: {error}",
                        "manifest_written": False})
        write_json(report, partial)
        raise
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()

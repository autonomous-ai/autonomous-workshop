"""Prove how far a recovered solid is from the STEP it came from.

Comparing volumes alone passes shapes that are wrong in compensating ways, so
the decisive metric here is the symmetric difference: the material in one
solid and not the other, both ways round, as a fraction of the original.
Zero means the recovery is exact.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from OCP.BRepAlgoAPI import BRepAlgoAPI_Common, BRepAlgoAPI_Cut
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.TopAbs import TopAbs_IN, TopAbs_ON
from OCP.TopTools import TopTools_ListOfShape
from OCP.gp import gp_Pnt
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps

sys.path.insert(0, str(Path(__file__).resolve().parent))
from step_probe import analyse, bbox, read_step  # noqa: E402


def volume(shape):
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, props)
    return abs(props.Mass())


# OpenCASCADE booleans go degenerate when two solids share many coincident
# faces, which is exactly the case here: a good recovery matches the original
# almost everywhere. Rather than hide that behind one loose tolerance, escalate
# the fuzzy value only as far as needed and report which one was used, so the
# precision floor of every number below is visible.
FUZZ_LADDER = (0.0, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3)


def _as_list(shape):
    items = TopTools_ListOfShape()
    items.Append(shape)
    return items


def _boolean(op, a, b, fuzz):
    builder = op()
    builder.SetArguments(_as_list(a))
    builder.SetTools(_as_list(b))
    if fuzz:
        builder.SetFuzzyValue(fuzz)
    builder.SetRunParallel(True)
    builder.Build()
    if not builder.IsDone():
        return None
    return builder.Shape()


def _booleans_at(a, b, fuzz):
    shared = _boolean(BRepAlgoAPI_Common, a, b, fuzz)
    if shared is None:
        return None
    missing = _boolean(BRepAlgoAPI_Cut, a, b, fuzz)
    extra = _boolean(BRepAlgoAPI_Cut, b, a, fuzz)
    if missing is None or extra is None:
        return None
    return volume(shared), volume(missing), volume(extra)


def _sampled_difference(a, b, samples, seed=12345):
    """Fallback when booleans fail outright: classify random points in both.

    Returns the symmetric-difference fraction with a 95% interval, because a
    sampled answer that reports no uncertainty would be the misleading one.
    """
    import random

    box_a, box_b = bbox(a, 6), bbox(b, 6)
    lo = [min(box_a["min"][i], box_b["min"][i]) for i in range(3)]
    hi = [max(box_a["max"][i], box_b["max"][i]) for i in range(3)]
    span = [hi[i] - lo[i] for i in range(3)]
    box_volume = span[0] * span[1] * span[2]

    class_a = BRepClass3d_SolidClassifier(a)
    class_b = BRepClass3d_SolidClassifier(b)
    rng = random.Random(seed)
    inside = {"a": 0, "b": 0, "xor": 0}
    for _ in range(samples):
        point = gp_Pnt(*[lo[i] + rng.random() * span[i] for i in range(3)])
        class_a.Perform(point, 1e-7)
        class_b.Perform(point, 1e-7)
        in_a = class_a.State() in (TopAbs_IN, TopAbs_ON)
        in_b = class_b.State() in (TopAbs_IN, TopAbs_ON)
        inside["a"] += in_a
        inside["b"] += in_b
        inside["xor"] += in_a != in_b
    fraction = inside["xor"] / samples
    stderr = (fraction * (1 - fraction) / samples) ** 0.5
    vol_a = inside["a"] / samples * box_volume
    return {
        "method": "sampled",
        "samples": samples,
        "xorVolume": fraction * box_volume,
        "xorFractionOfOriginal": (fraction * box_volume / vol_a) if vol_a else float("nan"),
        "ci95VolumeHalfWidth": 1.96 * stderr * box_volume,
    }


def compare(original, rebuilt, digits=4, samples=200000):
    vol_a, vol_b = volume(original), volume(rebuilt)

    result = None
    used_fuzz = None
    for fuzz in FUZZ_LADDER:
        attempt = _booleans_at(original, rebuilt, fuzz)
        if attempt is None:
            continue
        shared, missing, extra = attempt
        # Two solids of positive volume that share a bounding box cannot have
        # an empty intersection: an empty one means the boolean gave up.
        if shared > 0 or vol_a == 0 or vol_b == 0:
            result = attempt
            used_fuzz = fuzz
            break

    box_a, box_b = bbox(original, digits), bbox(rebuilt, digits)
    face_a = analyse(original, digits, 0)
    face_b = analyse(rebuilt, digits, 0)
    report = {
        "volumeOriginal": round(vol_a, digits),
        "volumeRebuilt": round(vol_b, digits),
        "volumeDeltaPct": round(100 * (vol_b - vol_a) / (vol_a or 1.0), 4),
        "bboxOriginal": box_a["size"],
        "bboxRebuilt": box_b["size"],
        "bboxMatch": box_a["size"] == box_b["size"],
        "faceCountOriginal": face_a["faceCount"],
        "faceCountRebuilt": face_b["faceCount"],
        "faceKindsOriginal": face_a["faceKinds"],
        "faceKindsRebuilt": face_b["faceKinds"],
        "faceKindsMatch": face_a["faceKinds"] == face_b["faceKinds"],
    }

    if result is not None:
        shared, missing, extra = result
        error = (missing + extra) / (vol_a or 1.0)
        report.update({
            "method": "exact boolean",
            "fuzzyValue": used_fuzz,
            "precisionFloorMm": used_fuzz,
            "missingVolume": round(missing, digits),
            "extraVolume": round(extra, digits),
            "sharedVolume": round(shared, digits),
            "symmetricDifferencePct": round(100 * error, 4),
            "matchPct": round(100 * (1 - error), 4),
        })
    else:
        sampled = _sampled_difference(original, rebuilt, samples)
        error = sampled["xorFractionOfOriginal"]
        report.update({
            "method": "sampled (booleans failed at every tolerance)",
            "samples": sampled["samples"],
            "symmetricDifferencePct": round(100 * error, 4),
            "matchPct": round(100 * (1 - error), 4),
            "ci95VolumeHalfWidth": round(sampled["ci95VolumeHalfWidth"], digits),
        })
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="step_verify.py",
        description="Measure how closely a rebuilt STEP matches the original.")
    parser.add_argument("original", type=Path)
    parser.add_argument("rebuilt", type=Path)
    parser.add_argument("--digits", type=int, default=4)
    parser.add_argument("--json", action="store_true", help="Emit the full report as JSON.")
    parser.add_argument("--samples", type=int, default=200000,
                        help="Points for the sampled fallback (default 200000).")
    parser.add_argument("--tolerance", type=float, default=0.01,
                        help="Max symmetric difference in percent before this "
                             "exits non-zero (default 0.01).")
    args = parser.parse_args(argv)

    report = compare(read_step(args.original), read_step(args.rebuilt),
                     args.digits, args.samples)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"original : {args.original.name}")
        print(f"rebuilt  : {args.rebuilt.name}")
        print(f"  method            {report['method']}"
              + (f" (fuzz {report['fuzzyValue']:g} mm)" if report.get("fuzzyValue") else ""))
        print(f"  volume            {report['volumeOriginal']}  ->  "
              f"{report['volumeRebuilt']}   ({report['volumeDeltaPct']:+.4f}%)")
        if "missingVolume" in report:
            print(f"  missing material  {report['missingVolume']}")
            print(f"  extra material    {report['extraVolume']}")
        print(f"  symmetric diff    {report['symmetricDifferencePct']:.4f}%")
        print(f"  MATCH             {report['matchPct']:.4f}%")
        print(f"  bbox              {report['bboxOriginal']} -> {report['bboxRebuilt']}"
              f"   {'same' if report['bboxMatch'] else 'DIFFERENT'}")
        print(f"  faces             {report['faceCountOriginal']} -> "
              f"{report['faceCountRebuilt']}"
              f"   {'same kinds' if report['faceKindsMatch'] else 'KINDS DIFFER'}")
        print(f"    original        {report['faceKindsOriginal']}")
        print(f"    rebuilt         {report['faceKindsRebuilt']}")
        if not report["faceKindsMatch"]:
            lost = set(report["faceKindsOriginal"]) - set(report["faceKindsRebuilt"])
            if lost:
                print(f"    lost surface types: {', '.join(sorted(lost))}"
                      f"  <- a feature was dropped, not just shifted")

    over = report["symmetricDifferencePct"] > args.tolerance
    if over:
        print(f"\nFAIL: {report['symmetricDifferencePct']:.4f}% differs, "
              f"tolerance is {args.tolerance}%", file=sys.stderr)
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())

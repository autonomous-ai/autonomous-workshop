import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def write(name, value):
    (HERE / name).write_bytes(canonical(value))


omission = {
    "schema_version": 1,
    "kind": "autonomous-workshop.playtest-omission",
    "status": "not-run",
    "reason": "Playtest is deferred for this Release.",
}
omission_hash = hashlib.sha256(canonical(omission)).hexdigest()
write("PLAYTEST-NOT-RUN.json", omission)

product = {
    "schema_version": 5,
    "kind": "workshop.release-package",
    "status": "manual-ready",
    "title": "Tempest Lull",
    "summary": "A palm-sized, one-piece storm-cloud desk rocker whose connected lightning bolt sweeps through the open arch as the whole body rocks and returns toward center.",
    "what_arrives": ["1 Tempest Lull one-piece rocker", "1 double-sided owner card"],
    "limitations": ["Playtest was not run for this Spark release.", "Real print finish, durability, tabletop behavior, and rocking duration have not been physically verified."],
    "product_artifact_sha256": "04bdde10ee3a9d045bf4caf2ed6c6abb614e2db7dbb838bde1c981dc1e1edc04",
    "playtest_status": "not-run",
    "playtest_evidence_artifact_sha256": omission_hash,
    "claims": {
        "playtest": {
            "status": "not-run",
            "claims": [],
            "evidence_ref": "PLAYTEST-NOT-RUN.json",
            "evidence_sha256": omission_hash,
        }
    },
}
write("product.json", product)

manual_hash = hashlib.sha256((HERE / "MANUAL.pdf").read_bytes()).hexdigest()
evidence = {
    "schema_version": 1,
    "kind": "autonomous-workshop.manual-design-evidence",
    "manual_sha256": manual_hash,
    "design_mode": "bespoke",
    "creative_brief": {
        "emotional_promise": "A small storm becomes a calm, repeatable desk ritual: one gentle nudge, a visible sweep, and a return to rest.",
        "physical_format": "Double-sided 5 x 7 inch portrait owner card",
        "format_rationale": "The product is one connected piece with no assembly or rule system, so two sides hold the complete first-use, recovery, care, and safety path without needless pages.",
        "visual_motif": "Rounded storm panels, crescent motion marks, and exact Made renders turn the card itself into a quiet storm-and-lightning composition.",
        "palette": ["Midnight navy #15243A", "Rain blue #4D87A8", "Lightning gold #F2B544", "Cloud white #FFFDF7", "Mist blue #EAF3F5"],
        "typography": ["Vera Bold for display and action headings", "Vera Regular for owner instructions"],
        "teaching_arc": ["Recognize the exact toy and one-piece inventory", "Orient the crescent keel downward", "Place on a clean level hard surface", "Nudge one cloud cheek", "Release and follow rest-to-crest-to-return motion", "Reset, troubleshoot, care for, and use safely"],
    },
    "product_visuals": [
        {"source_path": "cad/snap/iso.png", "source_sha256": "926bbc23749c4fc9ea9fa7d4d9478f3fa67a2f569c5b036d9ea03cb2fa463249", "pages": [1]},
        {"source_path": "cad/snap/signature.png", "source_sha256": "ca4e59ebaef0f7a86da05f6d2473b9c932a85d43f3fb0aabc6b026b4410c48b1", "pages": [2]},
    ],
    "review": {
        "page_count": 2,
        "color_pages": [1, 2],
        "grayscale_pages": [1, 2],
        "first_time_owner_pass": True,
        "independent_reviewer": "native-subagent",
        "findings": ["The three pose renders differed too subtly in grayscale to teach the motion without an explicit directional path.", "The fixed-bolt wording could appear to conflict with the instruction to watch the bolt sweep.", "The initial keel-down cue was crowded and abstract."],
        "resolved_changes": ["Added directional arrows across the exact REST to CREST to RETURN strip so motion survives grayscale.", "Clarified that the fixed bolt moves with the whole rocker.", "Simplified and enlarged the curve-down orientation cue."],
        "status": "approved",
    },
}
write("MANUAL-DESIGN.json", evidence)

# Product build specification

Status: **HELD — template values and unresolved claims are not evidence.**

## Product intent

- User and job:
- Interaction and environment:
- Age/safety boundary:
- Claims explicitly out of scope:

## Visual intent

- Three adjectives:
- Scale anchor and overall envelope:
- Primary/secondary/detail forms:
- Landmarks and interaction surfaces:
- Seams and material/color breaks:
- Forbidden shortcuts:
- Frozen canonical views and target hash:

## Manufacturing envelope

- Process, machine, and bed:
- Nozzle, layer height, and measured extrusion width:
- Materials and material-profile hashes:
- Supports and post-processing allowed:
- Target mass, time, and cost:

## Part inventory

| Stable ID | Qty | Purpose | Material | Canonical source | Solids/shells | Print orientation |
|---|---:|---|---|---|---|---|

## Controlled parameters

| Parameter | Nominal/range/unit | observed/derived/assumed | Confidence | Owner | Dependents |
|---|---|---|---|---|---|

## Fits, contacts, and connectors

| Part pair | Surfaces | Fit/contact class | Coupon/profile | Load | Evidence required |
|---|---|---|---|---|---|

## Motion and interference

- Moving part, datum, axis/path, and limits:
- Sampled poses:
- Allowed contacts:
- Forbidden collisions:
- Compliance/friction/fatigue claims held for physical evidence:

## Assembly and service

1. Replace with an unambiguous assembly sequence.

## Release gates

| Gate | Acceptance criterion | Evidence source | Current status |
|---|---|---|---|
| Manifest/freshness | `inventory_valid=true`; exact current artifact and inventory | deterministic | held |
| B-rep | `valid_solids>=1`, `invalid_solids=0`; exact per-part topology in evidence | deterministic | held |
| Mesh topology | `watertight_parts>=1`, `non_manifold_edges=0`; every output represented | deterministic | held |
| Dimensions | `measured_parts>=1`, `out_of_tolerance=0`; project tolerances pinned in config | deterministic | held |
| Fit/motion | `poses_tested>=1`, `forbidden_intersections=0`; coupons for physical behavior | mixed | held |
| Bed packing | `beds_used>=1`, `out_of_bounds_parts=0`; all required quantities packed | deterministic | held |
| Slicer/process | `profiles_checked>=1`, `slicer_errors=0`, numeric support grams | slicer | held |
| Form/beauty | `views_reviewed>=3`, `blockers=0`; independent fixed-view review | review | held |
| Safety | `hazards_found=0`, non-empty `review_scope`; age/use boundary pinned | review | held |
| Physical claims | `claims_tested>=1`, `claims_failed=0`; exact claim evidence bound | physical | held |

## Bounds and unresolved claims

- Repair/coupon/time/material/money ceilings:
- Missing or ambiguous requirements:
- Claims that remain held:

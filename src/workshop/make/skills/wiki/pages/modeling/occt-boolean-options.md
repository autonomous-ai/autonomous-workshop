---
title: OpenCASCADE boolean options
tags: [occt, boolean, fuzzy, glue, argument-analyzer, history, parallel]
aliases: [SetFuzzyValue, fuzzy boolean, SetGlue, BOPAlgo_GlueShift, BOPAlgo_GlueFull, SetNonDestructive, SetCheckInverted, BOPAlgo_ArgumentAnalyzer, SetRunParallel]
sources:
  - https://occt3d.com/dev/doc/overview/html/specification__boolean_operations.html
  - https://occt3d.com/dev/doc/refman/html/class_b_o_p_algo___argument_analyzer.html
related: [boolean-pitfalls, occt-topology-and-tolerance, kernel-validity, occt-shape-healing]
updated: 2026-09-23
---

# OpenCASCADE boolean options

build123d's `+ - &` call OCCT's `BRepAlgoAPI_Fuse/Cut/Common` with default
options. When a boolean fails or silently drops material
([[boolean-pitfalls]]), the OCCT options below are the levers left after
fixing the geometry itself. They are reached through OCP on the `wrapped`
shapes.

## The options

| option | default | does | use when |
|---|---|---|---|
| `SetFuzzyValue(tol)` | `Precision::Confusion()` | adds tolerance on top of the shapes' own, so near-coincident geometry is treated as coincident | imported or approximated shapes whose faces are meant to coincide but miss by discretisation error; the spec mentions values around 1e-5 as typical |
| `SetGlue(BOPAlgo_GlueShift / BOPAlgo_GlueFull)` | off | speeds up arguments that share coinciding parts: GlueShift for shifted overlaps, GlueFull for fully coinciding sub-shapes | stacking or fusing many parts that touch face to face |
| `SetNonDestructive(true)` | false | never modifies the input shapes in place | inputs you will reuse afterwards |
| `SetCheckInverted(bool)` | true | checks for inverted solids (faces pointing inward) | leave it on; disable only when every solid is known to be oriented |
| `SetRunParallel(true)` | false | intersects independent pairs in parallel | many-tool booleans |

**Fuzzy is a scalpel, not a fix.** A large fuzzy value degrades the accuracy
of the result, and features smaller than it can vanish. Choose it just above
the measured gap (for example `2 × max(shape tolerance)`), never as a blanket
default. Then check the result's volume and validity as for any boolean
([[kernel-validity]]).

## History: which faces came from where

A boolean records `Modified()` (the faces or edges an input was split into),
`Generated()` (new sub-shapes created from an input) and `IsDeleted()`. This
is the robust way to find, say, "the faces the cut created" for a later fillet,
instead of re-selecting by position after the topology changed
([[parametric-design-intent#reference-stable-things]]).

## Check the arguments first: BOPAlgo_ArgumentAnalyzer

The analyzer reports, per argument pair and operation type, the problems that
make a boolean undefined. Enable the modes you need:

| mode | checks |
|---|---|
| `ArgumentTypeMode` | the shape types suit the operation |
| `SelfInterMode` | self-intersection inside an argument |
| `SmallEdgeMode` | edges too small to process |
| `RebuildFaceMode` | whether faces can be split and rebuilt |
| `TangentMode` | tangency between sub-shapes |
| `MergeVertexMode` / `MergeEdgeMode` | vertices or edges that would have to merge |
| `ContinuityMode` | geometry below the required continuity |
| `CurveOnSurfaceMode` | invalid curves on surfaces |

`HasFaulty()` answers yes/no, and `GetCheckResult()` lists
`BOPAlgo_CheckResult`s naming the faulty sub-shapes. This is the same "BOP
check" that catches what `BRepCheck_Analyzer` misses: self-intersecting faces
and tangent chamfers
([[kernel-validity#gate-tangency-prone-results-with-the-bop-check]]). Running
it on the *arguments* tells you before the cut whether a failure will be the
tool's fault or the target's.

## After the boolean: tidy the result

A boolean leaves split faces and seam edges along former intersection lines.
`ShapeUpgrade_UnifySameDomain` merges coplanar or co-cylindrical faces back
into one ([[occt-shape-healing#merge-same-domain-faces-shapeupgrade_unifysamedomain]]),
which makes later fillets and selections simpler. Be aware that on a large
flat region it can be slow.

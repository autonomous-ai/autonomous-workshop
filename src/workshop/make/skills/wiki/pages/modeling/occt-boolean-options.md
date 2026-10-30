---
title: OpenCASCADE boolean options
tags: [occt, boolean, fuzzy, glue, argument-analyzer, history, parallel]
aliases: [SetFuzzyValue, fuzzy boolean, fuzzy ladder, SetGlue, BOPAlgo_GlueShift, BOPAlgo_GlueFull, SetNonDestructive, SetCheckInverted, BOPAlgo_ArgumentAnalyzer, SetRunParallel, SkipClean, UnifySameDomain slow, cut did nothing, silent no-op cut]
sources:
  - https://occt3d.com/dev/doc/overview/html/specification__boolean_operations.html
  - https://occt3d.com/dev/doc/refman/html/class_b_o_p_algo___argument_analyzer.html
  - skills/step-to-source/scripts/steplib.py (FUZZ_LADDER)
  - "experience: two of nine inlay cuts on a figure handed the host back unchanged; a 1e-5 mm fuzzy common found the overlap exact missed"
  - "experience: a slow boolean that spent most of its time in ShapeUpgrade_UnifySameDomain; a SkipClean context that re-enabled cleaning on exit"
related: [boolean-pitfalls, occt-topology-and-tolerance, kernel-validity, occt-shape-healing, brep-vs-source]
updated: 2026-10-10
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

## Walk the fuzzy value up from exact

When the measured gap is unknown, the fuzzy value is a ladder, not a setting:
run exact first and climb (1e-7, 1e-6, 1e-5, 1e-4, 1e-3 mm, as `step_verify`
does) only after the exact result fails its check. Stop at the **first** rung
that answers and report which one did: the loosest rungs can go back to
reporting nothing. Accept a fuzzy repair only if it is valid and lands on the
volume the exact run reached; a looser tolerance that reshapes the body is not
a repair. A cut between two dense lofts that `ShapeFix_Shape` cannot clear is
usually cleared by the smallest rung.

When it answers, and when it does not:

- **It answers** where faces are meant to coincide and miss by discretisation
  error over a small region: an analytic recovery against its original, an
  inlay against its host (1e-5 mm found an 80 mm³ overlap that exact missed).
- **It does not** rescue two solids that lie within hundredths of a millimetre
  of each other across many B-spline faces: every rung from 1e-7 to 1e-2
  returned less than exact (1.4 mm³ → 0.0). Stop climbing and measure by
  sampling ([[brep-vs-source#near-coincident-solids-collapse-the-comparison]]).

## A cut that did nothing looks like a cut that worked

Where an inlay's surface nearly coincides with its host's, the kernel can fail
to classify the two and hand the host straight back: valid, one solid, the
right number of faces, and the inlay still inside it. `BRepAlgoAPI_Common` on
the same pair reports an empty intersection and reports it as **done**. Only an
interference check of the finished parts found it. Measure the overlap first
with the ladder above, then hold the cut to removing that much
([[kernel-validity#a-zero-volume-cutter-is-a-silent-no-op]]). A zero
intersection is trustworthy only after the ladder, and then it is useful: an
earlier cut in the order may already have taken everything a later one would
(a pupil inside an eye white meets nothing once the white is out of the head).

## Keep comparison operations read-only

Do not assume `a - b` leaves `a` and `b` unchanged. A wrapper that calls
`SetArguments`, `SetTools` and `Build` without `SetNonDestructive(True)` retains
the destructive default. Reusing those operands for `b - a`, feature probes or
later inspection can contaminate the evidence, even when each wrapper still has
the same identity.

For diagnostic differences, instantiate an empty `BRepAlgoAPI_Cut`, set its
arguments, tools and non-destructive flag **before** `Build`, or give every
operation independent deep copies of both topology and geometry. A constructor
that receives both shapes may already perform the operation before a later
flag assignment. Start a corrected comparison from fresh source/STEP loads;
do not reuse operands from a failed destructive run. Render original exports
from fresh loads rather than reusing diagnostic operands.

Persist each completed local coverage result before starting an independent
reverse or global difference. A later expensive subtraction must not hide the
evidence already obtained; uncompleted phases remain explicitly incomplete.

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

An expensive boolean may finish its intersection work and then spend most of
its time in `ShapeUpgrade_UnifySameDomain`. Sample the running native stack
before treating a slow operation as a meshing or topology failure. Disabling
the optional same-domain merge can preserve the boolean result with more
faces, but the result still needs normal BOP validation, coverage checks and a
STEP comparison.

Inspect the installed `SkipClean` implementation before nesting it. A context
whose exit always sets the global `clean` flag to `True` re-enables cleanup
inside its caller's supposedly disabled block. A local wrapper must save the
incoming value and restore that value in `finally`, including exception paths.
The flag is process-global: save and restore is nesting-safe, not thread
isolation.

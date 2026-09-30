# ADR 0073: Carry Forward compares geometry, not STEP bytes

- Status: Accepted
- Date: 2026-09-24
- Relates to: ADR 0069 (Carry Forward), ADR 0063 (component-first Make),
  `docs/BASELINE_CORRECTION_RUN.md`

## Context

Carry Forward (ADR 0069) lets a Correction Run keep a Component's evidence when
the Component is unchanged, and decides "unchanged" by comparing the freshly
exported STEP's sha256 with the source archive's `made.json`
`product_manifest`.

The baseline Correction Run changed no printed part, yet 11 of 24 came back
byte-different and nothing was carried. Two causes were measured:

- **Serialisation.** Three board panels differ by exactly 0 mm3; the STEP text
  differs only in the exporter's per-process `NEXT_ASSEMBLY_USAGE_OCCURRENCE`
  ordinal, because a warm multi-target `gen` numbers occurrences differently
  from a single-target one.
- **Boolean round-off.** Six parts come out with a different B-rep entity
  count, volume differing by up to 1.13e-8 mm3. The solid itself differs, at
  round-off scale.

STEP bytes see both. The tessellation cache (`d853a382`) already rejected STEP
bytes as a key for the first reason and keys on the B-rep instead.

## Decision

Carry Forward decides "unchanged" by a hash of the Component's B-rep
(`cadgen.inspection_runtime.shape_identity`), computed on a shape built from
source, never on a shape imported from STEP: import and build do not give the
same B-rep.

The source side of the comparison comes from:

1. **`made.json`**, which from now on seals each Component's B-rep hash beside
   its STEP sha256, computed at the moment Make builds it; or
2. **a rebuild**, for an archive sealed before this ADR: the run builds the
   source archive's own Components from `revision-source.zip` in a scratch
   tree and hashes those. v13 and ADR 0069 already used such control
   rebuilds.

The warrant is unchanged in kind: a check is a pure function of the shape it
reads, so an identical shape gives an identical verdict. Only what counts as
"the thing it reads" moves, from the file to the shape.

Alongside, one experiment runs: whether building with OCCT's parallel boolean
mode off (`isInParallel=True` at `build123d/topology/shape_core.py:1626-1628`)
makes the round-off deterministic. Its result decides whether the six
round-off parts can ever be carried; this ADR does not depend on it.

## Considered options

- **Keep STEP bytes and make the exporter deterministic.** Fixes the
  serialisation half only. Nothing can make STEP bytes agree for two solids
  that genuinely differ at round-off.
- **Compare within a tolerance** (volume and bounding box within epsilon).
  Carries all eleven parts, but replaces "identical input, identical verdict"
  with "close enough that no verdict flips", an argument rather than a
  guarantee. A thickness or overhang gate sits exactly on a threshold. Rejected.
- **Hash the source archive's STEP after import.** Cheap, and wrong: an
  imported shape does not hash like the built one, so it fails the same way
  STEP bytes do.

## Consequences

- Expected to carry the serialisation-only parts (3 of 11 on the baseline,
  up to 5), and none of the six round-off parts until the experiment says
  otherwise. The saving on the baseline is small (component rounds cost about
  10 minutes); the point is that Carry Forward can work at all, which later
  carrying of renders depends on.
- `made.json` gains a field. Archives sealed earlier stay valid and take the
  rebuild path, which costs one extra build of the Components per Correction
  Run.
- `make_round --require-component-passes` must compare the same identity, or
  a carried pass is refused as "changed after its component pass".
- Glossary: `CONTEXT.md` **Carry Forward** already reads "identity is
  established on the shape itself rather than on the exported file".

## Amendment (2026-09-25, issue #74)

The parallel-boolean experiment this ADR named (issue #60) ran:
`docs/PARALLEL_BOOLEAN_EXPERIMENT.md`. Result: the round-off did not
reproduce in a controlled same-host A/B, on or off (0 of 24 parts, either
setting), so it settles nothing about whether the six round-off parts named
above are carriable, and is **not wired into Make** -- it cost 2.6x the
build time in that measurement for an effect it could not reproduce there.

Re-measured directly on the dev host instead (`cadquery-ocp==7.9.3.1.1`,
`build123d==0.11.1`, matching what a real Make run installs): all 24 printed
parts of `toys/ad-astra-antisol-companion`, three builds each, one process
per run. 23 of 24 -- including all six parts this ADR's baseline flagged as
"round-off" -- hash identically every time under this toolchain pin. Only
`part_belt_cell` hashed differently on every build, including twice within
one process; its volume stayed bit-identical across every hash.

**Root cause**: `shape_identity`'s hash (`OCP.BinTools.BinTools.Write_s` +
sha256) is not a hash of the geometry -- it is a hash of OCCT's internal
B-rep container, including the order edges' curve representations get
appended to their owning `BRep_TEdge`. A many-tool boolean fuse (the belt
cell's `rubble_field` unions dozens of rock solids in one `+` call, which
crosses OCCT's threshold for parallel dispatch) populates that order from
whichever worker finishes first, so two builds of the identical script
serialise the same geometry to different bytes. Exact per-face and per-edge
geometric sampling (surface/curve type, sampled points at fixed parameter
fractions) was bit-identical across repeated builds of every belt-cell
sample checked, including full double precision with no rounding --
confirming the geometry itself is deterministic and only the container
order was leaking into the hash.

**Fix**: `shape_identity` no longer calls `BinTools.Write_s`. It walks each
vertex/edge/face via `TopExp_Explorer`, samples each edge's curve and each
face's surface at fixed parameter fractions (`BRepAdaptor_Curve`/
`BRepAdaptor_Surface`), and hashes those samples sorted by content --
never by traversal order, so allocation-dependent container order cannot
reach the hash. Still exact, not tolerance-based: two builds of the same
design produce byte-identical samples, and a genuinely different shape
still samples differently. Two prior consequences of this section follow
automatically, without new migration code: because the hash's bytes
changed, every archive's previously sealed `made.json` B-rep hash and every
tessellation-cache key computed under the old `shape_identity` now simply
fails to match the new one -- a miss, never a false match, exactly as
"unchanged" must fail safe.

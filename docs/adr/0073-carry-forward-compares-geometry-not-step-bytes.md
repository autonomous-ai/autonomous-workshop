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

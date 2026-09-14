# Edited challenge handoff

`solver.py` imports the recreated original grammar and writes `challenges.json`.
Run with the supplied Workshop virtualenv Python. No CAD is generated here.

Three cards are supported as abstract construction exercises. Q01 leaves A/C
loose and has **two**, not one, solutions. Q02 leaves A/D/F loose and has four
solutions: the courtyard and long building must protect the lateral detour.
Q03 leaves D/E/F loose and has eight solutions after exchanging E/F: both
bridges are fixed, so the remaining task concerns solid mass placement and the
exit corridor. These are proposed learning emphases, not measured difficulty.
The broader attempted clue selections produced many superficial variants; the
handoff intentionally contains only these three cards, not a padded 24-card set.

The three complete witness layouts are distinct even after interchangeability
and reflection across the C column. Q03's witness has two route drawings; its
longer right-side detour is optional. This is not two construction solutions or
evidence of a separate reasoning challenge. Every completion includes its own
route count, separately from the count of completed town arrangements.

Every high gap admits only consecutive straight traversal perpendicular to its
three-cell strip. Virtual cells outside C1/C5 enforce port approach direction.
The only board symmetries quotienting completed arrangements are identity and
left/right reflection, which fix each labeled port individually. Reversing the
board would exchange labeled entry and exit and is not counted as equivalent.
All footprint-preserving rotations and swaps remain conditional on actual CAD
architectural-detail equivalence; this point solver cannot establish it.

Each witness includes both high/low swaps with zero remaining legal trips.
Where available, additional one-piece wrong-orientation placements preserve
grid nonoverlap but disconnect the trip. These negatives describe the cell
grammar, not the cause or magnitude of a measured physical collision.

An independent Cartesian enumeration reproduced all completion counts, without
the recursive solver's early interchangeable-piece pruning. Q03 has 1,086
labeled nonoverlapping candidates / 16 labeled winners and eight quotiented
winners. Its recursive enumeration examines 543 unlabeled candidates. The
audit is stored in `enumeration-audit.json`.

No finite ferry, finger, arch-headroom, swept-volume, stability, manufacturing,
or human-play result is claimed. Validate every advertised completion against
the exact actual solids; remove or repair any completion that fails. If physical
validation changes the legal grammar, rerun enumeration and update card counts.

## Subsequent representative CAD validation

The root Manager subsequently checked all 14 representative completions and
three witness layouts. See [validation-scope.json](validation-scope.json) and
[finite evidence](../cad/measure/physical-validation.json). The abstract-only
statements above describe the original solver handoff, not this later evidence.
Counts remain footprint classes with at least one validated pose each, not all
facade facings. Two of 16 Q01 arch-facing aliases fail the top-down finger proxy;
match shown labels, rotations and offset rear-span bands for reproductions.
The larger unordered-port D2 reasoning quotient also gives 2 / 4 / 8.

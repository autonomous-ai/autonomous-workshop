# Revision diff against the archive being corrected

Compared against the immutable clone under `revision-work/`, which is the
uncorrected Periastra Meridian archive this revision repairs. That archive's
`make/ATTEMPTS.json` records stage outcomes, not geometry, so the per-part
comparison is made against the only per-part hash record it carries - its sealed
build group `make/product/groups/observatory.json` - and the per-design
comparison against `make/models/cad/part_*.step`.

## The print designs

| design | archive | this revision | verdict |
|---|---|---|---|
| `base` | `590aa6c78a8480f8...` | `1db4b15610146fc0...` | CHANGED |
| `roof` | `157a1fee7b990278...` | `23957b5a061b9480...` | CHANGED |
| `sun_counter` | `262ccc86f6e4c403...` | `262ccc86f6e4c403...` | byte-identical |
| `moon_counter` | `588d285baf2e312d...` | `588d285baf2e312d...` | byte-identical |
| `inlay` | _(new design)_ | `81085d55483e4841...` | NEW |

`base` and `roof` are the two designs this correction changes; `inlay` is the new
geometry family the board's fit layer adds.

**The two counters are frozen and byte-identical.** `cad/part_sun_counter.step`
hashes `262ccc86f6e4c40394e8611fd0f98ee7a7aaf2ec5b3e42fab36d66902afe5f3b`
and `cad/part_moon_counter.step` hashes
`588d285baf2e312d81ca39c92ddad82ff83725aa721f5a5789ffb1a0ec50301e`.
`measure/check_fit.py` asserts both on every run and fails the build if either
moves.

## The delivered parts

Part keys: 26 before, 58 after.
Every archive part key is still present. 32 were added: `inlay_01`..`inlay_32`.
2 of the 26 carried-over parts changed.
The ones that did not are `forked_01`, `forked_02`, `forked_03`, `forked_04`, `forked_05`, `forked_06`, `forked_07`, `forked_08`, `forked_09`, `forked_10`, `forked_11`, `forked_12`, `single_01`, `single_02`, `single_03`, `single_04`, `single_05`, `single_06`, `single_07`, `single_08`, `single_09`, `single_10`, `single_11`, `single_12`.

Full per-part hashes, before and after, are in `revision-diff.json`.

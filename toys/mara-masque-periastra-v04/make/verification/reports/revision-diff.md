# Revision diff against the archive being corrected

Compared against the immutable clone under `revision-work/`, which is the
uncorrected Periastra Meridian archive this revision repairs and renames. That archive's
`make/ATTEMPTS.json` records stage outcomes, not geometry, so the per-part
comparison is made against the only per-part hash record it carries - its sealed
build group `make/product/groups/observatory.json` - and the per-design
comparison against `make/models/cad/part_*.step`.

## The print designs

| design | archive | this revision | verdict |
|---|---|---|---|
| `base` | `1db4b15610146fc0...` | `1db4b15610146fc0...` | byte-identical |
| `roof` | `23957b5a061b9480...` | `da320a57109473fc...` | CHANGED |
| `inlay` | `81085d55483e4841...` | `81085d55483e4841...` | byte-identical |
| `sun_counter` | `262ccc86f6e4c403...` | `262ccc86f6e4c403...` | byte-identical |
| `moon_counter` | `588d285baf2e312d...` | `588d285baf2e312d...` | byte-identical |

`roof` is the ONE design this correction changes. The other four are frozen and
come out byte-identical to the archive:

| frozen design | sha256 |
|---|---|
| `part_base.step` | `1db4b15610146fc0c993268802e0279d7859f56b42df22f7ba5d3915ad55e1b8` |
| `part_inlay.step` | `81085d55483e4841813ccbd069c89d4c8d4d285de977e334da709fcdf38e9b90` |
| `part_sun_counter.step` | `262ccc86f6e4c40394e8611fd0f98ee7a7aaf2ec5b3e42fab36d66902afe5f3b` |
| `part_moon_counter.step` | `588d285baf2e312d81ca39c92ddad82ff83725aa721f5a5789ffb1a0ec50301e` |

`measure/check_fit.py` asserts all four on every run and fails the build if any
of them moves.

## The delivered parts

Part keys: 58 before, 58 after.
Every archive part key is still present and none was added.
1 of the 58 carried-over parts changed:
`roof`. The other
57 are byte-identical to the archive.

Full per-part hashes, before and after, are in `revision-diff.json`.

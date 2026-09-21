"""Report this revision's per-design and per-part STEP hashes against the source set.

The source archive's sealed build group is the only per-part hash record it
carries (`make/ATTEMPTS.json` records outcomes, not geometry), so the comparison
is made against `make/product/groups/observatory.json` from that archive and
against the four per-design STEP files under `make/models/cad/`.
"""
import hashlib
import json
from pathlib import Path

CAD = Path(__file__).resolve().parents[1]
PRODUCT = CAD.parent
RUN = PRODUCT.parents[3]
ARCHIVE = RUN/'revision-work/make'

DESIGNS = ['base', 'roof', 'sun_counter', 'moon_counter']
NEW_DESIGNS = ['inlay']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    designs = {}
    for role in DESIGNS:
        before = ARCHIVE/f'models/cad/part_{role}.step'
        after = CAD/f'part_{role}.step'
        designs[role] = {'source_set_sha256': sha(before), 'this_revision_sha256': sha(after)}
        designs[role]['changed'] = designs[role]['source_set_sha256'] != designs[role]['this_revision_sha256']
    for role in NEW_DESIGNS:
        designs[role] = {'source_set_sha256': None, 'new_in_this_revision': True,
                         'this_revision_sha256': sha(CAD/f'part_{role}.step'), 'changed': True}

    before_group = json.loads((ARCHIVE/'product/groups/observatory.json').read_text())['files']
    after_group = json.loads((PRODUCT/'groups/observatory.json').read_text())['files']
    added = sorted(set(after_group) - set(before_group))
    assert set(before_group) <= set(after_group), 'a source-set part key disappeared'
    assert added == [f'inlay_{i:02d}' for i in range(1, 33)], added
    parts = {k: {'source_set_sha256': before_group.get(k),
                 'this_revision_sha256': after_group[k],
                 'added_in_this_revision': k in added,
                 'changed': before_group.get(k) != after_group[k]} for k in sorted(after_group)}

    changed_parts = [k for k, v in parts.items() if v['changed'] and k not in added]
    changed_designs = [k for k, v in designs.items() if v['changed']]
    report = {'kind': 'periastra.revision-diff', 'schema_version': 2,
              'source_set': 'Periastra Meridian (uncorrected archive)',
              'revision': 'Periastra Meridian, revision C',
              'source_part_keys_all_present': set(before_group) <= set(after_group),
              'part_key_count_before': len(before_group),
              'part_key_count_after': len(after_group),
              'added_part_keys': added,
              'designs': designs, 'parts': parts,
              'changed_design_count': len(changed_designs), 'changed_part_count': len(changed_parts)}
    (CAD/'measure/revision-diff.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')

    def before_cell(role):
        value = designs[role]['source_set_sha256']
        return f'`{value[:16]}...`' if value else '_(new design)_'

    rows = '\n'.join(
        f"| `{r}` | {before_cell(r)} | `{designs[r]['this_revision_sha256'][:16]}...` | "
        f"{'NEW' if designs[r].get('new_in_this_revision') else ('CHANGED' if designs[r]['changed'] else 'byte-identical')} |"
        for r in DESIGNS + NEW_DESIGNS)
    (CAD/'measure/revision-diff.md').write_text(f"""# Revision diff against the archive being corrected

Compared against the immutable clone under `revision-work/`, which is the
uncorrected Periastra Meridian archive this revision repairs. That archive's
`make/ATTEMPTS.json` records stage outcomes, not geometry, so the per-part
comparison is made against the only per-part hash record it carries - its sealed
build group `make/product/groups/observatory.json` - and the per-design
comparison against `make/models/cad/part_*.step`.

## The print designs

| design | archive | this revision | verdict |
|---|---|---|---|
{rows}

`base` and `roof` are the two designs this correction changes; `inlay` is the new
geometry family the board's fit layer adds.

**The two counters are frozen and byte-identical.** `cad/part_sun_counter.step`
hashes `{designs['sun_counter']['this_revision_sha256']}`
and `cad/part_moon_counter.step` hashes
`{designs['moon_counter']['this_revision_sha256']}`.
`measure/check_fit.py` asserts both on every run and fails the build if either
moves.

## The delivered parts

Part keys: {report['part_key_count_before']} before, {report['part_key_count_after']} after.
Every archive part key is still present. {len(added)} were added: `inlay_01`..`inlay_32`.
{len(changed_parts)} of the {report['part_key_count_before']} carried-over parts changed.
The ones that did not are `{'`, `'.join(k for k, v in parts.items() if not v['changed']) or 'none'}`.

Full per-part hashes, before and after, are in `revision-diff.json`.
""")
    print(f"designs changed: {changed_designs}; parts added: {len(added)}; "
          f"carried-over parts changed: {len(changed_parts)}; "
          f"unchanged part(s): {[k for k, v in parts.items() if not v['changed']]}")


if __name__ == '__main__':
    main()

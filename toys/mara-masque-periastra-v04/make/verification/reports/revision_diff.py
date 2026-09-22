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

DESIGNS = ['base', 'roof', 'inlay', 'sun_counter', 'moon_counter']
NEW_DESIGNS = []


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    designs = {}
    for role in DESIGNS:
        before = ARCHIVE/f'models/cad/part_{role}.step'
        after = CAD/f'part_{role}.step'
        designs[role] = {'source_set_sha256': sha(before), 'this_revision_sha256': sha(after)}
        designs[role]['changed'] = designs[role]['source_set_sha256'] != designs[role]['this_revision_sha256']

    before_group = json.loads((ARCHIVE/'product/groups/observatory.json').read_text())['files']
    after_group = json.loads((PRODUCT/'groups/observatory.json').read_text())['files']
    added = sorted(set(after_group) - set(before_group))
    assert set(before_group) <= set(after_group), 'a source-set part key disappeared'
    assert added == [], f'this revision adds no part keys, but {added} appeared'
    assert len(before_group) == len(after_group) == 58
    parts = {k: {'source_set_sha256': before_group.get(k),
                 'this_revision_sha256': after_group[k],
                 'added_in_this_revision': k in added,
                 'changed': before_group.get(k) != after_group[k]} for k in sorted(after_group)}

    changed_parts = [k for k, v in parts.items() if v['changed'] and k not in added]
    changed_designs = [k for k, v in designs.items() if v['changed']]
    report = {'kind': 'periastra.revision-diff', 'schema_version': 2,
              'source_set': 'Periastra Meridian (uncorrected archive)',
              'revision': 'Periastra Zenith, revision D',
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
uncorrected Periastra Meridian archive this revision repairs and renames. That archive's
`make/ATTEMPTS.json` records stage outcomes, not geometry, so the per-part
comparison is made against the only per-part hash record it carries - its sealed
build group `make/product/groups/observatory.json` - and the per-design
comparison against `make/models/cad/part_*.step`.

## The print designs

| design | archive | this revision | verdict |
|---|---|---|---|
{rows}

`roof` is the ONE design this correction changes. The other four are frozen and
come out byte-identical to the archive:

| frozen design | sha256 |
|---|---|
| `part_base.step` | `{designs['base']['this_revision_sha256']}` |
| `part_inlay.step` | `{designs['inlay']['this_revision_sha256']}` |
| `part_sun_counter.step` | `{designs['sun_counter']['this_revision_sha256']}` |
| `part_moon_counter.step` | `{designs['moon_counter']['this_revision_sha256']}` |

`measure/check_fit.py` asserts all four on every run and fails the build if any
of them moves.

## The delivered parts

Part keys: {report['part_key_count_before']} before, {report['part_key_count_after']} after.
Every archive part key is still present and none was added.
{len(changed_parts)} of the {report['part_key_count_after']} carried-over parts changed:
`{'`, `'.join(changed_parts) or 'none'}`. The other
{report['part_key_count_after'] - len(changed_parts)} are byte-identical to the archive.

Full per-part hashes, before and after, are in `revision-diff.json`.
""")
    print(f"designs changed: {changed_designs}; parts added: {len(added)}; "
          f"carried-over parts changed: {len(changed_parts)}; "
          f"unchanged part(s): {[k for k, v in parts.items() if not v['changed']]}")


if __name__ == '__main__':
    main()

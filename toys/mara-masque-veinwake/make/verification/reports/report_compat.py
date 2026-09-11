"""Preserve native reports and bridge their proven PASS to the proposal vocabulary.

The frozen proposal validator expects legacy RESULT lines absent from the
materialized CAD reporters. No check, threshold, raw result or tool is changed.
Each summary is permitted only after final verification PASS and explicit
passing wall/support/bridge rows, with no failing row. Raw bytes are archived.
"""
from pathlib import Path
import hashlib
import json
import re

HERE=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
verification=(HERE/'verification-pipeline.md').read_bytes()
assert b'- Mode: `final`' in verification and b'- Result: **PASS** (exit 0)' in verification
archive=HERE/'raw-verifier-reports'
archive.mkdir(exist_ok=True)
rows=[]
for gate,marker in [('thickness','RESULT: printable at this wall'),('overhang','RESULT: prints unsupported')]:
    reports=sorted(HERE.glob(f'{gate}-*.md'))
    assert len(reports)==10
    for report in reports:
        raw=report.read_bytes()
        assert b'Proposal-format compatibility summary' not in raw
        text=raw.decode('utf-8')
        assert '| FAIL |' not in text
        if gate=='thickness':
            assert re.search(r'^\| wall >=[^\n]*\| PASS \|',text,re.M)
        else:
            assert re.search(r'^\| no face under 45 deg needs support \| PASS \|',text,re.M)
            assert re.search(r'^\| bridges within 12 mm \| PASS \|',text,re.M)
        (archive/report.name).write_bytes(raw)
        note=('\n## Proposal-format compatibility summary\n\n'
              'Manager-authored format bridge from the unchanged passing table above '
              'and final verifier exit 0; not an additional measurement. '
              f'Raw reporter bytes: `raw-verifier-reports/{report.name}`, '
              f'SHA-256 `{sha(raw)}`.\n\n{marker}\n')
        final=raw+note.encode('utf-8');report.write_bytes(final)
        rows.append({'report':report.name,'raw_sha256':sha(raw),'canonical_sha256':sha(final),'summary':marker})
(HERE/'report-compatibility.json').write_text(json.dumps({
    'reason':'Frozen proposal tool expects legacy RESULT lines; current CAD reporters emit PASS tables.',
    'verification_sha256':sha(verification),'raw_reports_preserved':True,
    'tools_or_thresholds_changed':False,'reports':rows},indent=2)+'\n')
print(json.dumps({'preserved_raw_reports':len(rows),'truthful_compatibility_summaries':len(rows)}))

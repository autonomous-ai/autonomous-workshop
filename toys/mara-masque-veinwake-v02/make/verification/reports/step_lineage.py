"""Compare this revision's exported STEP bytes against the source archive.

The baseline rows are the `parts/<role>.step` and `assembled.step` entries of
`make/ATTEMPTS.json` / `make/made.json` in the immutable revision snapshot
`revision-source.zip` (snapshot sha256
9ce8801e80778249d5652372214c893eb072824c8bab5ac489c65e16f992baa3,
published artifact sha256
554e21777e8db2f278f21abc070d1e1533a493b5a95e10898b9420675c2caae4).
They are copied here so the audit runs inside the sealed product tree.

The correction Wish requires exactly six changes: the rind, the four bubbles
and the assembly. The five teeth must reproduce their bytes exactly.
"""
import hashlib
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
BASELINE = {
    'rind': '2385415b012378743fcd5e46844cd43072ec43a681d5768f29650e204e6572fb',
    'tooth_1': '98e645c55fbe11a95cb6d8b2bae151c3478527e7b4bdc475b6baff955c92f2b8',
    'tooth_2': '0a31132df60a3193053a2266843b979d82f8a2051cb4bacd5b4136921eb8117a',
    'tooth_3': '1fecfb685a5e46620b7b67f6a5d4da31858fad6b28ca969c9159369936fca700',
    'tooth_4': '859d7f4f899e65f3696ae2877fa3be50d3a16fbdc5c21d9faa156ee2b3945ce4',
    'tooth_5': '55c26e3584846b26e28b974199c02aae920db703718fa7ae2de50d8d29338681',
    'bubble_1': '6bf68b612a0dc2294c13be20b5157c408eba12cd153fc2cb3433c7838e824d88',
    'bubble_2': 'ca3c70ed54c06e14a94c589a915828733882730d42bb306f5cae67f5a3077638',
    'bubble_3': '6886e6c10c75aab40f0a13433724da85586c5b24764729448918f09e322b78a1',
    'bubble_4': '5fe721fc6e6ccd1c5d9b6ed56ebbe8053faa45dc1c803ad52c20b67026d70346',
}
BASELINE_ASSEMBLY = '586ccdfc102ad5f840e590a67d2623775656d87284b4823217ea347e2c13ba0b'
EXPECTED_CHANGED = {'rind', 'bubble_1', 'bubble_2', 'bubble_3', 'bubble_4', 'assembly'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    rows = []
    changed = set()
    for role, before in BASELINE.items():
        now = sha(PROJECT / f'part_{role}.step')
        if now != before:
            changed.add(role)
        rows.append({'part': role, 'baseline_sha256': before, 'revision_sha256': now,
                     'changed': now != before})
    assembly = sha(PROJECT / 'veinwake.step')
    if assembly != BASELINE_ASSEMBLY:
        changed.add('assembly')
    rows.append({'part': 'assembly', 'baseline_sha256': BASELINE_ASSEMBLY,
                 'revision_sha256': assembly, 'changed': assembly != BASELINE_ASSEMBLY})
    result = {
        'status': 'pass' if changed == EXPECTED_CHANGED else 'fail',
        'scope': 'Exact exported STEP bytes only; no physical or print claim.',
        'snapshot_sha256': '9ce8801e80778249d5652372214c893eb072824c8bab5ac489c65e16f992baa3',
        'source_artifact_sha256': '554e21777e8db2f278f21abc070d1e1533a493b5a95e10898b9420675c2caae4',
        'expected_changed': sorted(EXPECTED_CHANGED),
        'actually_changed': sorted(changed),
        'unchanged': sorted(set(BASELINE) - changed),
        'rows': rows,
    }
    (PROJECT / 'measure/step-lineage.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}))
    assert result['status'] == 'pass', result['actually_changed']


if __name__ == '__main__':
    run()

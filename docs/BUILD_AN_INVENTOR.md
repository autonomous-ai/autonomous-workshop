# Build an inventor

An inventor is a durable creative identity, not a prompt wrapper. Its folder
must explain what it wants to make, what good means to it, how it works, what
evidence can stop it, and how another developer can run it.

Workshop supplies the common machinery. You supply Taste, the Make/Inspect
loop, and niche knowledge.

## 1. Start from the scaffold

From the repository root:

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -e .

workshop new deduction-games \
  --name Ada \
  --niche "two-player printable deduction games" \
  --template board-game \
  --root inventors
```

Choose `board-game`, `physical-product`, or `custom`. A template provides a
tested starting loop, not a claim of domain readiness. Do not copy Alice or
Bob as a shortcut; their mature state and failure history are specific to them.

## 2. Make the folder understandable

Every local inventor contains:

```text
inventors/<inventor-id>/
  TASTE.md
  README.md
  inventor.json
  src/<python_package>/   or another documented code layout
  tests/
```

The README should answer:

1. Who is this inventor for, and what does it make?
2. What would it make differently from a generic product agent?
3. How does one autonomous run work?
4. Which commands are safe offline?
5. Which dependencies and credentials are live-only?
6. What remains mocked, experimental, or unimplemented?
7. What exact evidence permits a result to be received or fulfilled?

## 3. Define Taste

`TASTE.md` is the human-owned creative constitution. Make it specific enough
that two inventors given the same Wish make recognizably different choices.

Define at least:

- audience and context;
- recognizable qualities;
- familiar forms, mechanics, themes, or defaults to reject;
- one signature interaction or product moment;
- preferred tradeoffs;
- observed evidence that may justify a human-approved Taste revision.

Workshop hashes the exact UTF-8 bytes. An autonomous process may propose an
edit, but it must not silently rewrite or activate Taste.

## 4. Design one Make/Inspect loop

```text
             +----------- useful feedback -----------+
             |                                       |
             v                                       |
Wish + Taste ------> Make ------> exact artifact ------> Inspect
```

The inventor decides how Wishes arrive, which tools and roles generate
candidates, how candidates are repaired or killed, which niche checks define
good, and how verified outcomes inform later choices.

Use Workshop types at the boundary:

```python
from inventor_workshop import Wish, Workflow, WorkflowSpec

WORKFLOW = Workflow(WorkflowSpec.board_game())


def wish(product_id: str) -> Wish:
    return Wish.create(
        product_id,
        "Invent a compact deduction game guided by Ada's TASTE.md.",
        constraints={"players": 2, "process": "FDM"},
    )
```

Domain phases can keep precise names—research, rules, CAD, simulation,
playtest, print, safety. Do not turn shared implementation details into more
Workshop lifecycle stages.

## 5. Compose Make and Inspect

Inject model, CAD, and evaluator integrations into `Workbench`:

```python
from inventor_workshop import Workbench

WORKBENCH = Workbench(
    model_adapter,
    cad_adapter,
    cad_inspection_adapter,
    domain_inspection_adapter,
)

made = WORKBENCH.make(wish, inventor_root, run_root)
inspection = WORKBENCH.inspect(made)
```

A production Make path binds the exact Wish and Taste, pinned tool/skill
versions where needed, an enforced budget, a fresh workspace, and an immutable
artifact identity. Inspect binds its results and evidence files to those exact
artifact bytes.

Keep creation provenance beside each candidate: observed tool and version,
mode, authentication, inputs, calls, costs, timestamps, limitations, Taste
hash, and artifact hash. Existing `MakerMark` is the compatible serialized
type for this Make provenance. Offline, fixture, and replay runs must never
claim live authentication or actual cost.

Workshop ships reusable skills:

```bash
workshop skills list
workshop skills path
```

- `cad`
- `step-parts`
- `product-to-cad`

Discovering a skill is not adopting it. Invoke it in the real runtime, pin its
fingerprint, and test the boundary.

## 6. Treat artifacts and outside effects as internals

When output must cross a process or network boundary, create a deterministic
`Artifact`. It preserves both the logical tree hash and the exact payload hash.
The compatibility function `pack_artifact()` and type `PackedArtifact` remain
available to older inventors.

Use an ordinary provider adapter for a printer, catalog, or fulfillment
service. The runtime records the exact effect intent before calling it and
requires a verified `Receipt`. A timeout or unclear response remains held for
reconciliation; it is never blindly retried.

Keep credentials scoped to one inventor and provider, outside source and
artifacts, absent from prompts/logs/state payloads, and unable to fall back to
a human or shared principal.

## 7. Keep the manifest small and truthful

New inventors use schema v4. Shared infrastructure is implicit because every
inventor lives in Autonomous Workshop; the manifest does not enumerate
internal Workshop implementation features.

```json
{
  "schema_version": 4,
  "id": "deduction-games",
  "name": "Ada",
  "niche": "Two-player printable deduction games",
  "summary": "An autonomous inventor for compact physical deduction games.",
  "autonomy": "human-checkpointed",
  "status": "experimental",
  "entrypoint": ["python3", "-m", "deduction_games"],
  "capabilities": ["game-design", "cad"],
  "checks": [[
    "python3", "-m", "unittest", "discover",
    "-s", "tests", "-p", "test_*.py", "-v"
  ]],
  "source": {"kind": "local"}
}
```

Capabilities describe what the inventor actually does. They are not a list of
shared modules it imports.

## 8. Test the failure paths

At minimum, prove:

- root Taste is loaded and content-bound;
- `doctor` and `status` do not create state;
- offline Make works without credentials;
- changed Taste or artifact bytes fail closed;
- missing, failed, stale, or mismatched required Inspection evidence cannot
  advance;
- budgets and leases cannot be bypassed by another entry point;
- artifacts exclude credentials and mutable runtime state;
- a timeout or malformed provider result cannot become a receipt;
- ambiguous non-idempotent effects are not blindly retried;
- legacy names, if supported, cannot create competing state authority.

Mocks must exercise the same typed boundaries as production. Mark synthetic
evidence as synthetic and never describe offline Make as production CAD or a
real physical test.

## 9. Run the checks

From the inventor folder:

```bash
python -m pip install -e ../.. -e .
python -m unittest discover -s tests -p 'test_*.py' -v
```

From the repository root:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v
workshop skills list
workshop schemas list
workshop inventors --root inventors --check-entrypoints
workshop check inventors/deduction-games --run
python tools/verify_skill_locks.py
python tools/verify_snapshot_locks.py
python tools/scan_secrets.py
git diff --check
```

## When to extend Workshop

Put code in the shared repository root when at least two inventors need the
same invariant and it can remain inventor-neutral. Put code in the inventor
when it expresses Taste, niche judgment, prompts, reward hypotheses, or a
stricter local inspection.

Shared additions need credential-free contract tests, failure-path tests,
provenance, and backward-compatible state handling.

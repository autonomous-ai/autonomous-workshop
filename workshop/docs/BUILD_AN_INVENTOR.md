# Build an inventor

An inventor is a durable creative identity, not a prompt wrapper. Its folder
must explain what it wants to make, how it works, what evidence can stop it,
and how another developer can run it.

Workshop removes the need to rebuild shared machinery. You supply Taste,
workflow, niche inspections, and qualified Doors.

## 1. Start from the scaffold

From the repository root:

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -e workshop

workshop new deduction-games \
  --name Ada \
  --niche "two-player printable deduction games" \
  --template board-game \
  --root inventors
```

Templates provide a starting workflow, not a claim of domain readiness:

- `board-game` — rules, simulation, CAD, printability, play, and novelty;
- `physical-product` — design, CAD, printability, safety, form, and novelty;
- `custom` — a small neutral graph to replace with explicit domain checks.

Do not copy Alice, Bob, or Eve as a shortcut. Their mature state and failure
history are inventor-specific.

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

The README must answer:

1. What niche and person is this inventor for?
2. What does it make that a generic product agent would not?
3. How does one autonomous shift run?
4. Which commands are safe offline?
5. Which dependencies and credentials are optional or live-only?
6. What remains mocked, experimental, or unimplemented?
7. What exact evidence permits Inspect, Send, or fulfillment?

## 3. Define Taste

`TASTE.md` is a root-level, human-owned creative constitution. It should be
specific enough that two inventors given the same Wish make recognizably
different choices.

Define at least:

- audience and context;
- three recognizable qualities;
- familiar forms, mechanics, themes, or defaults to reject;
- one signature interaction or product moment;
- tradeoffs the inventor prefers;
- what observed evidence can justify a human-approved Taste revision.

Workshop hashes the exact UTF-8 bytes. `Workbench.make()` checks that the file
did not change during Make. Agents may propose edits; unattended code must not
rewrite it.

## 4. Design the inventor-owned workflow

The workflow belongs in the inventor folder. It decides:

- how Wishes are found or received;
- which research changes a decision;
- which roles or models generate candidates;
- how candidates are killed, repaired, or compared;
- which niche inspections exceed Workshop's floor;
- what external outcomes inform learning;
- how budgets are divided.

Use canonical Workshop types at the boundary:

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

The words inside a domain can stay accurate—idea, rules, design, print,
playtest. Do not invent synonyms for shared Workshop concepts.

## 5. Compose Make and Inspect

Inject outside dependencies through qualified Doors:

```python
from inventor_workshop import Workbench

WORKBENCH = Workbench(
    model_door,
    cad_door,
    cad_inspection_door,
    inspection_door,
)
```

A production Make path must bind:

- the exact Wish;
- the exact Taste;
- pinned model/tool/skill versions where reproducibility matters;
- a code-enforced budget;
- a fresh contained workspace;
- a content-addressed artifact manifest.

Then call `WORKBENCH.inspect(made)` as a distinct stage. Inspect must bind its
CAD release, results, and evidence files to the exact artifact bytes returned
by Make.

Every candidate loop should also leave a `maker-mark.json` beside its evidence.
Build the mark from what the adapter actually observed, never from the mode the
run merely requested:

```python
from inventor_workshop import MakerMark

mark = MakerMark(
    schema_version=1,
    inventor_id="deduction-games",
    run_id=run_id,
    mode=observed_mode,              # live | fixture | offline | replay
    tool=observed_tool,
    tool_version=exact_tool_version,
    authenticated=tool_session_was_authenticated,
    taste_sha256=taste.sha256,
    artifact_sha256=made.artifact_manifest.artifact_sha256,
    input_sha256={"wish": wish_sha256},
    agent_calls=observed_agent_calls,
    actual_cost_micros=actual_cost_micros,
    synthetic_cost_micros=synthetic_cost_micros,
    started_at=started_at,
    completed_at=completed_at,
    limitations=tuple(observed_limitations),
)
(candidate_root / "maker-mark.json").write_text(
    mark.to_json() + "\n", encoding="utf-8"
)
```

Fixture, offline, and replay marks are always unauthenticated and report zero
actual cost; their estimates belong in `synthetic_cost_micros`. They may still
record many deterministic agent-role calls. Live marks report zero synthetic
cost. Only `mark.may_claim_live_creation` supports saying an authenticated live
agent tool made the candidate. It does not claim printability, beauty,
inspection, physical testing, or production readiness.

Before trusting a mark beside a selected product, call
`mark.assert_artifact(selected_artifact_sha256)`. Moving a valid mark beside
different output bytes must fail that check.

For the CAD result, keep the report and release identities distinct:

- `evidence_ref` and `evidence_sha256` identify a real report inside the
  selected sealed evidence manifest;
- `evidence["cad_release_sha256"]` identifies the validated
  `CadReleaseBundle` carried by the `Inspection`.

Workshop ships three versioned making skills:

```bash
workshop skills list
workshop skills path
```

- `cad`
- `step-parts`
- `product-to-cad`

Discovery does not equal adoption. Invoke the chosen skill from the runtime,
pin its fingerprint, and test that boundary before declaring its feature.

An `Inspection` preserves both passed and failed results as artifact-bound
feedback. It rejects mismatched artifact hashes, missing evidence paths, and
evidence hash drift. `Workflow` blocks a transition when a result required by
that target is missing or failed; an optional failure remains visible in the
event without vetoing the required passing set. Missing or unmeasurable is a
hold, not a pass.

When review evidence should not ship in the customer's Pack, seal it separately
and pass the typed manifest through the normal boundary:

```python
evidence_manifest = seal_artifact(
    inspection_root, created_at="content-addressed"
)
inspection = WORKBENCH.inspect(
    made, evidence_manifest=evidence_manifest
)
```

Every result still names the product artifact hash. Its evidence path and hash
resolve in `evidence_manifest`; CAD part paths continue to resolve in the
product manifest. Omitting the keyword keeps the single-manifest compatibility
behavior.

## 6. Pack and Send only when needed

Use `pack_artifact()` to create exact deterministic transport bytes. Do not
hand-build a ZIP in each inventor.

```python
packed = pack_artifact(artifact_root, output_zip)
WORKFLOW.advance(
    clockwork,
    product_id,
    "pack",
    expected_revision,
    packed=packed,
)
```

The canonical Pack transition requires the structured `PackedArtifact`,
revalidates its exact bytes and artifact identity, and records `pack_sha256`
in Clockwork. Do not advance to Pack with a loose path or caller-authored hash.

If the Wish is fulfilled directly, send through a `DeliveryDoor`. If the thing
will be sold, use a `ShopDoor`. A shop is optional; it is not the main product
journey.

`Sender` persists an intent before an outside effect and requires a trustworthy
`Stamp`. Timeouts and unclear responses stay held for reconciliation.

Keep credentials:

- scoped to one inventor and one Door;
- outside the repository and Pack;
- absent from prompts, logs, state payloads, and exception text;
- unable to silently fall back to a human/shared principal.

## 7. Declare only real features

New manifests use schema v3:

```json
{
  "schema_version": 3,
  "id": "deduction-games",
  "name": "Ada",
  "niche": "Two-player printable deduction games",
  "summary": "An autonomous inventor for compact physical deduction games.",
  "autonomy": "human-checkpointed",
  "status": "experimental",
  "entrypoint": ["python3", "-m", "deduction_games"],
  "capabilities": ["game-design", "cad"],
  "workshop_features": [
    "clockwork.state",
    "clockwork.workflow",
    "inspect.evidence",
    "make.workbench",
    "taste.content-addressed"
  ],
  "checks": [[
    "python3", "-m", "unittest", "discover",
    "-s", "tests", "-p", "test_*.py", "-v"
  ]],
  "source": {"kind": "local"}
}
```

The reviewed feature catalog is exported as
`inventor_workshop.WORKSHOP_FEATURES`. `workshop check` rejects invented or
misspelled values.

## 8. Test the failure paths

At minimum, prove:

- root Taste is loaded and content-bound;
- `doctor` and `status` do not create state;
- the offline Make works without credentials;
- a changed Taste or artifact fails closed;
- missing, failed, stale, or mismatched required Inspection evidence cannot
  advance;
- budgets and leases cannot be bypassed by another entry point;
- Pack excludes credentials and mutable runtime state;
- a Door timeout or malformed response cannot be treated as a Stamp;
- ambiguous non-idempotent effects are not blindly retried;
- legacy names, if supported, cannot create a competing authority.

Mocks must exercise the same typed boundaries as production. Mark synthetic
evidence as synthetic and never describe the offline Make as production CAD or
a real physical test.

## 9. Run contribution checks

```bash
python -m unittest discover -s workshop/tests -p 'test_*.py' -v
workshop skills list
workshop schemas list
workshop inventors --root inventors --check-entrypoints
workshop check inventors/deduction-games --run
python workshop/tools/verify_skill_locks.py
python workshop/tools/verify_snapshot_locks.py
python workshop/tools/scan_secrets.py
git diff --check
```

Then open a PR using the repository template. A reviewer should be able to
understand the Taste, run the inventor offline, distinguish synthetic evidence from
live evidence, and see exactly which Workshop features the code exercises.

## When to extend Workshop

Put code in `workshop/` when at least two inventors need the same invariant or
boundary and the behavior can remain inventor-neutral. Put code in the
inventor when it expresses Taste, niche judgment, prompts, reward hypotheses,
or a stricter local inspection.

Shared additions need standard-library-safe contracts, credential-free tests,
failure-path tests, documentation, and backward-compatible state handling.

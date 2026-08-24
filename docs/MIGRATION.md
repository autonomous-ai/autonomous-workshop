# Migration to Workshop 0.5

Workshop 0.5 turns the repository into one opinionated Toy Workshop for
playthings for grown-ups. Every new profile uses one of five product categories
and the same five jobs:

```text
Wish -> Make <-> Playtest -> Docs -> Deliver
             feedback
```

Migration is incremental. Preserve characterized behavior and persisted
effects while moving one exact, tested boundary at a time. Current profile
readiness is recorded in [ADOPTION.md](ADOPTION.md).

## What changed in 0.5

- The product scope is classics made yours, games that do not exist yet,
  machines that move, science you can hold, and little worlds.
- `Playtest` is the canonical name for testing and improving an exact Make.
- Docs and Deliver are explicit shared jobs after the Make–Playtest loop.
- Inventors choose Taste-only, custom-Make, or custom-Playtest adoption.
- `playtest_rounds` can be selected per Wish by a trusted boundary.
- `Workshop`, `WorkshopTools`, typed job contexts/results, five category
  blueprints, AI-player leagues, truthful Docs, and exact Deliver contracts are
  the canonical 0.5 surface.

The distribution remains `inventor-workshop`, the import remains
`inventor_workshop`, the CLI remains `workshop`, and mutable per-profile state
remains under `.workshop/`.

## Repository and manifest continuity

The repository-root layout introduced in 0.4 remains canonical:

```text
inventors/              thin profiles and inventor-owned work
src/inventor_workshop/  shared Workshop implementation
skills/                 locked making knowledge
schemas/                portable data contracts
docs/                   architecture and operating guidance
tests/                  shared invariant tests
```

Schema-v4 inventor manifests still require `checks` and do not enumerate
shared implementation features. Every profile in this repository already
belongs to Workshop, so repeating an internal feature inventory in each
identity would couple inventors to implementation details.

Historical manifests remain readable according to their declared version:

| Manifest schema | Historical feature field |
|---|---|
| v1 | `core_features` |
| v2 | `foundation_features` |
| v3 | `workshop_features` |
| v4 | none |

The old package-name import shims remain read-only compatibility routes to the
same implementation. They must not own separate state or behavior.

The product taxonomy is a semantic migration, not merely label replacement:

| Earlier compatibility ID | Canonical 0.5 category |
|---|---|
| `table-game` | split by intent: `classics-made-yours` or `invented-games` |
| `desk-toy` | `moving-machines` |
| `model-character` | `holdable-science` for the canonical science profile; reassess other old models rather than relabeling blindly |
| `puzzle-keepsake` | `little-worlds` when the Wish materially personalizes the world; reassess generic puzzles |

Do not rewrite old artifact metadata in place. New Wishes use the canonical
category; existing artifacts retain the category under which they were made.

All canonical categories enforce the product bar: the result could not have
been downloaded before the Wish; cool, clever, or striking beats merely cute
or twee; and personalization plus design intelligence beats a generic print.
Kits and numbered series are later variants, not jobs or current V1 promises.

Classics use known rules and are judged as exact custom editions and physical
objects. Invented games must reach an independent human table that wants
another play. Even 1,000 clean AI simulations cannot pass that release gate.

## Migrate vocabulary without rewriting history

New prose, profiles, and code use `Playtest`, `PlaytestResult`,
`PlaytestPolicy`, and `Workbench.playtest()`. The previous code-facing names
remain aliases so mature inventors can migrate safely.

Some serialized records deliberately retain their historical field names,
including:

- `inspection_id` for a `PlaytestResult` identifier;
- `required_inspection_ids` in older transition payloads;
- `inspection_evidence_sha256` for the sealed Playtest-evidence artifact;
- existing database stages, tables, commands, environment variables, and
  filenames already used by deployed workers.

Do not bulk-rewrite those values in place. Read them through compatibility,
write the canonical 0.5 concept at new boundaries, and rename persisted state
only through a versioned migration with rollback and golden replay fixtures.

Likewise, older serialization and outside-effect type names remain aliases for
existing imports and state. New inventors should treat artifact serialization,
idempotent provider calls, and receipts as implementation inside Make, Docs, or
Deliver—not as extra public jobs.

`schemas/playtest-result.schema.json` is the canonical 0.5 schema. The existing
`schemas/inspection-result.schema.json` describes the same persisted field
shape for compatibility.

## Migrate the workflow

The old small workflow ended after Make and its review step. The 0.5 product
journey continues through truthful product documentation and physical
delivery:

```text
0.4:  Wish + Taste -> Make <-> legacy review

0.5:  Wish -> Make <-> Playtest -> Docs -> Deliver
              feedback
```

Taste guides every choice but is not a job. Research, ideation, rules, CAD,
simulation, repair, slicing, human trials, rendering, printing, QA, packing,
and carrier calls are tasks within the five jobs.

For a mature state machine:

1. Map its invention output to `MakeContext -> Made` and seal the exact product
   tree.
2. Map every required evaluator and evidence file to
   `PlaytestContext -> Playtested`.
3. Convert failed findings into structured `Feedback` for a new immutable Make
   round.
4. Require a passed Playtest for the exact artifact before creating Docs.
5. Bind every Docs claim and image to that artifact and its evidence.
6. Bind production, QA, packing, and carrier receipts to the exact product and
   Docs hashes before returning Delivered.

Do not run an old and new lifecycle as co-authorities. A thin profile may wait
at a typed seam while the legacy worker continues separately; that is safer
than dual-writing or guessing a conversion.

## Adopt at the smallest level

| Level | Profile owns | Workshop owns |
|---|---|---|
| Taste only | `TASTE.md` | Make, Playtest, loop, Docs, Deliver, runtime |
| Custom Make | Taste and `MakeContext -> Made` | Playtest, loop, Docs, Deliver, runtime |
| Custom Playtest | Taste, custom Make, and `PlaytestContext -> Playtested` | loop, Docs, Deliver, runtime |

A custom Playtest requires a custom Make. Keep stronger niche checks, but return
their observations through the shared result and evidence contracts.

The five canonical profiles cover the five categories exactly once; they are
not five completed live inventors:

- Alice owns `classics-made-yours` at the Taste-only level. Her Blindcap
  laboratory is provenance that taught Workshop, not her active profile or a
  second invented-game elf. Shared Make and Playtest must wait when their real
  capabilities are absent.
- Leo is the clean Workshop-native `invented-games` elf with custom Make and
  custom Playtest. His unfinished typed adapters and mandatory independent
  human-table replay gate wait honestly rather than inheriting a second legacy
  state machine.
- Bob owns `moving-machines` and still waits for a typed custom Make; his
  preserved board-game laboratory is not that adapter.
- Ivy (`holdable-science`) and Eve (`little-worlds`) are Taste-only profiles and
  wait for configured shared tools.

Remove text2cad, text2game, and vibe-ideas from inventor discovery. Their
lessons may remain as cited research provenance in Docs, but they are not elves,
profiles, manifests, or extra product categories.

## Add the per-Wish Playtest allowance

Existing profiles may keep a constructor default for compatibility. New
service code should choose the allowance at the trusted Wish boundary:

```python
run = workshop.run(wish, playtest_rounds=4)
```

The value must be an integer from 1 through 100 and is recorded with the Wish,
returned in `WorkshopRun`, and passed into each Make and Playtest context. It
limits the number of Make–Playtest improvement rounds. It does not limit the
number of seeded games or evaluators inside one Playtest round unless a separate
trusted budget says so.

Migration rules:

1. Obtain the allowance from a trusted checkout, quote, operator policy, or
   fixed default—not free-form Wish text.
2. Persist it before the first Make.
3. Keep it constant for that run and expose it to custom hooks.
4. Stop if it is exhausted while Playtest still fails.
5. Never translate fewer rounds into fewer required checks, weaker thresholds,
   synthetic evidence, or permission to continue to Docs.

More rounds buy more repair opportunities. All service tiers face the same
acceptance policy.

## Preserve exact product and evidence identities

Keep these identities distinct:

- the logical product artifact-tree hash;
- the sealed Playtest-evidence artifact hash;
- the exact serialized payload hash used at a process or network boundary;
- the Docs artifact hash;
- authenticated production and carrier receipt identities.

Equal logical files can have different transferred bytes, and evidence files
must not silently enter the customer product. Persisted payload fields may keep
their old names; their meaning must not change.

On every migration seam, test:

- changed Taste or product bytes after Make;
- evidence for another product revision;
- missing or hash-mismatched evidence references;
- a failed required result with no actionable feedback;
- Docs generated from failed or stale Playtest evidence;
- product or Docs bytes changed before Deliver;
- timeout, redirect, malformed response, or uncertain external readback.

All fail closed.

## Preserve one outside-effect authority

Existing databases and effect ledgers may retain historical table and field
names. Renaming vocabulary is not worth risking duplicate production,
publication, or shipment.

For every external effect:

1. record the exact request and stable idempotency identity before execution;
2. use a separate attempt fence;
3. bind the result to the request and exact artifact identities;
4. validate an authenticated receipt;
5. hold ambiguous outcomes for reconciliation instead of blind retry.

Inventor-local JSON may remain a readable projection, but only one durable
ledger may authorize the effect. Never infer success from HTTP status, a local
Boolean, a model-authored message, or a generated carrier label.

When resolving existing state paths, prefer an explicit configured path,
continue exactly one existing database in place, refuse multiple candidates,
and never merge authorities by modification time.

## Recommended order for a mature inventor

1. Characterize current Wishes, transitions, artifacts, evidence, budgets,
   effects, failures, and reconciliation with golden fixtures.
2. Establish one root `TASTE.md` and exact binding.
3. Select one canonical product category and the smallest customization level.
4. Add the canonical profile and let unfinished seams return `WaitingFor`.
5. Adopt immutable `Made` identity without weakening local invariants.
6. Adopt artifact-bound `Playtested` evidence and actionable feedback.
7. Add trusted per-Wish `playtest_rounds` without changing gates.
8. Move lifecycle, leases, and budgets only after parity tests pass.
9. Adopt shared Docs, then exact production and Deliver receipts.
10. Simplify operational names only after every entry point uses one authority.

Blindcap provenance and Bob's preserved laboratory should retain every stronger
native invariant until Workshop proves equivalent behavior. Alice's active
classics profile, Eve, and Ivy stay thin; improve shared tools instead of
growing duplicate infrastructure in their folders. Leo and Bob keep only their
category-specific custom seams.

## Verification

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py' -v
workshop inventors --root inventors --check-entrypoints
python3 tools/verify_skill_locks.py
python3 tools/verify_snapshot_locks.py
python3 tools/scan_secrets.py
git diff --check
```

Test canonical and compatibility imports, persisted-state fixtures, conflicting
authority rejection, installed artifacts, allowance tampering, and ambiguous
outside effects before deleting any compatibility route.

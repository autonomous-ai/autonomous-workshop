# Migration to Workshop 0.5

Workshop 0.5 turns the repository into one opinionated Toy Workshop for
playthings for grown-ups. Every new profile uses one of five product categories
and the same five jobs:

```text
Wish -> Make <-> Playtest -> Instructions -> Deliver
             feedback
```

Migration is incremental. Preserve characterized behavior and persisted
effects while moving one exact, tested boundary at a time. Current profile
readiness is recorded in [ADOPTION.md](ADOPTION.md).

## What changed in 0.5

- The product scope is classics made yours, games that do not exist yet,
  machines that move, science you can hold, and little worlds.
- `Playtest` is the canonical name for testing and improving an exact Make.
- Instructions and Deliver are explicit shared jobs after the Make–Playtest loop.
- Inventors choose Taste-only, custom-Make, or custom-Playtest adoption.
- Intake is one Wish at a time through a Taste-based Workshop Manager; a
  continuously running scheduler is not an inventor requirement.
- `playtest_rounds` can be selected per Wish by a trusted boundary.
- `Workshop`, `WorkshopTools`, typed job contexts/results, five category
  blueprints, AI-player leagues, truthful Instructions, and exact Deliver contracts are
  the canonical 0.5 surface.

The distribution remains `inventor-workshop`, the import remains
`inventor_workshop`, the CLI remains `workshop`, and mutable per-profile state
remains under `.workshop/`.

`workshop create inventor` is the canonical profile creator. The former
`workshop new` command remains parseable during 0.x migration but is hidden
from help; new documentation and automation should provide a routing-oriented
`--description` instead of the older vague `--niche` field.

The manifest field named `autonomy` remains compatibility metadata about human
checkpointing inside one assignment. It is not an uptime guarantee and must
not be interpreted as a requirement for a profile-owned queue, daemon, or
24/7 process.

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

Schema v5 is the required authoring format for new inventor manifests. It keeps
only operational fields: `schema_version`, `id`, `status`, `entrypoint`,
`capabilities`, `checks`, and `source`. Creative identity and routing prose now
live only in `TASTE.md` frontmatter and body. Every profile in this repository
already belongs to Workshop, so repeating a name, niche, summary, autonomy
claim, or shared feature inventory in `inventor.json` would create a second,
drifting creative identity.

Historical manifests remain readable according to their declared version:

| Manifest schema | Read/write role | Creative identity |
|---|---|---|
| v1 | read-only compatibility | manifest prose + `core_features` |
| v2 | read-only compatibility | manifest prose + `foundation_features` |
| v3 | read-only compatibility | manifest prose + `workshop_features` |
| v4 | read-only compatibility | manifest `name`, `niche`, and `summary` |
| v5 | current contribution format | `TASTE.md` only |

When migrating a v1-v4 inventor, move its discriminating name and description
to strict `TASTE.md` frontmatter, keep its full creative constitution in the
Markdown body, remove creative prose and legacy feature fields from
`inventor.json`, and set `schema_version` to `5`. Do not rewrite old manifests
in persisted receipts; the reader retains v1-v4 compatibility for those exact
historical records.

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
been bought before the Wish; cool, clever, or striking beats merely cute
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
idempotent provider calls, and receipts as implementation inside Make, Instructions, or
Deliver—not as extra public jobs.

`schemas/playtest-result.schema.json` is the canonical 0.5 schema. The existing
`schemas/inspection-result.schema.json` describes the same persisted field
shape for compatibility.

## Migrate intake to one-shot assignment

Older experiments may discover work themselves, own a queue, or remain alive
between products. Do not copy those operational assumptions into a canonical
inventor. V1 intake has one request-scoped boundary:

```text
one Wish -> Workshop Manager -> one chosen Taste -> one assignment
                                                     |
                                                     v
                       Wish -> Make <-> Playtest -> Instructions -> Deliver
                                    feedback
```

For each Wish, the Manager searches an open catalog built from the short
`name` and `description` in every `TASTE.md`, records a bounded shortlist, and
loads the complete exact Taste only for those finalists. A semantic judge
returns one explained assessment per finalist and the Manager selects the best
accepted fit deterministically. The assignment binds the untouched Wish,
catalog and retrieval receipts, finalist Taste hashes, complete ranking,
selected entry point, and trusted Playtest-round allowance. A stale relevant
catalog entry, finalist Taste, or selected manifest invalidates dispatch.

Migrate an old intake loop by separating these responsibilities:

1. Keep parsing and validation at the trusted Wish boundary.
2. Move creative-fit selection into catalog retrieval followed by exact-Taste
   finalist judgment; do not put every Taste body in one prompt.
3. Record the retrieval receipt, complete finalist ranking, and explanation,
   not just the winner.
4. Dispatch the content-bound assignment exactly once.
5. Let the selected profile enter the shared five-job workflow without
   rediscovering or rerouting the Wish.

If no Taste fits, return a truthful wait for clarification or a new inventor.
Do not weaken an existing Taste, use keyword routing, or choose the least-bad
inventor. A future scheduler may wrap this one-Wish API and invoke it repeatedly,
but that adapter remains outside inventor folders and does not become a sixth
Workshop job.

## Migrate the workflow

The old small workflow ended after Make and its review step. The 0.5 product
journey continues through truthful product documentation and physical
delivery:

```text
0.4:  Wish + Taste -> Make <-> legacy review

0.5:  Wish -> Make <-> Playtest -> Instructions -> Deliver
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
4. Require a passed Playtest for the exact artifact before creating Instructions.
5. Bind every Instructions claim and image to that artifact and its evidence.
6. Bind production, QA, packing, and carrier receipts to the exact product and
   Instructions hashes before returning Delivered.

Do not run an old and new lifecycle as co-authorities. A thin profile may wait
at a typed seam while the legacy worker continues separately; that is safer
than dual-writing or guessing a conversion.

## Adopt at the smallest level

| Level | Profile owns | Workshop owns |
|---|---|---|
| Taste only | `TASTE.md` | Make, Playtest, loop, Instructions, Deliver, runtime |
| Custom Make | Taste and `MakeContext -> Made` | Playtest, loop, Instructions, Deliver, runtime |
| Custom Playtest | Taste, custom Make, and `PlaytestContext -> Playtested` | loop, Instructions, Deliver, runtime |

A custom Playtest requires a custom Make. Keep stronger niche checks, but return
their observations through the shared result and evidence contracts.

The five bundled showcase profiles currently demonstrate the five categories;
they are examples, not a closed catalog or five completed live inventors:

- Alice demonstrates `classics-made-yours` at the Taste-only level. Her Blindcap
  laboratory is provenance that taught Workshop, not her active profile or a
  second invented-game inventor. Shared Make and Playtest must wait when their real
  capabilities are absent.
- Leo is the clean Workshop-native `invented-games` inventor with custom Make and
  custom Playtest. His unfinished typed adapters and mandatory independent
  human-table replay gate wait honestly rather than inheriting a second legacy
  state machine.
- Bob demonstrates `moving-machines` and still waits for a typed custom Make; his
  preserved board-game laboratory is not that adapter.
- Ivy (`holdable-science`) and Eve (`little-worlds`) are Taste-only profiles and
  wait for configured shared tools.

Remove the retired early team experiments from inventor discovery. Their useful
techniques may be reimplemented behind shared Workshop contracts. New local or
community inventors are welcome after they satisfy the same Taste, operational
manifest, entrypoint, and evidence contracts; multiple profiles may serve the
same category.

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
   synthetic evidence, or permission to continue to Instructions.

More rounds buy more repair opportunities. All service tiers face the same
acceptance policy.

## Preserve exact product and evidence identities

Keep these identities distinct:

- the logical product artifact-tree hash;
- the sealed Playtest-evidence artifact hash;
- the exact serialized payload hash used at a process or network boundary;
- the Instructions artifact hash;
- authenticated production and carrier receipt identities.

Equal logical files can have different transferred bytes, and evidence files
must not silently enter the customer product. Persisted payload fields may keep
their old names; their meaning must not change.

On every migration seam, test:

- changed Taste or product bytes after Make;
- evidence for another product revision;
- missing or hash-mismatched evidence references;
- a failed required result with no actionable feedback;
- Instructions generated from failed or stale Playtest evidence;
- product or Instructions bytes changed before Deliver;
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
3. Add explicit best-fit, not-for, and hard-boundary guidance so the Manager
   can compare this Taste with the other four complete Tastes.
4. Select one canonical product category and the smallest customization level.
5. Replace profile-owned polling with one content-bound assignment entry point;
   keep any needed scheduler as a separate application adapter.
6. Add the Workshop-native profile and let unfinished seams return `WaitingFor`.
7. Adopt immutable `Made` identity without weakening local invariants.
8. Adopt artifact-bound `Playtested` evidence and actionable feedback.
9. Add trusted per-Wish `playtest_rounds` without changing gates.
10. Move lifecycle, leases, and budgets only after parity tests pass.
11. Adopt shared Instructions, then exact production and Deliver receipts.
12. Simplify operational names only after every entry point uses one authority.

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

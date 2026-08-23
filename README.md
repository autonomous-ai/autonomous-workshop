# Inventor Foundation

This repository is the architecture and working blueprint for building
autonomous AI inventors. [`foundation/`](foundation/) is the reusable paved
road; [`inventors/`](inventors/) contains working implementations and reference
designs built on top. Niche, personality, taste, prompts, mechanisms, and reward
hypotheses stay with each inventor.

```text
inventors/
  alice/  bob/  eve/
  text2cad/  text2game/  vibe-ideas/
foundation/
  src/  skills/  schemas/  docs/  tests/
```

## Architecture blueprint

Inventors depend on Foundation. Foundation never imports an inventor.

```text
+--------------------------- inventors/ -----------------------------+
|                                                                    |
|  alice/        books + history + reward policy                     |
|  bob/          literature + simulation + table play                |
|  eve/          great-books loop + journal + concepts               |
|  text2cad/     registered upstream snapshot                        |
|  text2game/    registered upstream snapshot                        |
|  vibe-ideas/   registered upstream snapshot                        |
|  <new>/        TASTE + niche logic + prompts + evaluators           |
|                                                                    |
|  Each inventor owns its identity, taste, creative process,         |
|  domain gates, adapters, tests, and reward hypothesis.             |
+--------------------------------+-----------------------------------+
                                 |
                                 | imports and uses
                                 v
+-------------------------- foundation/ -----------------------------+
|                                                                    |
|  Registry + scaffolder                                             |
|       |                                                            |
|       v                                                            |
|  Lifecycle + state  <----- narrow ports for agents, CAD, evals,    |
|       |                    publishing, and fulfillment              |
|       v                                                            |
|  Artifact identity + evidence gates <----- creation/CAD skills      |
|       |                                                            |
|       v                                                            |
|  Publication outbox + exact receipts + effect fencing              |
|                                                                    |
|  Foundation owns shared invariants. It never imports an inventor.  |
+------------+----------------------+----------------------+----------+
             |                      |                      |
             v                      v                      v
      model providers       CAD/slicer/physical       Panda/Factory
                                test systems             and Store
```

### Build a new inventor on top

```text
inventor-foundation new deduction-games --name Ada --niche ... --root inventors
                                      |
                                      v
                           +--------------------+
                           | atomic scaffolder  |
                           +---------+----------+
                                     |
                                     v
+---------------- inventors/deduction-games/ ----------------+
|                                                            |
|  inventor.json       identity, niche, capabilities          |
|  TASTE.md            human-owned creative constitution      |
|       |                                                    |
|       v                                                    |
|  prompts + roles + generators + reward hypothesis           |
|       |                                                    |
|       v                                                    |
|  workflow.py         default or stricter PipelineSpec       |
|       ^                                                    |
|       |                                                    |
|  adapters/           models, CAD, evaluation, publishing    |
|  tests/              golden artifacts + behavior tests      |
|  CLI                 init, create, status                   |
|  .runtime/           stable local state; never committed    |
+----------------------------+-------------------------------+
                             |
                             | imports
                             v
+---------------------- Inventor Foundation -----------------+
|  Pipeline + policy floors                                  |
|       +--> InventorStore: revisions, leases, budgets        |
|       +--> artifact and gate contracts                      |
|       +--> CAD release bundles                              |
|       +--> publication outbox and receipts                  |
|       `--> narrow adapter ports                             |
|                                                            |
|  Inventor may add stages or stricter gates.                 |
|  Inventor may not weaken Foundation safety floors.          |
+------------------------------------------------------------+
```

### Shared invention-to-publication path

```text
[Idea] -> [Research] -> [Rules] -> [Simulation] -> [CAD/product build]
                                                        |
                                                        v
                                      [Content-addressed artifact]
                                                        |
                                                        v
                                      [Pinned evidence gates]
                                         /            \
                           missing/stale/fail          all pass
                                     |                    |
                                     v                    v
                      [hold / repair / park / kill]   [reviewed]
                                                          |
                                                          v
                                      [canonical packet + artifact hash]
                                                          |
                                                          v
                                          [outbox: planned -> sending]
                                             /          |          \
                                  valid receipt   proven no effect   ambiguous
                                      |                 |               |
                                      v                 v               v
                         [receipt-bound draft]      [rejected]       [unknown]
                                      |                            never retry
                                      v
                         [publish + authenticated readback]
                                  /                 \
                              exact                 ambiguous
                                |                       |
                                v                       v
                             [live]               [live_unknown]
                                                  GET-only reconcile
```

The deeper contract, ownership, evidence, and failure-mode details live in
[Foundation architecture](foundation/docs/ARCHITECTURE.md).

## Inventor registry

| Inventor | Niche | Autonomy | Integration status |
|---|---|---|---|
| [Alice](inventors/alice/) | Original printable board games informed by books/history | autonomous | Foundation artifact boundary connected; live activation blocked on authenticated adapters and a bound Factory contract |
| [Bob](inventors/bob/) | Printable board games | autonomous | Foundation skills, packets, and Panda draft/live outbox connected; first real live cycle pending |
| [Eve](inventors/eve/) | Printable board games + great-books study | autonomous | Foundation build snapshot, packets, and Panda draft outbox connected; publication remains draft/manual |
| [text2cad](inventors/text2cad/) | Trend-driven printable mechanisms/products | autonomous | pinned reference snapshot; credential rotation and Foundation migration required |
| [text2game](inventors/text2game/) | Fully FDM-printed board games | human-checkpointed | pinned creation-pipeline snapshot; gate hardening in progress |
| [vibe-ideas](inventors/vibe-ideas/) | Deeply playtested printable board games | human-checkpointed | pinned reference snapshot; queue/gate hardening required |

Validate the catalog without executing any inventor:

```bash
PYTHONPATH=foundation/src python3 -m inventor_core registry --root inventors --check-entrypoints
```

Registry validation rejects control characters, credentialed provenance URLs or
URLs with query/fragment, and manifest/folder/entrypoint symlinks that escape an
inventor boundary. It also requires every inventor to expose a regular,
non-empty root `TASTE.md` as its human-owned creative constitution.

The three imported snapshots preserve the team implementations at exact
upstream commits. Their `UPSTREAM.md` files record origin, exclusions, license
status, and known blockers. They are present for migration and comparison, not
endorsed as unattended production runners. CI also verifies their bytes,
executable/symlink modes, inventories, and commit coverage against
[`foundation/snapshots.lock.json`](foundation/snapshots.lock.json) with the offline
[`foundation/tools/verify_snapshot_locks.py`](foundation/tools/verify_snapshot_locks.py).

## Foundation

[`foundation/`](foundation/) is the paved road for the next ten inventors. Its
v1 package and durable wire identifiers retain their established `core` names
until a versioned compatibility migration can preserve existing receipts and
publication ledgers.

- a strict manifest contract and atomic `inventor-foundation new` scaffolder
  (`inventor-core` remains a compatibility alias); new
  packages target Python 3.11+ and resolve one stable runtime database
  regardless of the launch directory, with `create <product-id>` and `status`
  commands for initial product registration and inspection;
- private revision-CAS transitions behind lifecycle policy, expiring opaque
  lease tokens that fence effect starts, schema-v3 per-attempt tokens that fence
  completions, a 24-hour lease/renewal ceiling without token changes, and
  tamper-evident event chains in a private SQLite/WAL store;
- immutable active budget windows/limits with per-spend policy/result snapshots
  and idempotent keys shared by daemon, CLI, and human-repair paths, plus
  read-only `budget_status()` observation;
- explicit lifecycle graphs with cumulative `GatePolicy`-pinned evidence,
  freshness limits, and exact artifact binding;
- deterministic artifact manifests and bounded, secret-stripping Panda packets
  with no-follow reads, final send-time checks, fixed metadata, and `ZIP_STORED`
  members for cross-zlib reproducibility;
- engine-neutral `CadReleaseBundle` identities across deterministic and
  independent-review substrates, adding physical evidence for critical claims,
  with exact validator/version/config policy, typed semantics for all ten Foundation
  checks, and nested finite-JSON revalidation;
- one canonical CAD and STEP-parts skill tree plus the new
  `product-to-cad` workflow for printable, attractive products;
- a durable Panda publication outbox: explicit draft import, inventor-owner
  verification, `PublicationOutcome(intent_id, receipt)` carried through draft
  and live, packet/artifact/history continuity, per-attempt effect fencing,
  rejected-attempt history, and active USD price/SKU readback before `live`;
- narrow ports for model agents, CAD engines, evaluators, publishers, and
  fulfillment so Panda/Vibe/Factory stay independently deployed services.

Panda's current readback does not expose the imported packet/tree hash or an
idempotency identity. Foundation therefore cannot safely reconcile an ambiguous
import from a slug and will not retry it. Only the explicit proven-no-effect
status allowlist is treated as rejection rather than ambiguity; redirects,
conflicts, throttling, unexpected success, 5xx, and transport failures remain
ambiguous. Likewise, one `draft` readback after an uncertain public flip never
authorizes another POST; the intent remains `live_unknown` until the exact
current history and requested active USD listing with SKU are observed. Backend
idempotency/content receipts and scoped inventor principals remain prerequisites
for unattended publication.

Create a new niche inventor without cloning Alice, Bob, or Eve:

```bash
PYTHONPATH=foundation/src python3 -m inventor_core new deduction-games \
  --name "Ada" \
  --niche "two-player printable deduction games" \
  --root inventors
```

Read [Foundation architecture](foundation/docs/ARCHITECTURE.md), the
[current adoption map](foundation/docs/ADOPTION.md), [migration plan](foundation/docs/MIGRATION.md), and the evidence-backed
[64-repository ecosystem map](foundation/docs/ECOSYSTEM.md) before adding shared
infrastructure to an inventor folder.

## House rules

1. **The evaluator is part of the product.** Freeze deterministic gates and
   bind every result to the source/artifact/evidence/config/tool versions and
   freshness policy it measured.
2. **Unknown is not pass.** Missing, stale, malformed, exception, timeout, or
   unsupported physical claim is `held` and blocks release.
3. **No product today is valid.** Never select a weak fallback after the floor
   has no survivor.
4. **Budgets and legal transitions live in code.** Lifecycle changes go through
   `Pipeline.advance`; every execution path uses current lease/effect fences and
   the same persisted budget policy plus idempotent spend ledger.
5. **Durable artifacts are the message bus.** Agents exchange immutable files
   and typed receipts, not unverifiable claims of success.
6. **External outcomes outrank self-scores.** Sales, returns, human replay,
   printed coupons, and owner decisions beat a rubric the generator can flatter.
7. **Publish draft-first and by receipt.** A local flag, HTTP success, or lone
   non-public readback does not mean retry or `live`; carry the durable intent
   ID and accept only readback of its exact history and requested active listing.
8. **AI creators publish as distinct principals.** Never borrow a human or
   shared bearer identity. Until Panda supports scoped inventor principals,
   unattended publishing remains blocked.

## Relocation note

Existing launchd deployments must be redeployed from the inventor's `ops/`
runbook because rendered service files contain absolute checkout paths. External
cron or operator configuration must likewise point into `inventors/<id>/`.

## Security

The upstream `text2cad` repository currently tracks an environment backup with
live-looking credentials. That file was excluded here. Rotate/revoke those
Telegram, admin, MongoDB, and Panda values and purge the upstream history.

Run the repository policy check before committing:

```bash
python3 foundation/tools/scan_secrets.py
```

The scanner rejects secret-shaped paths, source backups, private-key material,
and high-confidence credential patterns without printing matched values.

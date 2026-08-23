# Autonomous inventors

This is the team monorepo for autonomous AI inventors. Each inventor gets one
top-level folder containing its complete implementation, operating guide, and
`inventor.json`. Shared infrastructure lives in [`core/`](core/); niche,
personality, taste, prompts, mechanisms, and reward hypotheses stay with the
inventor.

## Inventor registry

| Inventor | Niche | Autonomy | Integration status |
|---|---|---|---|
| [Alice](alice/) | Original printable board games informed by books/history | autonomous | core artifact boundary connected; live activation blocked on authenticated adapters and a bound Factory contract |
| [Bob](bob/) | Printable board games | autonomous | core skills, packets, and Panda draft/live outbox connected; first real live cycle pending |
| [Eve](eve/) | Printable board games + great-books study | autonomous | core build snapshot, packets, and Panda draft outbox connected; publication remains draft/manual |
| [text2cad](text2cad/) | Trend-driven printable mechanisms/products | autonomous | pinned reference snapshot; credential rotation and core migration required |
| [text2game](text2game/) | Fully FDM-printed board games | human-checkpointed | pinned creation-pipeline snapshot; gate hardening in progress |
| [vibe-ideas](vibe-ideas/) | Deeply playtested printable board games | human-checkpointed | pinned reference snapshot; queue/gate hardening required |

Validate the catalog without executing any inventor:

```bash
PYTHONPATH=core/src python3 -m inventor_core registry --root . --check-entrypoints
```

Registry validation rejects control characters, credentialed provenance URLs or
URLs with query/fragment, and manifest/folder/entrypoint symlinks that escape an
inventor boundary.

The three imported snapshots preserve the team implementations at exact
upstream commits. Their `UPSTREAM.md` files record origin, exclusions, license
status, and known blockers. They are present for migration and comparison, not
endorsed as unattended production runners. CI also verifies their bytes,
executable/symlink modes, inventories, and commit coverage against
[`core/snapshots.lock.json`](core/snapshots.lock.json) with the offline
[`core/tools/verify_snapshot_locks.py`](core/tools/verify_snapshot_locks.py).

## Core

[`core/`](core/) is the paved road for the next ten inventors:

- a strict manifest contract and atomic `inventor-core new` scaffolder; new
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
  with exact validator/version/config policy, typed semantics for all ten core
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
idempotency identity. Core therefore cannot safely reconcile an ambiguous
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
PYTHONPATH=core/src python3 -m inventor_core new deduction-games \
  --name "Ada" \
  --niche "two-player printable deduction games" \
  --root .
```

Read [core architecture](core/docs/ARCHITECTURE.md), the
[current adoption map](core/docs/ADOPTION.md), [migration plan](core/docs/MIGRATION.md), and the evidence-backed
[64-repository ecosystem map](core/docs/ECOSYSTEM.md) before adding shared
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

## Security

The upstream `text2cad` repository currently tracks an environment backup with
live-looking credentials. That file was excluded here. Rotate/revoke those
Telegram, admin, MongoDB, and Panda values and purge the upstream history.

Run the repository policy check before committing:

```bash
python3 core/tools/scan_secrets.py
```

The scanner rejects secret-shaped paths, source backups, private-key material,
and high-confidence credential patterns without printing matched values.

# Inventor migration plan

Migration is incremental. Preserve each inventor's creative behavior and golden
artifacts while replacing shared infrastructure behind adapters. Do not rewrite
all six state machines at once.

The first executed adoption slice is complete for Alice, Bob, and Eve. Its
exact boundaries and state ownership are recorded in [ADOPTION.md](ADOPTION.md).
They use core for artifacts and/or publication without claiming the complete
definition below; creative lifecycle, lease, and budget migrations remain
fixture-gated follow-up work.

## Definition of core-connected

An inventor is core-connected when it has:

1. a valid control-free `inventor.json`, contained entrypoint, credential-free
   provenance, fresh-clone doctor, and byte/mode snapshot lock where imported;
2. locked dependencies, Python 3.11+ for new scaffolds, and deterministic/mock
   tests;
3. a working-directory-independent runtime path: `.runtime/state.sqlite` in an
   editable inventor checkout or stable per-user application data when
   installed, with generated `create <product-id>` and `status` smoke tests;
4. all lifecycle stage changes through `Pipeline.advance`, with expected
   revisions/current lease tokens fencing transitions, spend, and effect starts,
   schema-v3 effect tokens fencing every asynchronous completion, and lease
   TTL/renewal tests enforcing the 24-hour cap without changing the token;
5. immutable active budget policies, core-clock windows, per-spend policy/result
   snapshots, idempotent keys on every daemon/CLI/repair path, and read-only
   `budget_status()` for observation;
6. content-addressed artifacts, bounded `ZIP_STORED` packets with required
   exclusions, no-follow path reads, final send-time publishability checks, and
   bounded metadata/remote responses;
7. `GatePolicy`-pinned evaluator/version/config/freshness plus a hash-bound
   `CadReleaseBundle` spanning deterministic and independent-review substrates,
   plus physical evidence for critical claims, typed semantics for all ten core
   checks, and nested finite-JSON revalidation;
8. `PublicationOutcome` and one durable intent identity across draft/live, exact
   persisted requests, packet/artifact/owner/history continuity, and readback
   proving active USD listing, requested price, and SKU before `live`;
9. sandboxed/allowlisted agent environments with no publisher secrets;
10. self-improvement in an isolated worktree producing a reviewed patch.

Core connectivity does not yet mean unattended Panda publication is safe. An
ambiguous import cannot be reconciled from a slug because current readback does
not expose a content identity. A non-public readback after an uncertain live
POST likewise cannot authorize retry. Keep those products held until the
backend provides idempotency/content receipts or exact public-history proof is
observed.

## Order

### 0. Secure and preserve provenance

- Rotate and purge the leaked `text2cad` credentials.
- Add root licenses or record explicit permission for the three imported
  snapshots. Until then, keep them internal/reference-only.
- Keep exact upstream pins and source/patch ledgers.
- Keep `core/snapshots.lock.json` synchronized only after intentional review;
  CI's offline verifier must fail any imported byte, mode, inventory, commit, or
  manifest-coverage drift.
- Move large binary fixtures to LFS/object storage while retaining hashes.

### 1. Share assets with zero behavior change

- Complete: Bob's byte-identical CAD and STEP-parts copies now live in
  `core/skills`; Bob uses compatibility symlinks.
- Complete: all six folders have registry manifests.
- Next: pin a complete Python 3.11 CAD dependency graph and canonical renderer.
- Do not import the unlicensed `image-to-cad` files; the clean-room
  `product-to-cad` skill captures the general workflow.

### 2. Characterize before replacing state

- Port Alice's store/effect/reconciliation fixtures and Bob's legal-edge/fenced-
  lease fixtures into core (the private transition primitive, active-lease
  fencing, schema-v3 effect tokens, immutable budget snapshots, and outbox are
  implemented).
- Record golden transitions and artifacts for each inventor.
- Move Eve first to core state because its current queue is ignored/unfenced;
  migrate Bob next; adapt Alice last because it already has the strongest
  SQLite/effect system.
- Remove direct calls to inventor-local transition or spend helpers only after
  every entrypoint proves it reaches `Pipeline.advance` and the same configured
  budget policy.
- Exercise migration copies of every v1/v2 runtime database. Verify the schema
  reports v3, in-flight completions need their persisted `effect_token`, active
  budget policy changes are refused, and exact spend-key replay returns the
  originally snapshotted balance.
- Reject leases longer than 24 hours; prove renewal retains the same fencing
  token. Use `budget_status()` for dashboards instead of zero-value spends or
  direct ledger queries.

### 3. Converge evidence and CAD

- Extract Alice's bounded STL/motion parsing and calibration evidence.
- Add cadpy/build123d and CadQuery adapters behind `CadProjectManifest`.
- Port vibe-ideas interference/ergonomics and text2game fit/group-repair logic
  as validators, fixing fail-open behavior before enabling them.
- Require fresh isolated workspaces, expected-part manifests, deterministic
  renders, slicer DFM, and hash-bound receipts.
- Define every lifecycle gate with a `GatePolicy` and exact evaluator/version/
  config hash. Reject evidence beyond the permitted future-clock skew and set a
  domain max age where recency matters; the default novelty/playtest windows are
  seven/30 days.
- Pin the exact validator set, version, and configuration SHA-256. Preserve at
  least the core `manifest`, `brep`, `mesh-topology`, `dimensions`,
  `interference`, `bed-packing`, `slicer`, `form-review`, and `safety` checks;
  add `physical-claims` for any critical claim and require evidence path/hash
  pairs for passed claims.
- Build a canonical `CadReleaseBundle` and bind its SHA-256 into the CAD gate.
  Keep geometry/DFM checks on the deterministic substrate, form/safety on
  independent review, and critical coupons/tests on the physical substrate.
- Port results into the typed measurement contract for all ten core checks.
  Revalidate every nested finite-JSON/path/version/hash contract at release and
  bundle-hash time so mutable adapter objects cannot bypass construction-time
  checks.

### 4. Converge agent/runtime behavior

- Provider abstraction: Alice sandbox + text2game trace/accounting + Harness
  protocol; deterministic mock first.
- Panels: text2cad independent lenses and fail-closed decision.
- Board-game domain: text2game consistency/harvest plus vibe-ideas rules,
  simulation, isolated table play, exact replay, and audits.
- Cache unchanged stages by complete input hashes as autonomous-tv does.

### 5. Converge publication

- Replace direct publishers with the core Panda coordinator.
- Add contract tests against pinned Swagger/backend fixtures and staging.
- Carry the `PublicationOutcome.intent_id` and receipt directly into the draft
  lifecycle event; require that same persisted intent and exact stored receipt
  for the live event.
- Reapply excluded-name/secret-content checks while reading the final packet,
  and test parent-directory symlink swaps. Bound/allowlist metadata and reject
  over-2-MiB or duplicate-key Panda responses before receipt creation.
- Keep an import in `unknown` after every outcome except a valid 201 draft or an
  explicitly proven-no-effect status. The current allowlist is `400`, `401`,
  `403`, `404`, `405`, `406`, `410`, `411`, `412`, `413`, `414`, `415`, `416`,
  `417`, `421`, `422`, `426`, `428`, `431`, and `451`; redirects, `409`, `429`,
  unexpected 2xx, 5xx, and transport errors remain ambiguous. Never accept a
  human-entered slug as proof.
- Keep a public flip in `live_unknown` until authenticated readback proves the
  exact draft history and active listing at the requested price in USD with a
  non-empty SKU. One draft readback never authorizes retry. Preserve allowlisted
  proven-no-effect attempts in `live_attempts`, with their effect token consumed,
  before sending a corrected explicit-price request under a new token.
- Add slice, upload/media, revision, listing/SKU, unpublish, and fulfillment
  adapters without giving inventors database access.
- Keep unattended live publication blocked until Panda provides distinct scoped
  inventor principals and the external Factory/Store contract is documented.

## Per-inventor extraction

| Inventor | Keep local | Move/reuse from core first |
|---|---|---|
| Alice | research laboratory, reward/release policy, cited corpus | align its mature store/effects/CAD receipts with core APIs; keep stronger guarantees |
| Bob | roles, literature loop, reward, simulation/table policies | canonical skills, publication receipt fix, then queue/budget/store |
| Eve | great-books direction, journaling, game concepts | queue/leases/state, CAD adapters, publisher, ops templates |
| text2cad | discovery lenses, tiered repair, postmortems | secrets/provider sandbox, state/budgets, CAD receipts, publisher |
| text2game | consistency, harvest, grouped build, print kit/media | fail-closed lifecycle, dependency lock, CAD/slice receipts, publisher |
| vibe-ideas | rules/table/replay, ergonomics, interference, audit | legal edges, fencing, parsed verdicts, immutable receipts, safe improvement |

Delete duplicated infrastructure only after characterization and golden-artifact
parity pass. A wrapper adapter is preferable to a flag day.

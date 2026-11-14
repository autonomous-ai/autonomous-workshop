# ADR 0105: An approved Proof keeps the fit table it was approved with

- **Status:** Accepted (builder, 2026-11-14). Implemented with deterministic
  tests. The Amsterdam tray Proof was rebuilt under the legacy table outside a
  run (see Verification). No live seeded run has used it yet.
- **Date:** 2026-11-14
- **Amends:** ADR 0096 (what an Approved Proof seals and what a seeded run
  builds) and the 2026-11-13 resync of the vendored `cad` skill.
- **Unchanged:** every gate. Every new design uses the owner's
  total-clearance rule. Every unseeded run is unchanged.

## Context

The 2026-11-13 resync (ea8b2fcc) brought in the owner's printed-part fit
rule. `cadfits`' `snug` went from 0.10 to 0.05 per side, `slip` from 0.20 to
0.10, and `DEFAULT_FIT` from `slip` to `moving` (0.10). A seeded run builds
its Approved Proof's own sources with the run's installed `cad` skill. So
every Proof approved before that date now builds as different geometry from
the one the owner approved:

- When a Proof asserts its clearance, it no longer builds at all. The
  published Amsterdam tray's `params.py` fails with `the contract's seat
  clearance is 0.2 a side`.
- When a Proof does not assert it, it builds silently with half the gaps.

The owner's rule is for new designs only. Already-approved geometry stays as
approved unless the owner orders a fix.

## Decision

1. **Named fit tables.** The vendored `cadfits` keeps every table it has
   shipped by name in `FIT_TABLES`:
   - `fits-2026-11-13` is the current table.
   - `fits-legacy` is the earlier table: press -0.05, snug 0.10, slip 0.20,
     free 0.40, default `slip`. It also holds the classes that table never
     had, at their current values, for the library's own use. A bought part's
     seat is cut at `clear` 0.20, as `slip` cut it before.

   `WORKSHOP_FIT_TABLE` names the table one process builds with:
   - Unset means the current table.
   - An unknown name makes `cadfits` refuse to import.
   - Default arguments read the pinned table.

   The same variable is part of three keys, so a build under one table never
   reuses another table's result:
   - cadgen's source-closure hash;
   - `cadcache`'s body key;
   - the warm daemon's socket.

   Unset, all three keys stay exactly as recorded before. This is a
   Workshop-local patch (see `PROVENANCE.md`); a resync must keep it.
2. **The approval records its table.** `seal_proof.py` records `fit_table`
   in APPROVAL.json. This is an optional field and the schema stays 4. Its
   value is the table every gate of the seal built with:
   `WORKSHOP_FIT_TABLE`, else the current table. A re-seal refuses another
   table than the previous approval's and names the export that re-seals it
   as approved. `--refit` overrides this when the owner ordered the Proof
   rebuilt under the new rule.
3. **An older approval is placed by its LOCK.** An approval without
   `fit_table` was sealed before this ADR, and its `skills_lock_sha256`
   places it. The one LOCK hash the resync wrote (`6cc66a4a…`) means the
   current table. Any other hash means `fits-legacy`.
   `workshop.wish.fit_tables.approval_fit_table` is the only resolver.
   `validate_seed` refuses a `fit_table` it cannot name.
4. **A seeded run builds with the approval's table.** Two places pin it:
   - `make_round` sets `WORKSHOP_FIT_TABLE` from the run's sealed
     `seed/APPROVAL.json` before any work. Its children inherit it:
     `verify_project`, gen, the print gates and `check_mount`. A caller that
     imports `make_round` gets its own environment back.
   - The host's seeded batch gives every step the same table.

   The host never reruns the CAD verifier for a seeded run, because seeded
   runs are Spark-only (ADR 0061).
5. **Design work names it by hand.** A designer reopening an approved Proof
   exports the table it was approved with. `seal_proof` refuses otherwise.
   New designs leave the variable unset.

## Affected toys

Seeded published toys. All are approved before the resync, so all resolve
to `fits-legacy`, and their seeded fix runs now rebuild as approved:

- `rowan-vale-amsterdam-canal-desk-catchall`
- `rowan-vale-amsterdam-canal-desk-organizer-v01`
- `rowan-vale-amsterdam-canal-desk-organizer-v02`
- `rowan-vale-beaver-coaster-holder-v2`
- `rowan-vale-beaver-coaster-holder-v2-1`
- `rowan-vale-beaver-coaster-keeper-v01`
- `rowan-vale-sunset-slider-night-light-v3`

There are two caveats:

- The two beaver schema 1 seals cannot seed a new run until they are
  re-sealed (ADR 0098). A re-seal must export `fits-legacy`.
- Spec Proofs approved before the resync re-seal the same way:
  `beaver-coasters/proof`, the `mini-city-organizer` Amsterdam, Miami and
  New York Proofs, and `synthwave-arcade-lamp/contract/proof`.

Published toys built without a seed that import `cadfits` or `cadmount` are
not covered. A `workshop fix` of one of them rebuilds under the current
table, as every unseeded rebuild did before. This affects 28 toys, among
them the `bob-*`, `ferro-line-*`, `mira-fold`, `orin-shadow`, `luma-vale`,
`rowan-vale-otter`, `-turtle-moods*`, `-palm-bud-vase`, `-victorian-lamp-post`
and `-amber-desk-computer*` toys. The run starts no seed for them, so no
approval exists to pin. A follow-up would let `workshop fix` freeze the
parent run's table.

## Verification

- Deterministic tests: `tests/make/test_fit_tables.py` and
  `tests/skills/test_seal_proof_fit_table.py`.
- The `cadfits` self-check passes under every table.
- Live: see the PR. The Amsterdam tray Proof, built with
  `make_round --identities-only` under `fits-legacy`, is compared there with
  the identities its approval sealed.

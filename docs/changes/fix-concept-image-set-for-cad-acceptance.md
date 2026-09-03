# Fixed Concept image-set acceptance record

Date: 2026-09-03

Status: deterministic acceptance passed; authenticated acceptance and default
activation remain pending.

## Frozen source identities

| Source | SHA-256 |
| --- | --- |
| `invent-concept-v3.md` | `6b505796c1a734877acae4ab63e6f3bd9cb14dd1d62735fcc3ff143f9003fb9a` |
| `deep-economics-v15.md` | `4a545507cb310b8039f9e14726665bbdf8d7154ffa717575c352886c60216be0` |
| `stage_proposal.py` | `eef25fc38124890a6cf8834d0d87d4200ec865aa1f0f6729106599ae5ff7ec8f` |
| `concept_validator.py` | `3a07f34282c0d239d99cece01d85bac4ec59bc5d914350d112c3a21c656b4a5f` |
| package Concept v4 implementation | `eeb38b2ba9f03be55f7ad60f5d745954e6221e39dc0d26eeccc57de471de79fe` |

These are source-tree identities for this acceptance run, not immutable release
identities. Any later edit requires the lock tests and this record to be
refreshed.

## Deterministic evidence

The opt-in offline Forge/Quest test
`test_fixed_view_forge_and_quest_produce_exact_reconstruction_inventory`
passed for both routes. Its two-component fixture authored only the consolidated
source and fixed instruction document, produced exactly six provider requests,
sealed ordered roles `front`, `top`, `bottom`, `exploded`, `component:board`,
and `component:pieces`, resumed the same native session at Make, and completed
the existing terminal route gates. The partial-effect test also passed: a
failure on the second request resumed from the durable ledger without repeating
the completed first request or the Invent turn.

The deterministic Quest revision route also passed. Its first v4 Concept had
one `board` component; exact Make/Playtest feedback returned the same lifecycle
to Invent, bound the prior source, fixed instructions, sealed Concept/effect,
and revision identity, then replaced the role set with `board` plus `pieces`
before invalidated downstream artifacts were rebuilt.

Contract/finalizer coverage rejects wrong-version flags, mismatched fixed keys,
unsafe component keys, empty notes, seventeen components, adaptive or
undeclared roles, path collisions, wrong role order, and changed, missing,
extra, or linked image-tree bytes. Make coverage rehashes Concept v4, requires
the exact stable-key component map, and preserves the copied-pixel prohibition.

## Commands and results

- `openspec validate fix-concept-image-set-for-cad --strict` — passed.
- Focused Concept/workflow/Make suites — 287 tests and 170 subtests passed.
- Repository suite outside the restricted process/network sandbox — 748 tests
  and 25,096 subtests passed; 34 skipped; no failures.
- Offline fixed-view Forge/Quest E2E with process supervision — one test and two
  route subtests passed in 97.56 seconds.
- Offline fixed-view partial-effect/resume E2E — passed in 2.30 seconds.
- Offline fixed-view Quest component-set revision E2E — passed in 90.34 seconds.
- `git diff --check` and Python compilation — passed.

## Claims and remaining gate

This record proves deterministic contract behavior, byte binding, role
inventory, effect reconciliation, session continuity, and preservation of the
existing software gates. It does not prove visual quality, CAD
reconstructability, dimensional accuracy, printability, tactile performance,
manufacture, delivery, or human satisfaction.

Authenticated Forge and Quest acceptance has not been run because it may
transmit private Wish data, consume paid model/provider capacity, and exercise
publication authority. Consequently `INVENT_CONCEPT_V3_ACTIVATED` remains
`False`; only explicit acceptance runs can freeze v3/v15.

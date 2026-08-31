# ADR 0032: Restore Make depth and blindly review first proof

- Status: Accepted
- Date: 2026-08-30
- Owners: Runtime, workflow, and product-run protocol maintainers
- Supersedes for new runs: ADR 0031's `deep-economics-v3` profile

## Context

Deep-v3 corrected the persistent-session profile-binding bug and shortened the
first Make boundary from 30 to 12 minutes. An identical production Quest Wish
then provided a paired comparison. Invent passed in 15m53s with 473,815 input,
397,056 cached input, 12,132 output, and 1,894 reasoning-output tokens. The
first Make turn persisted no product file and ended at its 12-minute boundary;
its terminal token event was unavailable, so no usage is guessed.

Recovery persisted the requested early-proof source about 5m43s later and
reached exact mechanism numbers and blockout images. Useful evidence therefore
arrived about 17m45s after Make began instead of roughly 34.5 minutes in the
deep-v2 run, and total bounded Make exposure fell from 60 to 42 minutes.

That was an elapsed-time improvement, not a product win. Medium-reasoning Make
recovery consumed 1,285,442 input, 1,148,928 cached input, 13,976 output, and
1,139 reasoning-output tokens—more gross input than the comparable deep-v2
high-reasoning recovery. Its images showed a generic cylindrical exposed
mechanism instead of the required smooth volumetric seed. The root session's
own inspection nevertheless called the pixels passing. No complete product,
final preflight, Playtest, Release, or publication followed before bounded
recovery stopped.

## Decision

New Codex Forge and Quest runs freeze `deep-economics-v4.md`.

- Invent and Make use high reasoning. Playtest and Release use medium.
- Make compacts at the runtime's minimum supported 16k; Invent, Playtest, and
  Release retain 24k.
- One immutable v4 profile-file hash remains the persistent session's runtime
  identity while the host selects those frozen settings per turn.
- The first Make turn retains its 12-minute proof boundary. Recovery and other
  normal turns retain 30 minutes; one CLI invocation retains the eight-turn
  cap.
- Before expanding the final part tree, one bounded independent native visual
  critic sees only the exact held/signature blockout images and records an
  unprompted object, form, control, action, and relationship read. Only then
  does it receive the Wish and sealed concept and compare every explicit
  positive and negative held-form requirement plus the anti-generic signature.
- A generic, plaque-like, board-like, box-like, container-like, or
  exposed-mechanism reading fails the early proof. Make repairs and rerenders
  once at most before expanding final parts.
- After a passing proof, Make persists the smallest complete baseline
  immediately and carries one source forward through preflight, final render,
  final blind review, integrated verification, and finalization.

The early blind report is native model evidence and is preserved in the product
tree; it is not a Python aesthetic judge or an intermediate lifecycle gate.
The later schema-v6 review remains hash-bound to the exact final renders and
passing print preflight, and every deterministic CAD, Quest Playtest, manual,
and authenticated publication gate remains unchanged.

Frozen deep-v3 runs retain their high-Invent, medium-later 24k profile. Frozen
deep-v2 runs retain their effective all-high session binding. Deep-v1 and older
runs retain their exact materialized protocol.

## Consequences

- The 12-minute boundary retains the proven elapsed-time saving.
- High Make reasoning is restored only because paired production evidence
  showed medium increased gross input while weakening visual judgment.
- The 16k Make ceiling targets repeated CAD/tool-history cost without reducing
  the context available to concept selection or downstream manual work.
- Blind review occurs before expensive complete CAD, where one silhouette
  repair is cheap, and the final authoritative review still occurs after
  print-preflight.
- A fresh paired Quest and Forge run must demonstrate a completed desirable
  product, terminal publication, elapsed time, and per-turn token telemetry.

## Verification

- Runtime tests prove v4 selects high for Invent and Make, medium afterward,
  16k for Make, 24k otherwise, 12 minutes for initial Make, and 30 minutes for
  recovery.
- Prompt tests prove only v4 receives the early blind-critic instruction; v3
  retains its exact original critical-path prompt.
- Session tests continue to prove stable whole-profile binding and fail closed
  on same-version profile drift.
- Compatibility tests retain deep-v3, deep-v2, deep-v1, Spark, and unmarked
  behavior.
- Full repository tests pass before the first v4 production run begins.

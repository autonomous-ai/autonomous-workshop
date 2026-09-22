# ADR 0069: Corrections carry byte-identical parts forward

- Status: Accepted
- Date: 2026-09-21
- Owners: CLI, Spark Make (component rounds, CAD skill), correction runs
- Relates to: ADR 0063 (component-first Make), ADR 0065 (published-toy
  correction runs), ADR 0066 (opt-in motion verification), ADR 0061 (Make-owned
  verification)

## Context

A `workshop fix` run pays the same price whatever it corrects. Measured on the
step-8 Antisol run from its own transcript, one correction spent 11,283 seconds
of wall clock: 9,561 s in Bash (85.2%), 1,572 s model (14.0%), 94 s Read
(0.8%). Inside Bash the largest items were the measure reports (3,000 s, 6
calls), the integrated verifier (2,410 s, 33), renders (1,672 s, 25), 24
component and assembly gate rounds (1,346 s, 40) and build plus export (940 s,
33). A blind review ran alongside as a background subagent for 3,852 s.

That price is independent of the edit. Steps 8 to 10 of that chain each changed
one marking family on one or two of 24 printed parts, and each rebuilt,
re-gated and re-measured all 24. The owner asked, reasonably, why a three-line
change costs six hours.

The reason the price looks unavoidable is ADR 0063. Its decision text says the
Manager runs an isolated `make_round --component` loop "for each component",
and a correction run reads that as: every component, every run, from zero.

## Decision

A `workshop fix` run carries unchanged parts forward **by default**;
`workshop fix --full` declines it. The host freezes `carry_unchanged: true`
into the read-only run-root `MAKE-OPTIONS.json` under `schema_version: 2`,
alongside ADR 0066's `check_motion` boolean and covered by the ordinary
immutable-input hash manifest; `motion_policy.carry_unchanged()` is the reader
the CAD and make-round tools call.

The policy changes exactly one thing: what a Make round may **carry forward**
from the correction's source archive. It lowers no threshold, relaxes no gate
and skips no assembly work.

It applies only to `fix`. `wish` and `start` have no source to carry anything
from, and the host refuses the option without a revision snapshot; those runs
keep writing schema 1.

The policy shipped opt-in, as `workshop fix --quick` writing `quick_fix: true`,
and became the default on 2026-09-21 once the first run had measured it. Both
field names read as the same choice, a document carrying both is refused, and
`--quick` is retained as a hidden no-op so an existing invocation does not
break.

The permission is conditional on a proof the run must compute first: build and
export **every** part and hash each against the source archive's
`make/made.json` `product_manifest`. For a part whose STEP is byte-identical:

1. its isolated component round history carries forward, and
2. its per-part measure reports carry forward.

Never carried, and recomputed every time: the hash proof itself; `refs`,
`validate` and `interfere` on the assembly; every gate on every changed part;
the assembled-object rounds; `verify_project`; the whole-set renders; and the
independent blind review. The run writes `measure/quick-fix-carry.md` naming
each carried part, the sha256 it was carried on, and what was regenerated.

## Alternatives considered

- **Scope the correction by hand** — tell the run which parts changed. Rejected:
  it makes the operator's guess load-bearing, and a shared helper edited by
  mistake would silently skip the part it broke.
- **Skip the final sweep too.** Rejected: `verify_project`, the renders and the
  blind review are the only checks that would catch an error in the
  carry-forward reasoning itself. Scoping them removes what makes the rest safe.
- **Leave it opt-in.** This is what shipped first, and it was right until the
  first run had measured the policy. Rejected once that run showed the host
  enforces the precondition by hash and that declining costs work already paid
  for: an operator who must remember a flag to avoid repeating a measurement
  is being charged for the interface rather than for the evidence. `--full`
  keeps the old behaviour for a correction that should be measured from
  nothing.

## Reconciliation with ADR 0063

ADR 0063 point 4 — a component whose STEP an assembly repair changed must pass
its isolated loop again — is not weakened; it is the mechanism the carry policy
depends on. `make_round --require-component-passes` freshly builds every part
and refuses assembly review unless each part's recorded component-pass digest
equals the bytes just built, reporting "<part> changed after its component
pass". So "byte-identical" is host-enforced by hash, not a policy the Make
agent is trusted to honour, and a changed part cannot carry anything forward
even if a run tried.

ADR 0063 point 2 — the Manager runs the isolated loop for each component — was
written for a newly materialized Spark baseline. A correction run imports a
product tree that already carries `measure/component-rounds/<role>/` with
passing histories, and `--require-component-passes` accepts those carried
passes today, without this ADR. The carry policy therefore adds no host permission.
What it changes is the default reading: an unchanged component's carried pass
is sufficient, and re-running its loop is work, not diligence. That is a
decision change on top of ADR 0063's text, which is why it is recorded here
rather than only in the skill pages.

The single claim the carry policy makes is that **a byte-identical part has
byte-identical gate results**, which is true by construction: a gate is a pure
function of the STEP it reads, and `print_context` in the carried state records
the tool and library hashes it was read with.

## Consequences

- **No ordinary run's bytes move.** A run that does not select the carry policy
  writes the exact schema-1 `MAKE-OPTIONS.json` bytes it wrote before the
  option existed, so no existing checkpoint hash changes. The carry policy declares
  `schema_version: 2`; an unknown schema, or a schema-2 document missing its
  selection, is refused rather than guessed.
- **Resume preserves the selection, unlike ADR 0066's motion boolean.** ADR
  0066 reselects `check_motion` on every operator resume, defaulting to false.
  `quick_fix` does not: it is a property of the correction's scope, chosen once
  at creation together with the source, and a half-finished run that has
  already carried parts forward must not have that permission revoked under it.
  A `--check-motion` rebind on resume rewrites the file preserving `quick_fix`.
  There is no `resume --quick`.
- **The deterministic print gates were already reused; the carry policy's saving is
  elsewhere.** `make_round` reuses a part's thickness and overhang verdicts
  whenever three conditions hold together: the STEP digest did not change, the
  prior entry is a PASS whose original tool logs still hash correctly
  (`reusable_print`), and `print_context` is identical -- the hashes of
  `check_thickness`, `check_overhang`, `meshlib.py`, `printlib.py` and the
  wrapper, plus nozzle, overhang angle, platform and the NumPy/SciPy/Python
  versions. So tool drift already invalidates a carried verdict without this
  ADR, and the carry policy inherits that guard rather than needing its own. What
  the carry policy actually removes is the per-component **isolated round** for an
  unchanged part -- its render packet and the native visual inspection of it --
  and the agent-authored per-part `measure/*.md` reports, which no host rule
  covers because they are written, not computed.

- **An exporter counter, not geometry, decides part of the carry rate.** On the
  first quick run (step 11, Jupiter's mirror, `parts/markings.py` the only
  changed source) 20 of 24 parts rebuilt byte-identical and all four board
  panels did not, although they do not import `parts/markings` at all. Each
  panel differs in exactly one line: a `NEXT_ASSEMBLY_USAGE_OCCURRENCE` label
  (`'221'` against `'1'`), the exporter's per-session occurrence count, because
  the source run wrote those files in a process that had already written 220
  shapes. The run proved this with a control -- it rebuilt the four panels from
  the unedited source archive in a scratch tree and reproduced its own hashes,
  not the published ones. STEP export is therefore deterministic given the same
  build order in the same process; the unstable input is the process-wide
  counter, which is fixable by building each part in a fresh process or
  normalising the label. Until it is fixed, a correction pays for parts it did
  not touch.
- **A component round cannot state its own provenance, so the carry note is
  load-bearing.** The round format already distinguishes a reused print verdict
  from a fresh one inside a round -- `summary.json` carries a `reused` list --
  but it records nothing about which *run* produced the round. `out` and
  `project` are rewritten to `<WORKSHOP_RUN>/...` placeholders when the archive
  is sealed, and no wish id appears anywhere in the record. Until now that did
  not matter, because every round in an archive came from the run that sealed
  it: steps 8, 9 and 10 each built their component histories from r0001 in
  their own session. The carry policy is the first case where one archive mixes
  rounds from two runs -- an unchanged part keeps the source run's r0003, a
  part that moved appends this run's r0004 -- and the two are formally
  indistinguishable, including the model prose in `visual.observation`, which
  was written by the earlier session. `measure/quick-fix-carry.md` is therefore
  the only place that provenance is written down. It is documentation, not a
  control: nothing in the host reads it, and nothing needs to, because the two
  hash guards above hold whatever the note says. A note that overclaims cannot
  produce an unsound archive -- a part that moved is refused at
  `--require-component-passes` regardless -- so the note serves readers, not
  correctness.

- **Inheritance has no depth bound, and nothing records the depth.** The
  condition that permits a carry -- the STEP did not change -- is also the
  condition under which the next correction may carry the same round again.
  A component round produced in run N can therefore reach run N+k unexamined,
  while every archive in the chain looks freshly inspected, and no record says
  how far back the judgment came from. The digest guard never breaks the chain
  because it only ever proves the bytes are the same. What bounds the risk is
  not the component loop but the whole-set evidence that the carry policy always
  regenerates: the renders, `verify_project` and the independent blind review
  run in full every time. Stamping the originating wish id into a round record
  would make the depth visible and is the prerequisite for capping it; it is
  worth doing separately.

## Compatibility and migration

No checkpoint schema migration, no Spark host rebuild, no change to any older
run. Runs created before this option read as declined, as do standalone tool
invocations outside a product run.

## Verification

`tests/make/test_quick_fix_policy.py` (13 cases): declining the carry policy
reproduces the pre-feature bytes for both motion settings; the carry policy declares
schema 2; non-boolean options are refused; absent, schema-1 and schema-2
documents read back correctly; a motion rebind on resume preserves the
selection; a corrupt selection raises rather than defaulting; standalone tools
are never in the carry policy; and the tool-side reader refuses an unknown schema or
a schema-2 document missing its key.

Measured, and smaller than predicted. The first quick run carried **717 s
(12.0 min)** of component-round work, read off the source archive's own
`make_round` logs rather than estimated -- roughly 3% of a correction measured
in hours, against the ~39% the step-8 cost profile suggested. That prediction
was a misattribution: the profile's largest item, "measure reports, 3000 s",
is project-wide analysis written about the change itself, which can never be
carried. The run's cost sits in rebuilding 220 colour bodies (266 s), the
52 MB assembly (268 s), the whole-set renders, `verify_project` and the blind
review -- none of which the carry policy scopes, by design. As the run put it: a set
whose printed parts are cheap and whose assembly is enormous is the shape of
project the carry policy helps least. The saving is real but it is not a reason to
make this the default; where a product's hours actually go has to be asked
before reaching for it.

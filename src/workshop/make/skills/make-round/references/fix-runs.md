# Fix runs: carrying unchanged parts forward

Read this once in a correction run: `workshop fix`, recorded as
`carry_unchanged: true` in the run-root `MAKE-OPTIONS.json` under
`schema_version: 2` (`motion_policy.carry_unchanged()` reads it). It is false
for every run with no source to carry from, and for every run created before
the policy existed -- those have no schema-2 document, so a refreshed tool
still reads them the way they were created. `workshop fix --full` declines it.
The policy changes only what a round may CARRY FORWARD. It lowers no
threshold, relaxes no gate and skips nothing about the assembly.

What it permits, and only after the changed-part set is established by
building EVERY part and comparing its B-rep identity against the source's
(ADR 0073 -- never STEP bytes, which an exporter can serialize differently for
an unchanged shape, and never a shape reloaded from a STEP file, which does
not hash like the one that was built):

- A part whose B-rep is identical to the source's needs no new isolated
  component round, even when its exported STEP bytes differ. The source
  archive's round history for that part is still exactly true of it, because a
  gate is a pure function of the shape it reads. Carry that history forward
  and record the B-rep hash it is carried on.
- Its per-part measure reports are carried forward the same way, unchanged.

For the source side of the comparison: read the source archive's
`make/made.json` first. If it is `schema_version: 2` and its `toolchain`
matches this run's own installed `build123d`/`cadquery-ocp` versions exactly,
use its `component_identities[path]` directly -- no rebuild. Otherwise
(schema 1, sealed before this change, or a toolchain that does not match -- a
sealed hash from a different OCCT is not comparable), get the source side by
rebuilding the source's own `part_<role>.step.py` in a scratch copy of its
`make/` tree with the same `gen --write --json` and reading its
`identitySha256` there; the source's own generator sources and shared helpers
are already inside the revision snapshot, so this needs no new input. There is
no tolerance on this comparison: two hashes either match or they do not.

You are not trusted on this, and do not need to be: `make_round
--require-component-passes` rebuilds every part and refuses assembly review
for any whose B-rep identity no longer matches its recorded pass. A part
whose shape moved cannot be carried even if you try -- and one whose exported
STEP merely serialized differently is no longer refused for it.

What the policy never touches:

- The hash proof itself. It is the whole warrant for everything above, so it
  is computed fresh, over every part, every time.
- `refs:assembly`, `validate:assembly` and `interfere:assembly`. The assembly
  changes whenever any part does, and interference is a property of the whole
  set, never of a part.
- Every gate on every CHANGED part, and the assembled-object rounds.
- `verify_project`, the whole-set renders and the independent blind review.
  The final sweep is what would catch a mistake in the carry-forward
  reasoning, so scoping it would remove the one check that makes the rest
  safe.

A Component's reviewer binding cloned from the source run binds nothing here
(issue #119): its next review in this run binds this run's reviewer.

Write a `measure/quick-fix-carry.md` naming every part carried forward, the
B-rep hash it was carried on, and what was regenerated instead. A reader must
be able to tell a carried report from a fresh one without diffing, because the
round record itself cannot say which run produced it. If the changed-part set
turns out to be most of the project, say so and regenerate everything: the
policy saves nothing there and the claim is weaker.

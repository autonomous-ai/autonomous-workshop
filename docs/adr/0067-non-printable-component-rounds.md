# ADR 0067: Review non-printable components without print gates

- Date: 2026-09-14
- Status: Accepted and deterministically tested
- Relates to: ADR 0063 (Spark component-first Make), ADR 0063 (print gates on
  source) and ADR 0060 (Make-round visual feedback)

## Context

ADR 0063 makes new Spark Make work component-first: every distinct physical
component gets its own `part_<role>.step.py` and must pass an isolated
`make_round --component` review before the combined entry is authored.

The CAD toolchain already distinguishes what is *modeled* from what is
*printed*. A purchased component — a bought latch, bearing, magnet, NFC tag,
screw — and a logical review part declare a literal module-level
`PRINTABLE = False`. `printlib` and `verify_project` both read that declaration
statically and pass only the resulting print targets to `check_mesh`,
`check_overhang` and `check_thickness`; those three gates refuse a declared
non-print target outright, exiting non-zero without measuring anything.

`make_round` did not read the declaration. It ran both print gates on every
part that built, so a component the Wish requires to be bought produced a
deterministic wall FAIL and overhang FAIL in every round, with no measurement
behind either. The isolated component review ADR 0063 mandates could not be
passed for such a component, no repair could clear it, and the run stalled at
Make rather than at a defect. A 2026-09-14 Spark run reproduced it twice with a
25 mm x 0.6 mm probe cylinder that declared `PRINTABLE = False`.

## Decision

`make_round` selects print targets exactly as `verify_project` does, from the
same static `PRINTABLE` literal: every `part_<role>.step.py` that does not
declare `False`, plus a combined entry that declares `True`.

A declared non-print target is built, rendered, visually inspected and recorded
like any other component. Its two print gates are not run and are recorded
`SKIP`, with no measurement, no printability claim, and no failure. A `SKIP` is
never reused as a passing pair and never reported as a pass; `summary.json`
names those roles under `not_printed`. A component whose round is otherwise
clean can therefore pass, and that pass counts toward
`--require-component-passes` like a printed component's.

`PRINTABLE` must be a literal `True` or `False`. Anything else exits 2 instead
of being guessed at, matching the toolchain's own reader.

This removes work that never measured anything; it weakens no gate. Print gates
on printable parts are unchanged, and the host CAD gate — `verify_project
--print-gates` at the declared nozzle, rerun by the host — already selected the
same targets, so no product becomes print-ready on less evidence than before.
The product-run instructions state the matching contract: a purchased component
is a pocket in a printed part, and declaring a part that will be printed
non-printable is a bypass, not a repair.

## Verification

- Make-round tests prove a `PRINTABLE = False` component round spends no print
  gate, records `SKIP` for both, passes on build and recorded visual evidence,
  and satisfies `--require-component-passes` alongside a printed component.
- A split model whose combined entry declares `PRINTABLE = True` is gated on
  that entry rather than on its logical parts.
- A computed `PRINTABLE` exits 2 and runs no tool.
- A parity test pins `make_round`'s reader to `printlib.declared_printable`
  across literal, annotated, absent and invalid declarations.

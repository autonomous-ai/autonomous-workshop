# ADR 0089: Guide Images explain the design and are never compared

- Status: Accepted; implemented and deterministically tested; not yet
  validated by a live run
- Date: 2026-10-14
- Issue: #122; amended by #125 (Guide Images scoped to Components,
  2026-10-16)
- Amends: ADR 0072 (what a Design Contract seals), ADR 0085 (the Contract
  Reviewer's answer), ADR 0083/0084 (schema 5 keeps cameras and Interface text)
- Relates to: ADR 0076 and ADR 0077 (who views which image), ADR 0084
  (Reference Conflicts)

## Context

A Design Contract seals only Reference Images, and every one is compared with
the model: a `geometry:<id>` image beside its Component in the Display Pose,
the `assembly` image in the assembly round. A toy designer often has a
picture that explains the design without being a likeness target. Racer
Mecha's colour-coded transformation sheet draws the car, each of the seven
moves and the robot in twelve panels: it shows the Workshop Manager how the
Components must meet so the toy transforms in exactly those steps, and shows
each Component from sides its reference does not. Today it cannot enter a
run: `--ref` refuses a file the contract does not list, and listing it as
`assembly` would put a twelve-panel sheet beside the model and in front of
every Contract Reviewer as a likeness target.

## Decision

1. **A new image kind.** A schema 5 Design Contract keeps schema 4 and adds a
   non-empty `guides[]`: `{"file": "guide-NN-<slug>.png", "shows": "<what it
   explains>", "steps": ["<each step it draws>", ...]}`, `steps` optional.
   Schema 1 to 4 contracts and frozen runs are unchanged.
2. **Sealed like a reference.** `workshop wish|fix --contract FILE --guide
   IMAGE` checks the guides against `guides[]` exactly as `--ref` checks
   `references[]` (count, names, order). They seal into `wish-references/`
   as `guide-NN-<slug>` after every `ref-NN`, bound by sha256, re-verified at
   every checkpoint, and they share the 99-image and 48 MiB budget.
3. **Never compared.** `make_round` leaves Guide Images out of every sealed
   reference list: no component round, assembly round, blind review,
   `--image-derived` coverage or Reference Camera touches them. Where one
   disagrees with the contract, the contract wins.
4. **Who reads it.** The Workshop Manager opens each before Make; every
   Component Worker is given every Guide Image and a component round's
   `summary.json` lists them under `guides`. The Component Reviewer never
   sees one: its packet does not carry them, so it cannot ask a Component to
   match a drawing that is not a likeness target.
5. **Accounted for, not judged.** The Manager writes
   `<cad-project>/guide-steps.json`: for each Guide Image, each contract step
   with the pose it was checked in or why it was skipped, and the conflicts
   it found between the guide and the contract. With `--check-motion true`
   the final verifier fails until every listed step has one entry; it
   counts, never judges. The record travels in `component-acceptance.json`,
   the finalizer copies it to `product.json`, and the host checks the same
   count again before sealing it into its Make receipt; the receipt and
   `workshop status` list it as `guides`.
6. **Amendments name the panels they make wrong.** An amendment packet lists
   the Guide Images; the fresh Contract Reviewer reads them and answers
   `guides_wrong`, the panels the change would draw wrongly. It never
   refuses the amendment (a Guide Image is never in `visible_in`): the run
   reports them, and `build-a-toy` redraws those panels with `design-a-toy`
   before the next attempt. Reference Images keep ADR 0085's visibility rule.
7. **Approved like the references.** `design-a-toy` draws a Guide Image,
   checks its step count, order and part colours against the contract's
   Transformation, and the owner approves it with the reference images.

## Consequences

- A transforming toy can carry its step sheet into the run without
  weakening any likeness comparison.
- Workers see more than one side of their Component; the reviewer still
  judges only against the Component's own reference.
- A missing step account is caught by the final verifier, the finalizer and
  the host, so a run with motion checks cannot quietly ignore a Guide Image.
- A Guide Image can go stale after an in-run amendment; the receipt names
  the panels, and the owner's redraw closes it before the next attempt.

## Amendment: a Guide Image can be scoped to the Components that read it (2026-10-16, issue #125)

Status: Accepted; implemented and deterministically tested; not yet
validated by a live run.

**Context.** Decision 4 gives every Component Worker every Guide Image. A
sheet that shows one part, its reference beside more views of it, then
reaches every worker: another worker can read that part as its own, and the
sheet has to stay small enough to share with the whole toy.

**Decision.** Decision 4 changes for new contracts:

1. **An optional `geometries`.** A `guides[]` entry may add
   `"geometries": ["<geometry id>", ...]`: a non-empty list of distinct
   strings, each the `id` of an entry of the contract's `geometries[]`.
   The Design Contract parser refuses an unknown id, a repeated id, an
   empty list and anything but a list of strings, and only schema 5 has
   guides at all. The field seals with the contract and parses back.
2. **Who reads a scoped guide.** Without `geometries`, every Component
   Worker reads the guide, as before. With it, only the Component Workers
   of the named Unique Geometries do: a Component Worker's Component is
   `part_<id>.step.py`, so its id is the geometry id. The Workshop Manager
   still opens every Guide Image, and gives each worker only the guides for
   its Component. A component round's `summary.json` lists under `guides`
   only those guides (`component_guides` in `make_round`).
3. **Unchanged.** The Component Reviewer never sees a Guide Image. A
   Contract Amendment packet still lists every sealed Guide Image, and the
   host's replay still refuses a packet that hides one (decision 6).
   `guide-steps.json`, the final verifier, the finalizer and the host's
   Make receipt still account for every guide, scoped or not (decision 5).

**Compatibility.** A contract without the field, every schema 1 to 4
contract and every frozen run behave exactly as before: every worker reads
every guide. A frozen run keeps its materialized `make_round`, guidance and
role agent text.

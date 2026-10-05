---
name: wiki
description: Searchable engineering knowledge base the agent consults before a design decision and adds to when it learns something - mechanisms (shafts, bearings, joints and fits with a variant index, gears, linkages, scissor and pantograph linkages, cams, drives, cables and tendons, hinges and hinge types, rod ends and clevises, ball-and-socket and posable-figure joints, shaft-hub connections, couplings and CV joints, rolling-contact and flexure joints, swivels and turntables, slides and telescoping tubes, latches and bayonets, kinematic mounts, arms and grippers, counterweights, fluid fittings, noise, automata, verification, failure classes), build123d/OCC kernel pitfalls, design for printing (walls, overhangs, part count, fits, print-in-place, interlocking joinery, resin, print time, finishing), reading reference images (scale, perspective, likeness), electronics (LEDs, batteries, motors, servos, drivers, boards, enclosures, power paths, lighting), materials (filament properties, anisotropy, creep, heat, fatigue, thermal expansion), fasteners (clearance holes, inserts, screws into plastic, snap-fits, push-in clips and pins, wall mounting, straps and buckles), structures (beam and plate stiffness, ribs, buckling, lightweighting), standards (ISO 286 fits, ISO 2768, GD&T, tolerance stack-up, STEP), product design (ergonomics, toy safety, DFA, sealing and IP ratings, stability, moulds and casting) and reverse engineering STEP/STL. Use whenever a part must turn, slide, swing, latch, carry load or be driven; whenever choosing a mechanism, sizing a shaft or joint, or writing a feasibility assert; and after a gate failure or research result teaches a rule worth keeping.
---

# Design wiki

A knowledge base, not a workflow and not a gate. It holds the engineering the
CAD tooling does not know: *which* joint to draw, *what* makes a shaft stiff
enough, *which numbers* make a linkage turn, and *why* a correct-looking
printed mechanism still does not run. It writes no geometry and changes no
other skill.

```bash
W="$(workshop skills path)/wiki/scripts/wiki"   # stdlib only: python3 or .venv/bin/python
$W search <words...>                 # ranked sections, path:line, snippet
$W search spindle --pages            # one line per page; synonyms expand
$W show <slug>[#section]             # print a page or one section
$W list [--tag gear]
$W new <topic>/<slug> --title "..."  # page from the template
$W lint                              # must pass before a wiki edit is done
```

**Inside a Workshop product run the wiki is consult-only.** Its bytes are
materialized read-only and bound into the run's input manifest like every other
skill, so `new`, a page edit and a `synonyms.txt` edit are all refused there —
and a run that tampered with them would fail its resume. Search, show and list
freely; step 5 below does not apply in a run. Report a rule the wiki lacked,
with its evidence, in the final response; the host's Make lessons loop carries
gate failures into the design vault, and a Workshop builder writes durable
rules back into this tree (or upstream). Paths written `skills/<name>/...` in
these pages name a sibling Make skill: read them under
`"$(workshop skills path)/<name>/"`. Upstream's `step-to-source` and
`stl-to-step` are not Workshop skills: a `reverse-engineering/` page that
names them describes tooling a run does not have, and its rules stand without
it. Machines and fixtures the pages cite by name live in the upstream
`autonomous-product-to-cad` repository, not in a product run; the numbers
quoted are the whole example.

## The loop: search, think, design, write back

1. **Search before deciding.** Whenever a part turns, slides, swings, latches,
   carries load or is driven, search the wiki for the joint, the element and
   the failure first — `search shaft deflection`, `search keyed phase`,
   `search worm back-drive`. Start a new machine at
   `show mechanism-design`, which holds the design sequence and the
   archetype chooser.
2. **Read the hits, not the whole wiki.** Open the two or three sections the
   search ranks highest with `show slug#section` and follow their `[[links]]`
   only where the design needs them.
3. **Think with the page's numbers.** Turn each rule you use into the
   project's parameter block and an `assert` (every page gives its assert).
   A decision you cannot write as a number or an assert is not designed yet.
   Record in the spec which page each archetype, fit and limit came from.
4. **Design the system in this order** — archetype → shaft and joint layout →
   parameters → feasibility asserts → kinematics → motion checks — and do
   not start geometry until the asserts pass.
5. **Write back what you learned.** Creating or editing any item ends here:
   when research, a calculation, a measurement, a gate failure, a kernel
   workaround or a user correction produces a rule the wiki did not have, add
   it before the task ends (below). When a search missed a page that exists, add
   the missing term to that page's `aliases` or to `synonyms.txt`.

If the wiki has nothing, research it (`$design-reference`, standards,
textbooks, vendor data), design from that, and write the page — the next
search should not have to research it again.

## What belongs in the wiki

- **Invariants with their mechanism**: a rule and the reason it holds
  ("locate a shaft at one support only: two locations fight print error").
- **Formulas written as asserts**, with symbols defined.
- **Reproducible properties of the toolchain** ("`mesh_to(backlash=0.0)` moves
  centres inward on a thinned pair").
- **Failure classes**: symptom, which gates passed it, the rule that prevents
  it.

Not in the wiki: one project's results — its name, its measured score, a path
into `output/`, its part count. The skills are vendored into other
repositories, where those numbers read as the tool's own. Keep the rule, drop
the run; lint rejects `output/...` paths and names of projects under
`output/`. Illustrative worked numbers ("m1, 4 starts, r1 = 4 → a = 10.93")
are fine: they demonstrate a formula, not a result.

Not in the wiki either: repository policy (that is `CLAUDE.md`), gate usage
(that is the owning skill's reference), or a copy of a standard's tables that
`stdpart` or `$step-parts` already serve.

## Writing a page

- One topic per page, pages grouped by topic directory under `pages/`:
  `mechanisms/`, `modeling/` (build123d and the OCC kernel), `printing/`,
  `structures/` (beams, plates, ribs, stiffness, buckling),
  `materials/`, `fasteners/`, `electronics/`, `standards/` (ISO fits, general
  tolerances, GD&T, STEP, drawings), `image-reading/`, `product-design/`
  (ergonomics, toy safety, DFA, colour), `reverse-engineering/`. Add a
  directory when its first page is written. Slugs are file stems,
  unique across topics, so `[[slug]]` never depends on the directory.
- Extend an existing page before creating a new one; `new` refuses a slug
  that exists. Split a page when it passes ~250 lines so a search hit lands on
  one idea.
- Front matter, all checked by lint:

```yaml
---
title: Shafts and bearings
tags: [shaft, bearing, deflection]          # English, singular
aliases: [spindle, journal, ball bearing]  # other names people search by
sources:                                    # at least one; each is one of
  - Shigley's Mechanical Engineering Design, ch. 7      # book / standard, with chapter
  - https://...                                          # a URL you read
  - skills/cad/scripts/cadfits.py                        # a toolchain file the rule describes
  - "experience: <the failure class that taught it>"    # a rule learned from a gate
related: [joints, gears]                    # slugs; must exist
updated: 2026-09-23
---
```

- `##` sections are what search returns, so give each one a heading that
  names its idea; link sections with `[[slug#section-anchor]]` (lower-case,
  accents dropped, spaces to `-`, punctuation removed).
- A number from outside the repository carries its source in `sources`; a
  number you are unsure of is written as a range or not at all.

## Finishing a wiki edit

```bash
$W lint           # 0 errors
$W --self-check   # after any change to scripts/wiki
```

A wiki edit is a skill edit: commit it with the change that motivated it.

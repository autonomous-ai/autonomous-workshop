---
title: Printed threads, bosses and fastening
tags: [thread, boss, rib, gusset, fastener, insert, tap, screw, fillet, draft]
aliases: [printed threads, heat-set inserts, threaded inserts, tapping printed holes, screw bosses, embedded nuts, captive nut, acme thread, dog point]
sources:
  - https://www.stratasys.com/siteassets/sdm/resources/design-guidelines/fdm/fdm_design_guidelines_2017-1.pdf
  - https://www.hydraresearch3d.com/design-rules
related: [fdm-hole-accuracy, fdm-bridging-and-sacrificial-layers, seating-bought-parts, fdm-design-rule-tables, heat-set-inserts, screws-into-plastic, printed-threads, nut-traps-and-captive-nuts, ribs-and-stiffening]
updated: 2026-09-23
---

# Printed threads, bosses and fastening

Plastic threads are the weakest way to hold a screw. Decide the fastening
method before modelling the boss.

## Fastening, strongest first

Stratasys Direct: lock nuts, embedded nuts and metal inserts are all stronger
than threads formed in the FDM plastic. Use a cap screw or flanged cap
screw: "the flat surface eliminates multidirectional stresses from cracking
the part". Use washers to spread the load over the largest area.

| method | use when |
|---|---|
| metal insert (heat-set or pressed) | repeated assembly, real torque |
| embedded / captive nut | a nut trap that closes over the nut (see [[fdm-bridging-and-sacrificial-layers#floating-holes-sacrificial-bridge]] for the roof) |
| tapped hole | occasional assembly: print a pilot and tap, or use a thread-forming screw |
| modelled thread | coarse, large threads only (below) |

Nut traps, insert bores and screw clearance holes are standard elements.
Take them from `stdpart` and the fastener's own geometry, never typed
([[seating-bought-parts]]).

## Modelled threads

- None below **Ø1.6 mm** holes or posts (Stratasys Direct).
- Hydra Research models threads only above **M5 / UNC #10**. Below that,
  post-process: tap, self-tap, or insert.
- Round the thread root; sharp roots concentrate stress. An **ACME profile
  with rounded roots and crests** works well in FDM (Stratasys Direct).
- Add a **dog point of at least 0.8 mm** (1/32 in) so the thread starts
  easily.
- A vertical thread axis prints the thread profile layer by layer. A
  horizontal axis turns the thread flanks into overhangs and loses the profile
  ([[fdm-hole-accuracy]]).

## Bosses, ribs and fillets

From Stratasys Direct (industrial FDM, but the geometry rules carry over):

- FDM parts can often stay solid instead of being hollowed around bosses and
  ribs, which saves support ([[wall-thickness-and-hollowing#when-not-to-hollow]]).
- A boss can be the part's wall thickness, or up to 0.5 mm less. There is no
  moulding reason to thin it.
- Support bosses with **gussets or ribs**; it raises the load the boss
  takes.
- Fillets are optional but reduce stress concentration. For constant wall
  thickness, **outer radius = inner radius + wall thickness**.
- Draft is unnecessary.
- Living hinges in FDM materials survive only a small number of cycles; use
  a pinned hinge for anything cycled ([[joints#revolute-joints]]).

Rib proportions, gussets and the fillet-to-wall rule: [[ribs-and-stiffening]].

## Checks

```python
assert THREAD_D >= 5.0 or THREAD_METHOD in ("tap", "insert", "self-tap"), "Hydra: no modelled threads below M5"
assert FILLET_OUTER == FILLET_INNER + WALL, "constant wall around a bend"
```

Fasteners in depth: [[heat-set-inserts]], [[screws-into-plastic]], [[printed-threads]], [[nut-traps-and-captive-nuts]], [[metric-screw-clearance-holes]].

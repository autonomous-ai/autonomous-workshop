---
name: electromechanical-integration
description: Research and specify power, control, wiring, lighting, removable lamp sockets, physical fit verification, and CAD integration for functional electrical loads such as motors, servos, solenoids, LEDs, lamps, beacons, light strips, and illuminated controls. Use when a product must run, spin, move, emit light, or carry its own power hardware; do not use for an inert decorative lens or for PCB design alone.
---

# Electromechanical integration

A mounted electrical part is not a powered product. Trace every functional load
from its source and back, select compatible hardware from authoritative
evidence, and reserve real CAD space for every carried component and wire route.

## Boundary

The design knowledge this workflow applies lives in the wiki. Search it
(`python "$(workshop skills path)/wiki/scripts/wiki" search <words>`) before selecting:
`electrical-component-selection` (contract, evidence, hard gates),
`power-path-design` (boundary, one path per branch, wires as solids),
`lighting-design` and `removable-lamp-interfaces`; a `skills/wiki/pages/...`
path in this skill's references is one of those pages, under
`"$(workshop skills path)/wiki/"`. The rules this skill enforces from them:

- GitHub open-hardware projects supply integration patterns only. Ratings and
  dimensions come from manufacturer datasheets, product pages or standards.
- `$step-parts` comes first for bought geometry, and `$cad` derives and
  verifies seats from the component STEP.
- Fit the powered system inside the approved product form; never redesign the
  exterior around an analogy.
- A visible coloured lens proves neither a functional light nor an MPN.
  Confirm the function, and preserve uncertainty when only the image is
  evidence.

## Two-phase workflow

This skill is invoked before CAD layout is fixed, but its final gates consume
CAD artifacts. Keep those moments explicit:

- **Phase A — research/spec, before geometry:** complete steps 1–4, choose the
  physical integration strategy in step 5, and write the evidence and decisions
  into build-spec sections 6c, 6e, 6f and 8a. Mount labels, project-local STEP
  files and motion conditions may only be planned at this point. Do not claim
  that `check_power`, `check_mount` or `check_motion` ran. Phase A owns the
  electrical, actuator and lighting selection: start with a measurable contract,
  research and compare, then write the selected topology, exact devices and
  rejected alternatives into build-spec section 6g. Do not arrive with an
  agent-guessed topology or MPN already locked.
- **Phase B — powered CAD handoff:** after `$cad` has materialized the selected
  component STEP/envelope files, assembly labels, seats, routes and motion
  conditions, write the three manifests and run their gates. A pre-CAD research
  packet is not a substitute for this phase.

## Workflow

1. **Define the product boundary.** State whether power is onboard or external
   and inventory every functional electrical load. Name the source, protection,
   switching/control, connectors, conductors and return path crossing that
   boundary. An external supply still needs a modeled inlet or lead.
2. **Classify and source each load.** When selecting or replacing hardware,
   first read
   [references/component-selection.md](references/component-selection.md) and
   write a measurable selection contract before searching. Reject candidates
   on hard functional, electrical, physical and evidence gates before ranking
   the survivors; a high preference score cannot compensate for a failed gate.
   For an actuator, record accepted voltage, running current, stall/start
   current and control method. For a light, also read
   [references/lighting-discovery.md](references/lighting-discovery.md), then
   inventory its function, position, colour, behavior, optical direction,
   emitter/module, driver and visible optic. If the lamp is removable, select
   its exact mating socket and contacts in the same pass. Do not identify an
   MPN or mating geometry from appearance alone. Only hardware explicitly
   required by the user begins as a fixed candidate, and it still has to pass
   the same ratings, geometry, interface and evidence gates before selection.
3. **Research and compare automatically.** Do not wait for a separate request
   to search. Search GitHub for analogous powered products and search
   purchasable parts by exact MPN and form. Start component geometry at
   `step.parts`; on a confirmed miss continue through the manufacturer and the
   public CAD services routed by the lighting reference. Build an
   evidence-backed candidate comparison rather than accepting the first catalog
   hit. If only one candidate remains, record why the alternatives failed or
   were unavailable. Review no more than five strong GitHub candidates. Prefer
   repositories with source CAD or KiCad, BOM, schematic or wiring, assembly
   instructions and an explicit license. Record used results, meaningful
   rejections and misses. A login wall or network failure is `unavailable`, not
   a catalog miss.
4. **Specify one complete path per independently rated branch**, from source
   through protection, control, interconnects and conductors to exactly one
   load and back, contained in voltage and sized for continuous and peak
   current (`wiki show power-path-design#one-complete-path-per-independently-rated-branch`).
5. **Specify the physical handoff without polluting the product render.**
   Holders, hatches, channels, clips, strain relief, visible lenses, bezels and
   diffusers are product geometry. A bought battery, hidden controller or
   flexible wire loom may instead use
   `cad.mode: validation_envelope`: keep each reference STEP out of the combined
   assembly/render, but give it a `measure/mounts.json` declaration so
   `check_mount` places the envelope into the real assembly and measures clashes
   against the named parts. A wire envelope is a solid, not a centerline
   (`wiki show power-path-design#wires-are-solids`). Use catalog STEP where
   available and a sourced, documented envelope when it is not. For a
   removable lamp, prefer a purchased socket; a justified printed receiver
   still uses bought contacts, derives its mate through `cadfits`, declares the
   five-phase sequence in `measure/motion.json`, and plans a real-hardware fit
   coupon before any physical-fit claim (`wiki show removable-lamp-interfaces`).
6. **Materialize and check schema 3 in the CAD phase.** Once the selected
   project-local STEP/envelope files, mount ids and motion condition ids exist,
   follow [references/power-manifest.md](references/power-manifest.md), save the
   declaration as `<project>/measure/power.json`, then run:

   ```bash
   POWER_SKILL_ROOT="$(workshop skills path)/electromechanical-integration"
   python "$POWER_SKILL_ROOT/scripts/check_power" \
       <project-dir>
   ```

   For a CAD project's integrated final workflow, also pass `--powered` to
   `"$CAD_SKILL_ROOT/scripts/verify_project"`; it refuses to start without
   the manifest.

   The gate checks declared evidence, GitHub and component-search provenance,
   voltage containment, continuous/peak current capacity, source-to-return
   paths, protection/control decisions, routed strain relief, service access,
   carried mount ids, CAD representation policy, and the minimum
   function/colour/behavior/installation ledger for lighting loads. For a
   removable lamp it also checks exact lamp/socket declarations, mating
   geometry fields, the five motion-manifest links and their clear/blocked
   semantics, and the fit-coupon record.
   It does not certify a circuit, battery pack, thermal design, EMI behavior,
   optical compliance or physical prototype. `check_mount` owns the actual
   clash calculation, `check_motion` owns rigid-body insertion/retention, and a
   passed coupon with exact hardware owns the physical-fit claim.

## Handoff

In Phase A, report the selection contract, candidate comparison, selected MPN
and nearest rejected alternative; then report the selected GitHub analogy and
exact idea borrowed, every public component-search result, authoritative
evidence, chosen paths, planned component files/mount ids/routes and every
removable-interface contract. Mark artifact-dependent checks as pending. In
Phase B, report every result used, rejected, missed or unavailable,
authoritative component evidence, the source range and load demand, each
complete path, modeled mounts/routes, each removable light's exact receiver,
mating-motion and coupon status, and the actual `check_power`, `check_mount` and
`check_motion` results. Treat a missing rating,
unresolved protection decision, absent carried mount, unmodeled wire route,
unidentified visible optic, unresolved removable mate or unrecorded catalog
search as incomplete powered-product work. Never report “physically fits” from
CAD alone; a `planned` coupon is an explicit unresolved verification item.

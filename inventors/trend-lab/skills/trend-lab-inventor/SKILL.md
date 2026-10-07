---
name: trend-lab-inventor
description: Build the exact sealed Design Contract that brainstorm-trend already judged and won, adding no independent creative judgment; use only when Trend Lab is pinned by --inventor, never when an open Wish is being matched or invented.
---

# Trend Lab Inventor

Use the exact Inventor identity and Taste embedded in the developer
instructions of `.codex/agents/trend-lab.toml` as the constitution. Do not
rediscover or substitute identity from another file. Read the current
`STAGE.json`, accept only a bounded task from the root Workshop Manager, and
return precise evidence and artifacts.

You are Trend Lab's native specialist subagent, not a lifecycle owner.
Author only requested run-local analysis or artifacts, preserve complete
executable evidence, and return them to the Manager. Do not invoke the stage
finalizer, advance a gate, or perform an external effect.

## Method

Trend Lab is only ever run pinned to a run whose Wish already seals a
Design Contract written by `brainstorm-trend` and approved by a person
(ADR 0053, ADR 0072). Every decision that would normally be this Inventor's
taste — Trend Hook, Signature Motion, mechanism, geometry, envelope, wall
thickness, per-component form, dimensions, placement, and interfaces — was
already made and sealed before this skill runs. Treat the contract's fields as settled facts, never as a
starting point to restyle:

- Read `envelope_mm`, every `geometries[]` entry, and every `requirements[]`
  entry from the sealed contract before doing any other work.
- Where the contract is silent on a genuinely necessary detail (a fastening
  method, an internal rib, a draft angle), choose the option that most
  directly serves the contract's stated geometry and requirements, favoring
  the plainest structural solution over a novel one.
- Never introduce a theme element, mechanism, or visual idea that the
  contract's requirements do not already name, and never add a name, logo,
  character, or trade dress belonging to the Trend's owners.

## The FDM print floor

Apply this to every geometry regardless of what the contract does or does not
say: opaque (no intentionally translucent or see-through shells), no wall or
feature thinner than 3 mm, and no overhang steep enough to need support
material on a consumer FDM printer. Where a contract dimension would violate
the floor, flag the conflict to the Manager rather than silently shrinking a
wall below 3 mm or steepening an overhang to fit it.

## Stage contributions

- **Invent:** Transcribe the sealed contract's envelope, wall thickness, and
  every component's form, dimensions, placement, and interfaces as the
  design's facts. Resolve only the narrow structural gaps the contract leaves
  open, using the plainest option and the FDM print floor above. Do not
  explore alternative Trends, mechanisms, or forms; there is nothing left to
  invent here, only to carry forward faithfully.
- **Make:** Use the shared `cad`, `image-to-cad`, and `step-parts` Workshop
  skills to build exactly the sealed geometry. Check every wall and feature
  against the 3 mm floor and every surface against the no-steep-overhang rule
  before returning the design to the Manager.
- **Playtest:** Exercise the exact Made revision against the contract's
  requirements only, including its Signature Motion. Report deterministic geometric facts and physical
  observations; do not add or relax a requirement the contract did not state.
- **Release:** Check that the manual and product facts describe only what the
  contract and the Made geometry actually show, with no claim of publication,
  physical production, or customer enjoyment beyond the corresponding
  evidence.

Treat shared Workshop skills and deterministic checks as authoritative for
their domains. Trend Lab contributes contract fidelity and the FDM print
floor; it does not invent toys or Trends, duplicate shared tooling, or
override host evidence.

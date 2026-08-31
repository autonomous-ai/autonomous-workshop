# ADR 0034: Bind proof to executable CAD entrypoints

- Status: Accepted
- Date: 2026-08-31
- Owners: Runtime, workflow, product-run protocol, and CAD-skill maintainers
- Supersedes for new runs: ADR 0033's `deep-economics-v5` profile

## Context

Deep-v5 introduced the right phase boundary but supplied the wrong executable
contract. The identical production Three-Sky Seed Quest preserved the evidence.

Invent wrote its source before the 20-minute boundary and its decisive medium
recovery passed the host gate in 1m40s, reducing Invent from v4's 32m23s to
21m40s. Make's first eight-minute proof turn still wrote nothing. Recovery then
wrote a reusable source after about one minute—where v4 had written no Make
file after 42 minutes—but failed to generate geometry.

Tool outputs identify two exact causes:

1. The v5 host prompt invoked `.agents/skills/cad/scripts/gen` directly. That
   path is a Python package directory, so the shell returned permission denied.
2. Recovery improvised `python -m gen`, but its source exposed a top-level
   `result` rather than the required module-scope `gen_step()`. The CAD loader
   rejected it as an unsupported source. The remaining time was spent reading
   tool internals and retrying the same invalid source.

The run stopped safely after two bounded Make turns. It remains checkpointed;
no Playtest, Release, Factory publication, or GitHub toy was claimed.

Local native-session diagnostics—not host telemetry—reported:

| Stage / turn | Input | Cached input | Output | Reasoning output | Elapsed |
|---|---:|---:|---:|---:|---:|
| Invent initial | 618,515 | 519,424 | 10,546 | 606 | 20m00s |
| Invent recovery | 117,521 | 76,544 | 1,181 | 142 | 1m40s |
| Make proof | 193,995 | 156,672 | 2,333 | 578 | 8m00s |
| Make proof recovery | 312,328 | 261,888 | 5,178 | 578 | 8m00s |

Compared with v4's failed 2,142,864 input and 25,925 output tokens over roughly
75 minutes, v5 failed after 1,242,359 input and 19,238 output tokens in about
38 minutes and left a source. That is lower failed-run spend, not a completed
product cost.

## Decision

New Codex Forge and Quest runs freeze `deep-economics-v6.md`.

- v6 retains v5's 20-minute high Invent, 10-minute medium Invent recovery,
  eight-minute medium Make proof phase, 30-minute high final Make, medium later
  stages, 24k compaction, proof marker, and eight-turn command cap.
- The host supplies only executable CAD command shapes. Every CAD package
  directory is invoked through the exact `"$WORKSHOP_PYTHON"` recorded in the
  product-run environment.
- The proof source must define exactly one module-scope `gen_step()` returning
  the build123d shape before generation begins.
- The exact critical path is interpreter-prefixed `gen <source.step.py>
  --write`, `export <source.step> --stl`, and `render_product <source.stl>` with
  explicit held and signature outputs. No `python -m`, execute-bit probing,
  package enumeration, or interface rediscovery is needed.
- All marker, stage, CAD, visual, Playtest, manual, publication, and GitHub
  authorities remain exactly as in v5. The correction changes execution
  fidelity, not gate strength or lifecycle topology.

## Alternatives considered

- **Make the package directory executable.** Rejected: a directory is not a
  portable CLI entrypoint; the supported interface is the active Python
  interpreter plus the package path.
- **Teach recovery to use `python -m gen`.** Rejected: module discovery depends
  on an improvised `PYTHONPATH` and does not address the missing `gen_step()`
  contract.
- **Let Codex inspect help and source until it adapts.** Rejected by production
  evidence: discovery consumed most of the bounded recovery without generating
  one STEP file.
- **Resume the v5 run under changed semantics.** Rejected for the controlled
  benchmark. The failed v5 run remains preserved; a fresh v6 Wish provides
  unambiguous evidence.

## Consequences

- The first proof command is now directly executable in a private run path,
  including macOS paths containing spaces.
- Source-shape incompatibility is prevented in the prompt before expensive CAD
  startup rather than diagnosed from a misleading downstream path error.
- v6 adds no new lifecycle state, retry loop, judge, or gate.
- Frozen v5 and older runs retain their exact capability paths and settings.
- Deep-route economics remain unproven until a v6 Quest and Forge complete,
  publish, and preserve desirable products.

## Compatibility and migration

`deep-economics-v5.md` remains recognized with its exact staged reasoning,
timeouts, context, and marker semantics. New runs bind the v6 file hash. V4,
v3, v2, v1, Spark, and unmarked historical profiles remain unchanged. Product
run roots continue to carry their own materialized instructions.

## Verification

- Profile tests prove v6 settings and v5 compatibility independently.
- Prompt tests require `"$WORKSHOP_PYTHON"` on all three proof commands and the
  exact one-`gen_step()` source contract only for v6.
- A real acceptance test runs interpreter-prefixed `gen`, `export`, and
  `render_product` from a workspace path containing spaces, then verifies STEP,
  STL, held PNG, and signature PNG outputs.
- Full deterministic repository tests pass before the v6 production A/B.
- A fresh untouched Quest must still pass every host gate and authenticated
  publication before the economics result counts as a product.

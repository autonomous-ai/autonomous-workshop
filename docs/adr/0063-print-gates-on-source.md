# ADR 0063: print gates return, fed from source

**Status:** accepted (2026-09-10). Supersedes the gate half of ADR 0062 and
restores the tier split ADR 0062 collapsed. ADR 0062's export half stands:
STEP is still the only geometry format Workshop writes, seals or ships.

## Context

ADR 0062 adopted upstream's `cad/drop-assembly-glb-export` removal in full. It
deleted the mesh exporter and, with it, the `check_mesh`, `check_overhang` and
`check_thickness` gates, because all three took an STL positional argument and
had no subject once nothing wrote one. The consequence was stated plainly:
nothing in the toolchain measured a wall, a mesh or an overhang, so **no stage
could call a product printable**, and the CAD gate collapsed to the single
`digitally-verified-not-print-ready` tier.

Upstream then reversed that coupling in `cad/restore-print-gates-on-source`
(`1cd2d20`, merged as `d434b36`, with the ordering follow-up `673a9fa`). Its
argument is that the coupling was an implementation detail rather than a real
dependency: a mesh gate needs a *mesh*, not an *artifact*, and OCP will
tessellate the B-rep on demand. New `scripts/printlib.py` owns the
source-to-mesh step — printable-entry discovery, building an entry with its
project on `sys.path`, and tessellation at 0.02 mm deviation, measured within
0.03% of exact volume, watertight and correctly wound on a bored solid. The
three gates keep their analysis untouched and change only their front end: each
now takes one printable `*.step.py` entry. `verify_project` regains the sweep
across parts behind `--print-gates`, with `--nozzle`, `--overhang-angle` and
`--skip-thickness`, collecting failures across every part rather than stopping
at the first. `repair_mesh` writes nothing: it repairs in memory to prove which
defect class you have and what the fix costs, then names the source fix.

So printability is measurable again without a mesh deliverable. Upstream's
policy: print-ready is claimable, but only behind a passing `--print-gates` run
at the nozzle the print will use; `PRINTABLE = True` on its own is not a claim,
and `--skip-thickness` forfeits it.

Workshop's terminal artifact is a physical toy that gets printed. ADR 0062 was
a capability loss Workshop absorbed because the alternative was forking the mesh
half permanently; it was never the preferred end state.

## Decision

Adopt the restoration in full. Printability is verifiable again, and the tier
split returns — but a print-ready claim now costs a print-gated verifier run
that the host reruns itself.

## Consequences

- **Two tiers, chosen by two agreeing hash-bound declarations.** A Made artifact
  seals either root product status `full-with-thickness` with
  `final_pipeline.print_ready_claim: true`, or
  `digitally-verified-not-print-ready` with `false`. A half-declared claim is a
  refusal, not a downgrade. The host reruns `verify_project` in the tier the
  pair names, so a claim the sealed project cannot reproduce fails the gate.
- **The full tier pays for all three gates.** Its command is
  `--fresh --strict-fit --print-gates --nozzle 0.4 --overhang-angle 45`, and it
  never carries `--skip-thickness`: skipping the wall gate forfeits the claim
  upstream, so the tier that carries the claim cannot use it. Both thresholds
  are in the command, and therefore in the receipt, because a wall that passes
  at 0.4 mm can fail at 0.6 mm and a face that passes at 45 deg can fail at 60 —
  a claim that does not name what it was measured against is not a claim.
  Naming the angle also keeps the receipt off a `verify_project` default that
  upstream owns and can move without Workshop noticing; passing it changes no
  report byte, since the flag parses to the same `45.0` the default produced.
- **Make, Playtest and Release require print-ready evidence exactly where they
  did before ADR 0062.** Make requires it when it hands straight to Release,
  Playtest when its verdict passes, Release always. Spark is unaffected: ADR
  0061 gives it Make's own verification and no host rebuild.
- **The legacy full-tier replay path stays retired.** It would rerun a
  `final-fresh-exports-strict-fit` verifier, and `--exports` is still gone. The
  restored tier is a different command, so a pre-tier receipt cannot be replayed
  into it; `legacy_full_tier_compatibility` remains permanently false and a
  historical receipt without a structured claim is refused rather than guessed
  at.
- **Per-part gate reports are sealed evidence, not volatile output.** Both
  `measure/overhang-<role>.md` and `measure/thickness-<role>.md` embed the
  argument vector they were run with, so the host compares them exactly apart
  from the two path arguments' directory prefix; every measurement, option,
  check, region and line of prose stays byte-exact, an entry cannot be
  re-pointed at another part, and an unknown report format fails closed. This is
  stricter than the pre-ADR-0062 arrangement, which allowlisted the thickness
  reports as fully volatile and checked only their mode.
- **`make-round` gates every part that builds** with `check_thickness` and
  `check_overhang` on the entry, and reports wall and overhang verdicts beside
  the build verdict. `built` and `printable at this nozzle` stay separate
  verdicts. A part that did not build is a gate failure, not a skip: there is no
  solid to measure. An unchanged part reuses its previous PASS only when both
  gates passed, the tool logs still hash to what was recorded, and the nozzle,
  angle, gate bytes and interpreter are identical.
- **The signature review binds the evidence behind its claim.** Schema 7 -> 8
  adds `print_gate_sha256s`, mapping each cited `measure/<gate>-<role>.md`
  report to its exact sha256. An empty map is the honest no-claim case; a
  non-empty one must cover both gates, hash correctly, and cite only passing
  reports. This binds the *review* to the measured state; the host's tier rerun
  remains the gate.
- **New runs freeze `deep-economics-v15`**, which restores the targeted repair
  route v13 had and v14 dropped, now reading the print-gate reports rather than
  a print preflight. Frozen runs are untouched: skills materialize once at run
  creation, so every earlier profile keeps its bytes and its behaviour.

## What is not restored

The mesh exporter, `verify_project --exports`, cadgen's STL and 3MF writers,
`make/cad/mesh.py`, the Workshop-local `--print-preflight` mode and its
`measure/print-preflight.md` record, `state-*.stl` motion evidence, and sealed
`parts/<name>.stl` / `assembled.stl`. Sealed products still carry
`parts/<name>.step`, the Factory handoff still ships exchange solids, and a
manifest holding `.stl`, `.3mf` or `.glb` is still rejected. Upstream also does
not restore the old source-vs-artifact staleness check, and neither does
Workshop: with no artifact there is nothing to go stale.

## Amendment (2026-10-05, issue #101)

Inside a `make_round` round the gates still measure the B-rep built from the
part's source, but they no longer build it themselves. Beside `gen --write`,
the round runs `cad/scripts/brepbundle.py build` once per part: it builds the
source in its own process exactly as a gate does (`printlib.build_entry`)
and keeps that shape as a native B-rep bundle (`BinTools`: every double,
tolerance and mesh as built, with every node's label, colour and children
and the print-details feature tags). `check_thickness`, `check_overhang`,
every `check_envelope` and both renders then read it, at the same time. The
bundle is used only when its build has the B-rep identity `gen` reported
(ADR 0073); otherwise every check builds from source as before. The
exported STEP is never what a gate reads, and STEP was not used for the
bundle: it keeps neither OCCT's per-edge and per-vertex tolerances nor the
build123d tree a render draws. `gen`'s own shape was not kept either: its
loader leaves a different mesh on the same B-rep.

`BinTools` keeps every double it writes, but reading a direction normalizes
it again, so a line or an axis can come back one unit in the last place off
(Broken God's spine-housing: 240 of 4472 edges and 1 of 786 faces moved, by
at most 3e-14 mm; topology, vertices, types and orientations unchanged). The
read shape's identity can then differ from the build's, so the bundle
records both: the build's, which stays the round's identity for every policy
decision, and the one every read of its bytes returns. It is written only
when every node reads back with the same topology, types, orientations,
labels and colours, its sampled geometry within 1e-9 mm, and two reads
agree. Each check recomputes the identity it read, must match the bundle's,
and is recorded in the round's `summary.json` (`brep`); a bundle that reads
back as anything else fails the check rather than falling back. Every check
of a round therefore reads one and the same B-rep, where before each read
its own rebuild.

What a check measures from a mesh can still notice the drift. Measured on
Broken God, the spine-housing round's reports and images were byte-identical
to a rebuild's; the wing's thickness gate drew 277560 samples where a
rebuild drew 277725, and 1-8 render pixels per view moved by 1-2 of 255,
with every verdict, thinnest wall and region unchanged. A verdict at the
very edge of a threshold could therefore differ from a fresh build's.
Outside a round -- `verify_project --print-gates` and the host's print-ready
rerun -- nothing sets the bundle, so every gate builds from source exactly as
this ADR decided, and that fresh build remains the print-ready authority.

# Mixed-material Spark CLI pilot record

The operator requested six original capability pilots, all launched through
the ordinary CLI with Spark, Codex Astra, ultra reasoning, and a **100,000,000
token total allowance per product**, including native children and resumes.
This is a limit, not a target to spend. No Daydream, Forge or Quest is used.

The user subsequently requested **500,000,000 total tokens and medium effort
for each existing product**, retaining Astra. The initial commands below are
historical; the explicit settings changes and continuation outcomes are recorded
at the end of this document.

Source branch: `make/mixed-material-products`.
Isolated checkout: `/private/tmp/autonomous-workshop-mixed-material-products`.
The source CLI uses the existing dependency environment without installing over
the user's other checkout. Run workspaces stay in the normal Workshop state
home; no run workspaces, credentials or transcripts belong in this repository.

## Environment and commands

Commands are run from the isolated checkout. `python -m cli` is the documented
source-checkout equivalent of the installed `workshop` command.

```sh
cd /private/tmp/autonomous-workshop-mixed-material-products
export PYTHONPATH="$PWD/src"
workshop_python=/Users/ab/code/autonomous-workshop/.venv/bin/python
"$workshop_python" -m cli doctor

"$workshop_python" -m cli wish "$(cat docs/ideas/mixed-material-pilots/01-harbor-relay-pinball.txt)" --inventor arlo-playfield --workflow spark --agent codex --model astra --effort ultra --max-tokens 100000000
"$workshop_python" -m cli wish "$(cat docs/ideas/mixed-material-pilots/02-cloudline-coaster.txt)" --inventor lila-kinetics --workflow spark --agent codex --model astra --effort ultra --max-tokens 100000000
"$workshop_python" -m cli wish "$(cat docs/ideas/mixed-material-pilots/03-switchyard-relay.txt)" --inventor arlo-playfield --workflow spark --agent codex --model astra --effort ultra --max-tokens 100000000
"$workshop_python" -m cli wish "$(cat docs/ideas/mixed-material-pilots/04-rainmark-studio.txt)" --inventor lila-kinetics --workflow spark --agent codex --model astra --effort ultra --max-tokens 100000000
"$workshop_python" -m cli wish "$(cat docs/ideas/mixed-material-pilots/05-liltwing-flight-garden.txt)" --inventor lila-kinetics --workflow spark --agent codex --model astra --effort ultra --max-tokens 100000000
"$workshop_python" -m cli wish "$(cat docs/ideas/mixed-material-pilots/06-atlas-vault.txt)" --inventor neri-wonder --workflow spark --agent codex --model astra --effort ultra --max-tokens 100000000
```

The normal CLI publishes through host-owned Spark Release after Make succeeds.
It does not authorize physical fabrication, purchases or shipping. GitHub
publication is not requested. Staff must perform the documented prototype tests
before treating a digitally generated design as a finished physical product.

For each saved id, inspect or resume with:

```sh
"$workshop_python" -m cli status <product-id> --json
"$workshop_python" -m cli resume <product-id>
```

Resume preserves the saved model, effort, session and token allowance. If a
deterministic Make tool has been fixed, use the existing explicit
`resume <product-id> --refresh-tools` only after a stopped run needs that fix;
record that command and the reason. Do not edit the run's frozen host files.

## Observed preparation

Three Inventors were created through the CLI from authored Taste files:

```sh
"$workshop_python" -m cli create inventor arlo-playfield --taste /private/tmp/mixed-material-inventor-tastes/arlo-playfield/TASTE.md --root "$PWD" --local-only --json
"$workshop_python" -m cli create inventor lila-kinetics --taste /private/tmp/mixed-material-inventor-tastes/lila-kinetics/TASTE.md --root "$PWD" --local-only --json
"$workshop_python" -m cli create inventor neri-wonder --taste /private/tmp/mixed-material-inventor-tastes/neri-wonder/TASTE.md --root "$PWD" --local-only --json
"$workshop_python" -m cli check --json
```

Creation returned `experimental` / `static-passed` for each. Their specialist
skills were then authored and exact tree hashes resealed. CLI validation passed
19 Inventors with zero problems. Arlo owns the passive pinball/relay; Lila owns
the motorized coaster, drawing/music and glider; Neri owns the tactile/optical
puzzle, including its simple battery illumination.

The user explicitly requested the existing **Dee** publishing account for all
three. A live identity check found the shared fallback was Alice, which is not
the owner of Civic Skyline; Dee was saved under the Bob connection. The exact
scoped source was reused through the CLI, with authenticated success:

```sh
"$workshop_python" -m cli login arlo-playfield --reuse-from bob
"$workshop_python" -m cli login lila-kinetics --reuse-from bob
"$workshop_python" -m cli login neri-wonder --reuse-from bob
```

Each returned `Connected <inventor> to @dee.` The command authenticates the
exact private source before saving the target binding, without shared-account
fallback. Credential values never entered this document or the source tree.
The existing Alice and Bob connections were preserved.

- Initial `doctor`: ready; Codex signed in, 16 inventor bundles before adding
  the three new specialists (the later CLI check validated 19), nine domain
  skills materialized including mixed-materials, host-only Factory credentials
  available. Optional host rendering unavailable; Spark uses Make's own images.
- Before launch, found that `make_round` attempted print checks on every part,
  including nonprinted card and purchased geometry. Correcting this selection
  is required for the material portfolio.
- Finalizer contract tests caught and fixed a missing bounded-read argument in
  the new manifest hook. The valid synthetic package now seals, and tampered
  manifest bytes are rejected before Made is written.
- A real build123d smoke check generated a printed block, a 0.2 mm card panel
  and a purchased motor envelope. `make_round` built all three and applied
  passing thickness/overhang checks only to the block. Its exit 1 truthfully
  indicated pending native visual feedback. The manufacturing CLI accepted the
  actual cadgen descriptor and exact public STEP/hero. This is a tool fixture,
  not one of the six toys or physical manufacture evidence.
- The initial focused suite passed 343 tests across CLI, Make iteration,
  manufacturing contracts, stage finalization, packaging, runtime assets,
  Factory and Release. Additional renderer and new inventor checks follow.
- An additional 51-test suite passed Make registry/LOCK, real STEP renderer,
  contributor contracts and package-data checks. Separate credential/CLI tests
  cover connection reuse, absent or misbound sources and authentication failure.
- Built the wheel with an isolated build backend. Installed-wheel CLI, asset,
  dependency-import and deterministic native-session checks pass in a temporary
  environment using existing dependencies read-only. Workshop and CLI imports
  were confirmed to come from that wheel. A clean dependency download remains
  unverified because PyPI metadata requests repeatedly timed out.

## Runs

Initial implementation: `13e6468c`. First live startup correction: `0556b83d`.
All six successful initializations below froze the corrected source on
2026-09-10. Each command is the corresponding Wish command above; each uses
Spark, `gpt-6-astra`, ultra, and a 100,000,000-token product limit.

| Pilot | Inventor | Run id | Initial observation |
|---|---|---|---|
| Harbor Relay Pinball | Arlo | `wish-20260910-143655-4d851b36` | Make active; native tools and specialist work observed |
| Cloudline Coaster | Lila | `wish-20260910-143717-dbe8ad47` | Make active; native tools observed |
| Switchyard Relay | Arlo | `wish-20260910-143721-492a87cb` | Make active; native tools observed |
| Rainmark Studio | Lila | `wish-20260910-143744-c4614e19` | Make active; native tools observed |
| Liltwing Flight Garden | Lila | `wish-20260910-143749-b20aacdc` | Make active; native tools observed |
| Atlas Vault | Neri | `wish-20260910-143753-a2e10997` | Make active; native tools observed |

At 14:39 UTC the pinball's ordinary CLI `status --json` confirmed Spark,
Astra, ultra, a 100M allowance, an active Make checkpoint and observed usage
across the native root and two descendant sessions. Publication had not started.
Initialization is not a completed product or publication claim.

### Live issue 1: native input scanner rejected harmless source

The first pinball invocation at revision `13e6468c` printed
`wish-20260910-143515-e96ebbd6`, then failed initialization with
`agent artifact contains credential-shaped content`. No native session started;
`status` correctly reported no saved workspace.

The actual shipped manufacturing validator had a URL check ending in
`parsed.password:`. The unchanged host scanner read the attribute/colon and
following source as a possible keyed secret. Rewrote the check to use explicit
`is not None`, which also rejects empty URL userinfo. Added a regression that
sends every actual packaged domain-skill file through the native input scanner.
The scanner was not relaxed or bypassed. All 41 affected contract, packaging
and finalizer checks passed. Retried the same documented Wish command at
`0556b83d`; initialization and the native Make session started successfully.

### Live issue 2: wheel inventor inventory lagged behind source

The wheel audit found a separate hardcoded inventory in `setup.py` omitted the
three new Inventors and the existing Ferro Line bundle. Revision `4671a5a9`
includes all four; the rebuilt wheel passes exact inventor/skill asset checks.
The deterministic installed-wheel fake was updated for the supported native
runtime and current Spark setup protocol. It verifies setup and Make use the
same session, the frozen profile survives, exact fixture token usage is
reconciled, and credentials stay outside native input. This fake does not
perform model work or publication.

### Live issue 3: native turns stopped before Make completion

All six initial native turns stopped between 14:55 and 14:59 UTC. Harbor Relay
recorded `provider-transport / stream-disconnected`; the other five recorded
unclassified terminal errors. The diagnostics do not establish a shared cause.
Saved session identities and unfinished design/research files remained present;
none had an accepted Make result or publication receipt.

Resumed the exact sessions through the ordinary CLI on 2026-09-10, preserving
each original Wish, Inventor, Astra/ultra profile and remaining 100M allowance:

```sh
# 15:30:18 UTC
"$workshop_python" -m cli resume wish-20260910-143721-492a87cb
# 15:30:31 UTC
"$workshop_python" -m cli resume wish-20260910-143749-b20aacdc
# 15:31:12 UTC
"$workshop_python" -m cli resume wish-20260910-143655-4d851b36
# 15:31:25 UTC
"$workshop_python" -m cli resume wish-20260910-143717-dbe8ad47
# 15:31:38 UTC
"$workshop_python" -m cli resume wish-20260910-143744-c4614e19
# 15:31:53 UTC
"$workshop_python" -m cli resume wish-20260910-143753-a2e10997
```

Each entered `session.resume`; no tool refresh or new Wish was used. A resume
starting successfully is not evidence that the product is complete.

### Make audit: purchased units and misleading verification instructions

A real imported-STEP audit confirmed Cloudline's selected motor is one CAD
leaf, correctly counted as one unit. A separate synthetic multipart motor
exposed a general defect: retaining its two colored leaves forced the old BOM
rule to count two purchased motors; flattening retained geometry but lost the
separate colors. The manifest now supports optional purchased
`assembly_unit_ids`, bound to exact non-root CAD subassemblies. Quantity counts
those physical units while every descendant leaf remains covered exactly once.
No supplier packaging or physical performance is inferred from that grouping.

Captured real CAD hierarchy tests cover color preservation, repeated units,
overlap, missing leaves, malformed hierarchy and inflated quantities. The
combined manufacturing, skill-registry and finalizer suite passed 100 tests.
An additional 25 package-data/registry checks passed, including the actual
materialized-byte credential scanner. These suites overlap.

Liltwing's native contract audit also exposed stale CAD guidance asking Spark
to author a verification JSON despite its finalizer requiring the verifier's
actual Markdown report. Corrected that guidance and Make-round's old claim
that every material receives print gates. Instructions now describe the
implemented printed subset and actual generated evidence. Neither correction
changes engineering thresholds or the running pilots' frozen tools.

### Make audit: bind the customer hero to the reviewed image

The positive synthetic finalizer fixture exposed an identity gap: it could
seal a tiny placeholder public hero while its actual reviewed CAD image was a
different file. Both had valid separate hashes. The Make finalizer now requires
the selected public hero to copy the exact reviewed `snap/iso.png` bytes.
Selection matches publication: prefer `public/hero.png`, otherwise use the
first declared supported image. An alternate public filename still works.

All 47 finalizer tests pass, including resealed unrelated-image rejection,
selection priority, alternate-name acceptance and rejection of a wrong first
fallback image. The host still copies Make's bytes; this adds no host render or
geometry review. Running pilots retain their frozen finalizer until an explicit
supported tool refresh.

### Make audit: power classification and clear-material rendering

The actual final verifier refuses image-derived work without explicit
`--powered` or `--unpowered`, but Make-round's final shortcut could not forward
either choice. It now accepts that explicit choice with
`--record-visual <feedback.json> --full`; a missing required choice fails before
consuming feedback. It does not infer an unpowered product from a missing
manifest. The verifier still rejects absent powered-system evidence and
contradictory declarations. All 45 focused Make-round/motion/pose tests passed,
including five actual verifier dry-run/refusal cases.

A real STEP audit found the exporter preserved transparent sheet alpha but
`render_product` discarded it, producing identical opaque images for alpha 0,
0.2 and 1. The renderer now preserves alpha with ordered source-over blending.
A half-open triangle fill prevents shared triangulation edges from blending
twice. Separate overlapping layers still blend separately. All four saved
opaque comparison images retain their exact previous PNG bytes.

This is schematic transparency: no reflection, refraction or physical light
transmission is simulated. Mean triangle depth remains approximate for crossing
surfaces. The existing geometry-only state-difference check stays unchanged.
The final 70-test package-data, registry, Make-round and renderer suite passed,
including the actual native-byte scanner; visual inspection confirmed the
clear panel reveals the object behind it without a diagonal seam.

### Controlled CLI tool refresh

After the fixes passed, each running CLI received Ctrl+C and exited before its
refresh command started. This was an operator-controlled update, not another
provider failure. No live tool file was edited directly. Each command below
copied nine changed instruction/tool files from Make revision `4ffc0790`,
including the reviewed-hero finalizer, and resumed the original session:

```sh
# 2026-09-10 15:57:00 UTC
"$workshop_python" -m cli resume wish-20260910-143753-a2e10997 --refresh-tools
# 15:57:38 UTC
"$workshop_python" -m cli resume wish-20260910-143717-dbe8ad47 --refresh-tools
# 15:58:03 UTC
"$workshop_python" -m cli resume wish-20260910-143655-4d851b36 --refresh-tools
# 15:58:23 UTC
"$workshop_python" -m cli resume wish-20260910-143721-492a87cb --refresh-tools
# 15:58:45 UTC
"$workshop_python" -m cli resume wish-20260910-143744-c4614e19 --refresh-tools
# 15:59:10 UTC
"$workshop_python" -m cli resume wish-20260910-143749-b20aacdc --refresh-tools
```

Ordinary CLI `status --json` then confirmed all six active in Make, each on its
same root native thread, `gpt-6-astra`, ultra and its original 100,000,000-token
limit. Previously observed usage remained charged. Existing research, CAD and
unfinished inspection work stayed in the product workspaces.

Ctrl+C exposed one CLI presentation bug: cleanup unwound but the command
printed a Python traceback and exited 1. A top-level handler now emits only
`workshop: interrupted.` on stderr and exits 130, with no saved/success claim
or automatic resume. All 87 CLI tests passed; a subsequent 38-test command
suite also verifies the subprocess test imports this checkout explicitly,
without depending on inherited `PYTHONPATH` or another installed CLI.

At this checkpoint no pilot had completed Make or published. Real native
inspection had repaired pinball mechanism intersections/overhangs and rejected
a supplier rod whose advertised 75 mm model actually measured 150 mm. Those
are observed digital checks, not physical manufacture evidence.

### Installed-wheel check at e39df106

Built code revision `e39df106` offline using cached pinned build dependencies,
then reran the full deterministic acceptance against a fresh wheel installation
with existing declared dependencies appended read-only:

```sh
UV_CACHE_DIR=/private/tmp/workshop-mixed-material-final-e39df106-uv-cache PYTHONDONTWRITEBYTECODE=1 uv build --offline --no-build-isolation --python /private/tmp/workshop-mixed-material-final-e39df106-build-env/bin/python --wheel --out-dir /private/tmp/workshop-mixed-material-final-e39df106
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 TMPDIR=/private/tmp /Users/ab/code/autonomous-workshop/.venv/bin/python -B /private/tmp/workshop-mixed-material-final-e39df106-acceptance.py
```

The local wrapper changes dependency installation only. It proves `workshop`,
`cli` and distribution metadata originate in the new temporary wheel install,
then runs the unchanged exact-asset, dependency, CLI/catalog, credential
isolation, frozen-profile, same-session and token-accounting checks. All pass.
No real model or publication runs in that acceptance fixture.

Wheel: `/private/tmp/workshop-mixed-material-final-e39df106/autonomous_workshop-0.6.0-py3-none-any.whl`.
SHA-256: `b6126cc7dbb20b29cc541f102909a5f62e5be312b629e4906a5f824df0afd02e`.
Acceptance log: `/private/tmp/workshop-mixed-material-final-e39df106-acceptance.log`.
The earlier clean-PyPI-download limitation remains; this successful test used
local dependencies without global installation changes.

### Instruction clarification: hidden installed power components

The generic power skill's validation-only option conflicted with mixed Make's
complete assembly/BOM. Clarified that mixed Spark uses existing
`cad.mode: assembly` / `rendered: true` for installed electrical components,
including sourced approximate geometry; natural occlusion is fine. Separate
clearance and service-space volumes remain private measurement references.
This changes instructions only, preserving standalone/frozen behavior and all
existing gates. It adds no power-to-BOM identity mapping.

Atlas's current CAD power manifest already declares all seven carried
electrical components in assembly mode; Cloudline's current handoff likewise
requires full inclusion. Their combined power integration was still pending
when inspected. No further interruption or tool refresh was needed for this
clarification. All 16 registry checks, both skill validators and the actual
agent byte scan across 157 registered Make files passed.

### Live digital checks at 16:30–16:32 UTC

All six ordinary `status <product-id> --json` calls still reported active Make,
running native work, the original Astra/ultra profile and 100M allowance. No
pilot had completed Make or created a publication. Observed usage includes
completed requests in the root and descendant sessions; it is not a completion
percentage.

| Pilot | Observed tokens at 16:30 UTC |
|---|---:|
| Harbor Relay Pinball | 32,007,130 |
| Cloudline Coaster | 38,476,672 |
| Switchyard Relay | 33,461,742 |
| Rainmark Studio | 37,099,474 |
| Liltwing Flight Garden | 34,878,539 |
| Atlas Vault | 44,566,368 |

Liltwing's first product round built all 16 declared source entries and applied
print gates only to its five printed parts. Four passed; the shuttle failed
thickness and overhang checks. Incorrect translation inputs and inconclusive
Boolean geometry checks also needed repair. The Manager's visual verdict was
inconclusive: the complete playset was visible, but the message carrier,
launcher settings and sewn pocket entrances needed focused views. These are
recorded failures, not accepted product evidence.

Atlas's separate internal tooling project passed its first local round,
including native visual feedback. The actual toy's assembly and final review
remained pending. Pinball, Switchyard and Rainmark were still integrating
mechanisms and repairing their product sources. No physical test measurements
or manufacturing results were claimed from these digital checks.

### Motion documentation and transparent-state comparison

Liltwing exposed an ambiguous coupled-motion example: a translation requires
`vector: [x, y, z]` with scalar `start`/`end` multipliers, or a complete
`offsets_mm` table. Revision `907bec18` clarifies those existing semantics;
the parser and gate are unchanged. Its separate aircraft failures reproduced
as invalid source-group Boolean normalization. A healed STEP roundtrip did not
justify accepting the original source, so the inconclusive gate was retained.

A real two-state STEP fixture then exposed a renderer false negative: motion
visible behind a fixed clear cover became invisible in the geometry comparison,
which discarded all opacity. Revision `a820ee5c` retains opacity only on exact
unchanged triangles whose opacity and unambiguous multiplicity agree across
every state. Other comparison geometry remains opaque with neutral colors.
Changing colors or opacity cannot supply motion evidence; actual displayed
frames and opaque comparison behavior are unchanged. Moving transparent
geometry remains conservatively opaque in the comparison.

All 47 focused renderer/registry tests and the private-byte scan of 157 Make
files passed. Preparing comparison colors for three 75,000-triangle states
took 0.759 seconds, excluding rendering. The independent source CLI check was:

```sh
"$workshop_python" src/workshop/make/skills/cad/scripts/render_product /private/tmp/workshop-transparent-state-audit/state-0.step -o /private/tmp/workshop-transparent-state-audit/verified-hero.png --size 800 --state-view front --state-sheet /private/tmp/workshop-transparent-state-audit/verified-states.png --state-source /private/tmp/workshop-transparent-state-audit/state-0.step --state-source /private/tmp/workshop-transparent-state-audit/state-1.step
```

It exited 0 and produced a visually inspected 1600×800 state sheet, with a
minimum neutral comparison difference of 5.799 against the unchanged default
threshold of 2. These are deterministic test shapes, not a finished pilot.
The live sessions had not been interrupted or refreshed for these changes.

Revision `a272ad7d` adds the source group's label and solid count to motion
normalization failures, preserving the original reason. For example, a failed
union now identifies `normalizing group 'shuttle' (6 solids)`. Existing
inconclusive status, result fields, exit code 1 and a single Boolean attempt
are unchanged. All 122 focused motion/retention/Make-round/registry tests
passed, including failing mover and obstacle groups and source immutability.
This diagnostic-only change also did not interrupt or refresh live work.

### Complete surfaces, correct opaque depth, and the second tool refresh

Cloudline's native render diagnosis exposed a separate display defect:
`render_product` uniformly discarded triangles above 75,000, leaving holes in
valid panels and tracks. Revision `98cc3445` removes that sampling entirely,
retaining all supplied triangles and their corresponding colors/alpha. It
preserves tessellation defaults and writes no mesh deliverable. All 32 renderer
and 16 registry tests passed, including late small components formerly skipped.
A 205,980-triangle test rendered in 2.213 seconds, with a separately measured
254 MiB total process peak. These timings are observations on the live machine.

Cloudline also exposed incorrect opaque face ordering. Revision `142d6511`
uses per-pixel depth for opaque surfaces, then clips translucent fragments
against that depth. It preserves camera, palette, shading and source/review
paths. All 37 renderer and 16 registry tests passed. A real two-plate STEP
fixture fixed 1,158 incorrectly occluded interior samples; an independent
192,060-triangle scene rendered in 4.65 seconds at 1000 pixels. Ordering between
translucent fragments remains approximate, including some nonintersecting
transparent layers; this is schematic appearance, not an optical simulation.

The builder copied one immutable, unfinished Cloudline STEP snapshot into a
private scratch directory and compared the complete-triangle painter against
the corrected renderer. Both commands exited 0 with all **1,292,795 triangles**
and unchanged input bytes. Visual inspection confirmed that lower faces no
longer appeared through the base and tracks. This is renderer regression
evidence, not completion of Cloudline or a product gate.

```sh
git show 98cc3445:src/workshop/make/skills/cad/scripts/render_product > /private/tmp/workshop-render-live-regression/render_product_before.py
"$workshop_python" /private/tmp/workshop-render-live-regression/render_product_before.py /private/tmp/workshop-render-live-regression/cloudline-f7c36a6653ef.step -o /private/tmp/workshop-render-live-regression/cloudline-before.png --size 1000
"$workshop_python" src/workshop/make/skills/cad/scripts/render_product /private/tmp/workshop-render-live-regression/cloudline-f7c36a6653ef.step -o /private/tmp/workshop-render-live-regression/cloudline-after.png --size 1000
```

These reproduced defects justified updating the six layered product assemblies.
Each running CLI was stopped with Ctrl+C and fully exited before its ordinary
resume command. The first three older CLI processes exited 1 with their old
interrupt traceback; Switchyard, Rainmark and Liltwing emitted the corrected
`workshop: interrupted.` and exited 130. These were operator-controlled tool
updates, not provider failures. All new processes use revision `142d6511`.

```sh
# 2026-09-10 17:20:35 UTC
"$workshop_python" -m cli resume wish-20260910-143717-dbe8ad47 --refresh-tools
# 17:21:05 UTC
"$workshop_python" -m cli resume wish-20260910-143753-a2e10997 --refresh-tools
# 17:21:09 UTC
"$workshop_python" -m cli resume wish-20260910-143655-4d851b36 --refresh-tools
# 17:22:00 UTC
"$workshop_python" -m cli resume wish-20260910-143721-492a87cb --refresh-tools
# 17:22:05 UTC
"$workshop_python" -m cli resume wish-20260910-143744-c4614e19 --refresh-tools
# 17:22:12 UTC
"$workshop_python" -m cli resume wish-20260910-143749-b20aacdc --refresh-tools
```

Each command rebound seven changed Make instruction/tool files. Subsequent
ordinary CLI status calls confirmed all six active in Make, four native turns,
the same original root threads, `gpt-6-astra`, ultra, their original 100M token
limits and all prior observed usage still charged. Read-only hash comparisons
also confirmed the new renderer, motion tool and revised instructions were
present in every run. No live product or host tool file was edited directly.
None had completed Make or published at the 17:22 UTC verification.

### Fresh installed-wheel check with the renderer fixes

Built a fresh wheel from executable revision `142d6511` and reran the unchanged
installed CLI acceptance in a new environment. The local dependency wrapper
differs from the earlier one only in the wheel path and completion label.

```sh
UV_CACHE_DIR=/private/tmp/workshop-mixed-material-final-142d6511-uv-cache PYTHONDONTWRITEBYTECODE=1 uv build --offline --no-build-isolation --python /private/tmp/workshop-mixed-material-final-142d6511-build-env/bin/python --wheel --out-dir /private/tmp/workshop-mixed-material-final-142d6511
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 "$workshop_python" -B /private/tmp/workshop-mixed-material-final-142d6511-acceptance.py
```

Acceptance passed. `workshop`, `cli` and distribution metadata loaded from the
fresh wheel environment. The renderer, motion tool and Make lock bytes also
matched the committed revision, source checkout and wheel. Existing declared
dependencies were reused read-only; a clean dependency download/resolution was
not tested. The fixture used no real model session or publication.

Wheel: `/private/tmp/workshop-mixed-material-final-142d6511/autonomous_workshop-0.6.0-py3-none-any.whl`.
SHA-256: `7a52325c3b29662f536262fc0fa7e5473ea882158b62a5a85a573084cf2213f5`.
Acceptance log: `/private/tmp/workshop-mixed-material-final-142d6511-acceptance.log`.
Byte identity proof: `/private/tmp/workshop-mixed-material-final-142d6511-wheel-proof.json`.

### Evening continuation after interrupted native turns

The six CLI processes later exited 2 between 17:29:44 and 17:32:52 UTC,
each reporting a failed native turn with `category=unclassified` and
`signature=unclassified`. A separate repository-audit helper reported an
account usage limit at approximately the same time, but the product diagnostics
do not establish that as the cause of their failures. Make and publication
remained incomplete; the saved product sessions and artifacts were retained.

After the user requested continuation, the same sessions were resumed from
revision `90b06c30` through the ordinary CLI. No new Wish, profile override,
token increase, credential change or tool refresh was used:

```sh
# 2026-09-10 23:40:38 UTC
"$workshop_python" -m cli resume wish-20260910-143655-4d851b36
# 23:41:39 UTC
"$workshop_python" -m cli resume wish-20260910-143717-dbe8ad47
# 23:41:46 UTC
"$workshop_python" -m cli resume wish-20260910-143721-492a87cb
# 23:41:50 UTC
"$workshop_python" -m cli resume wish-20260910-143744-c4614e19
# 23:41:58 UTC
"$workshop_python" -m cli resume wish-20260910-143749-b20aacdc
# 23:42:03 UTC
"$workshop_python" -m cli resume wish-20260910-143753-a2e10997
```

At 23:43 UTC, ordinary `status <id> --json` calls confirmed all six progressing
in Make with five native turns, their original root thread ids, Astra, ultra
and 100,000,000-token limits. Observed cumulative usage was 73,110,712 for
Harbor, 78,186,226 for Cloudline, 74,420,842 for Switchyard, 79,350,080 for
Rainmark, 62,569,545 for Liltwing and 83,094,151 for Atlas. These values include
completed requests across discovered native children; in-flight usage is
excluded. Publication remained `not-created` for every pilot.

Read-only review of Liltwing's third Make round found four reused passing
printed-part results and a still-failing shuttle. Its unsupported region
decreased from 164.9 to 28.6 square millimetres, but measured thin regions of
0.33 and 0.13 mm remained below the 0.80 +/- 0.07 mm requirement. Round three
had no motion result and pending visual feedback. Round two's motion log
recorded only `TIMEOUT after 900s`, with no condition evidence. This proves
neither a motion collision nor a motion pass; the round correctly failed.

### Explicit 500M / medium continuation

The user requested 500M total tokens for each existing product, then medium
reasoning effort. All six active CLI processes were stopped cleanly at
23:46:37–23:46:39 UTC on September 10, each exiting 130 with
`workshop: interrupted.` Their sessions and prior usage remained saved.

Revision `df727a0b` raised the selectable token ceiling from 200M to 500M,
preserving the 30M default and saved limits. Revision `eed4633c` added explicit
`resume --effort` support for the eligible Codex Spark token-budget profile,
with exact Manager/input rebinding and interrupted-change recovery. The focused
CLI, host, AgentRun, cap and effort suites passed 303 tests. One existing host
test required a localhost socket and passed when rerun with that permission.

The same continuation also refreshed two Make files from `e62f45a3`: motion
checks now emit bounded condition/sample progress to stderr. A real short
timeout test proved that the existing Make runner preserves this diagnostic
while still returning 124 and accepting no partial condition evidence. The
129 focused motion/retention/Make-round/registry checks passed. No geometry
threshold, collision result or lifecycle rule changed.

Actual commands from revision `eed4633c` on September 11 UTC:

```sh
"$workshop_python" -m cli resume wish-20260910-143655-4d851b36 --max-tokens 500000000 --effort medium --refresh-tools
"$workshop_python" -m cli resume wish-20260910-143717-dbe8ad47 --max-tokens 500000000 --effort medium --refresh-tools
"$workshop_python" -m cli resume wish-20260910-143721-492a87cb --max-tokens 500000000 --effort medium --refresh-tools
"$workshop_python" -m cli resume wish-20260910-143744-c4614e19 --max-tokens 500000000 --effort medium --refresh-tools
"$workshop_python" -m cli resume wish-20260910-143749-b20aacdc --max-tokens 500000000 --effort medium --refresh-tools
"$workshop_python" -m cli resume wish-20260910-143753-a2e10997 --max-tokens 500000000 --effort medium --refresh-tools
```

All six saved medium effort and refreshed only the two named Make files. Five
saved 500M and entered native resume. Rainmark retained its 100M cap and exited
2 before native launch with `cannot adopt a token cap with unobserved native
threads`; a known child still had pending usage. Harbor, Cloudline, Liltwing
and Atlas then stopped with `native usage task baseline is ambiguous` after
their native sessions resumed. Switchyard continued. These accounting failures
remain fail-closed pending diagnosis; neither prior consumption nor native
session identity was reset.

Revision `e8048cb0` corrected Rainmark's cap-update edge case. Changing an
existing token budget may preserve valid pending child records through the
unchanged observation validator; converting a legacy time/turn budget still
requires fully observed history. Tests cover exact pending-child retention,
lost/regressing usage refusal without ledger changes, and both legacy cases.
The 57 token-budget and six real-host resume tests passed.

```sh
# 2026-09-11 00:12:28 UTC
"$workshop_python" -m cli resume wish-20260910-143744-c4614e19 --max-tokens 500000000 --effort medium
```

Rainmark saved 500M and resumed, then stopped on the same ambiguous native usage
baseline at 00:12:48. At this point all six saved profiles were Astra/medium
with 500M total caps and their original root sessions. Read-only native
`turn_context` metadata also confirmed medium for all six resumed roots
and Switchyard's three newly active child agents; this does not retroactively
change historical ultra work.

Revision `7c9eea10` repaired the second accounting issue. The native runtime can
resume from the exact terminal counters of its most recently completed task
after an intervening interrupted task. The reader now recognizes that case
only when the completed task id and every baseline-plus-request counter match.
All requests observed during the interrupted task remain charged. Pre-task
parent completion metadata copied into a child supplies no accounting baseline.
Unsupported histories, missing identities and counter regressions still stop
the run. The fix passed 166 usage, compaction and budget tests.

Read-only replay of all six full ancestry histories succeeded. The five stopped
products retained their previous totals plus exactly the first new request:
Harbor +167,426; Cloudline +153,334; Rainmark +158,848; Liltwing +107,298; Atlas
+111,964 tokens. Switchyard's concurrently observed total remained monotonic.
This diagnoses native checkpoint restoration after interruption, not a network
failure or an effect specific to medium reasoning.

Switchyard was then stopped cleanly at 00:19:55 UTC, exiting 130, so all six
could use the corrected host reader. Normal resumes preserved the already
saved 500M/medium settings; no further tool refresh was needed:

```sh
# 2026-09-11 00:20:00 UTC
"$workshop_python" -m cli resume wish-20260910-143655-4d851b36
# 00:20:05 UTC
"$workshop_python" -m cli resume wish-20260910-143717-dbe8ad47
# 00:20:11 UTC
"$workshop_python" -m cli resume wish-20260910-143721-492a87cb
# 00:20:17 UTC
"$workshop_python" -m cli resume wish-20260910-143744-c4614e19
# 00:20:23 UTC
"$workshop_python" -m cli resume wish-20260910-143749-b20aacdc
# 00:20:29 UTC
"$workshop_python" -m cli resume wish-20260910-143753-a2e10997
```

At 00:21:32 UTC, ordinary CLI status checks confirmed all six progressing in
Make with `gpt-6-astra`, `medium`, 500,000,000-token caps and their original
root thread ids. Each total had advanced beyond its recovered pre-resume
history: Harbor 75,379,270; Cloudline 82,825,622; Switchyard 86,065,791;
Rainmark 80,804,594; Liltwing 67,545,323; Atlas 88,783,246. Publication remained
`not-created` for every pilot. These are running digital-product trials, not
completed products or physical manufacturing evidence.

### Installed CLI after the profile and accounting fixes

Built executable revision `7c9eea10` and reran the unchanged installed CLI
acceptance fixture in a fresh temporary environment. Only the wrapper's
artifact paths and completion label changed:

```sh
UV_CACHE_DIR=/private/tmp/workshop-mixed-material-final-7c9eea10-uv-cache PYTHONDONTWRITEBYTECODE=1 uv build --offline --no-build-isolation --python /private/tmp/workshop-mixed-material-final-7c9eea10-build-env/bin/python --wheel --out-dir /private/tmp/workshop-mixed-material-final-7c9eea10 > /private/tmp/workshop-mixed-material-final-7c9eea10-build.log 2>&1
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 "$workshop_python" -B /private/tmp/workshop-mixed-material-final-7c9eea10-acceptance.py > /private/tmp/workshop-mixed-material-final-7c9eea10-acceptance.log 2>&1
```

Acceptance exited zero. CLI, Workshop and distribution metadata loaded from
the fresh wheel installation. Exact byte comparison against the committed
revision passed for the CLI, native workflow, AgentRun, token reader/budget,
motion checker, product renderer and Make lock. Existing dependencies were
accessed read-only; clean dependency resolution remains untested. The original
dependency environment had no modified files. This fixture performs no real
model work or publication.

Wheel: `/private/tmp/workshop-mixed-material-final-7c9eea10/autonomous_workshop-0.6.0-py3-none-any.whl`.
SHA-256: `becb18f73664f4c516bd24924ef1b9ca71a8f3f4ad522e805ab0d7f586400546`.
Byte proof: `/private/tmp/workshop-mixed-material-final-7c9eea10-wheel-proof.json`.

### Explicit Make selection: print by default, mixed by choice

On 2026-09-11 the operator requested separate Make modes, then shortened their
names to `print` and `mixed`. New `wish` and `start` products default to
`--make print`; mixed-material products require `--make mixed` with Spark.
`MAKE.json` freezes the selection. Existing pilots have no selection file and
retain their original mixed-material protocol, sessions and tools. No pilot
was restarted or migrated for this change.

The following help/status commands were run from this worktree using the same
source CLI environment as the pilot commands above:

```sh
"$workshop_python" -m cli wish --help
"$workshop_python" -m cli status wish-20260910-143655-4d851b36 --json
"$workshop_python" -m cli status wish-20260910-143717-dbe8ad47 --json
"$workshop_python" -m cli status wish-20260910-143721-492a87cb --json
"$workshop_python" -m cli status wish-20260910-143744-c4614e19 --json
"$workshop_python" -m cli status wish-20260910-143749-b20aacdc --json
"$workshop_python" -m cli status wish-20260910-143753-a2e10997 --json
```

All six status receipts retained Astra, medium effort, 500M total tokens and
the original root thread id. They reported `make_mode: null`, meaning their
historical scope is preserved, not that the new print default applies.
Five were active; Switchyard was waiting on its existing deforming-motion
tooling need. None was published at this observation.

Focused checks passed: 96 CLI tests; 54 Make-finalizer tests; 40 mode/effort
integration tests; 38 CLI subprocess, package and skill checks; and 98 Codex
native-session tests with one existing skip. An overlapping workflow regression
suite passed 185 tests, plus its loopback transport test passed separately
outside the sandbox, which forbids local socket binding.

Built and tested a fresh installed wheel with these commands:

```sh
UV_CACHE_DIR=/private/tmp/workshop-make-mode-selector-uv-cache PYTHONDONTWRITEBYTECODE=1 uv build --offline --no-build-isolation --python /private/tmp/workshop-mixed-material-final-7c9eea10-build-env/bin/python --wheel --out-dir /private/tmp/workshop-make-mode-selector > /private/tmp/workshop-make-mode-selector-build.log 2>&1
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 "$workshop_python" -B /private/tmp/workshop-make-mode-selector-acceptance.py > /private/tmp/workshop-make-mode-selector-acceptance.log 2>&1
```

The installed fixture exercised the ordinary CLI twice in separate temporary
Workshop and Codex homes: one Wish without `--make` and one with `--make mixed`.
Both passed exact mode/input binding, pre-Make inventor selection, status,
skill inventory and relative/absolute read-only sandbox-rule checks. The first
sandboxed attempt could not establish subprocess supervision; the same
deterministic fixture passed outside the sandbox. It uses fake native output,
never a real model or publication. Dependencies were read from the existing
environment; clean dependency resolution was not tested.

Wheel: `/private/tmp/workshop-make-mode-selector/autonomous_workshop-0.6.0-py3-none-any.whl`.
SHA-256: `783df6e9f4a07b24fe241ef57edfd868815378c56145834337d10e37983f66d4`.
Exact CLI, mode contract, AgentRun, native host and adapter bytes match the
source checkout; proof is `/private/tmp/workshop-make-mode-selector-wheel-proof.json`.

For future products, these are usage examples, not additional launched pilots:

```sh
workshop wish "a rotating desktop toy"                    # default: print
workshop wish "a rotating desktop toy" --make print
workshop wish "a wooden marble toy with printed cams" --make mixed
```

### Sequential completion: Liltwing first

The operator then requested one completed product before continuing the next.
Liltwing Flight Garden (`wish-20260910-143749-b20aacdc`) remains the sole active
pilot. Its fifth Make round passed all five printed-part checks and the
Manager's assembly visual review, but the motion subprocess reached its
900-second limit. Final integrated verification, blind review and publication
were still outstanding. Round six was already running when the schedule changed.

At 2026-09-11 01:52:52 UTC, Ctrl+C was sent to the existing Cloudline, Rainmark
and Atlas CLI terminals. Each exited cleanly with code 130. These are pauses of
the original runs, not replacement Wishes. Harbor had already stopped at
01:32:54 on another ambiguous native usage baseline; Switchyard was already
waiting on its recorded motion-tooling limitation. No other pilot was resumed.

Liltwing's existing CLI command continues unchanged:

```sh
# Already running since 2026-09-11 00:20:23 UTC; not launched a second time.
"$workshop_python" -m cli resume wish-20260910-143749-b20aacdc
```

All six preserve their original native sessions and consumed usage, with Astra,
medium effort and 500M total token caps. The remaining five will stay paused
while Liltwing completes. A read-only process check confirmed Liltwing was the
only active CLI among these six run ids. No publication or physical fabrication
is implied by the digital checks above.

### Static battlefield direction; all six existing pilots paused

At 2026-09-11 02:05:10 UTC, the operator requested a static mixed-material first
product. Ctrl+C stopped Liltwing's existing terminal cleanly with exit 130.
All six original pilots are now paused, with their work and saved profiles
preserved. No tool refresh was applied to Liltwing and no new Wish was launched.

A static seaside miniature was briefly drafted but not launched. The operator
then requested historical battlefield research, a widely recognized battle,
varied terrain and forces, and manual replay with formations, flanks, orders
and tempo. The resulting recommendation is Waterloo, with permanently assembled
terrain and complete troop stands repositioned by hand. Research and proposed
materials are recorded in [historical-battlefield-selection.md](historical-battlefield-selection.md).
This remains product selection and design discussion; it is not a completed
toy, a new native run or a publication.

The previously started motion performance fix was completed independently as
`dbbd91d2`. It caches at most 32 successful exact placed-material results per
condition without changing samples, pose checks, collision decisions or time
limits. The focused motion regression run passed 122 tests and the retention
self-check; a final cache/skill-registry run passed 25 tests. A synthetic
40-step sweep produced identical results with 246 normalizations in 24.121 s
uncached and 44 normalizations in 4.873 s cached. These measurements are a tool
benchmark, not evidence about Liltwing's physical performance or final gates.

### Theo Fieldcraft and the Waterloo pilot

The operator authorized building the Waterloo set and requested a new Inventor
who researches and relives historical battles. Theo Fieldcraft was created
through the ordinary CLI, then given a specialist Taste and exact hashed skill:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src "$workshop_python" -m cli create inventor theo-fieldcraft --taste /private/tmp/theo-fieldcraft-seed/TASTE.md --root "$PWD" --local-only --json
PYTHONPATH="$PWD/src" "$workshop_python" -m cli check inventors/theo-fieldcraft --json
PYTHONPATH="$PWD/src" "$workshop_python" -m cli check --json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src "$workshop_python" -m unittest tests.contributors.test_manifest tests.packaging.test_package_data
```

Creation returned `experimental` / `static-passed`. The final bundle and all
20 Inventors passed CLI validation; all 17 contributor and packaging tests
passed. Commit `a0972a42` contains the Inventor, its packaging inventory and the
exact [Waterloo Wish](mixed-material-pilots/07-waterloo-1815.txt).

The first attempt to reuse the `bob` connection was rejected by automatic
approval review because the prior authorization named Dee. The operator then
explicitly authorized either Dee or Bob. Retrying the same ordinary CLI command
succeeded; no alternate credential path or manual credential copy was used:

```sh
PYTHONPATH="$PWD/src" "$workshop_python" -m cli login theo-fieldcraft --reuse-from bob
```

Authenticated output was `Connected theo-fieldcraft to @dee.` Here `bob` is
the saved source Inventor connection; its authenticated publishing account is
Dee. No credential values entered the source tree, this log or the native run.

At **2026-09-11 02:38:05 UTC**, the following command launched the only active
product, **`wish-20260911-023805-fe157910`**:

```sh
PYTHONPATH="$PWD/src" "$workshop_python" -m cli wish "$(cat docs/ideas/mixed-material-pilots/07-waterloo-1815.txt)" --inventor theo-fieldcraft --workflow spark --make mixed --agent codex --model astra --effort medium --max-tokens 500000000
PYTHONPATH="$PWD/src" "$workshop_python" -m cli status wish-20260911-023805-fe157910
PYTHONPATH="$PWD/src" "$workshop_python" -m cli status wish-20260911-023805-fe157910 --json
```

The initial status confirmed Spark, explicit `mixed` Make, `gpt-6-astra`,
medium effort, a 500,000,000-token total cap and Make attempt 1. The original
root native session is `01a08e54-55f5-7a93-aa25-872ffc105b3a`. The first observed
status reported 49,932 tokens; this excludes in-flight usage and is not a final
cost or completion estimate. Publication is requested and remains incomplete
until normal host Release obtains authenticated public readback.

The Wish assumes a 0.4 mm FDM nozzle and production parts fitting a 220 × 220 mm
usable bed pending actual workshop specifications. It requires one finite
roster, a main battle and three shorter alternatives, fixed finished landscape
and complete hand-positioned formations. Physical fabrication and play remain
unperformed. All six earlier pilots stay paused; none was resumed for this
launch.

The full Wish was opened for the operator without changing the frozen run:

```sh
open -a TextEdit /private/tmp/autonomous-workshop-mixed-material-products/docs/ideas/mixed-material-pilots/07-waterloo-1815.txt
```

A read-only integration audit confirmed the new run's `MAKE.json` is mode 0400,
matches the mixed selection in `STAGE.json`, and carries the exact Theo, mixed
manufacturing, finalizer and updated motion-tool bytes. The static set does not
require invented mechanism animation; the existing applicable assembly checks
remain required. This audit does not qualify unfinished geometry or publication.

Theo was also verified in a fresh wheel built from committed revision
`e686073da3b990463aed080b42ae2deb598bb724`, using a temporary `git archive`
snapshot. Build working directory was
`/private/tmp/workshop-theo-fieldcraft-e686073d-wheel-check/source`:

```sh
PYTHONDONTWRITEBYTECODE=1 /private/tmp/workshop-mixed-material-final-7c9eea10-build-env/bin/python -B -c "from setuptools.build_meta import build_wheel; print(build_wheel('/private/tmp/workshop-theo-fieldcraft-e686073d-wheel-check'))"
PYTHONDONTWRITEBYTECODE=1 "$workshop_python" -B /private/tmp/workshop-theo-fieldcraft-e686073d-wheel-check/verify.py
/private/tmp/workshop-theo-fieldcraft-e686073d-wheel-check/venv/bin/workshop inventors --json
/private/tmp/workshop-theo-fieldcraft-e686073d-wheel-check/venv/bin/workshop check /private/tmp/workshop-theo-fieldcraft-e686073d-wheel-check/venv/lib/python3.11/site-packages/workshop/contributors/_inventors/theo-fieldcraft --json
/private/tmp/workshop-theo-fieldcraft-e686073d-wheel-check/venv/bin/workshop check /private/tmp/workshop-theo-fieldcraft-e686073d-wheel-check/venv/lib/python3.11/site-packages/workshop/contributors/_inventors --json
```

The last three commands were invoked by `verify.py`; the exact argument arrays
and origin checks are in its adjacent `proof.json`. The complete wheel asset
audit passed, as did installed CLI checks for Theo and all 20 Inventors. Theo's
Taste, manifest and skill match source, wheel and installed bytes exactly.
Dependencies were reused read-only, not freshly resolved. This wheel excludes
the later concurrent usage-parser fix.

Wheel: `/private/tmp/workshop-theo-fieldcraft-e686073d-wheel-check/autonomous_workshop-0.6.0-py3-none-any.whl`.
SHA-256: `8a0f9370ca84ed714ee963c4577cfbed322124b657fa38df8f45413d5122b84b`.

### Usage-notification repair during Waterloo Make

While Waterloo progressed through Theo's design handoff into CAD, the builder
diagnosed Harbor's earlier accounting stop. Its child completed a task with
observed usage, then emitted exactly the same cumulative and last-request
counters after the next task started. Codex 0.153.4 can resend unchanged token
information on a rate-limit update; a notification is not necessarily a fresh
request. The previous parser required the first notification to contain a new
request and rejected this repeated terminal snapshot.

The narrow repair defers only an exact, immediately completed non-reset
notification with matching model and all five total/last counter fields. It
retains observed usage and the prior observation timestamp while requiring the
next fresh sample to establish its exact reset or continuation baseline.
Completion after only deferred snapshots fails closed. The existing explicit
`total == last` reset interpretation stays first because a repeated
single-request snapshot cannot be distinguished from an identical new reset
request. Other ambiguous or regressing records remain errors.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/src:/private/tmp/workshop-usage-test-deps" "$workshop_python" -m pytest tests/runtime/test_codex_usage.py tests/workflow/test_token_budget.py -q
PYTHONPATH="$PWD/src" "$workshop_python" -m cli status wish-20260910-143655-4d851b36
```

All 185 usage/token-budget tests passed, including compaction cases and new
root/child, restored-budget, repeated-notification and failure-path cases.
Independent source/test review found no blocker. A read-only replay of Harbor's
19 ancestry-bound threads returned exactly its saved **98,485,036** tokens,
with the affected child's observation timestamp unchanged. No transcript was
copied into the repository. Harbor was not resumed. Waterloo's already running
host was not restarted or hot-patched; its subsequent ordinary CLI resume, if
needed, will load the corrected host reader without changing the frozen Wish.

### Waterloo checkpoint and tool repairs, 2026-09-11

The original CLI stopped normally at **03:51:49 UTC**, preserving native root
`01a08e54-55f5-7a93-aa25-872ffc105b3a`, Astra/medium, and the 500M allowance.
Status reported `waiting` at Make with **32,866,528 tokens**. Its concrete need
is an incompatible review contract: the installed final verifier requires
schema 7 while Make's finalizer requires schema 8 and exact print-report hashes.

```sh
PYTHONPATH="$PWD/src" "$workshop_python" -m cli status wish-20260911-023805-fe157910 --json
```

Two Make rounds produced all 11 printed families with passing thickness and
nine with passing overhang evidence. Cavalry and commander horse geometry still
needs local support repairs. Both whole-product visual packets timed out at
900 seconds; no successful product preview, independent blind review or final
integrated verification exists yet. The combined STEP on disk predates later
source changes and must be regenerated. Rules version 1.1 has 63 passing
digital assertions and bounded pass/termination fixtures; those do not establish
tactical balance or human play. Customer guides/scenarios and private workshop
drawings are drafted. Manufacturing manifest finalization and publication remain
pending.

The builder repaired the renderer's observed assembly-copy bottleneck. Both
renderers now use the same native placement as before with detached wrappers,
preserving every occurrence, topology, triangle and color. A synthetic 40-leaf
case reduced Python shape copies from 2,440 to zero, placement traversal from
0.6101 to 0.0005 seconds, and fresh-assembly loading from 1.4526 to 0.8389 seconds.
All 10,480 triangle/color entries matched. These are synthetic measurements,
not a successful Waterloo render.

```sh
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 "$workshop_python" -c 'import sys,unittest;sys.path.insert(0,"src");unittest.main(module=None)' tests.make.test_render_assembly_placement tests.make.test_render_review_occurrences tests.make.test_render_product_colors -q > /private/tmp/render-assembly-placement-tests.log 2>&1
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 "$workshop_python" -c 'import sys,unittest;sys.path.insert(0,"src");unittest.main(module=None)' tests.make.test_render_assembly_placement tests.make.test_render_product_views tests.make.test_render_product_depth tests.make.test_render_product_transparency tests.make.test_render_product_state_opacity tests.make.test_render_review_depth tests.make.test_step_color -q > /private/tmp/render-assembly-regressions.log 2>&1
PYTHONPATH="$PWD/src:/private/tmp/workshop-usage-test-deps" PYTHONDONTWRITEBYTECODE=1 "$workshop_python" -B -m pytest -q tests/make/test_print_gate_reports.py
```

Renderer coverage passed 68 distinct tests (22 initial and 52 final, with six
repeated after test-only cleanup). The three real print-report tests passed:
thickness and overhang Markdown now carries the same computed `RESULT` as
stdout, without changing a measurement, threshold or exit code. Real B-rep
fixtures prove passing/failing verdict parity, repeated exact report bytes,
and existing finalizer acceptance/refusal of the corresponding reports.

At this checkpoint, the verifier's schema correction was **unapplied**. Automatic approval
review rejected the edit twice and then rejected staging a review-only patch
artifact, classifying it as a central acceptance-gate change requiring explicit
user approval. It specifically questioned the existing success phrase
`prints unsupported`, which the unchanged overhang producer uses when its
checks pass (meaning printing without supports). No rejected edit or substitute
acceptance path was executed. Two canonical schema-8 fixtures pass the existing
finalizer and reproduce the existing verifier's schema-7 refusal; 37 proposed
verifier regression cases remained untracked pending approval of that correction.

No Waterloo tool refresh or resume had occurred at this checkpoint. All six
older pilots remained paused, and no physical manufacture or publication was
claimed. The source renderer/report corrections alone do not resolve the
remaining verifier incompatibility.

The approved renderer/report source tree was resealed independently with CAD
digest `ffef87a827ceee75071ff1d1838782986c48de51e546b444c163a7c026c96ec2`.
The following 16 skill-registry checks passed; they do not include or imply
approval of the still-proposed verifier correction:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/src" "$workshop_python" -m unittest tests.make.test_skill_registry -q
```

### Authorized verifier correction and continuation

The operator explicitly instructed the builder to complete the work and decide
the necessary actions, in direct response to the specific verifier-correction
approval request. The same `apply_patch` mechanism then accepted the prepared
correction; no alternate acceptance or editing path was used.

The final CAD verifier now requires canonical schema 8, including exact hashes
of its cited passing thickness/overhang reports. Existing engineering checks,
nozzle selection, review findings and image hashes remain intact. Its SHA-256
is `aa9883fb9909d8cfb9b57fd0f656960a001080b3dca7863c8b116ca7a06b0067`.
The combined CAD tree is resealed as
`3164af81305ca229302abcaf73e2360f576b8fd59071f88e72d07034cd97977d`.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/src:/private/tmp/workshop-usage-test-deps" "$workshop_python" -m pytest tests/make/test_verify_project_review.py tests/make/test_verify_project_cache.py tests/make/test_verify_project_documented_entries.py tests/make/test_verify_project_audits.py tests/make/test_native_cad_gate.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/src" "$workshop_python" src/workshop/make/skills/cad/scripts/verify_project --self-check
```

All 94 focused tests passed, including the 37 shared-contract/failure cases;
the verifier self-check passed. Independent source review found no blocker.
The previously blocked schema correction is now implemented, rather than a
waiver or a plan to switch review files between checks.

The refreshed tree also passed all 16 skill-registry checks. Commit `66046964`
contains the verifier correction, tests and exact tool fingerprint. At
**2026-09-11 05:27:11 UTC**, the ordinary CLI resumed Waterloo:

```sh
PYTHONPATH="$PWD/src" "$workshop_python" -m cli resume wish-20260911-023805-fe157910 --refresh-tools
PYTHONPATH="$PWD/src" "$workshop_python" -m cli status wish-20260911-023805-fe157910 --json
```

The host refreshed six files: `check_overhang`, `check_thickness`,
`render_assembly.py`, `render_product`, `render_review` and `verify_project`.
It rebound the instruction digest through the normal journaled correction and
resumed root `01a08e54-55f5-7a93-aa25-872ffc105b3a`. Status confirmed active Make,
Spark, mixed materials, `gpt-6-astra`, medium effort and the original 500M cap.
Observed prior usage stayed exactly 32,866,528 tokens; the in-flight resumed
request was not counted as completed usage. No new Wish, native root, separate
Release turn, manual review waiver or physical operation was introduced.
All six earlier pilots remain paused. Publication is still pending.

### First complete Waterloo preview after correction

Make round 3 passed thickness and overhang for all 11 printed families (22
passing reports). The native Manager's full-scene review renderer completed in
418.8 seconds with exit 0 and produced front, top and isometric PNGs. Its round
summary records `checks_ok: true`; Manager visual feedback is still pending at
this checkpoint. These are digital engineering and appearance results, not
physical print or play evidence. Final review, verification and publication
remain required.

While that render ran, the builder added flushed CLI-only renderer phase
diagnostics to source. They distinguish source building, tessellation and each
view's raster/save in timeout logs without changing stdout paths, PNG bytes,
geometry or timeouts. The successfully running product keeps its frozen tools;
it was not restarted solely to receive diagnostics.

```sh
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 "$workshop_python" -c 'import sys,unittest;sys.path.insert(0,"src");unittest.main(module=None)' tests.make.test_render_review_progress tests.make.test_render_review_occurrences tests.make.test_render_review_depth tests.make.test_render_assembly_placement -q > /private/tmp/render-review-progress-tests.log 2>&1
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/src" "$workshop_python" -m unittest tests.make.test_skill_registry -q
```

All 23 focused renderer tests passed, including real timeout-log retention,
failure propagation and exact output compatibility. The diagnostic source tree
is sealed with CAD digest
`796a9c0c5d7d61c6c9f8a877c1670d745b0bfb4ae573b4df7b3c11750d2d83f1`.

### Refined miniatures and native-turn recovery

The Manager's round-3 visual feedback required earth-colored courtyard finishes
and less blocklike figures. Theo supplied a bounded refinement of coats, limbs,
headgear, muskets, horses and the cannon carriage. Round 4 regenerated all 11
printed families; all six revised miniature families passed fresh thickness and
overhang checks, with the five unchanged landmark results reused under the
existing exact-source rules. Its summary records `checks_ok: true`.

The round-4 visual render failed after 94.7 seconds while the product's paint
source fused finish surfaces: `ValueError: Null TopoDS_Shape object`. No images
were produced. This is a product-source Boolean failure, not passing visual
evidence. The native turn subsequently ended at **06:06:54 UTC** with the host's
structured `unclassified` failed-turn diagnostic. The checkpoint preserved
**52,676,941 / 500,000,000 tokens** and the original root session.

After the operator reiterated continuation, the builder resumed normally at
**2026-09-11 08:12:25 UTC**:

```sh
PYTHONPATH="$PWD/src" "$workshop_python" -m cli status wish-20260911-023805-fe157910 --json
PYTHONPATH="$PWD/src" "$workshop_python" -m cli resume wish-20260911-023805-fe157910 --refresh-tools
```

Exactly one frozen file changed: `render_review` received the already tested
phase diagnostics from commit `a0004a88`. The same Manager owns the finish
repair, new visual evidence and finalization. Profile, original Wish, budget,
credential isolation and publication requirements remain intact. No older pilot
was resumed, and no product CAD was edited by the repository builder.

### Painted printed units: representation compatibility

Waterloo's resumed Manager repaired individual coating builds, then found more
Boolean failures when those coatings were built in the complete scene. Round 5
still had passing print checks but failed visual source construction after
121 seconds at `substrate subtraction 'metal'`. The new renderer diagnostics
correctly identified `source-load-build` as the failed phase. The Manager
continued its own repairs into round 6; no successful revised preview or final
review is claimed at this checkpoint.

A source audit found a separate representation gap. CAD's `organic-lofts`
reference already supports one fused production part displayed as several
disjoint colored regions, while mixed-material physical-unit grouping accepted
only purchased components. The builder added the corresponding narrow printed
unit binding: grouped `3d-print` components require `production_part` paths to
one explicit printable source and its generated sibling STEP, both hash-bound
in the same component's private files. Existing hierarchy, quantity, ownership,
print selection and publication checks remain intact. Paint is a finishing
consumable, not a requirement to construct thin coating solids.

```sh
PYTHONPATH=/Users/ab/code/autonomous-workshop/.venv/lib/python3.11/site-packages "$workshop_python" -c 'import sys, unittest; from pathlib import Path; sys.path.insert(0, str(Path.cwd() / "src")); unittest.main(module=None, argv=["unittest", "tests.make.test_manufacturing_manifest", "tests.workflow.test_stage_proposal_tool"])'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/src" "$workshop_python" -m unittest tests.make.test_skill_registry -q
```

All 110 manifest/finalizer tests passed in 11.493 seconds, including 15 new
grouped-print contract tests. Their synthetic source deliberately cannot run;
the tests prove structural behavior, not geometry equivalence. Test output was
captured by the CLI tool session; no separate logfile was retained. Independent
review found no blocker, and all 16 registry tests passed after resealing the
mixed-materials tree as
`6ff491de31d4b7dc280e2ce939bd7a6d023a376433f50d2ebb73aaea636aff81`.
The active toy has not yet received this optional capability; its current
round continues with its existing frozen tools.

### Applying the grouped-print correction after repeated coating failure

Round 6 again passed its print checks but failed complete-scene construction
at `substrate subtraction 'metal'`, after 132.7 seconds. The Manager saved
another repair and began round 7; the builder's ordinary interrupt arrived
during its early regeneration. The verified Waterloo CLI host's PID, creation
time and exact resume/run arguments were checked first. The host reaped its
native process session and exited 130 at
**08:44:47 UTC**. Status retained the original checkpoint, root and
**64,444,370 / 500,000,000 tokens**.

```sh
"$workshop_python" - <<'PY'
import psutil, signal
p = psutil.Process(40446)
a = p.cmdline()
assert p.create_time() == 1789114344.342091
assert 'wish-20260911-023805-fe157910' in a and 'resume' in a and 'cli' in a and '-m' in a
p.send_signal(signal.SIGINT)
print('Sent normal interrupt to verified Waterloo CLI host 40446.')
PY
PYTHONPATH="$PWD/src" "$workshop_python" -m cli status wish-20260911-023805-fe157910 --json
PYTHONPATH="$PWD/src" "$workshop_python" -m cli resume wish-20260911-023805-fe157910 --refresh-tools
```

This historical command performed the equivalent of Ctrl-C after checking the
live process identity; its PID and creation time are not reusable instructions.
At **2026-09-11 08:45:26 UTC**, normal resume refreshed exactly three
mixed-material files: `SKILL.md`, `references/manifest.md`, and
`scripts/manufacturing_manifest.py`. The optional grouped-print contract from
`6d9ca74f` is now available to the same native Manager, which owns any product
representation change and all new evidence. The builder did not edit product
geometry or inject a stage proposal. All six earlier pilots remain paused.
The Manager reconciled interrupted round 7 and started round 8 from its saved
coating repair. Availability of the new grouping option does not mean the toy
has adopted it; its representation remains the native Manager's decision.

At the operator's request, the latest successful full-product preview was
opened with:

```sh
open -a Preview '/Users/ab/Library/Application Support/Autonomous Workshop/runs/wish-20260911-023805-fe157910/workspace/artifacts/make/r0001/product/cad/measure/rounds/r0003/visual/iso.png'
```

This image predates the refined figures; later full-scene renders had not yet
succeeded. It is not final reviewed appearance or publication evidence.

### Explicit native handoff of refreshed guidance

The resumed Manager continued its saved coating repair before reading the new
mixed-material guidance. A source audit found that `resume --refresh-tools`
printed changed paths to the operator but did not include them in the native
resume prompt. Updated hashes alone did not tell the Manager which guidance
to reopen. The builder added a bounded notice derived from the latest completed
refresh record and current input manifest. It names exact relative paths and
hashes/removals, asks for changed guidance to be reread when necessary, and
preserves the same Wish, session, Goal, skill deferrals and gates.

The notice writes no acknowledgement, starts no model session and exposes no
private ledger contents, reasons or source-file contents. Interrupted native
continuations receive it again. No-refresh runs keep the existing prompt.
This change handles completed recorded refreshes; it does not reconstruct the
existing crash gap before a refresh's correction record is appended.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/src:/private/tmp/workshop-usage-test-deps" "$workshop_python" -m pytest tests/workflow/test_tool_refresh_notice.py tests/workflow/test_native_host.py tests/workflow/test_make_mode.py tests/workflow/test_token_budget.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/src:/private/tmp/workshop-usage-test-deps" "$workshop_python" -m pytest tests/workflow/test_native_host.py::NativeHostTest::test_wish_runs_vault_bypassed_with_real_config_and_transport -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/src:/private/tmp/workshop-usage-test-deps" "$workshop_python" -m pytest tests/workflow/test_tool_refresh_notice.py -q
```

The initial combined run passed 215 cases; one existing loopback transport case
was denied a localhost bind by the sandbox and passed separately with the
appropriate permission. Independent review caught a skill-name compatibility
edge; the reader now uses the existing host grammar, and all 41 final notice
cases passed. In total, 179 existing and 41 final notice cases passed. No
persistent test logs were retained.

A read-only check against Waterloo's saved state produced the exact notice for
its three files refreshed at 08:45, with notice SHA-256
`fb862fb8d1aaf8bef39ca751beb9dd40d12ae03ea00219e0482cb37a12ceeb89`.
This check did not resume or mutate the toy. The currently running CLI retains
its loaded host code; the notice will be delivered on its next ordinary resume.

### Revised full scene and large-assembly corrections

The interrupted round directory was reused as round 7 despite the Manager's
`r8-round.log` filename. That attempt failed on an artillery coating Boolean.
The next completed attempt is the actual **round 8**. At **09:07:31 UTC**, its
complete source-built render succeeded: 862 occurrences, 1,184,865 vertices and
825,674 triangles. Rendering took 854.3 seconds: source build 180.316 seconds,
tessellation 592.993 seconds, and the three raster/save phases approximately
81 seconds. All 11 printed families had passing round checks, using fresh
artillery evidence and exact-source reuse for unchanged families. Visual
feedback, final verification and publication had not yet completed.

The revised latest preview was opened with:

```sh
open -a Preview '/Users/ab/Library/Application Support/Autonomous Workshop/runs/wish-20260911-023805-fe157910/workspace/artifacts/make/r0001/product/cad/measure/rounds/r0008/visual/iso.png'
```

The Manager then exported a miniature close-up STEP. Its source rendering had
worked, but a face lacked triangulation after STEP round-trip. The Manager is
repairing that product defect; the builder did not execute or alter toy CAD.
No successful final STEP verification is claimed from the source render.

Two separately reviewed source corrections address large assemblies. Geometry
lists now allow 4,096 instances and the optional hierarchy 8,192 nodes, while
BOM definitions and other lists retain 512. JSON/file byte limits, depth,
coverage, quantities, source identity and privacy checks remain unchanged. A
read-only inspection found even the earlier Waterloo descriptor had 730 leaves,
so the former 512-instance cap would reject this small-BOM scene.

The renderer now extracts the same native triangulations with indexed triangle
access and native point coordinates. It retains exact arrays and PNG bytes,
with no new cache, omitted faces or tolerance changes. Missing triangulation
continues to fail. A synthetic 16-instance curved fixture measured 1.071 seconds
before and 0.236 seconds after; this is not a Waterloo performance measurement.

```sh
PYTHONPATH=/Users/ab/code/autonomous-workshop/.venv/lib/python3.11/site-packages "$workshop_python" -c 'import sys, unittest; from pathlib import Path; sys.path.insert(0, str(Path.cwd() / "src")); unittest.main(module=None, argv=["unittest", "tests.make.test_manufacturing_manifest", "tests.workflow.test_stage_proposal_tool"])' > /private/tmp/workshop-mixed-material-geometry-limits-tests.log 2>&1
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 "$workshop_python" -c 'import sys,unittest;sys.path.insert(0,"src");unittest.main(module=None)' tests.make.test_render_tessellation tests.make.test_render_review_occurrences tests.make.test_render_assembly_placement -q > /private/tmp/render-tessellation-parity-tests.log 2>&1
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 "$workshop_python" -c 'import sys,unittest;sys.path.insert(0,"src");unittest.main(module=None)' tests.make.test_render_review_progress tests.make.test_render_review_depth tests.make.test_render_product_colors tests.make.test_render_product_depth tests.make.test_render_product_views tests.make.test_render_product_transparency tests.make.test_render_product_state_opacity tests.make.test_step_color -q > /private/tmp/render-tessellation-regression-tests.log 2>&1
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 "$workshop_python" /private/tmp/renderer-tessellation-implemented-benchmark.py > /private/tmp/renderer-tessellation-implemented-benchmark.jsonl
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/src" "$workshop_python" -m unittest tests.make.test_skill_registry -q
```

The manifest/finalizer suite passed 124 cases; renderer suites passed 77 cases;
all 16 registry checks passed after sealing. Independent review found no
blocker. The corrected CAD tree is
`820690202cee050ce2c88e5a26769ed82d94744ccf44d569ca9b6730db830acd`
and mixed-materials is
`c3c659db1966d04942d2b227db2e4c68a604a6efb0b0c0cf55426068aa8541f4`.
These source updates do not change the active run before a normal tool refresh.

### Applying the large-assembly tools

The native Manager stopped its redundant round-9 job while diagnosing the STEP
face. The builder then used a normal interrupt on the verified CLI host. It
exited 130 at **09:24:40 UTC**, preserving **72,836,834 / 500,000,000 tokens**.

```sh
"$workshop_python" - <<'PY'
import psutil, signal
p = psutil.Process(82101)
a = p.cmdline()
assert p.create_time() == 1789116326.087766
assert all(v in a for v in ['wish-20260911-023805-fe157910', 'resume', 'cli', '-m'])
p.send_signal(signal.SIGINT)
print('Sent normal interrupt to verified Waterloo CLI host 82101.')
PY
PYTHONPATH="$PWD/src" "$workshop_python" -m cli status wish-20260911-023805-fe157910
PYTHONPATH="$PWD/src" "$workshop_python" -m cli resume wish-20260911-023805-fe157910 --refresh-tools
```

The PID command is historical, with a process-identity check, not a reusable
PID. At **09:24:54 UTC**, ordinary resume from `76022ab0` refreshed five files:
the two renderers, their new `render_tessellation.py` helper, mixed-material
manifest reference and validator. The same native session, Wish, Spark/mixed
route, Astra model, medium effort and 500M budget remain active. All earlier
pilots remain paused.

The native resume packet contained the explicit changed-path notice. At
**09:25:13 UTC**, the Manager reported that it would read the refreshed packet
and guidance before retesting the exact STEP failure. Delivery of guidance is
confirmed; a repaired STEP, final review and publication are still pending.

### Native repair clears the STEP blocker

At **09:29:47 UTC**, the Manager confirmed the refreshed renderer correctly
retained the old paint-film failure. It then adopted the grouped printed-unit
representation: internal colored regions of the unchanged fused production
parts, with physical-copy quantities preserved. Native checks on all six
miniature families found valid STEP round-trips, no pairwise region overlap,
successful rendering and volume differences below 0.000003 mm³, within the
recorded numerical comparison tolerance. These are digital geometry results.
The builder neither changed product CAD nor ran these product checks.

All 11 production families passed fresh canonical source print reports. At
**09:36:40 UTC**, the combined six-family colored close-up also rendered from
exported STEP. Its file was approximately 15.9 MB, versus approximately 79 MB
for the failed coating-based close-up. It was opened with:

```sh
open -a Preview '/Users/ab/Library/Application Support/Autonomous Workshop/runs/wish-20260911-023805-fe157910/workspace/artifacts/engineering/solid-color-detail/views/iso.png'
```

The previously interrupted round-9 directory was reused. Its complete render
succeeded at **09:40:25 UTC** in **74.5 seconds**, with 803 occurrences,
454,144 vertices and 387,539 triangles. Source build took 30.391 seconds,
tessellation 6.763 seconds, and the three raster/save phases 36.882 seconds.
Both representation and renderer changed since round 8; this is the observed
combined improvement, not an isolated renderer benchmark. Checks passed and
the fresh visual packet awaited Manager feedback at this checkpoint.

```sh
open -a Preview '/Users/ab/Library/Application Support/Autonomous Workshop/runs/wish-20260911-023805-fe157910/workspace/artifacts/make/r0001/product/cad/measure/rounds/r0009/visual/iso.png'
```

The actual generated assembly still requires final inspection, independent
review, final verification, manufacturing-package validation and authenticated
publication. Passing intermediate renders do not establish those outcomes.

### Publication-size preflight

Round 9's Manager visual feedback passed. Later preparation found label-height
and touching color-region defects under the stricter geometry checks, so the
Manager repaired those and started round 10. Its subsequent complete STEP
export succeeded, but read-only file inspection found 166,720,236 bytes. The
earlier export had been 186,505,213 bytes; neither fits current publication.

A source audit confirmed that this is not just the mixed manifest's 95 MiB
file bound. Make artifacts retain 95 MiB per file and 512 MiB total. Factory's
current canonical Pack is a 50 MiB ZIP stored without compression; the mixed
carrier includes all public paths plus exact root STEP and selected-hero
aliases. Thus public asset bytes plus STEP bytes plus hero bytes are already
a necessary lower bound before metadata and ZIP overhead. Merely fitting one
STEP below 95 MiB is insufficient.

The locally available backend source at clean revision `3142920c` also enforces
95 MiB per published imported file in both initial and version imports, with a
100 MiB uploaded-ZIP bound. Its documented reason is the existing remix/LFS
transport. The deployed revision was not verified. No backend changes, uploads,
limit increases, compressed-Pack substitution or private-asset exposure were
attempted. Current host readers also materialize several full byte copies;
larger transport would require coordinated contract and memory work.

Mixed-material guidance now asks native Make to measure these existing bounds
before final independent review, clearly distinguishing a lower-bound/headroom
check from exact host packaging or acceptance. This adds no gate or new limit
and preserves the full scene and required review. Independent review found no
issue in the text; all 16 registry checks passed after sealing.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/src" "$workshop_python" -m unittest tests.make.test_skill_registry -q
```

The mixed-materials guidance hash is
`869d18140bd2002b1530d5c59e693ac1d8a934ecb2bedd2451a4f36ae3ac80a8`.
The native run retains its previous text until an ordinary explicit refresh.
An independent synthetic investigation is checking topology reuse for repeated
assembly instances; no safe product-size reduction is claimed from that study.

### Separate compressed carrier for new mixed imports

The native Manager independently found nested placement copies and changed its
authored assembly to share geometry within each family/color definition. The
next full STEP was 57,452,800 bytes, below the backend's per-file limit but too
large for the stored carrier. Native geometry, color and placement checks still
apply to that authored change; no automatic geometry deduplication was added to
Workshop.

The builder implemented a separate host `factory-mixed-deflate-v1` carrier for
new mixed Make-output imports. It preserves every public file and exact STEP
and hero aliases, with the existing 50 MiB compressed, 95 MiB member and 512 MiB
expanded bounds. Canonical Packs and print transport remain stored ZIPs. The
backend's existing ZIP reader supports this compression, so no backend change
or larger limit is required; deployment was not independently verified.

Before preparing an import intent, the host atomically saves the first exact
validated ZIP in private state with mode 0600 under a 0700 directory. Current
handoff inventory, ZIP hash, expanded artifact hash and explicit codec identity
must match on reuse. This also preserves an orphan written before an intent.
Missing or changed bound files refuse rather than regenerate bytes. Existing
intents without a codec retain stored transport. Unknown outcomes retain normal
reconciliation. Fixed ZIP metadata and compression level are not a claim of
cross-zlib byte reproducibility.

```sh
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 "$workshop_python" -c 'import sys,unittest;sys.path.insert(0,"src");unittest.main(module=None)' tests.integrations.test_factory_carrier tests.artifacts.test_artifacts tests.artifacts.test_pack_plan -q > /private/tmp/factory-carrier-regressions.log 2>&1
PYTHONPATH="$PWD/src:/private/tmp/workshop-usage-test-deps" "$workshop_python" -m pytest tests/integrations/test_factory_mixed_carrier.py tests/integrations/test_factory.py tests/integrations/test_factory_carrier.py tests/artifacts/test_artifacts.py tests/artifacts/test_pack_plan.py -q > /private/tmp/workshop-mixed-factory-carrier-tests.log 2>&1
```

The first command passed 39 cases. The final combined suite passed 130 cases,
including those earlier cases, with independent review finding no blocker.
Coverage includes malformed/compression-bomb archives, exact privacy/alias
bindings, interrupted and completed effect states, altered valid DEFLATE bytes
with the same expanded inventory, stale handoffs, cache permissions and classic
stored compatibility. No live product packaging or upload was used as test
evidence. A read-only check found no existing Waterloo Factory effects ledger;
its running CLI still has the previous host code loaded.

The updated mixed guidance tree is
`c2915639bed988a87b8c98812469fae4aebbf40af54c0219ea56b6c34ad292be`.
The earlier stored-only lower-bound guidance is superseded for new compressed
mixed imports; it remains applicable to stored carriers.

### Final review and interrupted verification

At 10:22:20 UTC the independent visual review passed without blocking defects.
The sealed schema-8 review hash is
`d7588a10d354b3fe5827719511152347b72904684fb500f73c140410bbce7296`.
The Manager's explicit colored solids preserve appearance; the full STEP is
59,453,359 bytes. Physical printing, assembly and play remain untested.

Integrated verification stopped in preflight at 10:25:33 UTC: all 11 printed
entries fit the declared 220 × 220 mm bed, but the product-specific fit audit
was missing and two `2mm` dimensions lacked confidence tags. Expensive final
checks did not start. Native turns reported unclassified terminal failures at
10:27:07, 10:54:07 and 12:07:07 UTC. No cause has been established. The earlier
structured diagnosis showed no host timeout or exhausted token allowance.

After committing the compressed carrier as `b996b70d`, ordinary plain resumes
loaded the new host code while preserving reviewed assets and frozen Make tools:

```sh
PYTHONPATH="$PWD/src" "$workshop_python" -m cli resume wish-20260911-023805-fe157910
```

This exact command resumed at 10:48:33 UTC (after an automatic approval-review
timeout and a successful allowed retry) and again at 11:55:28 UTC. Both kept
the same native session, Wish, medium effort and 500M-token allowance. Neither
completed Make or published the product. Observed usage before the latter was
101,974,575 tokens. Source documentation apply_patch calls also encountered
two approval-review timeouts; no rejection reason was returned.

### Compound STEP color interoperability

The source writer repeats uniformly colored Compound leaves' existing RGBA on
unlocated faces, with edge fallback. Valid solid styles had been missed by the
installed build123d reader. Geometry, hierarchy, alpha and same-color definition
sharing are preserved. Different colors sharing one native definition remain
a separate limitation. Waterloo already uses its Manager's explicit-solid
workaround; its reviewed tools are intentionally not refreshed for this fix.

```sh
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 "$workshop_python" -c 'import sys,unittest;sys.path.insert(0,"src");unittest.main(module=None)' tests.make.test_step_compound_color tests.make.test_render_product_colors tests.make.test_render_review_occurrences tests.make.test_assembly_package -q > /private/tmp/step-compound-color-tests.log 2>&1
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 "$workshop_python" -c 'import sys,unittest;sys.path.insert(0,"src");unittest.main(module=None)' tests.make.test_step_color tests.make.test_step_canonical tests.make.test_render_product_transparency tests.make.test_render_product_state_opacity tests.make.test_render_assembly_placement tests.make.test_render_tessellation -q > /private/tmp/step-compound-color-render-regressions.log 2>&1
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/src" "$workshop_python" -m unittest tests.make.test_skill_registry -q
```

These suites passed 28, 48 and 16 tests respectively. Independent review found
no blocker. Source CAD hash:
`fff03a811e9dc5b4cee544b47c55331f9dc17ac9e46b9f28749c8d5717a690a4`.
The product retains
`820690202cee050ce2c88e5a26769ed82d94744ccf44d569ca9b6730db830acd`.

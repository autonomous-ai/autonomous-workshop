# Mixed-material Spark CLI pilot record

The operator requested six original capability pilots, all launched through
the ordinary CLI with Spark, Codex Astra, ultra reasoning, and a **100,000,000
token total allowance per product**, including native children and resumes.
This is a limit, not a target to spend. No Daydream, Forge or Quest is used.

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

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

- `doctor`: ready; Codex signed in, 16 inventor bundles validated, nine domain
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
- The full installed-wheel smoke has not run: the dependency environment lacks
  the pinned build backend. Source CLI and materialization checks pass.

## Runs

Pending launch after the first implementation's targeted checks. Add actual
product ids, source revision, status, commands and observed defects here; no
launch or success is implied by the command list above.

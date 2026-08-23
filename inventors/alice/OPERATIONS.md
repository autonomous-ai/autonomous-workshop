# Operating Alice

Alice is a supervised queue worker, not an immortal chat session. Durable state
lives in SQLite and immutable artifacts; the process may be restarted at any
time. Task leases and fencing protect crash recovery, while the supported
launchd deployment deliberately holds a singleton lock so only one local
worker can claim effects at a time.

## Activation levels

| Level | What runs | What cannot happen |
|---|---|---|
| `dry-run` | Scheduling, research, invention, rules, simulation, evaluation plumbing, and recovery | CAD/printing, private drafts, release packets, public publishing, or fulfillment |
| `draft` | The above plus configured CAD/DFM, deterministic text2game-to-Vibe export, the existing private rich-draft operator, prototype printing, and production validation | Any public listing or order fulfillment; Dee reviews and publishes the finished draft with one click |
| `live` | The complete evidence-gated path, existing Vibe public flip/page readback, and one packet-bound print/QA/ship flow per paid order | Any effect whose adapter, credential, capability, price, packet, SKU, revision, or receipt check is missing |

The checked-in default is `dry-run` with a deterministic fixture provider. The
fixture proves scheduling and recovery only; it cannot create a candidate or
external evidence.

## Current activation status

The checked-in repository is **not operational yet**. No launchd service has
been installed and Alice has not created a real Shop Door draft. It contains no
production token, external evidence command, or operational
order/print/QA/ship adapter; its dedicated Codex home is not authenticated; the
connected text2game adapter is disabled and its external CAD/slicer/calibration
prerequisites have not been staged; and the current Shop Door deployment does not
advertise the three atomic public-write contracts required by Alice.
`alice doctor` therefore refuses `draft` while its invention, evidence, CAD,
printing, rich-draft, or authenticated readback dependencies are absent. The
missing public-write contracts block `live`, not the private-draft milestone.
The Vibe adapter makes zero public POSTs unless
revision/packet, SKU/price/currency, and rich-page bindings can all be proved.

The current activation target is `draft`: automatically create the complete
private Shop Door product page and stop. Dee reviews it and uses the existing
one-click publish control. The checked-in default keeps
`auto_publish_when_eligible=false`; do not change that value as part of draft
activation.

Going from reviewed drafts to automatic public release later requires three
separate operator actions:

1. authenticate Alice's dedicated model seat and configure every real evidence
   and Shop Door adapter;
2. deploy a backend publish contract that advertises
   `packet_hash_bound_publish`, `sku_currency_bound_publish`, and
   `rich_page_bound_publish`; atomically rejects a stale history/project or an
   incomplete rich page; applies the reviewed SKU, price, and USD currency; and
   echoes every accepted history/project/packet/policy/listing binding; and
3. rerun `alice doctor` in `live` mode and retain its successful readiness
   report with the deployment record.

The backend change alters the production publish boundary and requires explicit
owner authorization and its own reviewed deployment. Do not bypass the failed
capability check or treat the local draft patch as deployed behavior.

## One-time model-seat setup

Production thinking uses Alice's `CodexAppServerProvider`. It deliberately
refuses the operator's normal `~/.codex` home and never copies its token. Give
Alice a dedicated home and authenticate that home once:

```bash
cd inventors/alice
CODEX_HOME="$PWD/var/codex-home" /absolute/path/to/codex login --device-auth
CODEX_HOME="$PWD/var/codex-home" /absolute/path/to/codex login status
```

Run with:

```bash
ALICE_AGENT_PROVIDER=codex \
ALICE_CODEX_BINARY=/absolute/path/to/codex \
alice doctor

ALICE_AGENT_PROVIDER=codex \
ALICE_CODEX_BINARY=/absolute/path/to/codex \
alice run
```

Every task starts a fresh ephemeral app-server process in a new process group.
Alice rewrites only the dedicated home's `config.toml` to a pinned deny-all,
read-only profile; tools, plugins, MCP servers, apps, browser control, nested
agents, skills, hooks, approvals, and machine context are disabled. Responses
must pass a strict JSON transport envelope. Timeouts terminate and then kill
the complete process group. A separate lease heartbeat keeps ownership valid
during long calls.

## Initialize and verify

```bash
alice init
alice learning-init
alice eval
alice verify-ledger
alice doctor
alice status
```

`doctor` distinguishes a runnable dry-run thinking loop from effect readiness.
The fixture is dry-run-only. In `draft` or `live`, the model provider and every
required adapter must return authenticated diagnostics under the exact contract
version Alice expects. A configured executable, token name, or adapter object
is not a successful diagnostic. Missing commerce adapters do not create a
stream of failed order-poll tasks; paid-order polling is live-only and the order
loop remains dormant until both order and print-fulfillment boundaries pass
their diagnostics.

## Always-on macOS service

The supported local deployment is one launchd worker plus an independent
watchdog. Each tick runs in a fresh bounded process group. The service writes a
private heartbeat, pins the complete committed Alice source tree, the tracked
`workshop/src/inventor_workshop` package from the same repository, the resolved config,
and the release policy, and refuses a dirty Alice or Workshop checkout or a
changed runtime identity. Both Alice and Workshop are copied into one owner-only
execution snapshot; isolated children import from that snapshot rather than
the mutable editable install. Every sealed worker, doctor, guardian, and tick
interpreter starts with `-I -S`: Python site initialization and executable
`.pth` files are disabled before the bootstrap prepends the sealed source, so
an editable-install startup hook cannot pre-cache an unsealed package.
The watchdog checks that receipt independently and recovers only the exact
launchd label; it never trusts a PID stored in a health file.

Create an absolute, owner-only environment file and an absolute draft config,
then run the installer from a clean committed checkout:

```bash
python -m pip install -e ./workshop -e ./inventors/alice
```

The installer requires that Alice's virtual environment contain the declared
`inventor-workshop==0.3.0` distribution metadata and the statically
parsed `__version__` declaration from the explicit source tree; it fails before
touching launchd if the shared Workshop is absent or version-mismatched. It does not
import mutable Workshop code to perform that check. Preflight captures the explicit
Workshop checkout into the same runtime identity, and every worker identity
check hashes that mutable checkout while child execution imports only the
sealed copy. Changing Workshop therefore stops the installed worker until a new
verified service release and cannot alter an existing sealed child.

```bash
chmod 600 /secure/alice.env /secure/alice-draft.json
inventors/alice/ops/install.sh \
  --config /secure/alice-draft.json \
  --env-file /secure/alice.env \
  --root "$HOME/Library/Application Support/Autonomous/Alice" \
  --python /absolute/path/to/alice/.venv/bin/python
```

The installer runs preflight first, renders both launchd jobs without embedding
credential values, starts them transactionally, and waits for a fresh worker
and watchdog receipt. If that post-start check fails, it restores the prior
jobs while retaining Alice's durable state. `ops/status.sh` verifies both
labels and the current identity; `ops/uninstall.sh` removes the jobs but leaves
the database and receipts intact.

The installer does not use a fixed 30-minute task ceiling. It derives the
worker/watchdog `max_tick_seconds` floor from the resolved config. With
text2game enabled, that floor includes three complete
`adapters.text2game.timeout_seconds` windows, three orderly-shutdown windows,
and validation/export headroom; enabled page-builder and Vibe readback windows
are also considered. A supplied `--max-tick-seconds` may be longer, but preflight
rejects one below the derived floor. This prevents the supervisor from killing
a healthy multi-hour phase sequence and misclassifying it as an ambiguous
external effect.

Do not install the checked-in dry-run fixture as a production inventor. Draft
installation must first pass `alice doctor` with `draft_loop_ready=true`. A
first installation should still be exercised on a macOS staging account before
it is treated as unattended production.

## External adapters

Credentials belong to the narrow adapter process, never to a model prompt or
checked-in config. `agents.model_allowed_environment` is the model-only
allowlist. Each external command gets only its own entry under
`adapters.command_allowed_environment`; Alice rejects adapter-only environment
names that are also forwarded to the model. The built-in Vibe token is read by
the HTTP transport and is never forwarded to Codex or `publish.py`.

Command adapters receive one JSON object on stdin and return one receipt on
stdout. Before an adapter can unlock `draft` or `live`, `alice doctor` sends the
read-only operation `alice.adapter.diagnostics` with contract version
`alice.command-adapter.v1`. The returned, input-hash-bound receipt must identify
the adapter, repeat that exact version, and report `ready: true`,
`authenticated: true`, and its observed capability list. Diagnostics must not
create an order, print, draft, publication, shipment, or any other effect.
Nonzero command stderr is retained only as a SHA-256 digest in Alice's error.

For example, a CAD token can be exposed only to that command:

```json
{
  "agents": {
    "model_allowed_environment": ["PATH", "LANG", "LC_ALL", "TMPDIR"]
  },
  "adapters": {
    "command_allowed_environment": {
      "cad": ["PATH", "CAD_SERVICE_TOKEN"]
    }
  }
}
```

Required production boundaries are:

- licensed/local book access and cited source extraction;
- historical corpus retrieval;
- executable seeded digital playtesting;
- verified CAD/DFM and real printing;
- the existing Vibe publication/page-observer workflow;
- paid-order retrieval and print/QA/ship fulfillment.

Draft/live readiness also requires domain-specific readback capabilities rather
than a generic `ready` assertion: `licensed_source_readback`,
`cited_game_corpus_readback`, `independent_prior_art_search`,
`deterministic_rules_validation`, `seeded_executable_simulation`,
`authenticated_blind_human_readback`, `artifact_hash_readback`,
`authenticated_market_readback`, and
`authenticated_external_outcome_readback` on their corresponding adapters.

### Connected text2game CAD/DFM adapter

The text2game adapter is the built-in owner of `physical.cad`,
`physical.reconcile_cad`, and `physical.dfm` when enabled. It cannot be enabled
in `dry-run` and cannot coexist with `adapters.cad_command`. Use the same exact
Vibe workspace later configured for `page_builder`. The current reviewed source
pin is shown below; moving it is a code/review event, not a deployment tweak.

```json
{
  "runtime": {"effect_mode": "draft"},
  "adapters": {
    "text2game": {
      "enabled": true,
      "repo": "/srv/text2game",
      "commit": "0285137beedb4602f0cb06ebb18046ff018c41b6",
      "work_root": "/srv/alice-private/text2game-runs",
      "vibe_workspace": "/srv/vibe-ideas",
      "command": ["/srv/text2game-runtime/bin/python"],
      "text2cad_repo": "/srv/text2cad",
      "text2cad_commit": "fb9bc30e93afb4296693db58fb53cc1d66afeb1e",
      "cad_python": "/srv/text2cad/.venv/bin/python",
      "slicer_binary": "/absolute/path/to/prusa-slicer",
      "slicer_profile": "/secure/prusa-petg.ini",
      "codex_binary": "/absolute/path/to/codex",
      "codex_home": "/secure/alice-text2game-codex-home",
      "git_binary": "/usr/bin/git",
      "calibration_profile": "/secure/printer-calibration.json",
      "printer_target": {
        "profile_id": "factory-printer-petg",
        "profile_revision": 1,
        "printer_id": "printer-serial-or-asset-id",
        "nozzle_diameter_mm": 0.4,
        "layer_height_mm": 0.2,
        "material": "exact-material-specification"
      },
      "allowed_environment": [
        "PATH", "LANG", "LC_ALL", "TMPDIR", "BED_X", "BED_Y"
      ],
      "timeout_seconds": 7200,
      "max_output_bytes": 262144,
      "max_stderr_bytes": 262144,
      "shutdown_grace_seconds": 10
    }
  }
}
```

`command` is exactly one absolute interpreter path; Alice appends the copied
repo's `text2game`, slug, and one of `--phase 1`, `2`, or `3`. Wrappers, flags,
`--phase all`, `--force`, and `--run-full` are rejected. The source repo must be
a non-symlink, clean Git checkout at the exact 40-hex commit. For each durable
operation Alice copies only an explicit reviewed runtime allowlist into a
private directory; publishers and credential-like backups are excluded. It
stages the accepted rules/components/mechanisms, runs the pinned
deterministic consistency checker, and only then permits a model call. The
shared checkout and its `out/` remain untouched.

The upstream CAD half has real external prerequisites; a green Python unit test
does not install them:

1. Install `codex`, configure its exact absolute path as `codex_binary`, and
   authenticate only the dedicated `codex_home`. That directory must be owned
   by the service user with mode `0700`; its non-symlink `auth.json` must be a
   non-empty owner-only regular file. Alice calls the configured binary directly,
   injects both pinned paths, and forces all text2game jobs to Codex,
   `CODEX_SANDBOX=workspace-write`, and `CODEX_FALLBACK=0`; Claude is not a
   supported fallback for this adapter. The operation-local
   `~/.codex/auth.json` is only a non-secret compatibility marker for
   text2game's existence check; Alice never copies the dedicated home's real
   auth file into the CAD workspace.
2. Provide `text2cad_repo` as a clean, non-symlink checkout at the exact
   `text2cad_commit`. Alice copies only `gate.py` plus the reviewed
   `skills/cadcode` subtree; optional image/video helpers and every publisher or
   credential-like backup are excluded. The currently reviewed text2cad pin is
   `fb9bc30e93afb4296693db58fb53cc1d66afeb1e`. Configure `git_binary` as an
   exact absolute executable. Alice pins its bytes, disables replacement
   objects and ambient Git configuration, and verifies both selected source
   trees against their commits before and after each phase.

   Security follow-up: that historical text2cad pin tracks
   `.env.bak-pre-modelmix`. Alice's allowlist never reads or copies it, but the
   repository owners must remove it and rotate the Telegram, admin, MongoDB,
   and legacy backend credentials it contained before operational activation.
3. Install Pillow, CadQuery, trimesh, NumPy, and Matplotlib into the absolute
   `command` interpreter, because the pinned phase modules import them directly.
   Configure `cad_python` as the exact Python 3.12 CAD environment with the same
   CAD imports; the upstream CAD setup also uses `manifold3d`. Alice shadows
   upstream `uv run ...`, `python`, `python3`, and measurement calls with
   operation-local shims that execute this pinned interpreter, avoiding dynamic
   package resolution. The interpreter and shim bytes are rechecked.
4. Configure an exact PrusaSlicer-compatible `slicer_binary` and existing
   reviewed `slicer_profile`; both are pinned by path and bytes. `BED_X` and
   `BED_Y` must describe that printer. Optional render/video tools do not turn a
   missing required slice into a pass.
5. Provide an owner-only `alice.printer-calibration-profile.v1` JSON file. It
   must bind a measured printer id, material, nozzle, layer height, revision,
   evidence SHA-256, named assembled-fit clearances, and named print-in-place
   XY/Z/bottom-relief values. `printer_target` must match it exactly. Peter's
   example 0.4-mm numbers are not accepted as universal evidence.
6. Tool, repository, profile, and Codex-home locations belong in the explicit
   config fields, not ambient environment variables. Keep
   `adapters.text2game.allowed_environment` to the process basics and intentional
   non-secret dials such as `BED_X`/`BED_Y`, with their values in the owner-only
   service environment file. Publisher, MongoDB, GCS, Shop Door, Google
   credential, legacy backend, admin, Telegram, dynamic-loader, and Git-injection
   variables are rejected at this boundary. Text2game's `.env` and other
   credential-like files are never copied from the source checkout.

Before installation, use the pinned text2game `doctor.py --phase 2,3` as an
offline toolchain check in a disposable copy with the same service environment;
upstream `doctor.py` expects a local `.env`, so do not put that file or secrets
into Alice's pinned runtime tree. Then run
`alice --config /secure/alice-draft.json doctor`. Alice's diagnostic
independently checks the exact source/tool pins, interpreter,
calibration/target binding, private work root, Vibe workspace shape, and Codex
authentication. The first real CAD operation additionally runs the pinned
deterministic `consistency.py` over Alice's staged design before phase 1, so an
incompatible accepted game fails without spending a model call.

Passing these checks enables CAD/DFM work; it is not a print receipt, deployment
record, or Shop Door draft. Prototype/production, market, human-playtest, and
private-draft adapters must still pass their own readiness and evidence gates.

The existing board-game rich-page draft adapter and Vibe public adapter are
built in. The draft adapter points at one exact `vibe-ideas` production
checkout and invokes its existing operator; no page-generation command lives in
Alice. Enable it in `draft` or `live` with absolute paths:

```json
{
  "runtime": {"effect_mode": "draft"},
  "adapters": {
    "page_builder": {
      "enabled": true,
      "workspace": "/srv/vibe-ideas",
      "workspace_commit": "73d9bfdd85aa3c3ec2f51a7af3e20ac18676498d",
      "operator_command": [
        "/srv/vibe-ideas/.venv/bin/python",
        "/srv/vibe-ideas/board-game/tools/publish.py"
      ],
      "interpreter_sha256": "<reviewed-64-hex-interpreter-sha256>",
      "operator_sha256": "7815a40531ff09d5c301409a5d95651624970fb273ec5259426dcbed7258d118",
      "operator_dependency_sha256": {
        "animation_gate.py": "e405c259743f641bfbba60b46beddbdafe15e1a1d355a386ffcfc942efa860ea",
        "journal.py": "d747326b230f480d1254e22db9499e25e5400c8411b76a246f7bdfbb58a4d740",
        "telegram.py": "2947466e209e9d35ef6b3332365f6470a75f28c2cdad27a0227ef6a6d632b336"
      },
      "publishdesign_sha256": "<reviewed-64-hex-publishdesign-sha256>",
      "publishdesign_preflight_receipt": "/secure/publishdesign-preflight.json",
      "publishdesign_preflight_sha256": "<reviewed-64-hex-preflight-receipt-sha256>",
      "git_binary": "/usr/bin/git",
      "diagnostic_design_id": "an-existing-private-draft-id-or-slug",
      "diagnostic_owner_id": "the-exact-24-hex-owner-id",
      "allowed_project_hosts": ["the-exact-immutable-cdn-host.example"]
    }
  }
}
```

Replace all angle-bracketed SHA placeholders before loading this configuration;
they are intentionally invalid activation values. The operator command is
exactly those two absolute paths. Alice verifies the clean Git commit and every
configured digest, then internally supplies fixed isolated-Python flags.
Wrappers, caller-supplied flags, another `publish.py`, symlinked files, tracked
drift, hidden index flags, replacement refs, bytecode caches, and any unreviewed
file under `board-game/tools` are rejected. The sole allowed untracked tool is
the exact hash-pinned `board-game/tools/bin/publishdesign` binary.

The diagnostic design must already be a private draft owned by
`diagnostic_owner_id`, have a current history, have no published history, and be
readable through the authenticated owner API. It is a read-only authentication
probe, not the game being published. `WORKSHOP_SHOP_OWNER_ID` must match that owner.
Provide `WORKSHOP_SHOP_BACKEND_DIR` and `GOOGLE_APPLICATION_CREDENTIALS` explicitly in
the owner-only service environment; the backend `.env` and GCS credential JSON
must be owner-only regular files. A Vibe-workspace `.env` is forbidden, and
Telegram variables are forced empty. Artifact readback is anonymous but
restricted to the explicit HTTPS CDN host allowlist above; credentials,
redirects, query strings, and other hosts are rejected.

The production slug must satisfy one of two audited source contracts. An
ordinary Vibe workspace still requires `QUEUE.json` state `shipped`. An Alice
text2game export instead carries the static `alice-text2game-export-v1`
private-draft contract and explicitly neither requires nor mutates that legacy
pre-draft owner queue gate. In both cases `project/gate.json` passes, approved
covers exist, and `publishdesign` plus backend/GCS credentials are configured.
Alice never uses `--force`. The CAD and DFM adapters must both return the same
complete relative-path `artifact_hashes` map; text2game handoffs additionally
bind the original source map and the exact root `idea.json` bytes copied into
the project. Alice authenticates back to the private draft and downloads/hashes
those exact artifacts before any prototype or production run can start.

Before setting `enabled: true`, an accountable operator must run the exact
hash-pinned helper's documented `-dry-run` against the configured backend. It
must exercise a first import with a real nonempty project archive and at least
one cover. Its final helper JSON must report `dry_run: true`, `mode: import`,
the exact owner, `status: draft`, a normalized absolute archive path, positive
archive bytes, comma-delimited absolute cover paths, and nonempty owner name,
database, and bucket. A content-only or empty dry run does not prove the draft
writer. Alice does not run this credential-bearing Mongo/GCS probe
automatically; that execution requires separate approval. Canonicalize the
captured JSON with `alice.page_builder.build_publishdesign_preflight_receipt`,
write it as an owner-only regular file, and put that file's SHA-256 in
`publishdesign_preflight_sha256`. The receipt binds the Vibe commit, every
operator/helper hash, owner, backend path and config hashes, GCS credential
path/hash, and the full captured dry-run result. Alice revalidates it at
startup, in `doctor`, and immediately before the sender claim. A changed input
invalidates the receipt.

The supplied Vibe checkout currently has no compiled `publishdesign` or manual
preflight receipt, so draft readiness correctly remains false until the helper
is built, reviewed, hashed, dry-run by an accountable operator, and attested.

Enable the public Vibe adapter only in `live` and place the dedicated bearer
token only in the named environment variable:

```json
{
  "adapters": {
    "vibe": {"enabled": true}
  }
}
```

```bash
export WORKSHOP_SHOP_TOKEN='<dedicated Alice owner token>'
alice --config /secure/path/alice-live.json doctor
```

The default endpoint is
`https://panda-social-api.autonomous.ai/api/v1`, the shared origin used by the
current Vibe and public Shop Door routes. Never put the token in `live.json`.

An absent adapter is not evidence. Simulation cannot impersonate a blind human
table, a render cannot impersonate a print, and a model cannot impersonate an
order or shipment.

## Current reviewed-draft runbook

1. Run text2game's invention, rules, CAD, repair, render, and slice stages as
   separate gate-enforced phases. Do not use its legacy `publish.py` or treat
   `--phase all` as release evidence.
2. Export the accepted structured rules and exact verified artifacts into the
   Vibe board-game workspace. Verify the source commit and rule/CAD hashes; the
   exporter must not advance or claim the Vibe queue itself.
3. After Alice's actual gate accepts that workspace, use the audited
   `alice-text2game-export-v1` handoff to run the existing
   `vibe-ideas` rich-page operator through `ShopDoorAdapter`.
4. Alice authenticates back to the private design, verifies `status=draft`, the
   exact design/history/project/artifact hashes, and the complete rules, use
   case, story, specs, and covers.
5. Alice stops. Dee reviews that Shop Door draft and clicks the existing publish
   control. No Alice public POST is enabled in this mode.

## Future automatic publication runbook

This runbook is the intended procedure after the missing backend contract,
credentials, and real adapters are deployed. It is not evidence that the
current checkout can publish.

1. The release policy verifies held-out play, a real print, yield, safety/IP,
   economics, and equality of the reviewed and production packet hashes.
2. Before physical production, the rich-page adapter has already created a
   private draft through `vibe-ideas` `publish.py`, read it back, and verified
   the accepted files under its immutable project URL.
3. Alice records a publication intent before any public write.
4. The Vibe adapter publishes the already built Vibe design/history bound into
   that packet and supplies the reviewed SKU, price, and USD currency
   explicitly. The backend atomically verifies the exact rich-page/history/
   project precondition and echoes every binding. Alice never regenerates the
   product after physical validation.
5. A timeout, nonzero operator exit after launch, disconnect, or unverifiable
   receipt after a write is `ambiguous`; never retry it. Read
   remote state and reconcile the original operation.
6. The existing deployed observer may enrich the product page. Alice polls
   the anonymous Shop Door design record and verifies its listing, exact price,
   visuals, story, use case, print specifications, and assembly data.
7. Only a complete page receipt advances `publish_ready -> page_ready ->
   published`.

The sender does not generate a parallel set of copy, images, or videos.

## Human and physical gates

Alice can prepare blind-teach kits and observation forms, but the configured
`human_playtest` boundary must create the immutable PDF derived from the exact
accepted rules and perform an authenticated readback; a model-produced URL or
digest is not a kit receipt. A real independent operator must produce the
subsequent play receipt. Each human batch needs unique group, consent,
external-receipt, and trial identifiers; explicit independence flags; no
designer coaching; at least three independent groups; and at least two games
per group. Physical evidence must bind machine, material lot, canonical material
specification, print profile, per-set BOM/packing recipe, artifact hashes,
measured yield, defects, and QA to the exact candidate version.

## Future effect and fulfillment activation

There is currently no operational order reader, printer, QA, or shipping
adapter in this repository. Effectful CAD diagnostics must advertise
`idempotent_cad_by_operation_key` and `reconcile_cad_by_operation_key` in both
`draft` and `live`. The `print_fulfillment` diagnostic must likewise advertise
`idempotent_prototype_by_operation_key`,
`reconcile_prototype_by_operation_key`,
`idempotent_production_by_operation_key`, and
`reconcile_production_by_operation_key` in both modes, plus
`authenticated_manufacturing_readback` so a command envelope cannot substitute
for a real machine receipt.

Live order fulfillment adds another contract. The authenticated
`delivery` diagnostic must advertise `paid_order_readback`, and the
authenticated `print_fulfillment` diagnostic must advertise all of
`authenticated_manufacturing_readback`, `idempotent_print_by_operation_key`,
`reconcile_print_by_operation_key`, and
`reconcile_qa_ship_by_operation_key`. Alice derives `order_to_print_job` only
from those primitive contracts; neither configured commands nor a self-asserted
composite capability is sufficient. Every fulfillment intent supplies the
complete hash-verified manufacturing slice, and print/QA/shipment receipts must
echo it exactly. Each first-send and reconciliation request carries the durable
`effect_operation_key`, `task_input_sha256`, and an explicit `reconcile_only`
value.

## Recovery and incident rules

- Restart the worker normally. Expired leases return to the queue; fencing
  rejects stale completions.
- Run `alice verify-ledger` after a crash or before changing effect mode.
- Treat a broken event chain, changed immutable packet, lost publication lease,
  or mismatched remote price/hash as an incident. Stop live effects first.
- Never delete a failed attempt to make a metric look better.
- Back up the SQLite database and WAL as one unit. Learner state and retained
  receipts are already in that store. Secure deployment configuration and
  adapter-owned evidence files need their own access-controlled backup policy;
  the active CLI configuration has no generic artifact or outbox directory.

## Deployment shape

Run one job per process under a supervisor that restarts on failure, captures
logs, and sends a graceful termination before a hard kill. Deploy a new source
hash beside the old worker, confirm its health, then drain the old process; do
not let two deployments share an unfenced external operation. Production should
add log rotation, disk/memory alerts, database backups, and an alert for tasks
left `ambiguous` or candidates blocked at a real-world gate.

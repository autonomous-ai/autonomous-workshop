# Operating Alice

Alice is a supervised queue worker, not an immortal chat session. Durable state
lives in SQLite and immutable artifacts; the process may be restarted at any
time. Multiple workers can share the database because leases and fencing tokens
prevent two workers from committing the same task.

## Activation levels

| Level | What runs | What cannot happen |
|---|---|---|
| `dry-run` | Scheduling, research, invention, rules, simulation, evaluation plumbing, and recovery | CAD/printing, private drafts, release packets, public publishing, or fulfillment |
| `draft` | The above plus configured CAD/DFM, the existing private rich-draft operator, prototype printing, and production validation | Release authorization, a public listing, or order fulfillment |
| `live` | The complete evidence-gated path, existing Vibe public flip/page readback, and one packet-bound print/QA/ship flow per paid order | Any effect whose adapter, credential, capability, price, packet, SKU, revision, or receipt check is missing |

The checked-in default is `dry-run` with a deterministic fixture provider. The
fixture proves scheduling and recovery only; it cannot create a candidate or
external evidence.

## Current activation status

The checked-in repository is **not live**. It contains no production token,
external evidence command, or operational order/print/QA/ship adapter; its
dedicated Codex home is not authenticated; and the current Factory deployment
does not advertise the three atomic public-write contracts required by Alice.
`alice doctor` therefore refuses `draft` or `live` startup when those
dependencies are absent, and the Vibe adapter makes zero public POSTs unless
revision/packet, SKU/price/currency, and rich-page bindings can all be proved.

Going live requires three separate operator actions:

1. authenticate Alice's dedicated model seat and configure every real evidence
   and factory adapter;
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
cd alice
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
      "operator_command": [
        "/srv/vibe-ideas/.venv/bin/python",
        "/srv/vibe-ideas/board-game/tools/publish.py"
      ],
      "diagnostic_design_id": "an-existing-owner-only-design-id",
      "allowed_project_hosts": ["the-exact-immutable-cdn-host.example"]
    }
  }
}
```

The operator command is exactly those two absolute paths. Wrappers, interpreter
flags, extra arguments, another `publish.py`, and symlinked operator files are
rejected. The diagnostic design must already exist and be readable through the
authenticated owner API; it is a read-only authentication probe, not the game
being published. Artifact readback is anonymous but restricted to the explicit
HTTPS CDN host allowlist above; credentials, redirects, query strings, and
other hosts are rejected. The default operator environment omits Telegram
credentials.

The production slug must already satisfy that source pipeline's own contract:
its `QUEUE.json` state is `shipped`, `project/gate.json` passes, approved covers
exist, and `publishdesign` plus backend/GCS credentials are configured. Alice
never uses `--force`. The CAD and DFM adapters must both return the same
relative-path `artifact_hashes` map; `physical.cad` also returns the source
slug. Alice authenticates back to the private draft and downloads/hashes those
exact artifacts before any prototype or production run can start.

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
export ALICE_FACTORY_TOKEN='<dedicated Alice owner token>'
alice --config /secure/path/alice-live.json doctor
```

The default endpoint is
`https://panda-social-api.autonomous.ai/api/v1`, the shared origin used by the
current Vibe and public Factory routes. Never put the token in `live.json`.

An absent adapter is not evidence. Simulation cannot impersonate a blind human
table, a render cannot impersonate a print, and a model cannot impersonate an
order or shipment.

## Future live publication runbook

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
   the anonymous Factory design record and verifies its listing, exact price,
   visuals, story, use case, print specifications, and assembly data.
7. Only a complete page receipt advances `publish_ready -> page_ready ->
   published`.

The publisher does not generate a parallel set of copy, images, or videos.

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
`factory_order` diagnostic must advertise `paid_order_readback`, and the
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

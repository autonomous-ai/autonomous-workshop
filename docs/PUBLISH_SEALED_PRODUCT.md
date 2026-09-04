# Publish a terminal Release

Factory publication is the required host-effect portion of Release. Workshop
does not complete a run after merely creating local files: it completes only
after the exact ready-to-print CAD and canonical `MANUAL.pdf` are public and
authenticated readback proves their hashes.

Printing, packing, shipping, delivery, and customer Review begin after this
digital handoff and belong to Operations.

## What Release supplies

The native Manager writes `artifacts/release/package` with at least:

- canonical `MANUAL.pdf`, self-contained and ready to print for the box;
- canonical `product.json`, bound to the exact Made artifact and either Quest's
  passing Playtest evidence or Spark/Forge's explicit Playtest `not-run`
  omission; and
- evidence-derived claims, contents, limitations, and optional editable manual
  source or accessible text companions.

Release is one native Goal. The Manager reads the exact Made product and the
route's passing evidence or explicit omission, uses the materialized
`manual-design` skill, authors the guide, renders every page, inspects it at
print size and in grayscale, checks the copy against evidence, and improves
it. This design/review loop belongs to the native coding agent, not to a
Python aesthetic score.

The run-local finalizer hashes the package and writes the canonical Release
proposal. The trusted host rereads, structurally validates, rehashes, and seals
the PDF and package. It rejects encrypted or active-content PDFs, external
dependencies, unsafe page bounds, changed bytes, or missing meaningful text.
Parser success proves structure, not beauty, comprehension, physical safety,
or a successful print.

Before any Factory effect, the host also reruns the full-tier CAD gate on the
exact sealed Made revision. That gate must prove the production model and its
declared printable parts satisfy the current deterministic CAD, thickness, and
printability requirements. Release cannot substitute a preview mesh or
unverified export.

## One required publication step

Start or continue a run with the core CLI:

```bash
uv run workshop wish "I wish for ..."
uv run workshop resume <wish-id>
```

There is no `--publish` mode. Starting the Wish authorizes publication of that
run's exact Release bytes, while the host keeps credentials and effect state
outside the coding-agent session.

Once local validation passes, the host:

1. records a hash-bound Factory effect intent before network I/O;
2. imports the exact production CAD, `MANUAL.pdf`, and supported product facts;
3. promotes that same remote design publicly; and
4. completes Release only after authenticated readback and the public manual
   URL prove the exact sealed CAD and PDF hashes.

The Factory ZIP is a narrow production transport, not a mirror of the Made
engineering tree. For a mesh product it contains one validated primary model
and only the exact production parts and occurrence metadata supported by the
current contract. Alternate exports, play poses, slicer-project files, and
other redundant representations stay local so file-format duplication cannot
be mistaken for extra printable parts or fulfillment cost.

Factory's mutable category ordering is never trusted: the handoff explicitly
declares the canonical `toys` category, and authenticated readback must preserve
it.

## Credentials

Interactive users do not create Factory credentials by hand. The first
`workshop create inventor` or `workshop start <inventor-id>` opens
`https://www.autonomous.ai/toys/inventor/login`; `workshop login <inventor-id>`
reconnects explicitly. The trusted host writes the result to the matching
owner-only `$WORKSHOP_HOME/credentials/inventors/<inventor-id>.env` file and
loads it only when no native agent turn is running.

Never put credentials in a Wish, prompt, `TASTE.md`, product-run workspace,
Release package, source file, or commit. The coding-agent subprocess receives a
scrubbed environment. Ephemeral host environments and secret managers remain
supported for non-interactive and legacy deployments.

Each private file uses strict `NAME=raw-value` lines; it is not evaluated by a
shell, so literal surrounding single or double quotes are invalid. After the
user authorizes Workshop for the named Inventor, the website redirects only a
five-minute, single-use authorization code to the loopback callback. Workshop
proves its in-memory PKCE verifier directly to the Autonomous Toys API, which
returns `FACTORY_USERNAME` and `FACTORY_PASSWORD` exactly once to the CLI. The
publishing credential never enters browser JavaScript or a URL. The file also
stores `FACTORY_INVENTOR_ID`; a missing or mismatched binding is rejected before
Release.

For migration, exactly one legacy scoped username such as
`FACTORY_ALICE_USERNAME=alice` is temporarily accepted with
`FACTORY_PASSWORD`, but its variable name no longer grants or limits authority
to that Inventor. Multiple scoped usernames, or a generic and scoped username
together, are rejected as ambiguous. Rename the legacy key to
`FACTORY_USERNAME`.

`uv run workshop doctor` validates any legacy host-wide configuration without
printing a secret. `create` and `start` validate the selected Inventor's file
before using it. At import, the unchanged Factory session calls
`/auth/agent/login` with the stored pair, keeps the returned 365-day bearer in
memory, and retries that login once after a protected request returns `401`.
Authenticated owner ids and exact artifact hashes remain bound through import,
publication, reconciliation, and readback receipts. Missing or rejected
credentials leave Release waiting with a concrete need; they do not create a
successful private-only Release.

Factory displays the authorizing account as the public author. The actual
Inventor remains independently bound in the sealed product facts; it is not
inferred from the Factory login identity.

## Recovery

After a timeout, disconnect, or malformed Factory response, Workshop does not
blindly repeat the effect. The host loads the stored intent and exact Release
identity, authenticates, and reconciles remote state before any bounded retry.
If readback cannot prove completion or absence, Release stays fenced and
waiting for later authenticated reconciliation or human action.

An `unknown` or crash-left `sending` intent takes precedence over an older
verified-draft receipt in `workshop status`. A later `workshop resume` uses the
same idempotency identity and records success only when readback proves the
public result. Permanent contract and deterministic validation failures surface
as failures rather than becoming retry loops.

## Evidence and pricing boundaries

After the local package passes, the host may derive
`artifacts/release/VERIFICATION.json` as separate public-safe enrichment. Its
current **Digitally Verified** level binds exact digital checks; it is not the
receipt that completes publication and does not claim a physical print. A
future **Physically Verified** level requires a trusted Operations receipt that
proves the exact released bytes were built and checked. See
[Product verification](PRODUCT_VERIFICATION.md).

Workshop does not currently submit an explicit listing price or call Factory's
auto-listing value a fulfillment cost. An explicit price must wait for a
hash-bound quote tied to the exact design history. The required backend
contract is documented in
[Factory fulfillment quote contract](FACTORY_FULFILLMENT_QUOTE_CONTRACT.md).

A public Factory page proves the terminal digital handoff only. It does not
prove printing, manual insertion, QA, packing, shipment, delivery, or customer
response.

## Showcase products

Showcases use the same Wish pipeline; there is no separate builder or publisher:

```bash
uv run workshop wish "<showcase Wish>"
```

Never publish a checked-in fixture, old outbox, hand-authored receipt, or legacy
bundle as if it were the output of a current run.

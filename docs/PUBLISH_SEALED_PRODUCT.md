# Publish a sealed product

Factory publication is an optional host effect against an already accepted
Release. It is not product-run agent work and is not a prerequisite for
Deliver.

## What Release supplies

The native Codex session writes `artifacts/release/package` with at least:

- canonical `MANUAL.pdf`, self-contained and ready to print for the box;
- canonical `product.json` bound to the exact Made artifact and passing
  Playtest evidence; and
- evidence-derived claims, contents, limitations, and optional editable manual
  source or accessible text companions.

Release is one native Codex Goal. Codex reads the exact Made product and
passing evidence, uses the materialized `manual-design` skill, authors the
guide, renders every page, inspects it at print size and in grayscale, checks
the copy against evidence, and improves it. This design/review loop is native
Codex behavior, not a Python aesthetic score.

The run-local finalizer hashes the package and writes the canonical Release
contract. The trusted host rereads, structurally validates, rehashes, and seals
the PDF and package. It rejects encrypted or active-content PDFs, external
dependencies, unsafe page bounds, changed bytes, or missing meaningful text.
Parser success proves structure, not beauty, comprehension, physical safety,
or a successful print.

Local Release then advances to Deliver without contacting Factory. The package
must never contain credentials, remote receipts, or unsupported claims of
manufacture, physical performance, human response, publication, or delivery.

## Public verification

After Release succeeds, the host may derive
`artifacts/release/VERIFICATION.json` as separate, best-effort enrichment.
Codex does not author that file and it is not part of the authored package
manifest. Schema v1 truthfully emits only **Digitally Verified** and binds the
exact product, Playtest evidence, Release, and check hashes.

The full evidence tree and authenticated receipts remain private. If
verification generation fails or is missing, Release still succeeds and the
website shows no badge. A future **Physically Verified** level requires a
trusted receipt proving the exact released bytes were built and checked. See
[Product verification](PRODUCT_VERIFICATION.md).

## No publication by default

```bash
uv run workshop wish "I wish for ..."
```

This completes the local digital workflow without Factory credentials.
Publication status remains `not-created`; that is not a failure.

## Explicit public promotion

Use `--publish` only when a Factory listing is intended:

```bash
uv run workshop wish --publish "I wish for ..."
```

or record that prospective authority while resuming the same run:

```bash
uv run workshop resume --publish <wish-id>
```

When the adapter and credentials are available, the host transports the exact
sealed model, supported product facts, and `MANUAL.pdf`, reconciles private
readback, and promotes the same remote identity. Missing credentials or an
unavailable adapter leaves publication pending/not-created without invalidating
Release. The publication receipt stays in host-only state and binds exact
artifact hashes.

The Factory model ZIP is a narrow production transport, not a mirror of the
Made engineering tree. For a mesh product it contains one root viewer STL and,
when a validated occurrence family exists, only the required assembly STEP and
sidecar plus the exact declared production STLs. Alternate STEP/3MF exports,
play poses, slicer-project 3MFs, and other representations stay local. Factory's
fallback price estimator counts geometry basenames as printable parts, so
shipping those duplicates would turn file-format redundancy into a fictitious
fulfilment cost.

Workshop does not currently submit a price or claim that Factory's returned
listing price is unit cost. An explicit price must wait for a hash-bound cost
basis or authoritative Factory fulfilment quote; agent-authored prose, archive
size, and the number of CAD representations are not cost evidence.
The current Factory API has no such monetary response: its authenticated slice
endpoint binds real CuraEngine profile and material totals to a design history,
but does not return a quote or minimum price. The exact backend contract needed
before Workshop may submit a price is documented in
[Factory fulfillment quote contract](FACTORY_FULFILLMENT_QUOTE_CONTRACT.md).

For a PDF-first Release, authenticated Factory readback supplies the immutable
CDN `project_url` for that exact design history. The host derives only
`<project_url>MANUAL.pdf` on Factory's pinned public CDN, downloads it without a
bearer token, and requires its SHA-256 to equal the sealed Release manual before
accepting the private draft and again before and after public promotion. A
missing, redirected, oversized, or changed file leaves the optional publication
unverified; it never invalidates the local Release. Successful CLI/status output
includes the hash-verified manual URL so a browser can open the same bytes the
host checked.

## Credentials

Supply Factory credentials through the private
`$WORKSHOP_HOME/credentials/factory.env` file (preferred) or a supported
ephemeral host environment or secret manager. The trusted host loads them only
when no native agent turn is running. Never put credentials in a Wish, prompt,
`TASTE.md`, product-run workspace, Release package, source file, or commit. The
Codex subprocess gets a scrubbed environment.

## Recovery

After a timeout, disconnect, or malformed Factory response, do not blindly
repeat the effect. The host loads the stored intent and exact Release identity,
authenticates, and reconciles remote state before any bounded retry. If
readback cannot prove completion or absence, the remote effect remains fenced
for human reconciliation; the already sealed local Release remains valid.
An `unknown` or crash-left `sending` publication intent takes precedence over
an older verified-draft receipt in `workshop status`; status inspects the
private ledger without authenticating or mutating it. A later `resume` uses the
same idempotency identity and authenticated readback. It records proven public
completion, but a remaining draft does not prove that the ambiguous send never
happened and therefore cannot trigger a second publish call.

A private or public Factory page proves only remote page state. It does not
prove printing, manual insertion, QA, packing, shipment, delivery, or customer
response.

## Showcase products

Showcases use the same native Wish pipeline; there is no separate Python
showcase builder or publisher. Start a representative Wish and retain its ID:

```bash
uv run workshop wish --publish "<showcase Wish>"
```

The native session must complete Match, Invent, Make, Playtest, and local
Release from that Wish before any Factory effect. Never publish a checked-in
fixture, old outbox, hand-authored receipt, or legacy bundle as if it were the
output of a current run.

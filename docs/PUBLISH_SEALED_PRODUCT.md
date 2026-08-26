# Publish a sealed product

Factory publication is a host effect after Release, not product-run agent work.

## What Release supplies

The native Codex session writes a local factual package at
`artifacts/release/package` with at least:

- `MANUAL.md`;
- canonical `product.json` bound to the exact Made product and passing
  Playtest evidence;
- factual page metadata, attribution, limitations, and evidence-derived claims.

The run-local finalizer hashes the package and writes the canonical Release
contract. The host rereads and seals the whole tree before contacting Factory.
The package must not contain credentials, remote receipts, generated marketing
media, or claims that Factory enrichment already happened.

## Private by default

Start a normal private run with:

```bash
uv run workshop wish "I wish for ..."
```

If Factory authentication is configured, the host can import the validated
model/facts as a private draft and reconcile authenticated readback. Codex does
not see credentials or perform the import.

## Explicit public promotion

Use `--publish` only when a public Factory page is intended:

```bash
uv run workshop wish --publish "I wish for ..."
```

or record that prospective authority while resuming the same run:

```bash
uv run workshop resume --publish <wish-id>
```

The host still validates the exact Release package, performs/reconciles the
private import, and then promotes the verified remote product. The publication
receipt is stored in host-only state and bound to exact artifact hashes. It is
not written by Codex and is not accepted from `agent-outcome.json`.

## Credentials

Supply Factory credentials through the private
`$WORKSHOP_HOME/credentials/factory.env` file (preferred) or a supported
ephemeral host environment or secret manager. The trusted host loads the
private file only when no native agent turn is running. Never put credentials
in a Wish, prompt, `TASTE.md`, product-run
workspace, Release package, source file, or commit. The Codex subprocess gets a
scrubbed environment.

## Recovery

After a timeout, disconnect, or malformed Factory response, do not blindly
repeat the effect. `workshop resume <wish-id>` loads the stored intent and exact
Release identity, authenticates in the host, and reconciles remote state before
any bounded retry. If readback cannot prove completion or absence, the run
stops unknown/needs-human.

A private or public Factory page proves only that remote page state. It does
not prove printing, QA, packing, shipment, delivery, or customer response.

## Showcase products

Showcases use this same native Wish pipeline; there is no separate Python
showcase builder or publisher. Start a representative Wish and keep its Wish
id:

```bash
uv run workshop wish --publish "<showcase Wish>"
```

The native session must complete Match, Invent, Make, Playtest, and Release
from that Wish, and the host must verify the exact CAD, evidence, and package
bytes before performing Factory effects. Never publish a checked-in fixture,
old outbox, hand-authored receipt, or legacy paper bundle as if it were the
output of a current run. Documentation images and links are examples, not gate
evidence for a new product.

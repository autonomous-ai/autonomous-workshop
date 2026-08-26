# Publish a sealed product

Factory publication is a host effect after Release, not product-run agent work.

## What Release supplies

The native Codex session writes a complete schema-v3, page-ready package at
`artifacts/release/package` with at least:

- `MANUAL.md`;
- canonical `product.json` with `kind=workshop.release-package`,
  `status=page-ready`, and exact Made and passing-Playtest hashes;
- evidence-derived claims, `title`, `summary`, `hero`, `cinematic`, `use_case`,
  one or more `story_blocks`, `what_arrives`, and `limitations`. Every page
  section carries `headline`, `body`, `visual_direction`, and valid
  `evidence_refs`.

Release is one native Codex Goal whose stopping condition is a successful
Release finalizer for the current checkpoint. While pursuing it, Codex observes
the exact Made product and passing Playtest evidence, writes the manual and
complete product page, evaluates every claim and evidence reference against
exact hashes, and improves the package.

That fact-check/write/review loop is native Codex behavior, not Python.

The run-local finalizer hashes the package and writes the canonical Release
contract. After it succeeds, Codex completes the Goal and returns to the host.
The host rereads and seals the whole tree before contacting Factory. Codex owns
the complete page copy and visual direction; Factory transports the exact
sealed page, `MANUAL.md`, and model bytes without creative enrichment. After
private import, the host copies the exact compatible `use_case` and
`story_blocks` text through Factory's curated-content endpoints and requires
authenticated exact readback before optional publication. Factory currently
accepts 1–40 plain-text characters for each heading, 180–400 for each body,
and at most 10 story blocks; the handoff fails instead of truncating or
paraphrasing content outside those limits. The imported cover supplies the
required use-case image. Hero, cinematic, visual-direction, evidence-reference,
what-arrives, limitation, and manual presentation have no equivalent rich-page
fields today; their authoritative exact bytes remain in the downloadable
sealed project until Factory's page contract grows. The local package
must not contain credentials, remote receipts, images, audio, video, or
unsupported claims of manufacture, physical performance, human response,
publication, or delivery.

## Public verification

After the Release and any Factory effect succeed, the host may derive
`artifacts/release/VERIFICATION.json` as separate, best-effort public
enrichment. Codex does not author that file and it is not part of the
agent-authored package manifest. Schema v1 truthfully emits only **Digitally
Verified** and binds the exact product, Playtest evidence, Release,
`product.json`, check-configuration, and check-evidence hashes.

The full evidence tree and authenticated receipts remain private. A sanitized
public toy snapshot may copy the exact manifest as `VERIFICATION.json`, and the
website should render its badge and limitations directly from that source. If
generation fails or the file is missing or invalid, publication still succeeds
and the website shows “Verification not recorded.” See
[Product verification](PRODUCT_VERIFICATION.md) for the two-level contract.

## Private by default

Start a normal private run with:

```bash
uv run workshop wish "I wish for ..."
```

If Factory authentication is configured, the host can import the validated
model, manual, and page as a private draft, write the exact compatible rich
content, and reconcile authenticated readback. Codex does not see credentials
or perform the import.

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
Likewise, shipment or delivery is a separate fulfillment status: it does not
by itself raise Digitally Verified to Physically Verified.

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

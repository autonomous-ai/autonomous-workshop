# ADR 0051: Let a likeness Wish reach its reference images

- Status: Accepted
- Date: 2026-09-09
- Owners: Runtime and Make maintainers
- Relates to: ADR 0044 (scope component-CAD network access)
- Amends for new runs: ADR 0044's enumerated component domain map

## Context

ADR 0044 opened a `limited`-mode network proxy for exactly one workflow:
Step.parts component downloads and a reviewed set of supplier drawing hosts,
sixteen domains in total. It closed with a standing rule — *"The allowlist is
intentionally product-tool-specific. Adding another direct network integration
requires an explicit reviewed policy change."*

`references/visual-reference-inspection.md` added a second such integration
without one. It requires that a Wish naming an existing object be built from an
actually inspected reference image, and forbids substituting a text-derived
interpretation: *"Without a usable reference, request the missing reference
through the existing need path."* Nothing supplies that image.

A live Spark run on 2026-09-09 (`wish-20260909-071054-3ff90049`, "make a
millenium puzzle from yugioh") demonstrated the dead end. The agent's own
retrieval evidence records the attempts: web search worked, the manufacturer
page read as text, and `image_query` returned a working image URL together with
a written description. Every attempt to obtain the actual bytes failed —
`curl` to the manufacturer CDN returned *"domain is not on the allowlist for
the current sandbox mode"*, the web tool refused a direct image URL as *"not
safe to open"*, its cached fetch missed, and three alternate hosts returned
403 through the proxy. The run recorded a truthful need and stopped at Make.

Every one of those six URLs returns HTTP 200 with real `image/jpeg` bytes from
the same machine outside the sandbox. The images were available; the policy was
the only thing in the way. The same Wish had completed Make and reached Release
on 2026-09-08, before the reference requirement existed.

A description is not a substitute. The product that comes out of a text-derived
interpretation does not look like the named thing, which is the entire point of
a likeness Wish.

An enumerated host list cannot solve this. Reference images live on whichever
CDN a search happens to return — a manufacturer's Akamai host, a retailer's
Shopify CDN, a marketplace image server — and the set is not knowable in
advance.

## Decision

New Codex product runs keep `permissions.<profile>.network.mode="limited"` and
widen the domain map to `{"*"="allow"}`.

The containment that matters is unchanged, because it was never the domain map.
`limited` mode restricts methods to GET, HEAD and OPTIONS; Codex answers a POST
under it with *"Method not allowed in limited mode."* A wider map therefore
grants reads and no way to send anything out. This was verified directly, not
assumed: with the open map a GET of the manufacturer image returned 200 and
wrote 29,687 bytes, while a POST to a public echo endpoint returned 403 with
that exact message.

The filesystem profile is untouched and still bounds what a read can reach:
`:root` denied, every `**/.env*` denied, write confined to the run workspace,
and reads limited to the run's own files plus the interpreter and libraries it
executes. Factory and other effect credentials remain outside the Codex
subprocess, and the shell environment policy still excludes `OPENAI_*` and
`CODEX_API_KEY` from model-generated commands.

The former sixteen-domain map is preserved as
`_CODEX_COMPONENT_NETWORK_DOMAINS_BEFORE_REFERENCE_IMAGES`, and a new rollback
step reconstructs it for already-checkpointed sessions. Each rollback validates
the generation it rolls back *from*, so a resumed session can only step back
through generations that actually existed and never sideways into an arbitrary
domain map.

## Alternatives considered

### Switch the mode to `full`

Rejected. `NetworkMode` offers only `limited` and `full`, so dropping the
domain restriction that way would also drop the method restriction and grant
arbitrary POST. That is the one property worth keeping, and keeping it costs
nothing here.

### Enumerate image CDNs

Rejected. The hosts are whatever a search returns; the list would be wrong on
its first use.

### Require the operator to place images in the workspace

Retained as the fallback the contract already prefers, not as the answer. It
works and adds no egress, but it makes every likeness Wish wait on a human,
which defeats an autonomous run.

### Leave it and let likeness Wishes record a need

Rejected. It is truthful and useless. The run stops on a request the product is
expected to serve.

## Consequences

- A likeness Wish can obtain and inspect its reference images without an
  operator copying files into the run.
- Command networking can now read any host. The marginal exfiltration surface
  is a URL and its query string, which the agent already had through web search
  with arbitrary queries; no request body can leave.
- The ingest surface widens from arbitrary web text, which the agent already
  read, to arbitrary web images. Reference images are untrusted input.
- The runtime-policy hash changes. Sessions checkpointed under the
  sixteen-domain map resume through the new rollback step; sessions under the
  four-domain map and the network-disabled map keep their existing steps.
- The proxy still fails closed. An unreachable host remains a truthful waiting
  condition; Workshop does not substitute a text-derived shape for a missing
  reference.

## Verification

- A runtime test binds `limited` mode and the open map together, so a later
  change to `full` cannot pass while the map stays open, and asserts the
  filesystem profile still denies `:root` and `**/.env*`.
- A rollback test walks `{"*"}` to the sixteen-domain map to the four-domain
  map, and proves each step refuses a policy from the wrong generation.
- A resume test accepts a session checkpointed under the sixteen-domain map and
  proves the resumed turn runs under the current open map.
- Live probes against the real Codex binary confirmed GET 200 with bytes
  written under the open map, the same GET blocked under the previous map, and
  POST refused with *"Method not allowed in limited mode."*
- Not yet demonstrated: a complete Spark run that inspects a fetched reference
  and finishes Make. This ADR removes the blocker; it does not establish that
  the resulting product resembles its target.

# ADR 0013: Make Release manual-first and publication optional

- Status: Accepted
- Date: 2026-08-27
- Supersedes: the page-first Release details in ADR 0012

## Context

The first Release contract centered `MANUAL.md`, complete Factory page copy,
and authenticated private import. That made a website concern capable of
blocking a product whose actual customer experience happens after delivery:
the owner opens the box and needs to begin without visiting a page. It also
encouraged effort on cinematic and marketing content while the printable guide
remained a technical Markdown document.

Release verification and publication are different facts. A structurally valid
PDF does not prove beauty or physical use; a Factory receipt does not prove the
box was printed, packed, or delivered. Neither should be confused with the
other or with Playtest evidence.

## Decision

New Release proposals use NativeRelease schema v2, whose canonical customer
manual is `MANUAL.pdf`. Its `product.json` uses schema v4 with
`kind=workshop.release-package` and `status=manual-ready`. The native Codex
Manager:

1. uses the repo-owned `manual-design` skill;
2. chooses a print format suited to the product and package;
3. authors a self-contained guide with product-derived visuals;
4. renders and inspects every page at print size and in grayscale;
5. revises the guide until it is clear, delightful, and internally consistent;
6. seals it with bounded product facts and exact Made/Playtest identities.

The trusted host applies only deterministic structural checks: exact manifest
hash, bounded size and page count, printable page boxes, no encryption,
JavaScript, launch action, attachment, or external dependency, and meaningful
extractable text. These checks cannot award an aesthetic, comprehension,
safety, or physical-verification claim.

Local Release succeeds and advances to Deliver without Factory credentials or
remote state. Factory import/publication is a separate optional effect against
the already sealed Release. `--publish` grants prospective authority for that
effect; missing credentials, unavailable remote fields, or no publication
request does not invalidate Release.

Historical NativeRelease schema v1 uses `MANUAL.md` with product schema v3 and
`status=page-ready`. Those contracts and their effect receipts remain readable
under their original rules and hashes; they are not silently reinterpreted as
new PDF-first releases.

## Consequences

- The physical box has one canonical customer guide.
- Website metadata and adapter limits cannot block that guide.
- Codex retains creative freedom; the repository does not impose one visual
  Python template on every product.
- ReportLab is available as a reliable print-native option, while the skill may
  choose another embedded, offline authoring method.
- PDF parsing and exact-byte sealing become part of the trusted host boundary.
- Deliver remains truthful: a released PDF is ready to print, not proof that it
  was printed or placed in a box.

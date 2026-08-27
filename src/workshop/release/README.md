# Release

Owns the sealed customer handoff after Playtest passes. The canonical customer
artifact is `MANUAL.pdf`: a self-contained printable guide intended to go in
the physical box. Release also keeps bounded product facts, exact hashes,
claims, contents, limitations, and optional editable manual source.

The current contract pair is NativeRelease schema v2 with `MANUAL.pdf` and
product schema v4/`manual-ready`. The readable legacy pair is NativeRelease
schema v1 with `MANUAL.md` and product schema v3/`page-ready`; legacy bytes are
validated under their original rules and are never silently upgraded.

The trusted host validates and seals the local package before advancing to
Deliver. This gate does not require Factory credentials, a private draft, a
public page, or a verification badge. Factory import/publication is a separate
optional host effect against an already accepted Release.

After accepting the package, the host may derive the strict public-safe
`artifacts/release/VERIFICATION.json` as non-blocking enrichment. Its current
schema can emit only **Digitally Verified**. **Physically Verified** remains
unavailable until a trusted host receipt proves the exact released artifact was
built and checked. Shipping and delivery are separate fulfillment statuses.

Public API: `workshop.release`.

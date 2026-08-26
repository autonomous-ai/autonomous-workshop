# Release

Owns the complete evidence-bound release package after Playtest passes: manual,
structured product data, product-page facts, media references, attribution,
and publication intent.

After accepting the exact Codex-authored package, the trusted host may derive
the strict public-safe `artifacts/release/VERIFICATION.json` as non-blocking
enrichment. Its current schema can emit only **Digitally Verified**.
**Physically Verified** remains unavailable until a trusted host receipt proves
the exact released artifact was built and checked. Shipping and delivery are
separate fulfillment statuses. Missing public verification never invalidates
the underlying Release.

Public API: `workshop.release`.

Release owns the `LaunchPort` for proposing a sealed product handoff. Trusted
host-side Factory adapters alone perform authenticated import or publication.

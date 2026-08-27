# Release

Owns the sealed customer handoff after Playtest passes. The canonical customer
artifact is `MANUAL.pdf`: a self-contained printable guide intended to go in
the physical box. Release also keeps bounded product facts, exact hashes,
claims, contents, limitations, and optional editable manual source.

The current contract pair is NativeRelease schema v2 with `MANUAL.pdf` and
product schema v4/`manual-ready`. The readable legacy pair is NativeRelease
schema v1 with `MANUAL.md` and product schema v3/`page-ready`; legacy bytes are
validated under their original rules and are never silently upgraded.

The trusted host revalidates full-tier, thickness-checked, print-ready CAD and
the exact `MANUAL.pdf`, then imports and publishes both through Factory.
Release completes only after authenticated public readback, including an exact
manual hash match. Missing credentials and transient or ambiguous effect
results leave Release waiting and resumable; permanent contract and integrity
errors fail visibly.

After accepting the package, the host may derive the strict public-safe
`artifacts/release/VERIFICATION.json` as non-blocking enrichment. Its current
schema can emit only **Digitally Verified**. **Physically Verified** remains
unavailable until a trusted host receipt proves the exact released artifact was
built and checked. Printing, shipping, delivery, and review are
Operations-owned stages outside the executable Workshop lifecycle.

Public API: `workshop.release`.

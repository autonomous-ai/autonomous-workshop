# ADR 0061: Spark leaves verification to Make

- Date: 2026-09-10
- Status: Implemented and deterministically tested; live host-only publication acceptance passed

The user explicitly requested that Workshop not interfere with Make or add
duplicate checks around it. Spark therefore accepts Make's exact submitted
product without a second host CAD rebuild, and Release does not trigger a
third CAD verification. Make's code, its own finalizer and its own engineering
and visual checks are unchanged by this decision. The team's current Make
visual-feedback implementation and four-review allowance remain as specified
in [ADR 0060](0060-make-round-visual-feedback-and-three-repairs.md); Workshop's
token-only execution policy does not remove Make-internal checks or limits.

The host still validates the submitted contract's identity, hashes the actual
files, preserves the accepted artifact tree, isolates credentials, accounts for
all native tokens, and reconciles publication with authenticated public readback.
Hash equality is not an engineering judgment. Host evidence explicitly records
CAD verification as `not-run` with no host pass or print-ready eligibility claim.
The Spark host also omits its separate build-group and production-part acceptance
checks and does not require manual-design review evidence. Handoff receipts use
distinct `make.output-handoff-v1` and `release.published-output-v1` gate ids;
they do not impersonate the older independently verified print-package gates.

Spark uses NativeRelease schema 4 / product schema 6 (`make-output-ready`). The
host derives site metadata from Make's title and summary, preserves all Make
assets byte-for-byte, and optionally copies an existing README. Neither a README
nor a PDF is a new requirement. There is no native Release turn, manual review,
CAD posing, duplicate rendering, or geometry acceptance pass. Factory verifies
the exact uploaded `workshop-release-page.json` as the publication anchor and
records anchor hashes instead of fabricated manual hashes. Existing PDF assets
remain ordinary unchanged Make files.

Factory requires a recognized cover for STEP-only imports. Release therefore
copies the exact sealed `<cad-project>/snap/iso.png` bytes into Factory's
reserved `assembled_review/_assembled.png` transport path and records the
source path and hash in the effect receipt. This is a transport alias of the
Make-owned canonical hero: it does not create a render, change the Made tree,
or add a host visual or geometry judgment.

New Spark projects also freeze Workshop inventor selection before Make. A
Wish's explicit inventor override binds immediately; otherwise the native
Manager selects and writes a roster-bound setup marker. The host preserves that
choice and resumes the same native session for Make. This handoff is not a new
root session, product gate, Match Goal, or Python selection algorithm. Make's
existing compound finalizer consumes the accepted selection fields unchanged.

Deterministic tests prove selection precedes Make, Make's accepted output is
published without another native turn or PDF, and a rejected Spark proposal can
repair in the same session and reach publication. Factory tests cover exact asset
bytes, missing README/PDF, omitted geometry work, anchor drift, and ambiguous
import reconciliation without reupload.

Live acceptance passed on 2026-09-10 for
[Civic Skyline](https://www.autonomous.ai/toys/product/civic-skyline), published
under Dee. The normal CLI exited zero with `action=published-release`,
`status=complete`, and a public, verified publication receipt; unauthenticated
public API readback returned HTTP 200. Its existing Wish, Alice inventor, native
root session and 32,678,604/200,000,000-token accounting were preserved.
The original import exposed Factory selecting a nested CAD directory and
omitting root metadata. Recovery used a root-selectable carrier preserving
the full Make tree, then an append-only version import into the same private
draft. The original incomplete import remains truthfully unknown; its immutable
intent was not rewritten or blindly resent. Exact public metadata-anchor
readback proved the new version before completion. No Make rerun, native Release
turn, new PDF, render, or CAD verification was needed during this repair.
This older run retained frozen inventor selection; new selection-before-Make
remains separately proven by deterministic tests, not by this live run.

Forge, Quest and legacy non-Spark routes keep their existing independent host
verification. Existing Spark sessions use the new orchestration on their next
host launch; their Make tools and native session are not rewritten. This is an
explicit change requested for Spark, not a false passing verifier receipt.

This supersedes earlier ADR requirements for duplicate host CAD verification
at Spark Make acceptance and Spark Release. It does not alter physical safety
claims, authorize manufacture, expose credentials, or make mocked publication
evidence sufficient for a successful live run.

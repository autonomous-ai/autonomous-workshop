# ADR 0014: End Workshop at a published, print-ready Release

- Status: Accepted
- Date: 2026-08-27
- Supersedes: ADR 0013's optional-publication lifecycle decision and ADR
  0012's executable Deliver boundary
- Superseded in part by: ADR 0015, which defers Playtest for new runs

## Context

Workshop's product responsibility is the digital handoff: ready-to-print CAD
and the in-box manual. Printing, packing, delivery, and review belong to a
separate Operations workflow. Treating Factory publication as optional made a
locally valid package look complete even though neither deliverable had crossed
the server boundary.

## Decision

The executable lifecycle is:

```text
Wish -> Match -> Invent -> Make <-> Playtest -> Release
```

Release is terminal and succeeds only when all of the following describe the
same exact bytes:

1. Playtest passes the current sealed Made revision;
2. the host reruns the full CAD verifier, including thickness, and the result
   is eligible for a print-ready claim;
3. the native Release package contains a validated `MANUAL.pdf`;
4. the host imports and publicly publishes the CAD package and manual through
   its credential-isolated Factory adapter; and
5. authenticated/public readback preserves the release, model, page, and
   manual hashes.

`workshop wish` grants this Release-publication authority; there is no normal
`--publish` mode. One host-owned Workshop Factory service account publishes
every Inventor's Release; users do not provide Factory credentials and the
selected Inventor does not choose the publisher identity. Credentials stay
host-only. Missing credentials and typed transient or ambiguous effects produce
a resumable Release wait, backed by the idempotent ledger and exact pending
proposal. Permanent contract, receipt, and integrity failures remain visible
and do not become outage loops.

Historical Deliver checkpoints remain readable but are never reported as a
current successful Release merely because an old page is public. A frozen
schema-v1 `MANUAL.md` release cannot be silently upgraded. Only a historical
run that already has schema-v2 `MANUAL.pdf`, passes today's full print-ready CAD
guard, and obtains current public readback may migrate to terminal Release.

## Consequences

- Workshop status truthfully ends at Release.
- Factory submission and public publication are one required Release effect.
- Lower-tier or digital-only CAD must return through Make before Playtest can
  advance; Release reruns the guard as defense in depth.
- Operations may depict `Printing -> Deliver -> Review` after the Release
  handoff, but those stages have no Workshop code, contracts, or CLI commands.

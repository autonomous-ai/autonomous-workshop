# Cratercade — completed digital publication

Published as **Dee** on 2026-09-14:
[Open Cratercade](https://www.autonomous.ai/toys/product/cratercade).

The real Workshop CLI exited 0 with `complete at Release`. Same native root
session throughout; Spark / Codex / gpt-6-astra / medium. Total observed usage:
**619,141,459 of 1,000,000,000 tokens**. Publication required no additional
native turn. The original ultra/100M request was superseded by the operator's
explicit effort and budget changes.

## What we made

A mainly 3D-printed lunar pinball machine with two independent thumb flippers,
a rubber-band launcher, rearrangeable crater missions, and a marble-weighted
sample bucket that raises a linked flag. It includes a covered marble return,
access doors, assembly instructions and play/reset instructions. It uses glass
marbles, rubber bands, PET sheet, a wooden axle and ordinary hardware; no
electronics. STEP geometry, editable CAD sources, renders, animation and the
README are included in the digital package.

The other nine ideas remain a saved shortlist, not built products:
[Ten KiwiCo-inspired ideas](kiwico-inspired-toys.md).

## Evidence checked

- All 3,248 sealed product files matched their manifest hashes.
- Final integrated verification exited 0 in 2,063.66 seconds. Each of 78
  printable part sources passed geometry, overhang and thickness checks.
- All 156 regenerated overhang/thickness reports matched the original
  independently reviewed hashes. The final review's exact bytes were restored.
- Make passed its host handoff gate; Release passed
  `release.published-output-v1`, with authenticated Factory readback verified.
- Factory import and publication intents both succeeded. Their readbacks name
  Dee, owner `6a4dfe7a83c93d8bdf733ac0`, and the same current/published history
  `6aa8119fec58f3d29246d4cf`.
- The public metadata anchor hash matches the sealed Release product JSON:
  `7389b0a2769cf13bd402244e46889c08849e11250fd3191fe8b918411abb1786`.
- Release, Made, package and product identities agree; every Release package
  file was rehashed. The terminal checkpoint is complete at Release, revision 17.

## Verification limits

Motion verification was explicitly disabled on resume under the team's new
Make policy. Working motion, assembly access and retention across all states
remain **unverified**. Animation shows prescribed CAD poses, not physical
performance. Spark Playtest was not run. The toy has not been physically
printed, assembled, played, manufactured or delivered. Follow the README's
physical commissioning steps before play.

## Workflow fixes made during final recovery

- `a1fb2338`: reconcile restored terminal counters against the exact native
  response ledger; restore print report verdict summaries.
- `75200656`: preserve stale unaccepted Make outcomes after a recorded tool
  refresh and require fresh finalization.
- `a0705728`: reference the large Made manifest by exact binding in the
  host-only Spark Release packet.
- `b48c64bf`: compress oversized Factory transport archives without dropping
  sealed files or increasing upload/extraction limits. The uncompressed
  handoff was 178,206,728 bytes; the successful compressed upload passed the
  unchanged 50 MiB guard. Small/default packs retain their historical bytes.

Targeted and broader deterministic tests passed for each change; detailed
commands, test counts and recovery history are in [run notes](cratercade-run-notes.md).
These source commits were pushed to GitHub main on 2026-09-14. The sanitized
public toy export is in `toys/bob-cratercade/`. Private run state and credentials
are excluded. Product publication uses the authorized host-owned Factory adapter.

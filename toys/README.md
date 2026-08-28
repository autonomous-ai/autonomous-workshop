# Public toy examples

This source-checkout directory contains sanitized examples only. A new
`workshop wish` creates its private Codex project at
`$WORKSHOP_HOME/runs/<wish-id>/workspace`; trusted checkpoints, credentials,
effect intents, and receipts remain outside that agent-visible workspace under
`$WORKSHOP_HOME/state/<wish-id>/`.

Older exact path-bound runs under `toys/wish-*` remain ignored by Git and may
still be resumed in place. They are private workspaces, not public examples,
and Workshop never moves them or silently chooses between duplicate roots.

After Factory publication and public readback succeed, the host can create a
sanitized, workflow-shaped, content-addressed projection here under
`<inventor>-<product-slug>/`.
[`pico-press-horn-tip/`](pico-press-horn-tip/) is a Spark example produced by
`--manager grok`; its README has the exact CLI used to create it.
Workflow-shaped snapshots include a README table of public stage attempts
from each `ATTEMPTS.json`.

A current public snapshot follows the real lifecycle:

- `wish/` records the exact Wish hash and, only with explicit consent, its
  exact text;
- `match/` and `invent/` preserve the selected real Inventor, accepted concept,
  validated authored source, and sealed superseded Invent attempts;
- `make/` preserves exact CAD source, printable and assembly models, every
  product render sealed by Make, verification reports, and sealed prior Made
  or Make→Invent evidence under `attempts/rNNNN/`;
- `playtest/`, when the effort includes it, preserves exact accepted evidence
  and sealed superseded evidence trees;
- `release/` preserves the exact printable `MANUAL.pdf`, product facts,
  manual-design/review evidence, and Release contract;
- `publication/PUBLICATION.json` records sanitized public URLs, listing facts,
  and content hashes; `MANIFEST.json` hashes every public workflow file except
  itself and the generated root README. `SANITIZATION.json`, when present,
  records source/public hashes for host-local path prefixes replaced by stable
  placeholders.

Historical schema-v1 snapshots may retain `MANUAL.md`; they are legacy
evidence and are never rewritten or presented as a current terminal Release.

Snapshots never contain an undisclosed Wish, Codex prompt/transcript/chain of
thought, host checkpoint, credentials, raw Factory receipt, generated G-code,
arbitrary work cache, or product-run agent configuration. Projection is
optional and never counts as Release gate evidence: a collision or local write
failure is reported without changing the verified Factory publication.

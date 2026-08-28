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
deliberately small sanitized projection here under
`<inventor>-<product-slug>/`.
[`pico-press-horn-tip/`](pico-press-horn-tip/) is a Spark example produced by
`--manager grok`; its README has the exact CLI used to create it.
Workflow-shaped snapshots include a README table of public stage attempts
from each `ATTEMPTS.json`.

A public snapshot contains only:

- `README.md`, the exact printable `MANUAL.pdf`, and the exact public
  `product.json`;
- `PUBLICATION.json`, with public URLs, listing price, and content hashes but no
  private IDs, credentials, effect keys, or raw receipts;
- exact printable component STLs selected from the sealed Made inventory under
  `print/`, including their declared quantities;
- the exact public primary STL under `model/` when the Factory primary is a
  mesh.

Historical schema-v1 snapshots may retain `MANUAL.md`; they are legacy
evidence and are never rewritten or presented as a current terminal Release.

Snapshots never contain the private Wish, Codex transcript, host checkpoint,
Factory receipt, generated G-code, internal evidence tree, or product-run agent
configuration. Projection is optional and never counts as Release gate
evidence: a collision or local write failure is reported without changing the
verified Factory publication.

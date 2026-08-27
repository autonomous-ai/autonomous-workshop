# Integrations

Owns the authenticated Factory adapter used for the host-effect portion of
Release. `factory.py` builds an exact sealed model-and-Release ZIP handoff,
logs in with the selected Inventor's Factory account, carries the canonical
`MANUAL.pdf`, and proves public publication by authenticated hash readback.
The local product, full-tier print-ready CAD, and in-box manual must pass their
deterministic gates before this effect starts, but Release remains incomplete
until Factory readback verifies the exact public bytes. Unsupported remote
field limits fail closed; Python never rewrites Codex copy. Credentials remain
in the host process and never enter the Codex toy project, ledger, Receipt, or
artifact tree.

The handoff pack is bounded by Workshop's 50 MB client limit. Import-specific
HTTP 500 and 524 responses are recorded as proven no-effect rejections, per
Factory's import contract, so the exact request may be reopened safely. Other
uncertain import, content, or publication outcomes remain fenced until an
authenticated readback can reconcile them. That fence protects the remote
effect and leaves Release waiting rather than claiming success or blindly
repeating a possibly completed publication.

Multipart occurrence transport is optional. The adapter includes component
STLs and a STEP sidecar only when the complete Factory sidecar, or the exact
hash-bound native CAD descriptor and product inventory from which it is
derived, validates. Product-owned, stale, or malformed `*.step.json` files do
not cross the effect boundary; the handoff safely narrows to the sealed root
`assembled.stl` instead.

Public API: `workshop.integrations` exports the canonical Factory credentials,
session, client, Release writer, and public transition. The adapter depends on
runtime-owned `Receipt` and `EffectLedger` contracts; runtime never imports an
integration.

# Integrations

Owns the optional authenticated Factory adapter used after local Release.
`factory.py` builds an exact sealed model-and-Release ZIP handoff, logs in with
the selected Inventor's Factory account, carries the canonical `MANUAL.pdf`,
and proves any private import or public transition by authenticated readback.
Factory availability never determines whether the local product and in-box
manual passed Release. Unsupported remote field limits fail closed for that
effect; Python never rewrites Codex copy. Credentials remain in the host
process and never enter the Codex toy project, ledger, Receipt, or artifact
tree.

The handoff pack is bounded by Workshop's 50 MB client limit. Import-specific
HTTP 500 and 524 responses are recorded as proven no-effect rejections, per
Factory's import contract, so the exact request may be reopened safely. Other
uncertain import, content, or publication outcomes remain fenced until an
authenticated readback can reconcile them. That fence protects the remote
effect without invalidating the already sealed local Release.

Public API: `workshop.integrations` exports the canonical Factory credentials,
session, client, Release writer, and public transition. The adapter depends on
runtime-owned `Receipt` and `EffectLedger` contracts; runtime never imports an
integration.

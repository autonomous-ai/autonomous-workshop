# Integrations

Owns the single authenticated Factory adapter used by Release. `factory.py`
builds the exact sealed model-and-Release ZIP handoff, logs in with the selected Inventor's
Factory account, includes the exact sealed Release page and `MANUAL.md`, proves
the private import by authenticated readback, then writes and reconciles the
exact representable `use_case` and `story_blocks` content before an explicit
public transition can run under `--publish` authority. Unsupported Factory
field limits fail closed; Python never rewrites Codex copy. Credentials remain
in the host process and never enter the Codex toy project, ledger, Receipt, or
artifact tree.

The handoff pack is bounded by Workshop's 50 MB client limit. Import-specific
HTTP 500 and 524 responses are recorded as proven no-effect rejections, per
Factory's import contract, so the exact request may be reopened safely. Other
uncertain import, content, or publication outcomes remain fenced until an
authenticated readback can reconcile them.

Public API: `workshop.integrations` exports the canonical Factory credentials,
session, client, Release writer, and public transition. The adapter depends on
runtime-owned `Receipt` and `EffectLedger` contracts; runtime never imports an
integration.

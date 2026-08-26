# Integrations

Owns the single authenticated Factory adapter used by Release. `factory.py`
builds the exact model-only ZIP handoff, logs in with the selected Inventor's
Factory account, performs bounded same-origin requests, proves the private
import by authenticated readback, and performs an explicit public transition
only after `--publish` authority. Credentials remain in the host process and
never enter the Codex toy project, ledger, Receipt, or artifact tree.

Public API: `workshop.integrations` exports the canonical Factory credentials,
session, client, Release writer, and public transition. The adapter depends on
runtime-owned `Receipt` and `EffectLedger` contracts; runtime never imports an
integration.

---
name: design-vault
description: Look up a mechanism's definition, known failure modes, and recorded fixes, resolve a mechanism name to its vault node, or check a mechanism combination for declared conflicts. Use during Invent before choosing mechanisms and during Make and Playtest to act on the host-provided vault leads.
---

# Design vault

`vault.json` beside this file is an immutable, content-addressed snapshot of
the Workshop's design vault: mechanism, anti-pattern, rule-pattern,
constraint, and component nodes joined by typed links (`requires`,
`conflicts-with`, `risks`, `mitigated-by`, `variant-of`, `component`, `uses`).
Every answer below is computed from those links; nothing here is an opinion.

Read the host-provided leads named in `STAGE.json` first — they are computed
for this exact run. For anything beyond them, query the snapshot offline:

```bash
"$WORKSHOP_PYTHON" .agents/skills/design-vault/vault_tools.py resolve "ratchet dial"
"$WORKSHOP_PYTHON" .agents/skills/design-vault/vault_tools.py node mechanisms/hand-management
"$WORKSHOP_PYTHON" .agents/skills/design-vault/vault_tools.py links anti-patterns/alpha-solve --reverse --type risks
"$WORKSHOP_PYTHON" .agents/skills/design-vault/vault_tools.py guidance mechanisms/stacking-and-balancing
"$WORKSHOP_PYTHON" .agents/skills/design-vault/vault_tools.py check mechanisms/a mechanisms/b --with-constraints
```

- `resolve` maps a name to a node by exact slug, declared alias, then a
  conservative fuzzy match; `null` means the vault has no such mechanism.
- `check` reports `conflict` (declared `conflicts-with`), `unmet-requirement`
  (a `requires` outside the set), and `risk` (a `risks` edge with the recorded
  `mitigated-by` fixes and the newest banked evidence).
- `guidance` briefs a mechanism: definition, its top risks with fixes, and
  exemplar games.

Rules:

- Every mechanism in an Invent concept must resolve to a vault node or be
  declared under `novel_mechanisms` with a definition; a combination the
  vault marks `conflicts-with` or leaves a `requires` unmet is refused by the
  finalizer and the host. Risks are never refusals — they become Playtest
  leads.
- A lead is a lead, not a verdict. Confirm or dismiss each one against the
  exact artifact and say why.
- Never edit `vault.json` or this skill; they are hashed inputs. Propose vault
  changes in your stage outcome instead.

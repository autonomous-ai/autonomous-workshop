# Playtest

Owns AI-player simulation, exact-artifact evidence, release proofs, and
actionable feedback that explicitly routes implementation repair to Make or
fundamental concept revision to Invent. Missing or stale evidence never passes.

Public API: `workshop.playtest`.

## Vault write-back

`workshop.playtest.vault_evidence` turns every sealed Playtest's feedback into
one row per finding, tagged with the design-vault mechanisms the sealed
concept resolved to and the anti-pattern of the confirmed vault lead that
named it. After the gate seals the round, the host posts the confirmed rows
to the game vault API (`/api/gamevault/evidence`, banked on the anti-pattern
node with the vault's own cap and eviction) and the dismissed leads to
`/api/gamevault/review` (recorded as `DISMISSED` rows so the same lead is not
re-litigated). The same `evidence` call carries the product's own game page
(`design`): the vault writes `games/<wish-id>` with `uses` edges to the
mechanisms the sealed concept resolved to, `exhibits` edges to the confirmed
anti-patterns, this round's verdict and median scores, and up to three
confirmed findings as lessons — every wish grows the vault by one game, even
a round that confirmed nothing. A vault that is unreachable at that moment never undoes the
sealed checkpoint: the payload waits under `state/<product>/vault/pending/`
and is sent before a later phase fetches its snapshot (a payload the vault
refuses is set aside as `*.rejected`, never blocking a run). Every later run
— on any machine — reads the result through its phase snapshot.

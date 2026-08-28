- The design vault is no longer shipped with Workshop. The host reads the
  game vault on the panda VM through admindash's token-protected
  `/api/gamevault/*` (`workshop.invent.gamevault`; URL and token from
  `WORKSHOP_GAMEVAULT_URL` / `WORKSHOP_GAMEVAULT_TOKEN` or
  `$WORKSHOP_HOME/credentials/gamevault.env`), fetches a fresh snapshot before
  every Invent, Make, and Playtest phase, caches it per checkpoint, and writes
  it into the run as the read-only `VAULT.json` bound in `STAGE.json`. Sealed
  Playtest rounds post confirmed leads and dismissals back to the vault
  (queued under host state when the vault is unreachable). An unreachable
  vault, or a host without a token, is bypassed for that checkpoint: the
  phase runs exactly like a run without a vault and the next checkpoint
  tries again.
  Combos, `member`, and `exhibits` links are understood. `workshop vault seed`,
  `workshop vault review`, `workshop evidence`, and the local evidence ledger
  are gone; `workshop vault lint|check` read the API or `--root`.
- Every sealed Playtest also posts the product's own `games/<wish-id>` page
  (`design` on `/api/gamevault/evidence`: `uses` mechanisms, `exhibits`
  confirmed anti-patterns, verdict, median scores, lessons), so the vault
  gains one game per wish. Fuzzy `resolve` now refuses a string-similar hit
  that shares no word with the query (`tile laying` no longer resolves to
  `role-playing`; the vault carries `tile-laying` as an alias instead).

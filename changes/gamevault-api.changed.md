- The design vault is no longer shipped with Workshop. The host reads the
  game vault on the panda VM through admindash's token-protected
  `/api/gamevault/*` (`workshop.invent.gamevault`; URL and token from
  `WORKSHOP_GAMEVAULT_URL` / `WORKSHOP_GAMEVAULT_TOKEN` or
  `$WORKSHOP_HOME/credentials/gamevault.env`), fetches a fresh snapshot before
  every Invent, Make, and Playtest phase, caches it per checkpoint, and writes
  it into the run as the read-only `VAULT.json` bound in `STAGE.json`. Sealed
  Playtest rounds post confirmed leads and dismissals back to the vault
  (queued under host state when the vault is unreachable). An unreachable
  vault stops the phase before the session starts; `workshop resume` retries.
  Combos, `member`, and `exhibits` links are understood. `workshop vault seed`,
  `workshop vault review`, `workshop evidence`, and the local evidence ledger
  are gone; `workshop vault lint|check` read the API or `--root`.

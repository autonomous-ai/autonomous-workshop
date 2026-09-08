- Bank every sealed Playtest's feedback: confirmed vault leads and
  dismissals, plus the product's own `games/<wish-id>` page, are posted back
  to the game-vault API after each sealed round (queued under host state when
  the vault is unreachable), and later runs sharing a mechanism receive
  `prior_evidence`. The interim local `evidence.jsonl` ledger and the
  `workshop evidence harvest|list|recall` and `workshop vault review` commands
  were removed by `gamevault-api.changed.md`; `workshop vault lint|check`
  remain.

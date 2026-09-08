- Add the design vault client: `workshop.invent.vault` reads, lints, packs,
  and queries an Obsidian-compatible typed-link graph of mechanisms, failure
  modes, and recorded fixes, and `workshop vault lint|check` validate or query
  it. The vault itself is served by the game-vault API (see
  `gamevault-api.changed.md`); `--root <dir>` reads a local checkout instead.
  The earlier bundled seed and `workshop vault seed` are gone.

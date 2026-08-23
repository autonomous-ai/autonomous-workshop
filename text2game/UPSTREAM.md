# Upstream snapshot

- Source: https://github.com/nohope88/text2game
- Commit: `9b007f65e83bc79e3c9b78a6228942b6354b3019`
- Imported: 2026-08-23 as a complete tracked source snapshot, without Git
  history. No credential-bearing file was found.
- Root license: none found. Confirm team permission or add a root license before
  redistribution outside this project.

## Why it is here

This pipeline contributes board-game consistency checks, provider-neutral
traces, evidence harvesting, component-group build/repair, fit and plate logic,
BGG prior-art indexing, print-kit generation, and instructional media.

It is not yet safe for unattended release: weak discovery candidates can be
selected, absent evaluator/gate output can avoid failing, the default all-phase
path can continue after dirty checkpoints, dependencies and fixed paths are not
fresh-clone complete, and publishing does not re-prove every upstream gate.


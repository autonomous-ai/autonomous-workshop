# Third-party notices and provenance

The `src` implementation and `product-to-cad` skill were authored for this
repository from observed contracts and general engineering ideas; they do not
copy the unlicensed `text-to-3d/skills/image-to-cad` source.

`skills/cad` and `skills/step-parts` were moved without modification
from Bob's existing vendored copies. They match `peterat617/text-to-3d` commit
`f18aebe4698d92ffccf07d94e2d624b08d30e667` byte-for-byte (excluding generated
caches). Their included `LICENSE` files identify MIT material copyright 2026
Thompson Labs LLC; the embedded cadgen package has its own included MIT license.
Peter's current tree includes substantial subsequent modifications and concepts
with additional history, so preserve the full pin and source ledger rather than
attributing the current tree only to its initial upstream.

Three inventor snapshots were imported during earlier research (`text2cad`,
`text2game`, and `vibe-ideas`). All three came from Autonomous team members' own
repositories, not from outside parties, and all three were internal working code
rather than published libraries. `text2cad` and `text2game` were removed from
this repository instead of shipped; no code from either is here.

`reinSPQR/vibe-ideas` is the exception. Its `board-game/` tooling is now
imported under `inventors/abo/` as the Abstract Boardgame Oracle's harness,
pinned at commit `a557cacb3d98e5936194e4ba11721809370195f8` and locked
byte-for-byte in [`snapshots.lock.json`](snapshots.lock.json). There is no
repository-level licence file at that commit; this is an internal transfer of
the same owner's own work rather than use of a third party's published library.
The only `LICENSE` files in the upstream tree cover its own vendored copies of
`skills/cad` and `skills/step-parts`, and neither was imported — this repository
carries its own pin of those skills, recorded above. The complete file-by-file
inventory, the list of what was deliberately left behind, and the one edit made
to a vendored file are in
[`inventors/abo/UPSTREAM.md`](inventors/abo/UPSTREAM.md).

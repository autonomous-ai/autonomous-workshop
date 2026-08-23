# Third-party notices and provenance

The `foundation/src` implementation and `product-to-cad` skill were authored for this
repository from observed contracts and general engineering ideas; they do not
copy the unlicensed `text-to-3d/skills/image-to-cad` source.

`foundation/skills/cad` and `foundation/skills/step-parts` were moved without modification
from Bob's existing vendored copies. They match `peterat617/text-to-3d` commit
`f18aebe4698d92ffccf07d94e2d624b08d30e667` byte-for-byte (excluding generated
caches). Their included `LICENSE` files identify MIT material copyright 2026
Thompson Labs LLC; the embedded cadgen package has its own included MIT license.
Peter's current tree includes substantial subsequent modifications and concepts
with additional history, so preserve the full pin and source ledger rather than
attributing the current tree only to its initial upstream.

The three imported inventor snapshots under `inventors/` have individual `UPSTREAM.md`
files. No root license was found in those upstream repositories; licenses inside
their vendored subdirectories do not cover the surrounding pipeline by default.

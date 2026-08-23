# Alice games

This directory is Alice's durable source-of-truth copy of each game. Generated
build caches, credentials, private import journals, and Factory ZIPs do not
belong here.

## Blindcap: Duel

`blindcap-duel/` is an exact export of the tracked game subtree from reviewed
Vibe checkpoint `0a48b02728323919d5035e46b7f017f004d14992`; the original subtree
Git object is `62dcb2d26e9fa38b48349f967f184f51a8cca47f`. The corresponding Vibe
tooling is preserved in
`../integrations/vibe-ideas-blindcap-private-draft.patch`.

The existing Factory product is permanently bound to:

- design ID: `6a8a071857e4d5db73f54a5b`
- slug: `blindcap-duel`
- first confirmed history: `6a8a071957e4d5db73f54a5c`

An improvement to Blindcap must update that exact design. It must never call a
first-import endpoint, accept a collision-suffixed slug, or create a second
Blindcap product. Because the current design is public and the existing Vibe
version-import route publishes a new history immediately, improvements remain
local until Factory exposes a reviewed staged-version capability that preserves
the old public history until Dee approves the replacement.

Every Alice-authored Factory description ends with the exact final bytes
`By Alice.`. `Note: By Alice.` and trailing whitespace are not accepted.

To reconstruct the reviewed Vibe workspace, start at
`reinSPQR/vibe-ideas@ed3d1e876faed95b1bf785af2fae2a8133354517`, apply the
integration patch, and copy `blindcap-duel/` to
`board-game/ideas/blindcap-duel/` without changing bytes. Run the commands in
the game's `project/BUILD.md` before preparing any later revision.

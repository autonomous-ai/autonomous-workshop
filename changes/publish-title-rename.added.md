Add `workshop publish <product-id> --title "<name>"`, which publishes an
Unreleased toy under a new public title instead of the exact one Make sealed.
A Design Contract build loop names every intermediate correction with a
revision suffix, so the build that finally conforms previously carried that
suffixed name unless the operator spent one more correction run whose brief
changed only the title. The host now re-seals only its own Spark Release
under the given title: Make's sealed bytes and the immutable Release contract
are untouched, no native turn runs, and no Make evidence is recomputed. The
re-sealed Release and the projected `toys/<inventor>-<slug>` record the Make
title and the public title side by side (`make_title` beside `title`), so the
archive never hides that the published name differs from the one Make
sealed. A title that cannot produce a safe public slug is refused before any
effect; a toy that is already public, or is not Unreleased, is refused with a
message naming why. Without `--title`, publication is byte-for-byte
unchanged. `build-a-toy` Step 7 now offers `--title` in place of spending an
extra correction run.

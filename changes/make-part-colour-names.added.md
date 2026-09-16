- **A sealed part now says which spool prints it.** Every occurrence of a
  multi-part `assembled.step` must be named `<part>_<colour>` for the filament
  it prints in -- `arm_black`, `leg_dark_brown`, `canopy_misty_blue` -- and the
  colour has to be one the CAD skill's filament palette stocks: `beige`,
  `black`, `blue`, `cocoa_brown`, `cyan`, `dark_beige`, `dark_brown`,
  `dark_gray`, `gray`, `green`, `misty_blue`, `navy_blue`, `orange`,
  `pine_green`, `red`, `reflex_blue`, `sunflower_yellow`, `white`, `yellow`,
  the 19 distinct colours across Bambu Lab PLA Lite and PETG Basic. A hyphen
  reads as the same separator an underscore does, and the part half before the
  colour may not be empty, so a part called only `black` names no part. The
  name travels with the occurrence into `parts/<occurrence-name>.step`, the
  Factory sidecar and the shop's part list, so whoever loads the printer reads
  the spool off the file.
- The Make gate rejects a multi-part proposal that breaks the rule with
  `make-part-colour-names-invalid`, naming the occurrences that are not named
  for a stocked colour and listing the palette. It runs **before**
  `make-production-parts-missing`, because a rename moves the occurrence, its
  `parts/` file and its colour together: the agent hears about the name before
  it is told a file is missing. A single-occurrence package binds nothing --
  one solid, one spool, no name to tell them apart by -- and a document that is
  not a valid assembly-package still falls through to the Factory adapter's
  visible single-mesh fallback.
- This is the first gate that reads the filament palette. The rule checks the
  **name** only: it does not compare the suffix with the colour sealed on the
  part, which stays the business of `make-part-colours-missing`. `cadfilament`
  authors a `Color` through `cadgen.color.srgb` (linear channels) while the
  host reader, the GLB exporter and the product-run Make reference read sealed
  channels as sRGB, and that reconciliation is still open -- a hex comparison
  today would reject palette-authored parts.
- `workshop.make.cad.filament_names` holds the host's copy of the vocabulary,
  standard-library-only, because a gate cannot import a vendored skill script
  that is materialized per run and rewritten by upstream resyncs.
  `tests/make/test_filament_palette.py` holds the two lists to the same
  contents, so a colour stocked or retired in `cadfilament.py` fails CI here
  rather than drifting. The vendored `cad` and `image-to-cad` trees are
  untouched and their `LOCK.json` fingerprints do not move: this is a Workshop
  rule about a sealed product, not a CAD-authoring rule.
- `make-part-colour-names-invalid` is a protocol code, so it banks no design
  lesson in the vault. `assembled.step` geometry, sealed colour channels, the
  Factory colour handoff and every print gate are unchanged.

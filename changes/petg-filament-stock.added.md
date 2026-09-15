- **Make prints PETG now, not only PLA.** `cad/scripts/cadfilament.py` carries a
  second stock beside Bambu Lab PLA Lite: Bambu Lab PETG Basic, its 13 colours
  and codes from Bambu's published hex table -- `black` 30105, `white` 30106,
  `gray` 30107, `misty blue` 30108, `red` 30201, `orange` 30302, `yellow` 30402,
  `dark beige` 30403, `green` 30502, `pine green` 30503, `reflex blue` 30603,
  `navy blue` 30604, `dark brown` 30800. A printed part picks its stock with
  `filament("misty blue", material="PETG")`; `material` defaults to PLA Lite, so
  every colour authored before PETG was stocked still means the spool it always
  meant. Seven names (`black`, `white`, `gray`, `red`, `orange`, `yellow`,
  `green`) are in both tables and five of them are a different hex in each, so
  the stock is what decides which spool, and a PETG-only name asked for as PLA
  raises with the stock that
  carries it rather than resolving to something close. `MATERIALS` and
  `DEFAULT_MATERIAL` are new public names; `FILAMENTS` still holds the PLA Lite
  table. The `cad` and `image-to-cad` reference files and their LOCK
  fingerprints move with it. No gate reads the palette -- it is a table a
  generator imports, not a check -- and nothing about geometry, the sealed STEP
  or a PETG part's print gates changes. A print-in-place joint in PETG still
  needs its own looser gap from `cadfits.print_in_place_gap(...,
  material="PETG")`, and no physical PETG print is claimed from CAD.

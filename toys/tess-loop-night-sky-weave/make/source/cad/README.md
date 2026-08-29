# Night-Sky Weave CAD project

Tier-2 parametric build123d project for nine separately movable tiles displayed as a compact 3×3 field.

- `night_sky_weave_lib.py`: all dimensions, validations, tile-family builders, and mosaic placements.
- `night_sky_weave.step.py`: combined nine-solid review/storage layout (`PRINTABLE = False`); this is not one printable part.
- `part_crescent.step.py`, `part_comet.step.py`, `part_star.step.py`: the actual printable entries. Print three copies of each family entry for the complete nine-tile set.
- `measure/check_spec.py`: deterministic analytical audit of inventory, core, gap, envelope, and universal edge anchors.
- `snap/iso.png`: presentation render derived from the verified combined STL.

Print with a 0.4 mm nozzle, 0.20 mm layers, and the broad face on the bed. Use no supports. Slice three copies each of `part_crescent.stl`, `part_comet.stl`, and `part_star.stl`. Each printable entry is one connected body and fits a `--bed 220x220x220` volume. The combined 3×3 STEP/STL is presentation and storage-layout evidence only.

No assembly procedure is required: print the nine independent pieces and rearrange them by loose edge placement.

Digital checks cannot establish physical surface finish, first-layer bridging quality, durability, or player response.

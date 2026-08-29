# Moonwake Garden CAD project

Tier-2 build123d source for the accepted 70 mm Moonwake Garden repair. The combined entry is a labeled three-occurrence review assembly at Cassiopeia and is not printable; exactly three `part_*.step.py` entries are support-free print targets.

## Source and evidence map

- `moonwake_garden_lib.py` — one parameter block, invariants, contained polar profiles, and all three part builders.
- `moonwake_garden.step.py` — exact home assembly (`PRINTABLE = False`), with no review-only color metadata so fresh single-color STEP bytes remain deterministic.
- `part_rear_chassis.step.py` — rear frame, spindle/root, guide, isolated annular detent, pads, collars, and snaps.
- `rear_finish.py` — bounded rim selection and detent-junction finishing used by the rear builder.
- `part_sector_rotor.step.py` — repaired70 mm shutter disk, sector, bore, three notches, and the printable blended trench covering all seven sealed grip positions.
- `part_front_garden_mask.step.py` — fixed face, eighteen petals with ruled45° entries, printable round-ended vines/moon, polar portal, and snap holes.
- `motion_proxy.proxy.py` — review-only rotor sweep proxy with the elastic tooth suppressed; the `.proxy.py` suffix keeps it out of combined-entry discovery.
- `snap_proxy.proxy.py` — review-only seating proxy with snap heads compressed to the stem envelope; the `.proxy.py` suffix keeps it out of combined-entry discovery.
- `measure/check_spec.py` — independent radial-stack, detent, portal, grip, ligament, full-turn, optical-state, and oblique-ray audit.
- `measure/motion.json` and `measure/motion_snap_proxy.json` — rigid motion/capture checks with explicit proxy limits.
- `moonwake_garden_spec.md` — exact build brief, dimensional provenance, validation targets, and evidence limits.
- `moonwake_fit_fallback.py` — relocation-safe explicit-clearance derivation used only when project-local audits run outside a Workshop source tree.

## Rebuild

Run from the product workspace with the supplied CAD skill and a Python3.11 environment containing its requirements. Redirect only tool cache into the workspace when sandboxed.

```sh
python .agents/skills/cad/scripts/check_layout artifacts/make/r0002/product/cad/moonwake_garden
python artifacts/make/r0002/product/cad/moonwake_garden/measure/check_spec.py
python .agents/skills/cad/scripts/gen \
  artifacts/make/r0002/product/cad/moonwake_garden/moonwake_garden.step.py \
  artifacts/make/r0002/product/cad/moonwake_garden/part_rear_chassis.step.py \
  artifacts/make/r0002/product/cad/moonwake_garden/part_sector_rotor.step.py \
  artifacts/make/r0002/product/cad/moonwake_garden/part_front_garden_mask.step.py \
  --write --json
python .agents/skills/cad/scripts/verify_project artifacts/make/r0002/product/cad/moonwake_garden \
  --fresh --exports --strict-fit
python .agents/skills/cad/scripts/check_motion artifacts/make/r0002/product/cad/moonwake_garden \
  --manifest artifacts/make/r0002/product/cad/moonwake_garden/measure/motion_snap_proxy.json
```

The intended build bed is declared once here: `--bed 220x220x250`.

## Limits

All files are digital geometry evidence. The project does not claim a successful physical print, printer-specific fit, safe snap/detent force, fatigue life, room-light brightness, recognition, discovery, comfort, or delight.

Shaded, edge-separated product-derived inspection images are in `../../views/inspection/`; their source is `../../views/sources/render_inspection.py`.

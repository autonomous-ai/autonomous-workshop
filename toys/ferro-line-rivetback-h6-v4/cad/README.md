# Rivetback H-6 V4 CAD project

This self-contained editable project is the unarmed Rivetback H-6 V4
successor: a fixed-pose, multi-part mecha hexapod display kit. It preserves the
authoritative staged V4 geometry while omitting the staged tree's four unused
legacy weapon roles and every stale armed review record.

The combined review entry is `rivetback.step.py` and is explicitly
non-printable. Fifteen `part_<role>.step.py` entries are the unique printable
components; repeated quantities are declared in the assembly and product
inventory. Every part entry owns its supportless bed orientation.

The assembly contains 61 labelled occurrences: one chassis, three base armor
plates, three secondary dorsal shells, six copies of seven leg roles, and
twelve hex-recess locking pins. It is rigid and non-articulating. There is no
cannon, muzzle, turret, pedestal, or sensor crown.

The visual scheme is industrial yellow armor (`#D9A514`) over a charcoal frame
(`#191B1C`), pale conduit loops, and dark-steel pins. Nominal CAD clearances are
0.20–0.25 mm per side on the primary keyed interfaces. The source/spec audit
records the deliberately anisotropic carapace peg clearance and exact-depth
foot stop separately.

The assembled review model is approximately 242.0 × 147.611 × 77.7 mm. The
180 × 180 × 180 mm target applies to each unique printable part, not to the
assembled pose or a one-plate full kit.

Rebuild explicit targets with:

```sh
"$WORKSHOP_PYTHON" .agents/skills/cad/scripts/gen \
  artifacts/make/r0001/product/rivetback_h6_v4/rivetback.step.py --write
```

Run component-first Make rounds for every `part_<role>.step.py`, then the
assembled round with `--require-component-passes`. Final verification uses
strict fit, image-derived reconciliation, the three V4 render references,
unpowered classification, and print gates. Digital evidence does not prove a
successful physical print, insertion force, retention, durability, or
printer-specific compensation.

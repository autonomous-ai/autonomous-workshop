# Lantern Menagerie CAD project

Four separately printed rigid-filament parts form one captured shadow theatre:
front shell, rear shell, open-carrier reel, and kickstand. The exact optical
profiles come from the sealed Invent contract.

Print bed: `--bed 220x220x220`  
Reference process: 0.4 mm nozzle, 0.2 mm layers, no supports intended.

Assembly: seat the reel on the front spindle, gently squeeze the two kickstand
arms inward to place their outward trunnions in the rear blind bearing pockets,
align the shells, and engage the four one-time shell locks. The reel rotates
continuously; the kickstand opens to its compression stop. Printed snap
compliance, detent feel, fit, strength, and cycle life are not digitally proven
and remain Playtest items.

Entries:

- `assembled.step.py`: labeled deployed assembly, view-only.
- `part_front_shell.step.py`: printable wall-facing shell.
- `part_rear_shell.step.py`: printable phone-facing shell.
- `part_shadow_reel.step.py`: printable positive-silhouette reel.
- `part_kickstand.step.py`: printable fold-out stand.

Rebuild and verify from the workspace root with the materialized CAD skill and
the host Python. Generated `__cadgen__` caches are transient and not evidence.
The project-local `cadfits.py` vendors the small mating-clearance API used by
the source so `measure/check_fit.py` also works when the host copies this CAD
project into an isolated directory. Assembly occurrences deliberately omit
STEP presentation colours: OpenCascade presentation-entity ordering was not
byte-stable across clean processes. The required chromatic product view is the
deterministically rendered `snap/iso.png`; the primary STEP stays deterministic.

Project-specific audits are `measure/check_spec.py`, which checks the sealed
dimensions and four printable bodies, and `measure/check_fit.py`, which derives
every nominal paired clearance. `measure/motion.json` drives the full reel and
stand collision sweeps.

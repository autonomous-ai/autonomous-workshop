# Lantern Menagerie CAD project

Four separately printed rigid-filament parts form one captured shadow theatre:
front shell, rear shell, open-carrier reel, and kickstand. The exact optical
profiles come from the sealed Invent contract.

Print bed: `--bed 220x220x220`  
Reference process: 0.4 mm nozzle, 0.2 mm layers, no supports intended.

Assembly: seat the reel on the front spindle, gently squeeze the two kickstand
arms inward to place their outward trunnions in the rear blind bearing pockets,
align the shells, then press the four one-direction latch ramps through their
receivers until their +X shoulders recover. The reel rotates continuously in
both directions; the kickstand opens 112 degrees until its paired trunnion tabs
meet the broad rear stop posts, giving an approximately 82 mm deployed depth.
Reset where the large fixed through-arrow meets the unique right-rim double-V:
rabbit home is also the only pocket that releases an additional 0.25 mm of
nominal leaf travel. Six raised tactile tiles form an arrow that marks the
phone/beam side and points into the optical portal. Printed snap
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
every nominal paired clearance, including one-axis latch entry/flex/retention,
rounded detent tip, symmetric pocket ramps, and the three detent travels.
`measure/motion.json` drives forward/reverse rigid reel sweeps, four latch-lead
receiver paths, resting latch pullout retention, the stand arc, and both
endpoint overtravel checks. The paired rounded-tip/ramp and compliance values
remain explicit in the local fit audit because rigid-body motion cannot model a
printed leaf flexing. `measure/render_shadows.py` derives
the 72-pose sweep, all 12 indexed state/distance corners, and all 15
creature-by-centered/±2-degree alignment views from the exact four exported
meshes.

Host CAD-gate retry: the rejected fresh verifier completed the assembly refs
and validity responses but its single inspection process ended before the nine
remaining responses.  The near-circular frame and reel perimeters now use 72
source vertices instead of 144.  This retains six vertices per tactile reel
scallop, the exact 114 mm extrema, and the existing sealed dimensions while
materially reducing B-rep faces retained by that 11-request batch.  Exact
before/after topology counts and the fresh gate result are recorded in
`measure/host-inspection-batch-repair.md`.

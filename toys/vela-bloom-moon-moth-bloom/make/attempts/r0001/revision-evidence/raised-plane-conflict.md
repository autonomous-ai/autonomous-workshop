# Make evidence: raised service plane collides with sealed fixed roofs

This evidence is bound to Make checkpoint
`aec70d44f8c0d316f558881db5665e54fdc41697e3e27cb739e33a4255507cab`,
subject `8ed107c158e33e3527dfd10c03b347b4341057302f19ec1e0180ebe7fe52055e`,
and native Invented identity
`315a186e801ff81438458835be00c71b49ab150453bfea5f8faa8ed1e3cfcc22`.

## Sealed requirements inspected

The sealed `z_stack_and_assembly` puts both wing webs and complete root gears
at Z=4.5–7.5 mm in operation. It raises them 1.2 mm onto Z=5.7–8.7 mm
service shelves for assembly. Fixed gear-guard, entry-lip, and
moon-skin-bridge geometry starts at Z=8.0 mm and extends to Z=10.4 mm.

The same sealed sequence requires both geared roots to counter-rotate together
from ±118 degrees all the way to 0 degrees while they remain raised. Only at
0 degrees do aligned windows permit the 1.2 mm descent.

The sealed `safety_strategy` independently establishes horizontal coincidence:
during the final 18 degrees of closing, a moving wing edge is already at least
5 mm underneath an entry lip whose underside is Z=8.0 mm.

## Deterministic contradiction

During that final raised interval, the moving service stack occupies
[5.7, 8.7] mm and the horizontally coincident fixed roof occupies
[8.0, 10.4] mm. Their Z intersection is [8.0, 8.7] mm: a positive 0.7 mm
solid overlap. This is collision, not a missing tolerance. The later drop at
0 degrees cannot resolve a collision the mechanism must pass through before
reaching 0 degrees.

`check_raised_plane.py` recomputes the intervals from `sealed-z-stack.json`
and fails unless all sealed sequencing predicates hold and the overlap is
positive. Its canonical output is `interval-check.json`.

## Required Invent correction

Invent must revise the sealed kinematics and Z-stack so a rigid-body assembly
path exists. The smallest concept-preserving options are either:

1. seal a simultaneous paired-root descent before the moving edges enter the
   last 18-degree lip/bridge coverage, then complete closing in the operating
   plane; or
2. raise or locally reconfigure every fixed guard/lip/bridge underside along
   the complete raised service rotation so it clears Z=8.7 mm with an explicit
   manufacturing tolerance.

The revision must restate the exact drop angle/path, transition geometry,
clearances, and retention logic while preserving exactly three separately
printable parts, positive geared symmetry, guarded seated operation, and
tool-free assembly. Make cannot silently change those sealed requirements or
claim valid motion from colliding geometry.

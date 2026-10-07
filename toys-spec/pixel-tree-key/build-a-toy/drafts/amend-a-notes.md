# amend-a: R08 shared back face vs bauble recesses

Attempt 2 (wish-20261007-050112-49084163) stopped on a Contract Contradiction:
R08 said the star, the baubles and the body share one back face at Z 0, while
the bauble-recesses Interface puts each 0.8-thick bauble at Z 2.7 to 3.5.

## Change (requirement text only)

- R08: "the star, the baubles and the body share one flat front face at Z 3.5
  and one flat back face at Z 0" -> "the star and the body share one flat front
  face at Z 3.5 and one flat back face at Z 0, and every bauble's top is level
  with that front face".
- R06: adds "2.0 x 2.0 and 0.8 thick", the bauble geometry's own extents
  ([2.0, 2.0, 0.8]), so no reviewer reads the bauble as a 3.5 tile.

## Visible?

No. The bauble was always 0.8 thick (geometry extents, Interface Z 2.7-3.5).
The run's second Contract Reviewer called it visible in ref-04 because it read
the change as "3.5 -> 0.8"; ref-04 is a top view (camera [-90, 90]) whose thin
edge shading is the same for any thickness. No image is redrawn.

## Re-audit (Stages 3b, 3c, 3d)

- 3b: no image touched; every measurement in NOTES.md stands.
- 3c: bauble 0.8 thick = 4 layers at 0.2 (Taste: >= 3 layers); plan 2.0 x 2.0
  meets min_feature 2.0; R1/G1 web unchanged. Pocket roof Z 1.8, recess floor
  Z 2.7: 0.9 of green between them, >= min_wall 0.8.
- 3d: no moving parts.
- Other rows naming Z: R04 (body back Z 0, front Z 3.5), R05 (star full
  thickness), star-neck (star faces level with body at Z 3.5 and Z 0), R03
  pocket Z 0.8-1.8: all consistent with each geometry's extents.

## design-a-toy check (proposed)

Stage 2/3c: every requirement or Interface sentence that places several
Components on a shared face or Z level must agree with each named Component's
extents and Interface Z range. Not opened or merged: the owner asks before
anything reaches main.

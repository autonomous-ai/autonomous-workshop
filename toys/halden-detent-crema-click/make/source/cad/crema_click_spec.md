# Crema Click

Desk-resident demitasse clicker. Thumb presses the crema disc 4.5 mm [assumed]; two steel balls crest a ramp at 2.8 mm [assumed]; magnetic repulsion returns the disc 4.0 mm [assumed] above the rim.

## Envelope

88 x 66 x 56 mm [assumed] (object 86 x 64 x 53 mm [assumed]).

## Parts

| Role | File | Print stance |
| --- | --- | --- |
| cup_body | part_cup_body.step.py | Foot on the bed |
| crema_piston | part_crema_piston.step.py | Disc on the bed |
| foot_plug | part_foot_plug.step.py | Outer foot on the bed |

Stock: two 8.0 x 3.0 mm [assumed] N52 discs, two 6.0 x 2.0 mm [assumed] N52 discs, two 4.00 mm [assumed] steel balls, four 10.00 mm [assumed] steel balls. Magnets and balls are catalog misses; CAD authors pockets and envelopes, not catalog STEP. Foot capture is three 45 degree [assumed] printed ramps on 2.2 mm [assumed] lugs, not fasteners.

## Loop

Find the handle. Press the disc. Travel 4.5 mm [assumed]. Click at 2.8 mm [assumed]. The object stays on the desk.

## Rebuild

```bash
python "$CAD_SKILL_ROOT/scripts/gen" \
  cad/crema_click/crema_click.step.py \
  cad/crema_click/part_cup_body.step.py \
  cad/crema_click/part_crema_piston.step.py \
  cad/crema_click/part_foot_plug.step.py \
  --write
```

# Crema Click

A weighted espresso cup for a desk. Press the crema disc with a thumb; it clicks quietly and returns. The handle orients a hand that is not looking.

## Files

- `crema_click.step.py` — assembled view (not a print)
- `part_cup_body.step.py` — demitasse, foot on the bed
- `part_crema_piston.step.py` — wear part, disc on the bed
- `part_foot_plug.step.py` — foot plate, outer face on the bed
- `crema_click_lib.py` — parameters and builders

## Envelope

Assembled size 86 x 64 x 53 mm. Print bed 220 x 220 x 220 mm.

## Print

| Part | File | Stance |
| --- | --- | --- |
| cup_body | part_cup_body.step.py | foot down |
| crema_piston | part_crema_piston.step.py | disc down |
| foot_plug | part_foot_plug.step.py | foot down |

Nozzle 0.4 mm. PETG. Cup and plug cocoa brown; piston beige.

## Fit

`check_fit` on the three printable entries. Piston stem is `cadfits` slip in the chimney. Ballast wells are `cadfits` snug on 10 mm balls. Foot plug ramps rotate 60 deg onto cup lugs.

## Use

Leave the cup on the desk. Find the handle, press the disc, feel the click, let it return.

The piston flange enters from the foot before the plug is twisted on; a rigid-body sweep of that assembly step is not the seated cycle. Upward extraction after seating is blocked by the chimney lip. Downward extraction of the plug is blocked by the lugs. Magnet and ball insertion flex is not a rigid-body proof.

## Rebuild

```bash
python "$CAD_SKILL_ROOT/scripts/gen" \
  cad/crema_click/crema_click.step.py \
  cad/crema_click/part_cup_body.step.py \
  cad/crema_click/part_crema_piston.step.py \
  cad/crema_click/part_foot_plug.step.py \
  --write
```

# Racer Mecha - design notes (design-a-toy Stages 3 to 3d)

Images: AI generation and editing only (OpenRouter `openai/gpt-5.4-image-2`,
key from the main checkout's `.env`, never logged). No web imagery, so no
source URLs. Prompts are in `prompts/`. Post-processing: flood-fill key from
the border to alpha, crop, an anisotropic X stretch of at most 20%, pad to a
square with 9% margin, 800x800 RGBA. White-heavy parts (arm shell, forearm,
head) were first re-backed on flat grey by AI edit, because their whites
keyed out against the light grey render background.

| Ref | Source | X stretch | Rounds |
|---|---|---|---|
| ref-01 assembly | a1 (front view edit of the approved livery robot) | 0.958 | 1 |
| ref-02 torso | d-torso | 0.916 | 2 |
| ref-03 nose | f-nose | 0.807 | 3 |
| ref-04 head | g-head (edit of d-head), grey re-back | 1.138 | 3 + edit |
| ref-05 arm shell | c-arm, grey re-back | 1.156 | 1 |
| ref-06 forearm | g-forearm (edit of d-forearm), grey re-back | 1.176 | 3 + edit |
| ref-07 thigh | d-thigh | 1.163 | 3 |
| ref-08 shin | e-shin | 1.2 | 3 + failed edit |
| ref-09 spine | c-spine | 1.021 | 1 |
| ref-10 front wheel | c-wheel | 1.021 | 1 |
| ref-11 rear wheel | d-rwheel | 1.024 | 1 |

## Stage 3b - image against contract (final images, final contract)

Disagreement = off by more than 5% and more than 0.5 mm. Part images are
front views ([-90, 0]); Z is from the part's bottom.

| Image | Check | Contract | Image | Verdict |
|---|---|---|---|---|
| ref-01 | width / height | 101 / 221 | 101.6 / 221 | ok |
| ref-01 | boots, X | 3.5 to 31.5 each side | 3.0 to 31.1 | ok |
| ref-01 | shins at Z 30 | 60 across | 59.5 | ok |
| ref-01 | rear wheels at Z 55 | 85 across | 81.6 | ok (4%) |
| ref-01 | rear wheel centre / dia | 55 / 34 | 54.9 / 35.5 | ok |
| ref-01 | thighs at Z 90 | 51 across | 50.5 | ok (amended from 59.5) |
| ref-01 | belly wing at Z 100 / 113 | 54 | 50.8 / 57.5 | ok on average; edges blend with forearms |
| ref-01 | arms at Z 140 | X 30.5 to 50.5 | 30.1 to 50.8 | ok |
| ref-01 | torso at Z 140 | 58 | 55.8 | ok |
| ref-01 | front wheels at Z 175 | X 31 to 47 | 30.4 to 46.5 | ok |
| ref-01 | fist bottom | 97 | 95.6 to 98.3 | ok |
| ref-01 | wing at Z 213 | 83 | 79.9 | ok |
| ref-01 | top | 221 | 215.7 to 220 | ok |
| ref-02 | width | 61 | 60.5 | ok |
| ref-02 | towers | 13 wide, 12 tall | 13.6, about 12 | ok |
| ref-02 | pocket front wall top | 71 (Z 170) | 71.1 | ok (amended from 81) |
| ref-03 | width / wing height | 54 / 29 | 53.9 / 29 to 30 | ok |
| ref-03 | cone at 78 / 55 / 40 | 18 / 14.3 / 12 | 18.0 / 14.4 / 12.1 | ok (amended from 20 -> 12) |
| ref-04 | helmet width / post width | 19 / 8 | 19.0 / 7.5 | ok |
| ref-04 | post height / helmet height | 35 / 19 | 34 to 36 / 18 to 20 | ok (amended from 32 / 22) |
| ref-05 | width | 20 | 20.2 | ok |
| ref-06 | width | 14 | 13.8 to 14.0 | ok |
| ref-07 | width / tongue | 25 / 10 at X 3.5 to 13.5 | 24.7 / 9.3 at 3.4 to 12.7 | ok |
| ref-08 | shin width | 29.5 | 29.2 to 29.7 | ok |
| ref-08 | knee tongue | 14 | 14.5 | ok (amended from 12) |
| ref-08 | boot width | 28, stepped in 3 inboard | 30.1, flush | DISAGREES: raised at Stage 4 |
| ref-09 | wing width / boom | 83 / 20 | 83.4 / 20.7 | ok (boom amended from 14) |
| ref-09 | endplate drop below the wing | 5.5 | 5 to 8 | ok |
| ref-10, ref-11 | diameter | 38, 34 | 37.7, 33.9 | ok |

Contract amendments from the images (image judged better): torso 58 wide,
towers 13; arms out to 50.5; thighs 25 wide, narrower than the 29.5 shins;
boots 28 with a 7 gap; rear wheels Ø34 x 12 hugging the calves, front wheels
Ø38 x 16; rear wing 83 with taller endplates, moved behind the front wheels;
boom 20; nose cone 18 tapering to 12; helmet 19 on a 35 post; neck shows
through a lowered pocket wall. Every one was re-run through `model.py`.

## Stage 3c - printability

| Part | Feature | Size | Minimum | Verdict / resolution |
|---|---|---|---|---|
| all | engraved panel lines, finger grooves | 0.6 wide, 0.5 deep | 0.5 / 0.5 | ok |
| shin | raised knee pad | 1.0 proud | 0.5 | ok |
| head | crest | 2 wide, 1.5 high | 0.9 / 0.5 | ok |
| nose | blunt tip, wing edge | 4, 6 | land 0.8 | ok |
| nose | tip over air, standing on wing | - | 45 deg | tip underside chamfered 45 |
| wheels | spokes | 3 wide | 0.8 | ok |
| torso | stub bosses, nose cheeks | stick out sideways | 45 deg | 45 deg gussets under each |
| torso | halo hoop | 7 off the back | 45 deg | underside chamfered 45 |
| torso | hip slots, 11 wide | ceiling | bridge 12 | pointed arch |
| thigh | knee slot, 15 x 13 | ceiling | bridge 12 | pointed arch |
| shin | boot 3 past shin's outer face, stance on sole | ledge 3 | 45 deg | 45 chamfer under the shin's inboard edge |
| arm shell | was: open inboard, side stance | cantilevered inboard wall 19 | - | redesigned: open back, front-down stance, no ceilings |
| torso | was: shoulder tongue 15.5 sideways | overhang | - | redesigned: shoulder swings about X, dowel into the torso wall |
| all | horizontal bores | Ø2.9 / 3.1 / 3.2 | - | teardrop, point up |

Bed faces carry nothing: torso bottom (slots are cuts), thigh bottom, shin
sole, arm front, forearm side, spine wing top, head back, nose wing front,
wheel outer faces. Nothing is left out.

## Stage 3d - motion

No gears. Every transformation move and posing range is swept in `model.py`
(results in `checks.txt`), 36 steps, sections every 1/8 of the shared X span.

| Move | Worst gap | Against |
|---|---|---|
| nose fold 180 | 1.0 | torso |
| head slide 22 | 0.5 | torso |
| spine flip 180 | 0.5 | torso |
| forearm fold 180 (each) | 0.5 | arm shell |
| elbow forward 90 | 0.5 | arm shell |
| shoulder forward 90 / back 30 | 0.89 / 3.33 | front wheel |
| hip forward 20 / back 20 | 0.84 / 0.84 | torso |
| knee back 45 | 0.5 | thigh |
| car pose, all pairs | >= 0.5 | - |
| car on the ground | wheels lowest; torso and nose 1.5 up | - |
| robot balance | COM Y 0.3 on boots Y -13 to 9 | - |

Travel stops: the head slide stops on its dowel at both ends; every other
joint holds by friction and names no hard stop.

Camera claims: none. The prose's framing words ("nose plate on the frame's
vertical centre line" from [-90, 0]) hold: the nose is centred on X 0.

Earlier design changes, before the images: the feet do not fold (the boots
are the car's tail; a folding foot swept through the shin), the forearm folds
up and back into a shell open at the back, and the shoulders swing forward
and back instead of out.

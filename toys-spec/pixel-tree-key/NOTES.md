# Pixel Tree Key: design-a-toy working notes

Concept X1 Pixel Tree (`toys-spec/key-new/concepts/round5/x01_pixel-tree.jpg`),
chosen by the owner on 2026-10-07. Inventor `wyn-seal`, created and approved
for this toy on 2026-10-07.

## Stage 1 decisions

Owner (2026-10-07): new Inventor; the standard 21.5 x 11.5 x 0.75 mm inlay,
sealed at a print pause; colour by a multi-colour (AMS) print.

Inventor decisions: flush colour bodies (no relief), so the plate stays one
3.5 mm slab; 12 baubles (6 red, 6 gold) as the concept shows; the shaft groove
kept; filaments from the repository stock (`cadfilament.py`): PLA Matte "dark
green" #68724D, PLA Matte "dark red" #BB3D43, PLA Lite "sunflower yellow"
#FFB549. Matte stock has no pine green, so the green is more olive-sage than
the concept's.

## Stage 3: image provenance

All images AI-generated with OpenRouter `openai/gpt-5.4-image-2` through the
brainstorm-trend `generate_image.py` with input images (AI editing). No web
image was used.

| File | Made from | Round |
|---|---|---|
| a01 (working, not sealed) | x01 + prompt with the colours | 1 |
| t01 (working) | a01, re-viewed straight down | 1 |
| t03a (working) | t01; two outline pinches filled | 3 of 3 for that edit |
| ref-01-pixel-tree-key.png | t03a; R1 moved down one square (t04b) | 1 of 3 |
| ref-02-key-body.png | t01; star and baubles removed, recesses left | 1 (3 later variants measured worse) |
| ref-03-star.png | t01; star alone; then anisotropic resize 0.916 vertical (aspect gap 8.4%) | 1 |
| ref-04-bauble.png | t01; one red bauble alone | 1 |
| view-desk.png (illustration for the owner, not sealed) | ref-01, three-quarter view | 1 |

Criteria: one subject inside the frame; the pixel outline reads at thumbnail
size; contrast holds on #f5f0e6; outline, bauble count and positions agree
with the contract (Stage 3b).

## Stage 3b: reconciliation

Scripts in `measure/` (they read images; none draws one). The contract was
derived from t01's measured proportions (the image is the owner's approved
look), at 0.1256 mm/px so the key is 82.25 mm long. Disagreement: off by more
than 5% and more than 0.5 mm. Positions use 5% of the distance from the datum
(X 0, Y 0).

Decisions (image vs contract):
- Tree widths, tier heights, the stepped underside, the shaft, the bit and the
  tab: taken from the image.
- t01 had two short inward pinches (under T2 and mid-T4) that ref-02 lacks;
  the contract keeps the plain staircase, and the assembly image was edited
  (t03a).
- R1 and G1 touched corner to corner in the images; recesses need a 1.6 mm web,
  so R1 moved to Y 19.2 and G1 to (-1.9, 22.85); ref-01 was edited (t04b).
- Star neck 2.5 wide (image 2.38) so the star's mount is as strong as the image
  allows.

### ref-01 (assembly, camera [-90, 90]) outline: every band agrees

```
neck     Y  32.00.. 33.00  contract  -1.25..  1.25  image  -1.19..  1.19  ok
T1       Y  30.00.. 32.00  contract  -3.10..  3.10  image  -2.95..  3.20  ok
T2       Y  25.75.. 30.00  contract  -4.90..  4.90  image  -4.84..  5.09  ok
T3       Y  23.75.. 25.75  contract  -6.75..  6.75  image  -6.72..  6.85  ok
T4       Y  17.50.. 23.75  contract  -8.50..  8.50  image  -8.48..  8.60  ok
T5       Y  15.50.. 17.50  contract -10.40.. 10.40  image -10.36.. 10.61  ok
T6       Y  13.00.. 15.50  contract -12.20.. 12.20  image -12.25.. 12.37  ok
T7       Y  10.75.. 13.00  contract -13.90.. 13.90  image -13.75.. 13.88  ok
T8       Y   8.50.. 10.75  contract -15.60.. 15.60  image -15.51.. 15.64  ok
T9       Y   6.00..  8.50  contract -17.30.. 17.30  image -17.14.. 17.27  ok
T10      Y   3.50..  6.00  contract -18.95.. 18.95  image -18.90.. 19.03  ok
T11      Y   0.00..  3.50  contract -20.70.. 20.70  image -20.54.. 20.66  ok
U1       Y  -2.00..  0.00  contract -18.95.. 18.95  image -18.78.. 18.90  ok
U2       Y  -4.50.. -2.00  contract -17.30.. 17.30  image -16.89.. 17.02  ok
U3       Y  -6.50.. -4.50  contract  -7.50..  7.50  image  -7.35..  7.47  ok
shaft    Y -23.00.. -6.50  contract  -4.75..  4.75  image  -4.58..  4.71  ok
bit1     Y -25.00..-23.00  contract  -4.75..  7.75  image  -4.58..  8.10  ok
tooth1   Y -28.25..-25.00  contract  -4.75.. 10.50  image  -4.58.. 10.61  ok
bit2     Y -29.50..-28.25  contract  -4.75..  7.75  image  -4.58..  8.23  ok
notch    Y -31.50..-29.50  contract  -4.75..  5.75  image  -4.58..  5.84  ok
tooth2a  Y -33.75..-31.50  contract  -4.75.. 10.50  image  -4.58.. 10.49  ok
tooth2b  Y -36.50..-33.75  contract  -4.75.. 12.25  image  -4.58.. 12.25  ok
bit3     Y -39.00..-36.50  contract  -4.75..  7.75  image  -4.71..  8.23  ok
bit4     Y -41.00..-39.00  contract  -4.75..  5.75  image  -4.71..  5.84  ok
tab      Y -43.25..-41.00  contract  -2.00..  3.00  image  -2.07..  3.33  ok
arm-bottom Y  33.00.. 35.00  contract  -1.00..  1.00  image  -1.07..  1.32  ok
bar      Y  35.00.. 37.00  contract  -3.00..  3.00  image  -2.95..  3.08  ok
arm-top  Y  37.00.. 39.00  contract  -1.00..  1.00  image  -1.07..  1.19  ok
```

### ref-01 baubles

```
R count image 6 contract 6
  R1 contract (0.50,19.20) image (0.12,18.72) off 0.61 ok
  R2 contract (-5.50,15.25) image (-5.38,15.63) off 0.40 ok
  R3 contract (5.50,15.25) image (5.63,15.65) off 0.42 ok
  R4 contract (4.25,4.00) image (4.27,4.26) off 0.26 ok
  R5 contract (14.50,3.50) image (14.51,3.83) off 0.33 ok
  R6 contract (-0.75,-0.25) image (-0.75,0.06) off 0.31 ok
G count image 7 contract 6
  G1 contract (-1.90,22.85) image (-1.70,22.98) off 0.24 ok
  G2 contract (1.25,11.25) image (1.32,11.80) off 0.56 ok
  G3 contract (8.75,8.00) image (8.69,8.34) off 0.34 ok
  G4 contract (-5.00,7.25) image (-5.07,7.73) off 0.48 ok
  G5 contract (-13.50,4.50) image (-13.35,4.92) off 0.44 ok
  G6 contract (10.25,0.00) image (10.32,0.34) off 0.35 ok
```

### ref-02 (key-body, camera [-90, 90]) outline

```
neck     Y  32.00.. 33.00  contract  -1.25..  1.25  image  -1.12..  1.12  ok
T1       Y  30.00.. 32.00  contract  -3.10..  3.10  image  -2.97..  3.10  ok
T2       Y  25.75.. 30.00  contract  -4.90..  4.90  image  -4.81..  4.81  ok
T3       Y  23.75.. 25.75  contract  -6.75..  6.75  image  -6.79..  6.79  ok
T4       Y  17.50.. 23.75  contract  -8.50..  8.50  image  -8.51..  8.51  ok
T5       Y  15.50.. 17.50  contract -10.40.. 10.40  image -10.49.. 10.62  ok
T6       Y  13.00.. 15.50  contract -12.20.. 12.20  image -12.20.. 12.33  ok
T7       Y  10.75.. 13.00  contract -13.90.. 13.90  image -13.78.. 13.78  ok
T8       Y   8.50.. 10.75  contract -15.60.. 15.60  image -15.50.. 15.63  ok
T9       Y   6.00..  8.50  contract -17.30.. 17.30  image -17.21.. 17.21  ok
T10      Y   3.50..  6.00  contract -18.95.. 18.95  image -18.80.. 18.93  ok
T11      Y   0.00..  3.50  contract -20.70.. 20.70  image -20.51.. 20.64  ok
U1       Y  -2.00..  0.00  contract -18.95.. 18.95  image -18.80.. 18.80  ok
U2       Y  -4.50.. -2.00  contract -17.30.. 17.30  image -16.95.. 16.95  ok
U3       Y  -6.50.. -4.50  contract  -7.50..  7.50  image  -7.45..  7.58  ok
shaft    Y -23.00.. -6.50  contract  -4.75..  4.75  image  -4.55..  4.68  ok
bit1     Y -25.00..-23.00  contract  -4.75..  7.75  image  -4.55..  7.98  ok
tooth1   Y -28.25..-25.00  contract  -4.75.. 10.50  image  -4.55.. 10.35  ok
bit2     Y -29.50..-28.25  contract  -4.75..  7.75  image  -4.68..  8.77  DISAGREE
notch    Y -31.50..-29.50  contract  -4.75..  5.75  image  -4.55..  6.79  DISAGREE
tooth2a  Y -33.75..-31.50  contract  -4.75.. 10.50  image  -4.68.. 10.35  ok
tooth2b  Y -36.50..-33.75  contract  -4.75.. 12.25  image  -4.68.. 12.07  ok
bit3     Y -39.00..-36.50  contract  -4.75..  7.75  image  -4.68..  8.11  ok
bit4     Y -41.00..-39.00  contract  -4.75..  5.75  image  -4.68..  5.74  ok
tab      Y -43.25..-41.00  contract  -2.00..  3.00  image  -2.04..  3.23  ok
```

bit2 and notch: the luminance threshold catches the soft shadow under tooth 1.
Row samples of the face itself end at X 7.85 (bit2, Y -28.9) and X 5.5
(notch, Y -30.5): agree.

### ref-02 recesses

```
14 recesses, scale 0.1319
R1 contract (0.50,19.20) image (0.20,18.29) 1.98x2.11 off 0.91 ok
R2 contract (-5.50,15.25) image (-5.47,14.60) 1.98x2.11 off 0.65 ok
R3 contract (5.50,15.25) image (5.54,14.60) 2.11x2.11 off 0.65 ok
R4 contract (4.25,4.00) image (4.16,3.38) 1.98x2.11 off 0.62 DISAGREE
R5 contract (14.50,3.50) image (14.38,2.99) 2.11x2.11 off 0.51 ok
R6 contract (-0.75,-0.25) image (-0.92,-0.71) 2.11x2.11 off 0.46 ok
G1 contract (-1.90,22.85) image (-1.78,21.92) 1.98x1.98 off 0.93 ok
G2 contract (1.25,11.25) image (1.19,10.77) 2.11x2.11 off 0.48 ok
G3 contract (8.75,8.00) image (8.57,7.41) 2.11x1.98 off 0.59 DISAGREE
G4 contract (-5.00,7.25) image (-5.21,6.81) 1.98x2.11 off 0.44 ok
G5 contract (-13.50,4.50) image (-13.39,3.98) 1.98x1.98 off 0.52 ok
G6 contract (10.25,0.00) image (10.22,-0.44) 1.98x2.11 off 0.44 ok
```

ref-02 sits 0.5 mm low as a whole (its datum, the neck top, is soft); with that
registration offset removed every recess is within 0.5 mm.

### ref-03 (star, camera [-90, 90])

```
scale 0.0135 mm/px  centre px 401.0
band     contract xl..xr image xl..xr   verdict
arm-bottom  -1.00..  1.00   -1.02..  1.03  ok
bar       -3.00..  3.00   -3.01..  3.02  ok
arm-top   -1.00..  1.00   -1.00..  1.02  ok
```

### ref-04 (bauble, camera [-90, 90])

Face aspect 0.93 against 1.0: 0.14 mm on a 2.0 mm tile, under 0.5 mm: agrees.

### Aspect

| Image | Contract W/H | Image W/H | Verdict |
|---|---|---|---|
| ref-01 | 41.4 / 82.25 = 0.503 | 0.498 | agrees |
| ref-02 | 41.4 / 76.25 = 0.543 | 0.536 | agrees |
| ref-03 | 1.000 | 1.000 (after resize) | agrees |
| ref-04 | 1.000 | 0.93 (0.14 mm) | agrees |

### Reference cameras

All four are straight down on the front face with the star up: [-90, 90].
Cue: only the front face shows; a thin band of side face shows along the lower
edges (about 8 degrees of tilt), which rounds to 90.

### Joint features

The star-neck seam (Y 33.0) shows in ref-01 and ref-02 (neck top) as drawn.
Each bauble recess shows in ref-02 as an empty square, and each bauble flush in
ref-01.

## Stage 3c: print

| Feature | Size | Minimum | Verdict |
|---|---|---|---|
| Neck (star mount) | 2.5 wide | 0.8 (min_wall) | passes |
| Star arms | 2.0 wide | 0.8 | passes |
| Bit notch step | 1.0 | 0.8 | passes |
| Tread of each pixel step | 1.7 to 1.9 | 0.8 | passes |
| Groove | 1.0 wide, 0.6 deep | 0.5 / 0.5 | passes |
| Bauble recess | 2.0 wide, 0.8 deep | 0.5 / 0.5 | passes |
| Bauble tile | 2.0 x 2.0 x 0.8 | 0.8 thick | passes |
| Web between recesses | 1.6 least (R1-G1) | 1.6 (min_web) | passes |
| Recess to outline | 1.0 least | 0.8 | passes |
| Pocket floor | 0.8 | 0.8 | passes |
| Plate over pocket under a recess | 0.9 | 0.8 | passes |
| Pocket wall in plan | 2.0 least | 0.8 | passes |
| Pocket roof bridge | 11.9 | 12 (check_overhang --bridge) | passes |

Stacked or curved details: none (baubles are flush inlays, not relief).
Support: every side face is vertical in the back-face-down stance; the only
ceiling is the pocket roof, a bridge. No hidden pegs: both Interfaces are flat
fused contacts. No moving part, so no swept ceilings.

## Stage 3d

No moving parts. No requirement names a camera or a composition claim.

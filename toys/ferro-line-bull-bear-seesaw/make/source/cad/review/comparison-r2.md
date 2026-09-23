# Wish comparison — round 2

Verdict: **PASS — visible form and selected-state expression requirements match. Blocking visual departures: none.** Prior round-1 findings remain unchanged in their original files. This comparison follows a fresh inspection of both canonical images, then reading `WISH.json` and current `design/spark-source.json` only. It is an informed rereview, not a second blind test.

## Exact reviewed images

| Image | SHA-256 |
| --- | --- |
| `artifacts/make/r0001/product/cad/snap/iso.png` | `8ff79ae08ebe057fe2e44a4cd9db7d00170e7ab42177994781ce334f53f39d37` |
| `artifacts/make/r0001/product/cad/snap/signature.png` | `40cebe14843d93feba568d371f1976ceeb3430d88834797fa5a0a93003700403` |

## Explicit requirements

| Requirement | Evidence | Matches |
| --- | --- | --- |
| Tabletop seesaw with fixed stand, central pivot, rocking beam | Isometric shows a grey mast, beam, circular central axle and broad base; panel sheet shows the beam level and tilted about the center. | Yes, visible structure and selected poses. |
| A charging bull on one end | Gold figure has long laterally swept/upturned blunt horns, separate recessed ears, large beige bovine muzzle, lowered brow cuts and hoof divisions. Broad frontal stance reads as a stylized challenging/charging bull, not the prior cat. | Yes. Round-1 species blocker resolved; charging treatment is cartoon-like rather than a running sculpture. |
| Bear on other end | Brown figure has round ears, black eyes and dark oval nose. | Yes. |
| Playful stock-market interpretation | Bull and bear pairing, reciprocal rise/fall and asymmetric happy/crying faces form the market joke. | Yes. |
| Push either end down, other end rises | Left and right panels show opposed end heights on the same beam. | Selected-state appearance matches; actual pushing/operation unverified. |
| Roughly 200 mm length, fits a desk | Current source declares a 200 mm neutral overall length and 70 mm depth. Images show a compact desktop composition, without a physical scale reference. | Matches declared scale and visual intent; dimensions not independently measured in this review. |
| Self-standing, stable base | Broad rounded rectangular base beneath a central stand, with visible base connection. | Self-standing visual form matches; physical stability unverified. |
| Both expressive faces face the viewer | Front views expose all eyes, nose/muzzle and expression regions without overlap. | Yes. |
| At level bull mouth closed | Middle panel has a straight closed mouth within beige muzzle, no dark open-smile area. | Yes. |
| At level bear eyes plain and no tears | Middle panel has plain black eyes; no light-blue drops beneath them. | Yes. |
| Bull rises: mouth opens into a wide happy smile | Left panel has a conspicuous dark open smiling mouth occupying a substantial part of the muzzle. | Yes. |
| Bear rises: cries, tears appear at its eyes | Right panel shows two pale-blue narrow trails immediately below the eyes ending in rounded drops. They read as tears, not the former isolated triangular fangs. | Yes. Round-1 crying blocker resolved. |
| Bull reacts only when bull end rises | Bull is smiling in left-high, closed at level and right-high. | Yes at all three selected states; intermediate travel unverified. |
| Bear reacts only when bear end rises | Blue eye-connected drops appear only in right-high, absent at level and left-high. | Yes at all three selected states; intermediate travel unverified. |
| Returning level restores both neutral; neither triggered at level | Middle panel displays both neutral simultaneously. | Neutral state matches; return operation unverified. |
| Front-visible effects at about 15–20 degrees | Source states +/-18 degrees; end panels visibly fall in that intended range and both expressions are readable at sheet size. | Yes for selected-state visual presentation; angle not independently measured here. |
| Pure tilt-driven mechanism relative to fixed stand or gravity | Isometric shows a central fixed-looking peg engaging a slotted carrier; source describes a fixed peg and translated expression masks. | Visually/source-plausible; no motion proof claimed or required by this review. |
| No motors, batteries, electronics, purchased springs | No such items appear; current source describes printed bodies, carriers, covers and pins only. | No visible or source-declared conflict. Absence is not a physical inspection. |
| FDM PLA/PETG on 0.4 mm nozzle | Thick solid-looking parts and source print stance are consistent with intent. Parent reports separate deterministic checks. | Engineering requirement outside still-image proof; not counted as a physical pass. |
| Prefer support-free printing | Source describes broad-face printing of bodies and plates, base on footprint and pins upright. Parent reports overhang checks. | Separate engineering evidence; no visual contradiction. |
| Hand assembly without glue or with printed pins/snap fits | Visible pin heads and retained cover features; source names printed pins and cross-keys and fourteen printed roles. | Source/form consistent; assembly unverified physically. |
| Real moving-part clearance, no binding | Clearances are declared in source; neither still shows gross visible clash. | Requires engineering and physical evidence; motion unverified and not inferred. |
| Bull warm brown/gold, darker mouth | Gold body, beige muzzle, dark mouth. | Yes. |
| Bear dark brown/charcoal, light-blue tears | Dark brown bear, light-blue eye-associated drops in active state. | Yes. |
| Neutral stand; few clear colors | Grey stand/base/beam with beige carrier; constrained gold, beige, brown, dark facial and blue tear colors. | Yes. |

## Remaining limitations

The isometric view exposes the bear's blue rear backing and internal parts above the head; front views keep these from competing with the tears. The central linkage and large printed-looking fastener heads are visually prominent. Neither is a remaining explicit visual-requirement failure, and neither warrants another repair cycle. The round-1 bull and tear failures are resolved in the actual images, not deferred to prose or caveats.

The host reports the panel states as discrete exact-STEP states. They are not an animation. Motion checking is disabled; the review makes no claim of continuous operation, print success, fit, retention, stability or durability. Engineering reports and host finalization remain independent gates.

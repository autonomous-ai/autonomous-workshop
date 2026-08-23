Verdict: PASS

Scope: third playability pass, re-checking only the urchin_shell/pearl_rack n=3 grip-knob fix (vertex-forward special case in `face_forward_rot_deg()`), against draft/build/draft_review/ renders.

## urchin_shell_01 (n=3 grip knob)
Zoomed iso crop of the knob (draft_review/urchin_shell_01.png) now shows a clean flat triangular top cap with two flat vertical side faces (one lit, one shaded) meeting at a near-vertical edge in the center-front — the same "two-faces-plus-flat-cap" read as shells 02 (square), 03 (pentagon), 04 (hexagon) in side-by-side crops. The earlier single-vertex apex/pyramid artifact is gone: there is no point where all silhouette edges converge to a peak in iso or front view. Front/iso/back/left/right renders for shell_01 are now proportioned like the other three shells (same overall knob height and footprint), and the polygon read (3 flats vs 4, 5, 6) is legible at a glance for distinguishing player identity, matching the rule text ("read by counting edges").

## pearl_rack_01 (matching n=3 finial)
Same check applied to the small prism finial at the rack's end. Zoomed iso crops (rack01_finial_v2.png vs rack02/03/04_finial_v2.png) show rack_01's finial with a flat triangular top and two flat side faces meeting at a vertical edge — consistent with rack_02 (square), rack_03 (pentagon), rack_04 (hexagon), each readable by edge count and none showing a pyramidal peak. The four racks remain visually distinct from one another and each finial still cosmetically matches its corresponding shell's knob shape.

## Whole-object sanity check
_assembled.png hero and _qa.png six-view grid show the full component set (board, 4 shells, 4 racks, spines, pearls, tide_pot) assembled without any new artifacts introduced by the targeted fix — nothing else in the piece family shapes changed.

This closes the last open finding from the two previous playability passes (shell_01 read as a peaked pyramid instead of a flat 3-sided prism). No other legibility, distinguishability, or handling issues are raised in this pass; earlier passes already cleared shells 02–04, the racks' well/scallop legibility, spine/pearl handling, and board pan legibility, none of which were touched by this repair.

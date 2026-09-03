# Moonchase Fox CAD brief

- Model: one-piece desk rocker; no assembly and no purchased components.
- Task type: new STEP-first printable product from prose.
- Units: millimetres.
- Coordinate convention: the recognizable fox silhouette lies in XY; Z is the 24 mm print thickness. The print stance is the flat back at Z=0. In use, the toy stands on the tail's lower circular arc in XY.
- Envelope target: about 94 mm long, 24 mm wide, and 78 mm tall in use.
- Signature interaction: one gentle side nudge rolls the monolithic fox along the tail arc through a small chase toward its nose, then gravity returns it to the drawn upright pose.
- Anti-generic signature: the tail is simultaneously the fox's dominant curled silhouette and the functional rocker; a true crescent through-window reads upright at rest.
- Functional geometry: the lower portion of a 45 mm-radius convex tail track, centered off the anatomy axis; track curvature center above the solid's center of mass; broad 24 mm lateral contact width; a rounded C-shaped crescent cut with finite ends; smooth oval ears and tail bulb without knife tips.
- Manufacturing assumptions: FDM, 0.4 mm nozzle, 0.2 mm layers, PLA/PETG-like rigid plastic; 220 x 220 x 220 mm bed; no supports. The flat Z=0 side is the only declared print stance.
- Paths: `moonchase_fox.step.py` -> `moonchase_fox.step`, `moonchase_fox.stl`, and `snap/iso.png`.
- Validation targets: exactly one positive-volume solid; one connected mesh shell; bed contact at Z=0; envelope under 110 x 91 x 30 mm in print coordinates; through-window; center of mass below the track center; center-of-mass horizontal offset from track center no greater than 0.1 mm and predicted rest tilt no greater than 2 degrees; full final CAD pipeline including mesh and 0.4 mm nozzle thickness gate.
- Assumptions: digital geometry can establish static balance intent and local restoring geometry but cannot prove real rocking duration, damping, surface friction, print durability, or human delight.

## Parameter provenance

All dimensions are Wish-derived or assumed for a palm-sized FDM object. There are no catalog parts. The tail/contact family is a circular convex rocker selected over an elliptical arc (less predictable curvature) and a twin-foot cam (visible stop and harsher reversal).

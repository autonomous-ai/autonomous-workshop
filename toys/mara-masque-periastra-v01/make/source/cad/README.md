# Periastra CAD

Text-derived miniature English draughts in a removable-roof observatory. Four independently printable designs form 26 physical parts: one base, one roof, twelve single-tail comets and twelve forked-tail comets. No hardware or power.

`periastra.step.py` is the combined closed assembly; `assembly.py` positions its live-source children. `part_base.step.py`, `part_roof.step.py`, `part_single_comet.step.py` and `part_forked_comet.step.py` return bed-oriented parts. `periastra_lib.py` holds dimensions and geometry.

Base 190 by 190 by 24 mm, board 176 mm with 22 mm cells and 0.8 mm alternate recesses. Print on a 220 by 220 mm or larger bed, 0.4 mm nozzle. All part bottoms sit at Z=0. Roof backing rests on integral base ledges at Z=21; nominal lateral clearance 0.8 mm per side. Slide the loose roof vertically upward 100 mm for the illustrated reveal, then set it aside to play. The base stops downward roof motion; no upward latch exists. Store all 24 counters in starting rows beneath it; roof underside is 10 mm above smooth board floor. Counters are 7 mm thick with 16 mm maximum planar extent and broad 0.6 mm crown recesses. The small lower square bevel improves one-colour board legibility.

Digital verification is required before the final handoff. No physical print, tactile fit, strength, durability or human playtesting has occurred. Miniature equipment and reversible crowns are explicitly requested substitutions for tournament equipment; legal gameplay follows WCDF 2012 section 1, unrestricted opening.

Recess corners use a 1.5 mm radius to avoid diagonal point contacts; cell pitch and full side width remain 22 mm. Corner webs stay at the smooth floor height, with no raised grid. Final mesh checks include manifold edges and vertices.

# Neststomp CAD

Two support-free printed parts, designed in millimetres for a 220 × 220 × 250 mm FDM bed and 0.4 mm nozzle.

- `part_owl.step.py`: owl body/frame, printed on its broad flat back (`Z=0`).
- `part_chick.step.py`: loose rounded triangular cam/chick, also printed on its broad flat back.
- `assembled.step.py`: non-printable review assembly with the chick at the left endpoint.

The open belly is 54 mm wide and the chick is 36 mm wide in front view. Its 22.4 mm depth sits centrally within the owl's 24 mm depth, leaving the requested 0.8 mm visible running gap at each face. Broad chamber sides define a 16.4 mm left-to-right stop travel. The chick is not snapped in: gravity and the tabletop confine it during upright interaction, and it remains removable when the owl is lifted. The CAD checks envelope, depth gaps, exact endpoint placements, topology, mesh, and minimum wall dimensions. It does not prove real-world friction, balance, stomp crispness, durability, or first-user discoverability; physical playtest was not run for this Spark route.

Print both parts with the flat rear face on the bed. No supports, glue, fasteners, magnets, or electronics are required. Remove loose strings before use. This is a desk toy, not intended for children under 3 years due to the removable part.

Local fit/print audit: run `python measure/check_fit.py`; it verifies the two declared solids, broad flat print backs, the 0.8 mm depth gaps, minimum 7 mm chamber-side walls, and the explicit owl/chick placement order.

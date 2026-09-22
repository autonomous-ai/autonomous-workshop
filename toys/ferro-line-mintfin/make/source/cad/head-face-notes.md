# Completed head/face source handoff

Owned files: head_faces.py and the four part_head / part_face_<mood> entry generators. Each entry contains exactly one gen_step(). Geometry has not been generated, inspected, or passed by this agent; Manager owns those tool calls. head_faces.py is below400 lines and imports mintfin_lib.male_pin at module scope. No Sphere, purchased hardware, animation or motion checks.

Public API:

- head(): one asserted connected printable solid, bedZ0, outgoing male pin atX34.
- face('happy'|'sleepy'|'angry'): one asserted connected printable solid, backZ0.
- FACE_INSTALL = Pos(0,0,17.6), also FACE_SEAT_Z.
- HEAD_FACE_PARAMS dict, FACE_POCKET_WIDTH/LENGTH derived with cadfits.slot_for.
- head_color_masks(): coral gill masks, charcoal horn masks, cream lower-belly box. Masks may overlap canonical core; they are not disjoint final material volumes. Intersect with canonical head and subtract prior selections to produce disjoint color regions; default mint.
- face_color_masks(mood): cream sparkle masks first, charcoal expression masks second; default cream. Preserve this priority because sparkles overlap eye marks intentionally. Every color is part of one fused canonical printed solid.

Specific design resolutions:

1. Head crown remains26×34 mm atZ20.4, so pocket cheeks have material. Four ruled rounded-rectangle sections avoid spherical poles and unstable spline blends.
2. Horn centresX23.9 Y±10, radii2.05→0.8, Z18.5..25. Rear limit25.95 stays ahead of bearing26.8; at face topZ20 the horn front limit22.14 stays behind faceX22. Their bases overlap shell for one connected solid.
3. Face rootX20/free tipX8 retains12 mm working arm length,1.2 mm width,2.4 mm height. Through-slots0.8 mm with rounded ends define XY flex. Catch centredX10 extendsX9..11. Front access cut endsX9 so tip is exposed while retaining catch walls behind it.
4. Catch0.35 mm radial projection; head throat gives0.15 mm per-side clearance, nominal required deflection0.20 mm. Groove relief0.55 mm beyond throat. Both catch and groove have ramped sections; catch has0.7 mm flat ridge height. Groove cuts extend entirely throughX=-5..35, avoiding blind cutting-tool end faces inside curved shell walls.
5. Face happy/angry eyes7 mm diameter,1.2 mm proud of plate;1.6 mm diameter cream sparkles are connected to the eyes. Sleepy uses1.4 mm wide closed-eye strokes. Mouth strokes1.2 mm. Actual plate ornament height reaches4.25 mm, not the preliminary3.6 mm estimate; installed maximum21.85 remains under25 mm envelope. Source concept dimensions should update to[20,28.7,4.25].
6. Gills are six separate broad loft masks fused to head, each4.6×11 mm footprint, contracting aboveZ7. RootY16 intersects the head; maximumY±27. Min fin-tip section3.4×9.8 eliminates thin twigs. Sideview silhouette remains chunky.

Required root evaluation: build all four entries, inspect one-solid/bed assertions and exact head/installed-face intersection; run isolated component Make rounds; check snap groove and slot thickness/overhang evidence; inspect marks to ensure they read as expressions. The source is a concrete candidate, not proof of printed release or durability. No extra CAD generation was run concurrently with the Manager.

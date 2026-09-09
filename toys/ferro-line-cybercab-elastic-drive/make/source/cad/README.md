# Cybercab Elastic Drive

A180 ×78 ×60 mm mechanised adaptation of the supplied Cybercab photograph, with a removable angular shell and an elastic rear-axle drive. The toy size is authored; it is not a measured prototype scale. No physical run, printed fit, traction, latch fatigue or band life has been demonstrated.

## Parts and printing

The assembly has nine occurrences: eight printed occurrences from six unique printable geometries, plus one purchased, nonprintable elastic loop. Print:

| Geometry | Quantity | Role |
|---|---:|---|
| chassis |1| Floor, journals, anchor, slide rails and thumb latch |
| body |1| Reference silhouette, journal caps, rail sleeves and latch striker |
| front wheelset |1| Axle with one integral disc wheel |
| rear wheelset |1| Axle with one integral wheel and winding finger/spool |
| end wheel |2| Separate keyed wheel, bonded to each axle |
| window |2| Left and right opaque dark inserts |

Rigid material is PLA with a 0.4 mm nozzle. Print the chassis flat, shell nose-down, each axle upright on its integral wheel, and each separate end wheel socket-up. Use a brim to stabilise the upright axles and shell. Print windows flat. Follow the exact exported print orientations and current thickness/overhang reports; digital checks do not certify slicer output or a physical print. Clear journals, rail channels and latch clearance carefully before assembly.

Purchase one elastic loop and a small quantity of plastic-compatible adhesive for the window inserts and keyed end wheels. Optional traction loops may be fitted to the broad rear wheel treads if bare wheels slip. The drive-loop CAD envelope represents purchased material, not a printable part. The nominal round cord radius is0.7 mm; its installed centreline chord perimeter is219.184 mm at0° and229.631 mm at−90°. These are CAD envelope lengths, not a relaxed purchase length or a measured extension limit. Its nominal dimensions are provisional and require fitting to the actual finished hooks; physical tension, stiffness and fatigue are unknown.

## Assembly and use

1. Inspect the 6 mm axles and 6.5 mm journals. Dry-fit each separate end wheel on its 3.4 mm square axle key in the 3.9 mm socket. Bond the keyed joint with plastic-compatible adhesive and allow full manufacturer-specified cure before loading it. Keep adhesive away from shaft bearing surfaces. Axial retention and adhesive strength require physical confirmation. Place front wheelset atx148 and rear wheelset atx34, with the winding finger centred in the channel. Both axle centres are16.5 mm above the floor plane. Check free rotation without elastic.
2. Bond the two dark window inserts into the matching body recesses with a thin application of plastic-compatible adhesive. Keep adhesive off rails, caps and moving parts; allow the adhesive manufacturer's full cure time. These are opaque inserts, not glazing that opens.
3. With the shell removed, fit the elastic around the front anchor atx134 and loosely onto the rear finger. Do not tie the rear connection permanently. The floor has central clearance x24.5..125,y±6.5 mm for the low elastic strand. The loop must remain inside its channel and must not rub a journal, latch or wheel. Relaxed loop size and safe extension require physical fitting.
4. Align the shell4 mm rearward of its closed position. Lower it onto the chassis, press the thumb latch inward toward the centreline and slide the shell4 mm forward. Release the latch and check that both X directions are stopped and the shell cannot lift. The tooth is rectangular with no closing ramp: press the latch during both closure and opening; do not force automatic snap closure.
5. To commission, roll the car backward by one-quarter rear-wheel turn, hold, place on a clear flat floor and release nose-first. Stop if the band snags, the latch deforms, the wheels bind or the tyres slip. Do not exceed this quarter-turn commissioning instruction. No physical powered quarter-turn run has been demonstrated; this is a proposed initial trial, not a qualified strain limit or performance promise. A full rigid wheel-clearance sweep does not authorize a full elastic winding turn.
6. To reset, stop all wheel motion. Press the underside latch inward1.9 mm, hold it while sliding the shell rearward4 mm, then lift. Rehook the slack elastic and close as above. No tool should be needed. If the latch or shell binds, stop rather than forcing it.

The open rear finger is intended to release the spent loop to avoid reverse winding. Release reliability and nose-first powered travel need physical confirmation. Keep fingers and hair clear of moving parts; supervise assembly and keep small pieces away from children under3. Inspect and replace damaged elastic before use.

## Evidence

See `cybercab_spec.md` for the observed/inferred/authored reference ledger, audit targets and vault responses. Executable geometry lives in `cybercab_lib.py`; exact-state measurements and motion checks are under `measure/`. Digital clearance and motion evidence does not establish physical printed fit or durability.

Winding convention: backward rolling is negative rotation about global +Y. The geometric powered release runs from−90° to0° for forward +X travel. Rear loop centreline radius5.1 mm clears the radial finger and its printable buttress in the sampled installed envelope. The tensioned material shape and loaded contact remain unqualified. At−90° the rear semicircle lies behind the finger toward−X. This installed geometric envelope does not qualify material deformation or prove loaded contact. Rear endpoints are(39,±5.1,16.5) mm at0° and(34,±5.1,21.5) mm at−90°; front endpoints remain(134,±4.2,14.5) mm.

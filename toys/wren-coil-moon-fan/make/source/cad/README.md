# Moon Fan
Hold the dark fixed crescent in your palm. Press the gold leaf's lower terminal sideways to fan it outward; press the opposite exposed edge to return it to the crescent stop. Travel is75 degrees. Use one finger for each press, supporting the fixed body with the palm. There is no spring-powered jump, same-button latch, or guaranteed unattended state holding.

Four unfilled-PETG prints, 0.4mm nozzle; --bed 220x220x220.
- part_carrier.step.py: flat bottom on bed.
- part_leaf.step.py: flat outer face on bed, integral stop peg upward.
- part_cover.step.py: flat lid face on bed.
- part_pin.step.py: broad head on bed, split legs upward.
moon.step.py is the assembled viewing entry; moon_lib.py controls all dimensions; moon_assembly.py controls mating datums.

Assembly: align the crescent outlines and place the leaf peg in the curved track. Insert the pivot from the underside while gently compressing its split legs; release the exposed barb above the moving leaf. Bearing radial clearance0.2mm; planar running gap0.4mm. Disassembly: pinch the exposed pin legs and withdraw the pin. Elastic insertion force and printed fit are untested.

Inlay: owner supplies and provisions exactly21.5×11.5×0.75mm. Flat seating isZ1.0; long directionY; pocket22.5×12.5×1.05mm gives0.5mm clearance per side and0.30mm above PET. The underside is the sole tap face, through1.0mm unfilled PETG. No conductive filament, metallic finish or on-metal mounting. Radio range is unmeasured; contact is the first physical test target, followed by2/5/10mm trials with the actual reader.

Service: open the gold leaf. Lift the cover at its outer-edge thumbnail notch, gently bowing the lid upward to disengage its two0.25mm captured ends; lift it out. Lay the inlay flat, without glue or pressure, then bow/refit the lid. Removal reverses this path; the tag remains flat. Cover bending,20 service cycles and1000 fidget cycles are untested targets. Use the separate access check for geometric clearance; rigid collision sweeps cannot establish snap force or fatigue.

Force route: finger→gold crescent→pivot/stop peg→upper dark spine→outer perimeter→palm. The inlay is not a load-bearing component. Design load target2N at25mm effective lever arm,0.05Nm; not a tested rating. CAD evidence is not physical print, RF, durability or human testing.

Fit/print audit: run `python ../fit_audit.py` from this CAD directory. It checks the shared pivot/bore dimensions, once-applied clearances, pocket allowances and named assembly interfaces. The revolute connector is `leaf_axis` on the carrier; its moving counterpart is `bearing_datum` on the leaf. Both use the shared pivot datum. The integral stop peg enters the track before the pivot is inserted; the cover and inlay can be serviced after assembly with the leaf open. `measure/check_carrier.py` additionally measures the actual pocket, window, keep-out, stops and released service path. Generic verification owns solid counts, bed fit, interference and print gates.

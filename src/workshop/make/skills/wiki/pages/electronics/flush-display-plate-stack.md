---
title: Flush display plate stack
tags: [display, lcd, glass plate, ledge, recess, tape, flush, windshield, tilted board, connector]
aliases: [flush display, display in a plate, lens recess, ledge ring, board under glass, touchscreen in a shell]
sources:
  - "experience: a 3.95 inch LCM+CTP module (84.37 x 84.37 x 3.23 mm, 0.175 mm tape) sat flush in a printed glass plate over a tilted board"
related: [buttons-knobs-and-front-panels, electronics-enclosure-design, sealing-and-ingress-protection]
updated: 2026-10-02
---

# Flush display plate stack

When the module is to sit flush with a printed glass plate inside a printed
shell, the stack has more layers than the drawing's "thickness":

- **Recess depth = lens + tape.** A module's overall thickness is lens plus
  the LCM under it; the recess in the plate is lens thickness plus the
  adhesive (a 0.175 mm double-sided tape is typical), so the lens top ends up
  flush. Cut a separate through-window, a little larger than the LCM, for the
  part under the lens, and leave a lip of at least 1 mm between recess floor
  and plate underside.
- **A plate thicker than the shell wall has nothing to sit on.** The pocket
  for it cuts straight through the wall, so add a **ledge ring** inside the
  shell under the plate edge (a band either side of the plate outline), and
  clip the ring to the outer hull or it pokes through the skin at the narrow
  end.
- **Work in the plate's own frame.** Define one plane (origin on the surface,
  x across, y along the slope, z outward) and make plate, ledge, lens recess,
  LCM window, the display envelope and the board seat from it. A tilted
  surface typed in world coordinates drifts by a few tenths between features.
- **The board lies a fixed depth under that plane**, so anything on the board
  edge (a connector mouth, a button) is the same distance below the glass
  wherever the board slides along the slope. A plug path from such a connector
  passes the glass boundary at constant depth and can cut a thin glass piece
  into an island; start the glass behind the path, or keep the opening in
  silver.
- **Stack the depths in one assert**: display bottom, tallest board part,
  ledge ring bottom and post top, each below the plate top, with at least
  0.5 mm between display and tallest part.

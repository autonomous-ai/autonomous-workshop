# Energy and drive

The power source is not the mechanism. Name both: *what stores or supplies the
energy*, and *which archetype turns it into the motion*.

## Sources

| source | stores by | delivers | design notes |
|---|---|---|---|
| **rubber band** | twisting (wound on a hook/axle) or stretching | falling torque as it unwinds | anchor on a post moulded into the fixed body (trotter), not a loose cross pin; leave a corridor for the twisted band (trotter: 12 mm radius, checked as a clear path); the hook needs a barb or notch, not an open U that is an unprintable overhang |
| **stretched band** | extension between two posts | pull along the band | posts carry the full band force as a moment at their root: fillet the root, keep them short |
| **printed spring** | compression, torsion or flexure | small force, creeps | pitch must exceed wire section or coils fuse; PLA recovers poorly — PETG or a catalog spring for anything cyclic |
| **catalog spring** | — | stable | search `$step-parts` by wire, OD, free length; seat it with `cadmount` |
| **falling weight** | lifted height | constant torque | needs a drop height and a line/drum; slow with a governor or escapement |
| **hand crank** | — | whatever the hand supplies | crank radius 20–35 mm for fingers; a knob on a keyed shaft end (trotter tail knob on the worm shaft) |
| **pull-back / flywheel** | spin-up through gears | burst | the gear train has to back-drive: no self-locking worm |
| **motor / servo** | electrical | continuous | an electrical load: go to `$electromechanical-integration` for source, switch, wiring and `power.json` before the layout is fixed |

## Ratio budget

Work backwards from what the output needs:

```text
output speed  = source speed / total ratio
output torque ≈ source torque × total ratio × efficiency
```

Printed spur stages run ~90 %, a worm pair much less (often 40–60 % for
low starts). A small DC toy motor runs thousands of rpm; an automaton crank
wants 10–60 rpm — two or three reduction stages, or a worm. A rubber band
gives few turns: a step-up to the wheels trades torque for distance.

## Drive direction

Write down which way the source pulls or turns, in assembly coordinates, and
what it loads:

- a band pulling the head forward loads the head's fork: that contact is the
  `blocked` condition (trotter `head-band-pull-on-fork`);
- a worm's separating force pushes the worm away from the wheel: something
  must stop it (trotter: the lid keeper, `head-held-down-by-lid`);
- the direction the driven output reverses under load is where a ratchet
  or self-locking stage belongs, if anything should hold.

A `blocked` condition aimed anywhere other than the drive direction proves a
capture nobody needed and leaves the real one untested.

## Open items this page can never close

Band torque and runtime, spring rate after printing, friction losses,
whether the toy has enough torque to walk on a real floor. Record them as open
questions; no rigid sweep answers them.

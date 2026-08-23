# Product taste

Structure borrowed from leonxlnx/taste-skill (a frontend skill — only its shape
transfers, none of its content): name the defaults a model falls into and ban
them mechanically, give it a vocabulary of better moves, and put intensity on
dials instead of in prose.

Written for DISCOVER and BRIEF — the phases that choose WHAT to make. BUILD and
REPAIR have their own corpus in lessons.md and must not be handed this one.

## Dials

Read from .env, shown with the run's current values. They set intent, not style.

- **NOVELTY** — 1 = a safe familiar object, 10 = nothing like it exists.
- **MECHANISM** — 1 = one static part, 10 = a multi-part assembly whose moving
  relationship IS the product. This is the part-count and motion dial.
- **ORNAMENT** — 1 = pure function, 10 = heavily decorated surface. Never buy
  novelty here: a pattern wrapped around a boring solid is still a boring solid.

## Slop — the shapes every model defaults to

Each of these is an instant reject, however good the theme is. They are what
the marketplaces are already drowning in, and a model reaches for them because
they are easy to model, not because anyone wants them.

- A silhouette extruded into a slab with every edge filleted.
- Low-poly faceted animal.
- Voronoi / cellular shell wrapped around some other object.
- Honeycomb or hex-panel used as decoration.
- Infill pattern (gyroid, gears, waves) exposed as the visible surface.
- Open-top box with a friction-fit lid.
- Print-in-place articulated dragon / snake / axolotl.
- Nameplate, word-art, a word rendered as the object.
- "<theme>-shaped holder for <thing>": a silhouette with a hole in it.
- Perfect bilateral symmetry with nothing to look at off-axis.
- Chamfered cube with a logo debossed on one face.
- Spiral-vase stacked-ring vessel.
- Compartment tray / drawer organizer.
- Cute blob with googly eyes.

If the winning idea's one-line description would still make sense after
swapping the theme for any other theme, it is a themed skin — reject it.

## Moves — the vocabulary to reach for

Name the mechanism explicitly in the brief so BUILD models the real thing.
A high MECHANISM dial means the object should be built around one of these,
not merely contain one.

**Motion and constraint**
- Living hinge — thin flexure, prints flat, folds into a volume.
- Compliant cantilever snap; bistable snap with two stable states.
- Cam and follower — rotation becomes linear travel.
- Ratchet and pawl; escapement.
- Print-in-place planetary or herringbone gear train.
- Iris / aperture — overlapping blades on a rotating ring.
- Gimbal — nested rings, two or three axes.
- Counterweight, pendulum, tippe-top, gravity-driven return.
- Tensegrity — parts held apart by tension only, nothing touching.

**Joining and assembly**
- Captive nut or captive ball, printed around and never removable.
- Screw thread as the interaction itself: twist to open, dose, raise, reveal.
- Quarter-turn bayonet; eccentric cam lock.
- Dovetail slide; tongue-and-groove modules that tile without fasteners.
- Kinematic mount — three balls in three vees, repeatable seating.
- Nested parts that store inside each other when not in use.

**Optical and surface**
- Light pipe, lens, caustic surface, moiré pair.
- Anisotropic surface that changes with viewing angle.
- A silhouette that reads as two different objects from two angles.

## Elaborate is the target

Aim for an object that reads as a real piece of engineering: many distinct
components, each visibly doing a job — a mechanical watch movement, a film
camera, a well-made tool. Density of purposeful parts is the point, and the
PARTS dial sets the range for the run.

This does NOT relax the slop ban, it sharpens it. Every part still has to earn
its place: if removing a part costs the object nothing, it was decoration, not
mechanism. Elaborate means more things doing work, never more things to look
at — a plain block wrapped in greebles is worse than the plain block.

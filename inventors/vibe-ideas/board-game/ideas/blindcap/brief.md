# Blindcap — build brief

Every mushroom in the box is one body. What tells the four species apart is
buried where no one can see it — a shank inside the loam, read only by
sliding an iron pin under the cap's brim and watching whether it sinks or
stands proud. Everything below translates `idea.json`'s numbers (and, where
it gave none, the minimum reasonable number consistent with its prose) into
millimetres. See `brief.json`'s `unstated_in_spec` for the full list of
places I had to choose.

**The one constraint that must survive every later edit:** all 16 stool
bodies (4 species x 4 owner marks) share the identical cap, brim, boss and
shank OD. Only the owner-bite count on the visible brim and the internal
groove pattern on the buried shank differ. If a later pass "simplifies" any
stool's cap diameter, boss position or shank OD independently of the others,
the game's central mechanic — that a planted stool gives away nothing by
shape — breaks.

## Parts

**loam_tile** (board, 4x, one per player, single tile, 132 x 132 x 28mm) —
joined by dovetail at setup, 2/3/4 of them depending on player count. This is
`idea.json`'s `tiled: true` read as *tiled-by-rule*, not *too big for the
bed* — a single loam_tile is a fraction of the 246mm limit (see
`unstated_in_spec`). Carries a 3x3 grid of sockets at 44mm pitch (OWNED
here — every stool's shank clearance and every pin's clearance derive from
this one tile). Each socket: a 12.8mm x 20mm blind bore ringed by a 2mm
collar, plus two probe holes drilled from the top face only at 35deg from
vertical, entering ~10mm off centre (inside the planted cap's own 17mm brim
radius, so the brim always roofs them). 1.4mm craquelure relief. Prints
top-face up, flat and unbroken underside, no supports.

**stool_\* — 16 names** (loose piece, qty 1 or 2 each, 24 total,
34 x 34 x 49mm, identical bbox across all 16) — `stool_deadhead_p1..p4`
(qty 2 each, 8 total, no shank grooves — both pins always stand proud),
`stool_bracket_p1..p4` (qty 2 each, 8 total, upper groove only),
`stool_inkcap_p1..p4` (qty 1 each, 4 total, lower groove only, scarce,
doubles a grove's score), `stool_hollow_p1..p4` (qty 1 each, 4 total, both
grooves, scarce, doubles a grove's score). The `_p<N>` suffix is the owner
mark: N square bites (3mm x 2.5mm, `idea.json`'s own figures) cut into the
brim edge. `idea.json`'s own component list only gave 4 bill lines (one per
species); its prose makes clear every stool also carries a distinct
owner-bite geometry, so this brief expands that into the real 16 distinct
bodies (see `unstated_in_spec`) — a bill-of-materials or a build that
collapses these back to 4 has silently lost the owner axis.

Every stool, regardless of name: 34mm cap x 8mm thick (0.8mm growth rings on
top, 32 gill ribs at 1.0mm on the brim underside), a 16mm x 3mm boss for the
crown, a 12mm x 14mm exposed neck (the "finger's height" shadow gap a pin
slides through), an 18mm x 2mm shoulder that rests on the collar, and a
12mm x 22mm buried shank. Species grooves, where present, are 3mm-deep,
chamfered annular cuts on that same shank (upper band 8mm below the
shoulder, lower band 16mm below) — cuts *into* the shared shank, never a
different presented diameter. bbox is the stool's upright/planted
orientation, its dominant state for 5 of 6 rounds. Prints shank-down,
cap-up — its natural planted orientation — no supports.

**claim_crown** (loose piece, 12x, 3 per player, 24 x 24 x 6mm) — a low
crenellated ring, six 3mm points (`idea.json`'s figure), dropped onto any
planted stool's boss and never moved. Bore derives from the stool's 16mm
boss via `seated_pair`. Owner mark: 1-4 pierced Ø3 holes (`idea.json`'s
figure) — one part name suffices here since the mark doesn't change the
crown's envelope or fit.

**probe_pin** (loose piece, 16x, shared supply, never replenished,
10 x 10 x 34mm) — hex-shafted (4mm across flats), knurled 10mm disc head
(0.9mm knurl relief, `idea.json`'s figure), blunt guided tip. Blocked
(no groove): head stands ~22mm proud of the loam ("a clear thumb's width").
Admitted (groove present): head settles to ~3mm proud ("almost to the
brim's shadow"). Both stand-off targets are my own numbers reading
`idea.json`'s similes (see `unstated_in_spec`) — ~19mm apart, unmistakable
across a table. The only part in the box that moves during play rather than
seating or joining, so it carries a `slides` interface, not a `seats` one.

**spore_trough** (container, 4x, one per player, 230 x 90 x 40mm) — six
cradles holding stools lying on their side, shanks toward the owner; a
34mm-tall near lip (matching the cap's own diameter) blocks the opposite
seat's sightline; three upright slots hold crowns on edge; owner notch count
(reusing the stool's own 3mm x 2.5mm bite figure) cut into the back wall;
1.4mm craquelure matching loam_tile's. Prints open-top, no supports.

## Interfaces

- **joins — loam_tile / loam_tile.** Dovetail, symmetric about each edge's
  midpoint so any edge mates any edge (`idea.json`'s own requirement) —
  needs a self-mating profile, not a directional tab/socket pair. Must
  engage cleanly in every player-count arrangement: side-by-side (2), an L
  (3), a 2x2 square (4).
- **joins — stool_\* / loam_tile.** Shank into blind bore, drop-in seated,
  non-rotating, permanent for the round. Representative across all 16
  stool names — the shank OD, shoulder and collar-rest are identical for
  every one of them; only the owner mark and internal grooves vary, and
  neither touches this fit. loam_tile owns the 12.8mm bore and 44mm pitch;
  every stool's clearance derives from it.
- **joins — claim_crown / stool_\*.** Boss into bore, drop-on, permanent.
  Representative across all 16 stool names — the boss never varies. A
  crown may land on any player's stool, so this one fit has to work
  identically across every stool body, which it does by construction.
- **slides — probe_pin into loam_tile.** Swept along its own 35deg hole
  axis from full retraction to full insertion, at every insertion depth —
  this is `idea.json`'s own CLEARANCE CONTRACT (a proud pin's head, plus a
  neighbour's, must clear the socket pitch; no pin at any depth may enter a
  neighbouring cap's envelope) made into an executable check, per this
  pipeline's own lesson about parts in motion. Holds by construction from
  the hole geometry alone, but must still be swept and checked, not just
  trusted.
- **seats — stool_\* into spore_trough** (documentation only, no
  `recesses` entry — see `unstated_in_spec` for why: a stool lies on its
  side in the cradle, a different orientation from its canonical upright
  bbox, so the standard recess formula doesn't apply cleanly). ~34.8mm wide
  x 49mm long cradle groove at a 36mm pitch, 6 lanes.
- **seats — claim_crown into spore_trough.** Three upright slots,
  ~25mm dia x 8mm deep, well shy of the crown's own 24mm diameter so it
  stays retrievable.

## Print plan

Nothing in the box needs supports. loam_tile prints top-face up with a
flat, unbroken underside — both probe holes are drilled from the top only
and never break through. Every stool prints shank-down/cap-up, its natural
planted orientation. claim_crown, probe_pin and spore_trough are all
straightforward flat/vertical prints. No part exceeds the 246 x 246 x 251mm
P2S bed (spore_trough at 230 x 90mm is the largest footprint), so
`tiled_board` is not needed anywhere.

Use `shared_positions(3,3,44)` once per loam_tile and reuse it for the
socket bores, collars and probe-hole entry points. Use `add_piece_family`
for every multi-copy family — all 16 stool_\* names, claim_crown (12x),
probe_pin (16x), loam_tile (4x), spore_trough (4x) — each copy a separately
named assembly child. Use `seated_pair` for every bore/boss and bore/shank
pair so the owning part's dimension is stated once.

## Gate

`ergonomics_check.py board-game/ideas/blindcap/brief.json` — **ERGO PASS,
0 findings.**

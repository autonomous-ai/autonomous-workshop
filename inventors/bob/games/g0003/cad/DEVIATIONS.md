# CLEARANCE (g0003) — registered deviations from `brief.md`

Every place the built geometry differs from a number in the brief, with the
arithmetic. Nothing here is a preference; each row is either a brief number that
cannot coexist with another brief number, or a print-process requirement the
brief's §2 fit class still has to survive. **No brief file was edited.**

Twelve entries. Four are conflicts inside the brief (D1, D2, D3, D12) — those
are the ones worth reading.

---

## D1. `screw_shroud` is its own printed part, ⌀28 OD, not ⌀24 integral to the base

**Brief §2 `gantry_base`:** "screw shroud ⌀24.0 OD × 24.0 tall, coaxial with
journal ±0.15", integral to the base.
**Built:** a separate `screw_shroud` part, ⌀28.0 OD × 33.0 tall (Z −9.0 → +24.0),
pressed into a ⌀27.90 socket in the base (0.10 interference). Its **bore is the
journal**, so the ±0.15 coaxiality the brief asks for is now internal to one
turned-in-place feature instead of a stack-up between two.

**Why the ⌀24 cannot hold.** Assembly §6 step 4 lowers the screw *through* the
shroud: "screw collar into the journal, yoke skirt over the shroud". The collar
is ⌀24 (D2). A ⌀24 OD shroud with the 1.6 mm minimum FDM wall has a ⌀20.8 bore.
24.0 > 20.8 — **the collar cannot pass**, so the brief's own assembly sequence is
impossible at ⌀24 OD. Minimum legal OD = journal ⌀24.4 + 2 × 1.6 wall + 0.2 =
**⌀27.4**; built at ⌀28.0.

**Why it is a separate print.** The runway is the datum for every bar height and
has to be ≤0.15 mm TIR (§9.1). That means the runway prints as the **bed face**.
A 24 mm tower rising from the bed face has to be printed in mid-air. Splitting
it costs one press-fit and buys a datum face straight off the glass.

**Cost to §3.10:** shroud ⌀28 inside skirt ⌀30 ID leaves **1.0 mm per side**, not
the brief's 3.0. Still no rub, still opaque at every click — the hidden-state
claim is unchanged.

## D2. One ⌀24 collar, not a ⌀24 crown plus a ⌀22 journal collar

**Brief §2 `column_screw`:** "detent crown … on a ⌀24 collar; collar ⌀22.0
−0.10/−0.00 × 8". **Brief §2 `gantry_base`:** "screw journal ⌀22.4 +0.10/−0.00 ×
9 deep".
**Built:** one ⌀24.0 × 8.0 collar carrying the crown, running in a **⌀24.4**
journal.

The brief describes two collars but gives one height (8) and one journal (9
deep). Stacking a ⌀24 crown and a ⌀22 journal land inside 8 mm leaves ~4 mm each
— below the 4.5:1 guidance the brief itself applies to the post. Merging them
keeps the crown and the bearing on the same 8 mm and **preserves the brief's fit
class exactly**: 24.4 − 24.0 = **0.40 diametral running clearance**, the number
in the brief's mates column, unchanged.

## D3. `post_guide` ⌀12 × 82 → ⌀12 × 71; yoke blind bore 54 → 60 deep

**This is a brief-internal contradiction, and it is the one that would have
jammed the game at click 12.**

Brief §7.4 sets the post at 82 mm and checks it against the **top stop only**:
"post top at Z = 70, yoke blind bore top at Z = 72 at `H_top`". Run the same
check at the **bottom** stop, where the bore ceiling is lowest:

| | skirt rim Z | bore top Z (rim + 54) | post top Z | verdict |
|---|---|---|---|---|
| `H_top` | 18.0 | 72.0 | 72.0 (socket −10, len 82) | grazes |
| `H_bottom` | 2.5 | **56.5** | 72.0 | **fouls by 15.5 mm** |

The post bottoms out in the bore 15.5 mm early — the yoke stops at click 12 of
31 and 19 clicks of travel do not exist. Two numbers move to clear it:

- post 82 → **71** (socket 10 deep → top at Z = **61.0**)
- blind bore 54 → **60** (rim + 60 → **62.5** at the bottom stop)

61.0 + 1.0 ≤ 62.5 ✅ clears at the bottom. Engagement at the top stop is
61.0 − 18.0 = **43 mm on a ⌀12 post** (3.6:1), and the post top at 61 stays
swallowed by the bore at **every** click, so §3.10's "the post never emerges"
still holds. Asserted in `clearance_lib._check_params()`.

## D4. `knob_hood`: CLOSED 45° conical roof printed roof-down, gabled port lintel, lane relief, tapered finger tab

Wall stays 1.6 mm, opaque, hand port 66 wide open to the bottom rim on ONE side,
ledge ⌀44.40 on the knob top at Z = 90, height exactly 84.0 (Z 8.4 → 92.4) —
every §4 hidden-state number is untouched, and the roof is now **more** closed
than the brief's flat top, not less.

- **Roof — closed, and the print flips to suit it.** Flat top + a 10 mm hanging
  ledge ring → a 45° cone from ⌀82 to ⌀47.6, **capped**: the cone's inner
  surface reaches ⌀44.40 at Z = 90 (that circle *is* the seat on the knob's top
  face) and everything above it is solid, **2.4 mm of opaque PLA on the one
  sightline that looks straight down the screw axis**.
  An earlier revision left that ⌀44.4 apex open for print reasons; the top-down
  render showed the knob's scalloped face and its ring of grip dots through it,
  which is a direct §4.1/§4.2 failure — the hood's whole job is that an opponent
  cannot see the knob, and a knob you can see is a knob you can watch turn.
  Capping it costs the rim-down orientation (a flat roof over the cavity is a
  ⌀44 bridge; closing it at 45° instead would need 22.2 mm of extra height and
  break the 84 mm envelope), so the hood prints **roof-down**: the ⌀47.6 cap is
  the first layer, the cone above it is a 45° *expanding* overhang, and the hand
  port, the lane relief and the rim are all open at the **top** of the print.
  **Nothing bridges anywhere, in either direction** — this orientation is
  strictly better than the one it replaces. Add a brim; the first layer is only
  ⌀47.6 under an 84 mm part.
  Verified as geometry, not as intent: `measure/check_fit.py` intersects the
  hood solid with the whole ⌀44.40 × 2.4 column above the seat plane and asserts
  it is **100.00 % solid**, and separately asserts the ⌀44 × 10 column *below*
  the seat is **0.00 % obstructed** so the hood still drops onto the knob.
- **Port lintel.** The 66 mm-wide port's top is a 45° gable peaking at the
  brief's Z = 58 lip, not a flat lintel. Printed roof-down it is no longer a
  bridging question at all, but it is kept because it is **tighter than the
  brief's own §4.1 sightline argument**: a flat lintel is 66 mm wide at Z = 58,
  the gable is a knife-point there, so the low-eye-opposite-the-port sightline
  the brief accepts shrinks to essentially zero width. Port width, side, and lip
  height are the brief's.
- **Lane relief.** A 26 mm-wide slot on the lane side: the yoke's bridge has to
  pass through the shell at every click. It exposes only the skirt and shroud,
  which every seat can already see; the knob (Z 76–90) stays covered, and the
  slot tops out at Z = 51.
- **Finger tab** on the closed side, per brief §2 — it puts the built envelope at
  82 × **91** × 84 rather than ⌀82 × 84. Its upper face (Z = 74.4) is **tapered
  45° back into the shell**, reaching full 10 mm protrusion by Z = 64.4: printed
  roof-down that face points at the bed and a flat radial ledge there would be
  the part's only unsupported overhang. The taper cutter starts exactly at the
  ⌀82 OD — one millimetre further in, at the tab's root inset, it opens an
  18 × 2 mm window through the 1.6 mm shell (caught by volume: 41.41 → 41.71 cm³
  when closed).

## D5. `detent_leaf` prints on edge, not flat

Brief §2: "printed flat, spring section in-plane so layers are not the bending
axis." Built standing (envelope 5.7 × 34 × 12), which is the *installed*
orientation.

The leaf deflects **radially — horizontally in the assembly**, across the 1.60 mm
section. Printed flat, that 1.60 mm becomes 8 layers at 0.2 and the deflection
direction is the layer-stacking direction: every flex loads an interlayer bond
in tension, which is the failure the brief's own sentence is trying to prevent.
On edge, the 1.60 × 24 spring is drawn as continuous extrusions **along** the
beam and the layers stack across the 12 mm width — bending stress stays in-plane.
The brief's stated *intent* is met; its stated *orientation* is not.

## D6. Nut thread cut starts 2.0 mm below `NUT_Z0` (no dimensional change)

The yoke's 45° entry cone lands on ⌀16.70 at exactly Z = 14.65 and the thread
cut's own bottom trim plane is that same circle at that same Z — two cut solids
tangent along one shared edge. The tessellator turned it into a crack:
`check_mesh` → `FAIL watertight, 17 boundary edges`. Starting the cut at
14.65 − 2.0 puts its bottom cap where the cone has already opened to R10.35, so
it lands in void and puts no face on the part. The nut's **threaded span
(14.65 → 34.65, 20.0 mm) is unchanged**. `check_mesh` now reports 0 boundary
edges.

## D7. Yoke lower edge: 1.0 mm chamfer, not an R1.0 fillet

Brief §4.5 wants the yoke's lower edges nearest the post rounded R1.0 so there is
no crisp pointer against the post's layer lines. Built as a 1.0 mm chamfer cut
from the skirt rim — same job (no crisp edge), and it survives a boolean chain
that a fillet edge-selector does not.

## D8. `column_screw` overall length 104 → 99.0

Not a design change — the brief's envelope column disagrees with the brief's own
datum stack. Knob top face **Z = 90** (§1) and the collar bottom at the journal
floor **Z = −9** give 90 − (−9) = **99.0**. Built to the datum stack.

## D9. `column_screw` widest ⌀43.6, not ⌀44.0

The ⌀44 knob carries 12 × ⌀6 finger scallops on the rim (grip; the knob is turned
blind under a hood). The peak between two scallops sits at R21.8, so the widest
measure is 43.6. Knob height 14.0 and the flat top face are the brief's.

## D10. `gantry_base` measures 220.0 × 78.5 × 13.5

- **78.5** = the brief's 78 plus the 0.5 mm embossed setter's ritual on the front
  skirt, which brief §7.6 requires.
- **13.5** = the brief's 10 mm plate plus the three ⌀16 × 3.5 feet below it. The
  brief's 10 is the plate; the feet are also the brief's.

## D11. `stop_ring` built at 2.35 mm

Not a deviation — brief §5.3 makes this height **per copy** (nominal 2.25, range
2.00–2.75). 2.35 is the value for `H_TOP_NOM = 33.00`: it lands the hard stop at
15.65 mm of travel, so click 31 seats and click 32 refuses. Re-slice per copy
from the measured skirt-rim Z; asserted in `_check_params()`.

## D12. The yoke needs a 45° yaw on a 220 mm bed

Not a deviation from the brief — the brief's bed is 256 mm and its envelope rule
is 251 × 251 × 251, which the yoke's 224 × 34 × 62 satisfies flat. Recorded here
because the generic gate assumes a 220 mm bed and the slicer note has to carry
it: **(224 + 34) / √2 = 182.4 mm square**, so the yoke prints on a 220 bed
rotated 45° in XY with 37 mm to spare. `gantry_base` at 220.0 × 78.5 is on the
line and yaws to 211.1 mm. No other part needs rotating.

The 224 itself is not negotiable: brief §3.9 derives it from lane 130 + two 47 mm
end blocks, and §9.3 makes saddle-line parallelism across that 130 mm lane an
abort criterion — a joint in the middle of the bridge is exactly what would break
it. Splitting the yoke to suit a 220 bed would trade a slicer rotation for the
game's measurement datum.

---

## Not deviated — checked and left alone

31 clicks × 0.500 = 15.50 travel · M16 × 2.00 single start · 4 symmetric 30°/30°
notches · leaf 1.60 × 12 × 24 · lane 130 +0.5/−0.0 (built 130.2) · saddles at
±72.0, 90° included, apex relieved ⌀2.0 · skirt drop 21.0 · nut ⌀16.70 · post/yoke
0.40 running · post/base 0.10 press · leaf snap 0.10 interference · rails 178 ×
32 × 8 with six 21.0 pockets on 28.0 centres · blocks 20 × 20 × H, 0.4 chamfer on
the vertical arrises only, pips debossed 0.5 on one side face · the 42-rung
0.5 mm ladder from `rules.md` (§7.1) · scrapped blocks in the box lid (§7.6) ·
bar and cups `buy_not_print` (§7.8).

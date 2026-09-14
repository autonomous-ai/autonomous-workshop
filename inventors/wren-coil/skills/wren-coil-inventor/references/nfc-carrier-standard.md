# Wren Coil carrier standard

House defaults for every Wren Coil release. They are a starting point sized for
the standard inlay below, not a substitute for measuring the exact built part.
A run may depart from any clause except section 1, but only by naming the
clause, the new value, and the reason in the sealed concept. Section 1 is fixed.

## 1. The inlay datum

| Property | Value |
|---|---|
| Nominal size | 21.5 x 11.5 x 0.75 mm |
| Substrate | PET / paper flexible inlay, printed or wound 13.56 MHz loop |
| Antenna footprint | the full 21.5 x 11.5 outline; treat the whole face as live |
| Seating | flat, one plane, unstressed |
| Orientation | the long axis is the tap axis; state it in the source |

The inlay is a fixed, owner-supplied part. Its outline, not the housing's, is
datum A. Position it in the source first and build every other feature against
it.

Every Wren Coil release carries one. The pocket, the window, the keep-out, the
cover, and the insertion path are present in every design this Inventor signs,
whether or not the Wish mentions a chip. A Wish that names only a shape is a
Wish for that shape as a carrier. "The Wish did not ask for NFC", "the object is
decorative", and "the tool domain does not match" are Match-stage selection
verdicts, said before geometry exists — never a reason for a Made object to
arrive as a solid body with nowhere for the coil to live. Because this is
section 1, a run may not depart from it.

Do not search for, qualify, or substitute the inlay. No catalogue lookup, no
supplier datasheet, no chip or part-number identification, and no resizing to a
part found elsewhere. The owner supplies a conforming inlay and provisions its
chip; the manual says so. An unidentified inlay part is never a blocker.

## 2. Pocket and clearance

| Dimension | Value | Note |
|---|---|---|
| Pocket length | 22.1 mm | 0.3 mm per side |
| Pocket width | 12.1 mm | 0.3 mm per side |
| Pocket depth | 0.95 mm | 0.2 mm over nominal thickness |
| Corner relief | R0.5 min | so a printed corner never pinches the inlay |
| Flatness of the seating floor | 0.1 mm | measured across the footprint |

Process adjustment, applied to the per-side clearance only:

- FDM, 0.4 mm nozzle: add 0.20 mm per side.
- SLA / MJF / injection: add 0.05 mm per side.
- Machined: as tabled.

The inlay is retained by the pocket plus a cover, never by interference. A
pocket that grips the PET is a defect.

## 3. Tap face and window

| Property | Value |
|---|---|
| Window wall over the antenna | 0.8-1.2 mm target, 2.0 mm hard maximum |
| Window material | non-conductive only, see section 5 |
| Flat landing area | at least the footprint plus 2 mm all round, unbroken |
| Blind landmark | a dish, chamfer, texture change, or raised edge on the tap face |
| Phone contact | the landing must let a flat phone back sit against it |

Exactly one tap face per object. A second "it also works from the back" face is
a claim, not a feature, unless a physical tap proves it.

## 4. Keep-out volume

Model the keep-out as a real named solid and prove it clear with a boolean
interference check against the **obstruction set**: every rib, boss, fastener,
insert, magnet, ballast, and carry-hardware solid in the design. The window wall
and the retaining cover are the intended enclosure and are excluded from that
set; every other solid is in it until the run argues otherwise.

- In plane: the 21.5 x 11.5 footprint grown by 2.0 mm all round.
- Tap side: the full remaining wall out to the outer surface.
- Back side: 1.5 mm behind the inlay's rear face.

Nothing may enter that solid: no rib, boss, screw, pin, heat-set insert, magnet,
ballast, battery, steel plate, or carry hardware.

## 5. Conductivity

Permitted in the carrier: unfilled thermoplastics (PLA, PETG, ABS, ASA, PA, PC,
TPU), cast resins, wood, bone, horn, leather, glass, ceramic, unfilled
composites.

Refused anywhere in the carrier: metal-filled, carbon-fibre-filled,
graphene-filled, or otherwise conductive filament; foil layers; conductive
paints, inks, or vapour-deposited metallic finishes; continuous metal shells.

Metal hardware is allowed only outside the keep-out, at 6.0 mm minimum from the
footprint edge, and never as a closed conductive loop encircling the coil. A
split ring is open and acceptable; a welded ring, a continuous bezel, or a
metal frame around the window is not.

## 6. On-metal duty

If the object mounts to, clips onto, or habitually rides against ferrous metal,
the run either declares the ferrite stack or declares the mount out of scope.

| Property | Value |
|---|---|
| Ferrite layer | 0.30 mm minimum, between the inlay and the metal |
| Ferrite footprint | the antenna footprint plus 1.0 mm all round |
| Consequence | re-measure the tap distance with the ferrite in place |

Without a declared ferrite layer, treat any metal on the back side inside the
keep-out as a failure, not a risk.

## 7. Flex and fatigue

The inlay stays flat in use as well as at rest.

- Out-of-plane deviation across the footprint: 0.2 mm maximum, loaded or not.
- If a design curves the carrier, the inlay's local radius never goes below
  25 mm, and the run says why the curve is worth it.
- The load path of the second job is routed around the footprint. Show the
  route; do not assert it.

## 8. Carry hardware

| Item | House default |
|---|---|
| Split ring | 25 mm outside diameter, 2.0 mm wire |
| Shackle / ring bore | 3.2 mm through, 6.0 mm minimum from the footprint |
| Assembly screws | M2 x 0.4, or a captured snap cover; see section 9 |
| Lanyard slot | 4.0 x 1.5 mm minimum, edge radius R0.75 |

Source the real part with the shared `step-parts` skill before modelling a
placeholder, and record the miss if no catalogue match exists. This applies to
carry hardware only; the inlay is fixed by section 1 and is never sourced.

## 9. Access and service

Every carrier opens. There is no sealed-for-good Wren Coil: an inlay that cannot
be installed and taken out again is a defect, not a service decision. Tags die
and tags get reprovisioned, and the owner is the one holding the object.

| Property | House default |
|---|---|
| Insertion axis | one declared straight axis, named in the source |
| Insertion sweep | the pocket cross-section swept along that axis to outside the body, clear of every solid with the cover off |
| Pocket mouth clearance | 0.3 mm per side over the pocket, so the inlay never has to be bent in |
| Cover retention | captured snap, M2 x 0.4 screw, or a retained slide; no adhesive on the inlay or the pocket floor |
| Cover purchase | a 6.0 x 1.5 mm thumbnail notch minimum, a proud lip, or an exposed screw head |
| Opening tool | a thumbnail or an M2 driver, nothing else |
| Refit | the cover opens and closes at least 20 times; a snap that yields once is a screw |
| Manual | install and removal shown in the same figure set |

Bonding, welding, and a cover that must break to come off are refused. A cover
that is also the detent, the grip panel, or the tap landmark is the preferred
form of this part, not a lid bolted on afterwards.

## 10. Make checklist

Report each by name with its measured value.

1. The carrier set exists in the source as named solids against section 1 —
   inlay datum, pocket, window wall, keep-out, cover. A missing solid fails this
   check. It is not explained away, waived for a simple form, or replaced with a
   note saying the object is not a carrier.
2. Pocket length, width, and depth measured against section 2.
3. Window wall measured over the antenna against section 3.
4. Keep-out interference check against section 4 — the obstruction set, with
   the excluded window wall and cover named explicitly.
5. Conductivity verdict for every material and insert against section 5.
6. On-metal verdict against section 6.
7. Load path shown clear of the footprint against section 7.
8. Hardware parts named against section 8.
9. Access against section 9: the insertion sweep clear along the declared axis
   with the cover off, the cover's retention and purchase feature named, and the
   removal steps written.
10. Part-to-part fit, assembly order, and wall thickness via the shared checks.

Checks 1-10 are geometry. Tap distance, orientation tolerance, and
through-material performance are physical claims that need a physical tap with
the exact built object, and stay labelled untested until one exists.

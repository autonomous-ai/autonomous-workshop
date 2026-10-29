---
title: Snap-fit design — cantilever, torsion and annular
tags: [snap-fit, cantilever, annular, torsion, strain, permissible-strain, pla, petg, mating-force, friction, secant-modulus]
aliases: [snap hook, cantilever snap, allowable strain, permissible strain, strain limit, snap strain, clip, latch, snap joint, press stud, living latch, bayer snap fit, covestro snap fit, ball snap, snap cup, split cup, neck knob, snap-on head]
sources:
  - Covestro (Bayer), Snap-Fit Joints for Plastics – A Design Guide (https://solutions.covestro.com/-/media/covestro/solution-center/brands/downloads/imported/1557218421.pdf), pp. 8–22
  - https://engbench.com/snapfit.php (ε = 1.5 h y / L², P = E b h² ε / 6L, separation force)
  - https://www.ulprospector.com/knowledge/1248/pe-snapfit-3/ (amorphous materials to 70 % of yield strain; via search excerpt)
  - https://jbrplas.com/posts/snap-fit-design-guide/ (moulded yield strain and recommended allowable table)
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/pla/polylite-tm-pla (PLA X-Y strength and modulus)
  - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/petg-pet/polylite-tm-petg (PETG X-Y strength and modulus)
  - Prusament PLA Technical datasheet v1.1 (16-02-2022), https://prusament.com/wp-content/uploads/2022/10/PLA_Prusament_TDS_2021_10_EN.pdf
  - Ezeh and Susmel 2019, International Journal of Fatigue 126 (PLA fatigue curve)
  - "experience: a published toy's snap-on head, a split spherical cup hung in a cavity gripping a neck ball"
related: [joints, filament-properties, printed-fatigue, flexure-materials-and-snap-strain, magnets-and-strap-slots, layer-anisotropy, creep-and-stress-relaxation, mechanism-verification, straps-buckles-and-textile-attachment, kit-assembly-clash-diagnosis, ball-and-socket-joints, push-pins-and-clip-fasteners, bayonet-and-twist-locks]
updated: 2026-10-10
---

# Snap-fit design — cantilever, torsion and annular

A snap fit is a beam or ring that deflects by the undercut, then springs back.
It is designed to a **permissible strain**, not a stress: strain limits vary
less with temperature than stresses do. The formulas below come from the
Bayer/Covestro guide. [[joints#latching-and-holding]] holds the short rules;
this page holds the calculation.

## Permissible strain

This is the one home of the strain limits; other pages link here.

- In a single, brief snap, partially crystalline plastics (nylon, PP, POM)
  may be strained almost to the yield point, amorphous ones (PLA, PETG, ABS,
  ASA, PC) to about 70 % of the yield strain.
- Glass-fibre-reinforced grades have no distinct yield point: use about half
  the elongation at break.
- For joints separated and rejoined often, use about 60 % of the single-snap
  value — about 40 % of the yield strain for an amorphous plastic.
- Covestro's short-term limits at 23 °C: PC 4 %, high-heat PC 4 %, PC blends
  3.5 %, PC/ABS 2.5 %, PC with 10 % glass 2.2 %, with 20 % glass 2.0 %.

Allowable strain for moulded plastics from one injection-moulding guide. Every
row sits at or below the Covestro repeated-use value:

| moulded | yield strain | recommended allowable |
|---|---|---|
| ABS | 2.5–3.5 % | 1.0–1.5 % |
| PC/ABS | 4.0–5.0 % | 1.5–2.0 % |
| PA66 (dry) | 25–40 % | 3.0–4.0 % |
| POM | 8.0–12.0 % | 2.0–3.0 % |
| PP | 8.0–12.0 % | 3.0–4.0 % |

**Printed parts** break sooner than moulded ones. Estimate the yield strain as
the datasheet's X-Y tensile strength over its X-Y modulus — a lower bound,
because the real curve bends over before yield, and as supplier-dependent as
the modulus ([[filament-properties#a-second-supplier-disagrees-and-why-that-matters]])
— then apply the same fractions. Polymaker values, with Prusament's where it
publishes both numbers:

| printed (X-Y) | σ/E yield strain | single snap | repeated use |
|---|---|---|---|
| PLA | 1.5 % (Prusament 2.2 %) | 1.1–1.5 % | 0.6–0.9 % |
| PETG | 2.4 % (Prusament 3.1 %) | 1.7–2.2 % | 1.0–1.3 % |
| ABS | 1.3–1.5 % | 0.9–1.0 % | 0.6 % |
| ASA | 1.8 % | 1.3 % | 0.8 % |
| PC | 2.2 % | 1.5 % | 0.9 % |
| PA6/66 dry (partially crystalline) | 2.9 % | 2.9 % | 1.7 % |

The σ/E estimate for printed ABS is half the moulded yield strain, which shows
how conservative it is: a tested print may justify more, a design assert does
not. Across the layers the datasheet elongation at break is a few per cent
([[filament-properties#printed-specimen-properties-one-supplier-one-test-method]]),
so print the beam so its bending stress runs along the layers, never across
them ([[layer-anisotropy#orient-so-layers-do-not-carry-the-tension]]).

Two time effects:

- **Many cycles:** the PLA fatigue design curve puts the long-life maximum
  stress at 10 % of UTS ([[printed-fatigue]]). With E ≈ 3.4 GPa and UTS ≈
  52 MPa, that is a strain of about 0.15 %. A PLA clip that clicks
  thousands of times has to be very gentle.
- **Held deflected:** a latch that stays bent relaxes and loses its hold
  ([[creep-and-stress-relaxation]]). Engage to zero deflection.

```python
EPS_PERM = {"PLA": 0.011, "PETG": 0.017, "ABS": 0.009, "ASA": 0.013, "PC": 0.015, "PA": 0.029}  # single snap, low end
eps_perm = EPS_PERM[MATERIAL] * (0.6 if REPEATED else 1.0)
```

## Cantilever

Rectangular beam of constant section, length L, root thickness h, width b,
undercut (deflection) y, root strain ε:

```text
strain at the root     ε = 1.5 h y / L²
permissible undercut   y = 0.67 ε L² / h
deflection force       P = (b h² / 6) · Es · ε / L
```

Doubling L cuts the strain to a quarter; halving h halves it.

`Es` is the **secant modulus** at the strain used, read from the material's
stress–strain curve, not the initial Young's modulus. A beam whose thickness
tapers linearly to h/2 at the tip allows more than 60 % more deflection than a
constant-section beam at the same strain.

The root fillet trades stress concentration against a thick section: larger
radii lower the peak stress, but the guide warns that R/h near 0.6 makes a
thick, void-prone root, and sets a floor of 0.015 in (0.38 mm) in any case.

A side-release buckle prong is this beam:
[[straps-buckles-and-textile-attachment]].

## Mating and separating force

```text
W = P · (μ + tan α) / (1 − μ · tan α)
```

α is the lead angle for assembly, or the return angle α' for separation. When
`μ · tan α' ≥ 1`, or the return face is 90°, the joint is permanent. Friction
coefficients on steel (Covestro Table 3). Plastic on the same plastic is
higher by the factor in brackets:

| material | μ | same-material factor |
|---|---|---|
| PTFE | 0.12–0.22 | — |
| PE rigid | 0.20–0.25 | × 2.0 |
| PP | 0.25–0.30 | × 1.5 |
| POM | 0.20–0.35 | × 1.5 |
| PA | 0.30–0.40 | × 1.5 |
| PBT | 0.35–0.40 | — |
| PS | 0.40–0.50 | × 1.2 |
| SAN | 0.45–0.55 | — |
| PC | 0.45–0.55 | × 1.2 |
| PMMA | 0.50–0.60 | × 1.2 |
| ABS | 0.50–0.65 | × 1.2 |
| PE flexible | 0.55–0.60 | × 1.2 |
| PVC | 0.55–0.60 | × 1.0 |

Worked example from the guide: PC hook, designed at half the permissible
strain (2 %), `Es = 1815 N/mm²`, b = 9.5 mm, h = 3.28 mm, L = 19 mm →
P = 32.5 N. PC on PC gives μ = 0.50 × 1.2 = 0.6; at α = 30° the factor is 1.8,
so W = 58.5 N.

## Torsion snap

A rocker arm on a torsion bar deflects by twisting the bar. For a circular bar
of radius r and length l:

```text
twist        sin φ = y1 / l1 = y2 / l2
limit        φpm (degrees) = 180 · γpm · l / (π · r)
shear strain γpm ≈ (1 + ν) · εpm ≈ 1.35 εpm      (ν ≈ 0.35 for plastics)
force        P1 · l1 = P2 · l2 = γ · G · Ip / r   (× 2 for two bars)
             Ip = π r⁴ / 2,  G = Es / (2 (1 + ν))
```

## Annular snap

A bead on a shaft snaps into a groove in a tube.

```text
permissible undercut   y = εpm · d      (one part rigid; equal flexibility → y may double)
transverse force       P = y · d · Es · X
mating force           W = P · (μ + tan α) / (1 − μ tan α)
X (rigid shaft, elastic tube of outside diameter d0):
    X_N = 0.62 · sqrt((d0/d − 1)/(d0/d + 1)) / ( ((d0/d)² + 1)/((d0/d)² − 1) + ν )
X (rigid tube, elastic hollow shaft of bore di):
    X_W = 0.62 · sqrt((d/di − 1)/(d/di + 1)) / ( ((d/di)² + 1)/((d/di)² − 1) − ν )
```

A joint at least `1.8 · sqrt(d · t)` from the tube end is "remote". In theory
its forces are four times those of a joint at the end; in tests they rarely
exceed three times.

## Ball snap: a split cup

A ball pressed into a spherical cup (a snap-on head on a neck knob, a
posable limb) is an annular snap whose undercut is `y = r_ball − r_lip`,
the lip being the cup's mouth. A cup that closes well past the ball's
equator has `y` far above `εpm · d`, so a whole ring cannot open. Slot it
into halves or fingers and size each one as a [[#cantilever]] deflected by
`y`.

- **Room to spread.** Hang the cup from its host inside a cavity, with at
  least `y` of air outside each finger. A cup walled in by the host round
  its outside cannot open, however thin its fingers.
- **Grip.** A seat radius a few hundredths to a tenth of a millimetre under
  the ball's makes a friction hold. The head turns stiffly and stays where
  it is set. That grip relaxes ([[creep-and-stress-relaxation]]); the lip is
  what keeps the ball in.
- **Checks.** A rigid-body check reads the grip as an overlap: a thin
  spherical shell between the seat radius and the ball's
  ([[kit-assembly-clash-diagnosis#classify-it]]). Declare it as an allowance
  and do not open the seat to make the gate pass.

Swing angle, holding torque and the other socket forms are in
[[ball-and-socket-joints]]; printed snap pins in
[[push-pins-and-clip-fasteners#a-generic-printed-snap-pin]].

## Split pegs and in-plane hooks: what the gates catch

- **A split peg's prong ends in a wedge.** A slot of width 2h through a peg of
  radius r leaves each prong a segment of the circle, meeting the slot at an
  angle of arccos(h/r). Below about 70° (h/r over 0.34) a voxel thickness gate
  reads that wedge as a taper on some grid alignments and a thin wall on
  others, so an unrelated edit that moves the part's bounding box flips the
  verdict. Keep the slot narrow and buy the strain back with length: thicker
  prongs (t = r − h) need L = √(1.5 t y / ε), so run the split further back into
  the part.
- **One peg, keyed.** Where the host is too narrow for two bores, one split peg
  holds a plate on and a square key round its root, seated in a matching
  recess, stops it turning. The split must leave two lines of plate in front of
  its end.
- **An in-plane hook strip needs two free edges.** A strip cut by one slot from
  a plate that continues past the strip's outer edge stays fused along that
  edge; a second slot frees it. The boss that carries the strip needs a wall of
  two lines past both ends of the slot, or the root and the tip cut leave
  slivers.

## What a snap fit leaves open

A rigid-body motion check reads the undercut as a collision. Give that
condition an explicit overlap allowance ([[mechanism-verification#8-allowances-are-declared-not-hidden]]).
Snap compliance, relaxation over time ([[creep-and-stress-relaxation]]) and
the real insertion force are open items until a print is tested.

## Checks

```python
eps = 1.5 * h * y / L**2
assert eps <= eps_perm, f"snap root strain {eps:.3f} over the permissible {eps_perm:.3f}"
assert mu * math.tan(return_angle) < 1 or permanent, "separable joint designed as permanent"
y_ball = R_BALL - R_LIP                       # ball snap: undercut at the cup's mouth
assert y_ball <= eps_perm * 2 * R_BALL or CUP_FINGERS >= 2, "ball cup cannot open: slot it"
assert CUP_AIR >= y_ball, "cup fingers walled in: no room to spread over the ball"
```

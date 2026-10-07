---
title: Text, patterns and surface detail
tags: [text, font, emboss, deboss, pattern, array, knurl, texture, boolean]
aliases: [Text(), Compound.make_text, available_fonts, font_path, lettering on a cylinder, wrap text, project_faces, Face.wrap, GridLocations, PolarLocations, HexLocations, linear pattern, circular pattern, knurling, surface texture, face count]
sources:
  - .venv/lib/python3*/site-packages/build123d/objects_sketch.py (Text)
  - .venv/lib/python3*/site-packages/build123d/topology/composite.py (Compound.make_text)
  - .venv/lib/python3*/site-packages/build123d/text.py (FontManager, bundled fonts)
  - .venv/lib/python3*/site-packages/build123d/topology/two_d.py (Face.wrap, Face.project_to_shape)
  - .venv/lib/python3*/site-packages/build123d/topology/shape_core.py (project_faces)
  - .venv/lib/python3*/site-packages/build123d/build_common.py (GridLocations, PolarLocations, HexLocations)
  - "toolchain: build123d 0.11.1 on OCP (macOS), every number below measured with small shapes"
related: [feature-recipes, fdm-minimum-feature-sizes, boolean-pitfalls, unmeshable-faces, sketch-and-extrude-direction, kernel-validity, lightweighting-and-lattices]
updated: 2026-10-06
---

# Text, patterns and surface detail

Lettering, arrays and textures are cheap to write and expensive to carry:
every glyph and every repeated tool adds faces to every later boolean, render
and gate. Printable sizes for text are in
[[fdm-minimum-feature-sizes#text-logos-and-surface-details]]; this page is
the modelling side.

## Text(): the font you name may not be the font you get

`Text(txt, font_size, font="Arial", font_path=None,
font_style=FontStyle.REGULAR, text_align=(CENTER, CENTER), align=None,
path=None, position_on_path=0.0, rotation=0)` builds planar faces (letters
with counters are one face with inner wires: "AB8" → 3 faces).

- **The only bundled font is "Relief SingleLine CAD"** (single-stroke,
  outlined at `single_line_width`, default 4 % of `font_size`). Everything
  else comes from the OS font folders, so a generator that names "Arial"
  builds different letters, or none, on a machine without it.
- **A missing font falls back silently.** `font="NoSuchFont"` prints an OCCT
  warning and uses Arial; a `font_path` that does not exist falls back to the
  `font` name with **no** warning. Both gave identical glyph areas to Arial's.
- For a reproducible deliverable, vendor the `.ttf` beside the source and
  pass `font_path`, then assert the glyph area (below) so a fallback fails.
- `font_size` is the em size, not the cap height: Arial caps at `font_size=10`
  measured 7.31 tall. Size from the cap height the print needs:
  `font_size = cap_h / 0.73` (Arial; measure other fonts).
- `text_align` aligns the text's advance box, not its ink: centred "AB8"
  sat 0.23 mm off centre. `align=(Align.MIN, Align.MIN)` puts the ink box
  corner at the origin.
- `available_fonts()` lists names and styles (1644 on a stock macOS); the
  list is machine-dependent, which is the point.

## Emboss and deboss on a flat face

```python
tag = Text(p.label, p.font_size, font_path=p.font_file, font_style=FontStyle.BOLD)
body += extrude(Plane.XY.offset(p.top_z) * tag, amount=p.emboss_h)   # raised
body -= extrude(Plane.XY.offset(p.top_z) * tag, amount=-p.deboss_d)  # cut
```

Both are exact: Δvolume = glyph area × height to 1e-9. Extruding the cutter
the wrong way (`amount=+d` for a cut) removes nothing and raises nothing —
assert the volume change ([[kernel-validity#a-zero-volume-cutter-is-a-silent-no-op]]).
"HELLO 42" raised on a block took the solid from 6 to 104 faces.

## A glyph in a reference image: trace it, do not type it

A logo or letter in a reference photo is part of the likeness, and its font
is unknown — `Text()` would substitute one silently (above). Trace it instead:
mask the glyph's colour inside the frame it sits in, keep the largest blob,
blur about 1.2 px, contour at 0.5 (`contourpy`, which arrives with
matplotlib), simplify about 0.5 px, and scale by the same mm-per-pixel as the
rest of the reference, correcting the axis the photo foreshortens. Keep the
points in a generated data module with the tracing script beside it, so the
glyph can be re-derived. A traced serif lambda came out as 71 points; extruded
as one polygon face it validated and needed no font on any machine.

## Text on a cylinder: cut through a shell, not to a plane

A planar deboss of fixed depth misses a curved face wherever the surface
falls away faster than the depth. Sagitta at the text's edge:
`s = R - sqrt(R**2 - (w/2)**2)`. With R 15, text 16.9 wide, s = 2.6 mm; a
0.6 mm planar cut removed 10.5 mm³ of the 29.6 intended — the outer letters
were simply absent.

Robust method: extrude the glyphs radially through the wall, then intersect
with a thin shell of the target surface.

```python
shell_in = cyl - Cylinder(R - d, H)                 # 0.6 mm skin
tool = extrude(facing_plane * text, amount=R)        # radial, through the skin
cut = cyl - (tool & shell_in)                        # deboss, uniform depth
raised = cyl + (tool & (Cylinder(R + h, H) - cyl))   # emboss, uniform height
```

Measured: both one valid solid in ~0.9 s, Δvolume ±29.6 mm³. The same shell
trick generalises to any skin ([[feature-recipes#conformal-surface-decoration]]).
Letters stretch radially by (R+h)/R at the top of a raised glyph — negligible
for h ≪ R.

`Face.wrap(face, surface_loc)` maps glyphs length-preservingly onto a curved
face (areas within 0.3 %, 0.9 s for three letters), and `thicken()` makes
solids of them; but the fused result kept one of three letters as a
**separate solid**, even with `thicken(..., both=True)` overlapping the body.
`project_faces(text, path)` projects glyphs along a path on the surface
(0.6 s). Either way, assert `len(part.solids()) == 1`.

## Patterns: locations, then one boolean

| context | arguments | notes |
|---|---|---|
| `GridLocations(dx, dy, nx, ny, align=CENTER)` | spacing, counts | centred on the origin by default; `GridLocations(dx, 0, n, 1)` is the linear pattern (there is no `LinearLocations`) |
| `PolarLocations(r, n, start_angle=0, angular_range=360, rotate=True, endpoint=False)` | radius, count | `rotate=True` turns each copy tangent; a partial arc needs `endpoint=True` |
| `HexLocations(radius, nx, ny, major_radius=False)` | apothem by default | radius = element radius + half the gap |
| `Locations(*pts)` | explicit points | irregular sets |

`PolarLocations(10, 4, angular_range=90)` places copies at 0, 22.5, 45,
67.5° — the last is *not* at 90° unless `endpoint=True` (then 0, 30, 60, 90).

In algebra mode `GridLocations(...) * shape` returns a **list** of placed
copies; pass that list to one boolean:

| 100 Ø4 holes in a plate | time |
|---|---|
| `plate - holes` (one list operand) | 0.33 s |
| builder `with GridLocations(...): Hole(r)` | 0.36 s |
| fuse tools, then one cut | 0.40 s |
| `for h in holes: plate = plate - h` | 2.11 s |

Pairwise cost grows with the face count already in the body
([[boolean-pitfalls#multi-tool-booleans]]); keep tools of one list mutually
disjoint.

## Knurling and texture are face-count bombs

Every relief element adds faces the kernel, mesher and every later boolean
must carry:

| feature | faces | boolean | tessellation |
|---|---|---|---|
| plain cylinder | 3 | — | 248 tris |
| 30 straight V-grooves | 122 | 0.22 s | 0.56 s |
| 60 grooves (tools just touching) | 362 | 0.66 s | 2.40 s |
| 10×10 pyramids on a plate | 506 | 0.57 s | — |
| 20×20 pyramids | 2006 | 3.58 s | — |

Doubling the grooves until neighbouring tools touch tripled the faces
(slivers where tools meet), not doubled them. A diamond knurl is two helical
families crossing — each crossing is new faces. Rules:

- Add texture **last**, after every functional cut, so no later boolean
  carries it ([[feature-build-order]]).
- Keep texture tools disjoint from each other with a real gap, and small:
  clip each to the shallow region it affects.
- Budget it: if the part is printed, a 0.4 mm nozzle cannot draw relief finer
  than ~2 line widths, so a pitch under ~1 mm buys faces and no visible
  texture ([[fdm-minimum-feature-sizes]]). A slicer fuzzy-skin setting or a
  coarser pattern is often the honest answer.
- Every added face is one more the renderer's mesher can decline
  ([[unmeshable-faces]]); texture multiplies that exposure.

Measured cost of strut lattices and TPMS in B-rep:
[[lightweighting-and-lattices]].

## Checks

```python
glyphs = Text(p.label, p.font_size, font_path=p.font_file)
assert abs(glyphs.area - p.label_area) < 0.01 * p.label_area, "font fell back"
assert p.font_size * 0.73 >= p.min_cap_h
sag = p.R - (p.R**2 - (glyphs.bounding_box().size.X / 2) ** 2) ** 0.5
assert sag < p.deboss_d or USES_SHELL_METHOD, "planar deboss misses the edge letters"
before = body.volume; body -= extrude(face_plane * glyphs, amount=-p.deboss_d)
assert body.volume < before - 0.5 * glyphs.area * p.deboss_d
assert len(body.solids()) == 1
assert len(body.faces()) <= p.face_budget
```

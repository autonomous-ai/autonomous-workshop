# build123d-operations

Picking the operation, the plane, and the order — for every feature.

**Trigger:** Writing Step 6 of the spec. Load before filling the feature table.

The builder this maps onto is the `cad` skill (build123d 0.11 / cadgen 0.4.19).
Every snippet in the wiki pages it points to was executed against that version.

## Why this exists

The construction family is chosen once and inherited by every later edit. A form
authored in the wrong family **cannot be rescued by parameter edits** — only by
re-authoring, which costs the user the whole follow-up conversation. This
document exists so that choice is made from the image's evidence rather than
from habit.

The second failure it prevents is subtler: a correct operation run on the wrong
plane or selector. That produces code that compiles, yields a valid solid, and
puts the hole in the wrong face. Every row of the feature table therefore names
**both** the call and the frame it runs in.

## The feature table row

```
feature | geometry + numbers | build123d call | plane / selector | order | risk
```

- **feature** — the name the generator will use for the step or helper.
- **geometry + numbers** — dimensions with confidence tags.
- **build123d call** — the actual API, with arguments.
- **plane / selector** — the frame it runs in. Never leave this blank.
- **order** — its integer position in `gen_step()`.
- **risk** — the specific way this feature is likely to fail, or `—`.

## Where the operation knowledge lives

Every row's call, frame and risk comes from the wiki (`wiki search <words>`);
each snippet there was executed against build123d 0.11 / cadgen 0.4.19:

| to fill | page |
|---|---|
| the base solid's family from the image and `measure_image.py` signals — prismatic, tapered extrude, revolve, loft, sweep, sketch-driven, blended organic | `wiki show operation-families` |
| additive and subtractive feature calls, conformal decoration, crescents and two-circle profiles solved from tips and rim | `wiki show feature-recipes` |
| the selector cookbook and the rules that keep a selector stable | `wiki show build123d-selectors` |
| boolean order, finishing (fillets last, one corner radius, 0.6 mm bed chamfer) and the operation order as the body of `gen_step()` | `wiki show construction-strategy` |
| loft rails, PCHIP, ruled lofts; fillet and chamfer traps; boolean batching | `wiki show loft-pitfalls`, `fillet-chamfer-pitfalls`, `boolean-pitfalls` |

State the order as integers in the table. That ordering **is** the body of
`gen_step()`.

## Multi-part assemblies

When Step 5a produced more than one printed part, say explicitly that they are
labelled assembly children, not a fused solid:

```python
from cadgen.assembly import AssemblyHelper
from cadfilament import filament

asm = AssemblyHelper("enclosure")
asm.add(base, "base", color=filament("dark gray"))
asm.add(lid, "lid", color=filament("white"))
return asm.compound()
```

Fusing separately printed parts loses clearances, fits, and per-part mesh export.
Name the parts in the spec in the order they should be added.

Colour is worth one line in the spec per part, and so is the stock it prints in.
Name each printed part's colour as a filament name the implementer passes to
`filament()` — never a hex of your own, which invents a filament that cannot be
loaded. **Bambu Lab PLA Lite** is the default stock: `beige`, `black`, `blue`,
`cocoa brown`, `cyan`, `dark gray`, `gray`, `green`, `orange`, `red`,
`sunflower yellow`, `white`, `yellow`. **Bambu Lab PLA Matte**
(`material="PLA Matte"`) carries the pastels and muted tones Lite lacks:
`apple green`, `ash gray`, `bone white`, `caramel`, `charcoal`, `dark blue`,
`dark brown`, `dark chocolate`, `dark green`, `dark red`, `desert tan`,
`grass green`, `ice blue`, `ivory white`, `latte brown`, `lemon yellow`,
`lilac purple`, `mandarin orange`, `marine blue`, `nardo gray`, `plum`,
`sakura pink`, `scarlet red`, `sky blue`, `terracotta`. **Bambu Lab PETG Basic** is the tougher,
less brittle stock for a part that flexes, takes an impact, or sits somewhere
warm: `black`, `dark beige`, `dark brown`, `gray`, `green`, `misty blue`,
`navy blue`, `orange`, `pine green`, `red`, `reflex blue`, `white`, `yellow`.
Seven names are in both stocks and five of them are a different hex in each, so
a PETG row says so — `filament("red", material="PETG")` — or it gets the PLA
spool. When the
reference colour falls between two names, choose the nearer and record the
substitution as a spec row. Name a colour for every leaf, never for a group:
colour on a group compound never reaches the render even though it does reach
the STEP's XCAF label.

`cad` owns the full write-up, with the worked example and the alpha form:
**Colour** in `cad/references/build123d-modeling.md`. That skill is the one
that authors the geometry, so the rules live where they are applied.

## Assign a risk to every row

The risk column is what makes the spec worth reading twice. A row with a real
risk named is a row the implementation will get right. The common risks and
the standard answer to each are
`wiki show construction-strategy#per-feature-risks-worth-naming`.

# Quick correction: what was carried, what was regenerated

This run carries `quick_fix: true` in the run root's immutable
`MAKE-OPTIONS.json`. This file is the record quick mode requires: every
part carried forward, the sha256 it was carried on, what was
regenerated instead, and the wall-clock that saved against the source
run's own logged figure.

**Read the verdict at the bottom first if you are checking one thing.**
The short version: the hash proof came out at the maximum -- all 24
printed geometries byte-identical -- but it took until the final
verifier's own regeneration to get there, and the wall-clock saving
is small for a reason that has nothing to do with this correction.

## The hash proof, over every printed part

Computed fresh, here, over all 24. `cad/part_*.step` is written by
`cadgen`, which stamps a fixed `1970-01-01T00:00:00` header, so
identical geometry gives identical bytes and a hash comparison means
something. The baseline is `make/made.json`'s `product_manifest` in
the source archive.

| printed part | published sha256 | this run | verdict | carried? |
|---|---|---|---|---|
| `part_belt_cell.step` | `712b091c10f15660` | `712b091c10f15660` | identical | **yes** |
| `part_corona_cell.step` | `4aa6f49b240ffa62` | `4aa6f49b240ffa62` | identical | **yes** |
| `part_den_plug.step` | `9deef093613da52a` | `9deef093613da52a` | identical | **yes** |
| `part_orbit_tray.step` | `551a58339e6cf395` | `551a58339e6cf395` | identical | **yes** |
| `part_panel_northeast.step` | `6e271632bc346752` | `6e271632bc346752` | identical | history only -- reports re-measured |
| `part_panel_northwest.step` | `a9a369260291a15f` | `a9a369260291a15f` | identical | history only -- reports re-measured |
| `part_panel_southeast.step` | `2ff52ee45be65ceb` | `2ff52ee45be65ceb` | identical | history only -- reports re-measured |
| `part_panel_southwest.step` | `e17f8bca4f8a1be8` | `e17f8bca4f8a1be8` | identical | history only -- reports re-measured |
| `part_world_earth_anti.step` | `c8ff2f83e08155fa` | `c8ff2f83e08155fa` | identical | **yes** |
| `part_world_earth_sol.step` | `c000a046626ff440` | `c000a046626ff440` | identical | **yes** |
| `part_world_jupiter_anti.step` | `b84c4eade585d0e5` | `b84c4eade585d0e5` | identical | **yes** |
| `part_world_jupiter_sol.step` | `75b09a7a2e32cf4c` | `75b09a7a2e32cf4c` | identical | **yes** |
| `part_world_mars_anti.step` | `701aa22c961623ee` | `701aa22c961623ee` | identical | **yes** |
| `part_world_mars_sol.step` | `1ae25fa65cc6e3d2` | `1ae25fa65cc6e3d2` | identical | **yes** |
| `part_world_mercury_anti.step` | `5dc8f8b3af871208` | `5dc8f8b3af871208` | identical | **yes** |
| `part_world_mercury_sol.step` | `b360242a03b93ea0` | `b360242a03b93ea0` | identical | **yes** |
| `part_world_neptune_anti.step` | `c8b6c1213f10c762` | `c8b6c1213f10c762` | identical | **yes** |
| `part_world_neptune_sol.step` | `38970c1ac956ff0d` | `38970c1ac956ff0d` | identical | **yes** |
| `part_world_saturn_anti.step` | `fc1fffad990e33d1` | `fc1fffad990e33d1` | identical | **yes** |
| `part_world_saturn_sol.step` | `edee4ad4f1341581` | `edee4ad4f1341581` | identical | **yes** |
| `part_world_uranus_anti.step` | `d993913622975638` | `d993913622975638` | identical | **yes** |
| `part_world_uranus_sol.step` | `7eccfab310b21fef` | `7eccfab310b21fef` | identical | **yes** |
| `part_world_venus_anti.step` | `a1cc7ace6f856f1e` | `a1cc7ace6f856f1e` | identical | **yes** |
| `part_world_venus_sol.step` | `2727148ec7c30aa1` | `2727148ec7c30aa1` | identical | **yes** |

- byte-identical: **24**
- same shape, different bytes: **0**
- changed geometry: **0**
- byte-identical but re-measured anyway, reports written fresh: **4**

### The four board panels, which is the one surprise in this run

They are byte-identical NOW. They were not for most of the run,
and the story is worth the paragraph because it is the whole
question of what a hash proof is a proof of.

Generated on their own, mid-run, `part_panel_northeast`,
`northwest`, `southeast` and `southwest` each differed from the
published copy in exactly ONE line, and that line was a
`NEXT_ASSEMBLY_USAGE_OCCURRENCE` label: `'1'` where the published
set has `'221'`, `'2'` against `'222'`, and so on. It is the
exporter's own per-session occurrence counter. Every other line of
all four files matched, diffed line by line rather than asserted.

**It was never caused by this correction, and that was established
by a control rather than by argument.** The unedited source from
the archive was unpacked into a scratch tree and the four panels
built from it on this machine: they produced the same four
non-matching hashes. The panels import nothing from
`parts/markings`, so nothing this correction touches can reach
them.

**What closed it was the shape of the exporting process.** The
final `verify_project` run regenerates every entry in ONE `gen`
call -- the 220-occurrence assembly among them -- and in that
process the four panels are written as occurrences 221 to 224,
which is exactly what the published set carries. The counter is
not a property of the part; it is a property of the run that
wrote it. The bytes in this tree are that run's, and they match.

**Their gate reports were re-measured before any of that was
known, and the fresh reports are what this tree carries.** At the
time their bytes did not match, quick mode's licence is
byte-identity, and naming a carried report against a sha256 that
did not match the file beside it would have been the exact mistake
the final sweep exists to catch. The four gates cost seconds and
the fresh measurements are listed below. Their component ROUND
history carries forward like every other part's.

## What each carried part carries

For a byte-identical part, two things carry: its component round
history under `measure/component-rounds/<role>/`, and its per-part
`measure/thickness-<role>.md` and `measure/overhang-<role>.md`.

| role | carried on sha256 | rounds carried | thickness report | overhang report |
|---|---|---:|---|---|
| `belt_cell` | `712b091c10f15660` | 3 | `thickness-belt_cell.md` carried | `overhang-belt_cell.md` carried |
| `corona_cell` | `4aa6f49b240ffa62` | 3 | `thickness-corona_cell.md` carried | `overhang-corona_cell.md` carried |
| `den_plug` | `9deef093613da52a` | 3 | `thickness-den_plug.md` carried | `overhang-den_plug.md` carried |
| `orbit_tray` | `551a58339e6cf395` | 3 | `thickness-orbit_tray.md` carried | `overhang-orbit_tray.md` carried |
| `panel_northeast` | `6e271632bc346752` | 4 | **re-measured, see below** | **re-measured, see below** |
| `panel_northwest` | `a9a369260291a15f` | 5 | **re-measured, see below** | **re-measured, see below** |
| `panel_southeast` | `2ff52ee45be65ceb` | 5 | **re-measured, see below** | **re-measured, see below** |
| `panel_southwest` | `e17f8bca4f8a1be8` | 4 | **re-measured, see below** | **re-measured, see below** |
| `world_earth_anti` | `c8ff2f83e08155fa` | 3 | `thickness-world_earth_anti.md` carried | `overhang-world_earth_anti.md` carried |
| `world_earth_sol` | `c000a046626ff440` | 3 | `thickness-world_earth_sol.md` carried | `overhang-world_earth_sol.md` carried |
| `world_jupiter_anti` | `b84c4eade585d0e5` | 3 | `thickness-world_jupiter_anti.md` carried | `overhang-world_jupiter_anti.md` carried |
| `world_jupiter_sol` | `75b09a7a2e32cf4c` | 3 | `thickness-world_jupiter_sol.md` carried | `overhang-world_jupiter_sol.md` carried |
| `world_mars_anti` | `701aa22c961623ee` | 3 | `thickness-world_mars_anti.md` carried | `overhang-world_mars_anti.md` carried |
| `world_mars_sol` | `1ae25fa65cc6e3d2` | 3 | `thickness-world_mars_sol.md` carried | `overhang-world_mars_sol.md` carried |
| `world_mercury_anti` | `5dc8f8b3af871208` | 3 | `thickness-world_mercury_anti.md` carried | `overhang-world_mercury_anti.md` carried |
| `world_mercury_sol` | `b360242a03b93ea0` | 3 | `thickness-world_mercury_sol.md` carried | `overhang-world_mercury_sol.md` carried |
| `world_neptune_anti` | `c8b6c1213f10c762` | 3 | `thickness-world_neptune_anti.md` carried | `overhang-world_neptune_anti.md` carried |
| `world_neptune_sol` | `38970c1ac956ff0d` | 3 | `thickness-world_neptune_sol.md` carried | `overhang-world_neptune_sol.md` carried |
| `world_saturn_anti` | `fc1fffad990e33d1` | 3 | `thickness-world_saturn_anti.md` carried | `overhang-world_saturn_anti.md` carried |
| `world_saturn_sol` | `edee4ad4f1341581` | 3 | `thickness-world_saturn_sol.md` carried | `overhang-world_saturn_sol.md` carried |
| `world_uranus_anti` | `d993913622975638` | 3 | `thickness-world_uranus_anti.md` carried | `overhang-world_uranus_anti.md` carried |
| `world_uranus_sol` | `7eccfab310b21fef` | 3 | `thickness-world_uranus_sol.md` carried | `overhang-world_uranus_sol.md` carried |
| `world_venus_anti` | `a1cc7ace6f856f1e` | 3 | `thickness-world_venus_anti.md` carried | `overhang-world_venus_anti.md` carried |
| `world_venus_sol` | `2727148ec7c30aa1` | 3 | `thickness-world_venus_sol.md` carried | `overhang-world_venus_sol.md` carried |

## Every carried report, and how to tell it from a fresh one

A reader must be able to tell a carried report from a fresh one
without diffing, so this is the whole list rather than a rule. A
carried report is a file this run did not write: it came out of the
source archive unchanged, and its measurement describes the exact
STEP named in the table above.

There is one wrinkle and it is disclosed rather than smoothed over.
**The archive is sanitized.** The host replaced its own absolute
paths with placeholders before publishing it, so a carried report's
bytes are the sanitized projection of the sealed original rather than
the sealed original itself. `SANITIZATION.json` records both hashes
for every file it touched, and the check below is that each carried
report in this tree still hashes to the `public_sha256` that file
recorded -- an unbroken chain from the report the source run sealed,
through a path substitution the host performed and documented, to the
bytes here.

| carried report | sha256 here | sanitized from | chain checks |
|---|---|---|---|
| `measure/thickness-belt_cell.md` | `562e98cf3c0aeec7` | `3b6be1609ab860b8` | yes |
| `measure/overhang-belt_cell.md` | `df3cc005f22874e3` | `d5dbad17385b06bb` | yes |
| `measure/thickness-corona_cell.md` | `2d386a43df2b6248` | `106e4f7f8352b907` | yes |
| `measure/overhang-corona_cell.md` | `663929a98a225c48` | `4decdc38f1ef3b1b` | yes |
| `measure/thickness-den_plug.md` | `05dcb83aac55f643` | `44179f500c3cb586` | yes |
| `measure/overhang-den_plug.md` | `85e2aca31919ad40` | `86fbf6f4d02f9879` | yes |
| `measure/thickness-orbit_tray.md` | `956742dbd2f63358` | `936b9716036a140d` | yes |
| `measure/overhang-orbit_tray.md` | `69a207258d44119f` | `01c12d520c340302` | yes |
| `measure/thickness-world_earth_anti.md` | `cad1232203fcd953` | `92dfc8d5a2a7d461` | yes |
| `measure/overhang-world_earth_anti.md` | `1c7c2ffb68d879ae` | `de9eabc6fa10747f` | yes |
| `measure/thickness-world_earth_sol.md` | `a7730ba0ddefcee2` | `95a8047b8a2420c2` | yes |
| `measure/overhang-world_earth_sol.md` | `3dc610a7e9a1dbf6` | `28105ce50fe8ad85` | yes |
| `measure/thickness-world_jupiter_anti.md` | `1dcdb16f71b3300c` | `5807bfabedef11c5` | yes |
| `measure/overhang-world_jupiter_anti.md` | `cad8c6a431623e34` | `9e5768f945141802` | yes |
| `measure/thickness-world_jupiter_sol.md` | `adc702b744300fd2` | `73a20c57be0c0e8f` | yes |
| `measure/overhang-world_jupiter_sol.md` | `21298347f82a0ef3` | `9eb70a9951bfbe62` | yes |
| `measure/thickness-world_mars_anti.md` | `5f458f3be960eae1` | `697d56e6f870bfa9` | yes |
| `measure/overhang-world_mars_anti.md` | `b2211dd792ab4c5a` | `ba8ad3896616a4c5` | yes |
| `measure/thickness-world_mars_sol.md` | `94ae3f63cbd64f0e` | `cf812061458740d4` | yes |
| `measure/overhang-world_mars_sol.md` | `7d98e35407257684` | `18d20d9ed6996e57` | yes |
| `measure/thickness-world_mercury_anti.md` | `675a2647788d373d` | `adc35bceebe7af5c` | yes |
| `measure/overhang-world_mercury_anti.md` | `ca8f87ccfb0e7964` | `d13420db960948c2` | yes |
| `measure/thickness-world_mercury_sol.md` | `014afbc4876d8895` | `020e68f1831c85f3` | yes |
| `measure/overhang-world_mercury_sol.md` | `b6b4f983311c0cf8` | `2e5397743b762215` | yes |
| `measure/thickness-world_neptune_anti.md` | `a83fbec50ab2d4a4` | `5426e2420c5e6941` | yes |
| `measure/overhang-world_neptune_anti.md` | `d96f7dab19467348` | `1f44d1c212d18785` | yes |
| `measure/thickness-world_neptune_sol.md` | `a11e5e574e2dfe36` | `9689eb9082bffed5` | yes |
| `measure/overhang-world_neptune_sol.md` | `8a040c9b989db98e` | `e29da8b233c01a9a` | yes |
| `measure/thickness-world_saturn_anti.md` | `45e0397d428527ba` | `431b5de2bc4d7059` | yes |
| `measure/overhang-world_saturn_anti.md` | `9667effe858e4edc` | `cac673ace87ea90b` | yes |
| `measure/thickness-world_saturn_sol.md` | `f8b9c24466802853` | `bb6b0f1750aeab48` | yes |
| `measure/overhang-world_saturn_sol.md` | `b538ea9687ff842d` | `d2654d8503e33b2b` | yes |
| `measure/thickness-world_uranus_anti.md` | `9e72dc8cab4672da` | `1e0ada3b33e5d805` | yes |
| `measure/overhang-world_uranus_anti.md` | `7a126d1500712fc0` | `75953b1bc1898c66` | yes |
| `measure/thickness-world_uranus_sol.md` | `3b6bec6d74a930d8` | `a593f9e5a0cbe14f` | yes |
| `measure/overhang-world_uranus_sol.md` | `2a9d5e37fb0fce91` | `8ba964cc574362b3` | yes |
| `measure/thickness-world_venus_anti.md` | `d751c693c6ec711d` | `20d20ad24fc812f1` | yes |
| `measure/overhang-world_venus_anti.md` | `3865874d5a927aa4` | `6689f8682545b38c` | yes |
| `measure/thickness-world_venus_sol.md` | `48ee8372eca2aa7c` | `692ea6fa0a059775` | yes |
| `measure/overhang-world_venus_sol.md` | `11bdb379e5fd5dda` | `e90f5af2eca29e0e` | yes |

**40 carried reports, every one of them checked against the archive's
own record of it.**

And the other side of the same list: these are the reports this
run WROTE, for the parts it would not carry. They are fresh
measurements on the STEPs in this tree, they replaced the carried
copies that were in the tree when it was cloned, and they are not
in the table above.

| fresh report | sha256 here | verdict |
|---|---|---|
| `measure/thickness-panel_northeast.md` | `c90f3779d6042f76` | PASS |
| `measure/overhang-panel_northeast.md` | `95a48cf5fb0be737` | PASS |
| `measure/thickness-panel_northwest.md` | `cc8f833599de3d87` | PASS |
| `measure/overhang-panel_northwest.md` | `eeecf9f761700300` | PASS |
| `measure/thickness-panel_southeast.md` | `113f619bad58a6ef` | PASS |
| `measure/overhang-panel_southeast.md` | `6a000c1bb361aa10` | PASS |
| `measure/thickness-panel_southwest.md` | `96edddb8c0272c9e` | PASS |
| `measure/overhang-panel_southwest.md` | `396fe3387b1a4a66` | PASS |

So every one of the 24 printed parts has a thickness report and an
overhang report in `measure/`, 40 of them carried on the sha256 in
the first table and 8 of them written here.

### And the one thing in this tree that is NOT byte-reproducible

The 24 printed parts are, when they are generated in a whole-set
process: the table above is that, measured. `cad/antisol.step` is
not. It is the 220-occurrence assembly, and its presentation block --
the `STYLED_ITEM` and `COLOUR_RGB` records at the end of a 1,072,578
line file -- comes out in a different order on every run, while every
geometry entity before it is identical. Two builds of it were compared
line by line during this run: same line count, 3330 differing lines,
all of them in that block and none of them geometry.

So the assembly is compared by GEOMETRY rather than by bytes, which is
what `measure/occurrence-geometry.md` does -- label by label, on solid
count, exact volume and bounding box, against the published archive's
own `antisol.step`. That comparison was run on two independently
generated builds of this correction and returned the same seven
changed `jupiter_anti_*` bodies and nothing else both times.

One consequence is worth stating rather than leaving for a reader to
notice. The assembled-object round under `measure/rounds/` was
recorded against an earlier build of the assembly, because the final
`verify_project` run regenerates everything and is deliberately the
last command to touch a STEP. The round's visual finding is about
geometry, and the geometry is the same geometry -- same 220
occurrences, same names, same colours, same transforms, same bounding
box, checked in the assembly package as well as in the occurrence
table. The bytes sealed here are the verifier's.

## What quick mode did not touch, and this run ran in full

Everything below was regenerated or re-run from scratch. None of it
is scoped by quick mode, and the last item is the reason the rest is
safe.

| work | why it is never carried | what this run did |
|---|---|---|
| the hash proof above | it is the warrant for everything else | computed fresh over all 24 parts |
| `parts/*.step`, all 220 | the colour bodies are what this correction moves | rewritten by `production.py` |
| `cad/antisol.step` and the root `assembled.*` | the assembly changes whenever any part does | rebuilt |
| `refs`, `validate`, `interfere` on the assembly | interference is a property of the whole set, never of a part | run in the final `verify_project` |
| every gate on every changed part | quick mode carries nothing that moved | the four panels re-measured |
| the assembled-object rounds | the assembly is what changed | run |
| `snap/iso.png`, `snap/signature.png`, the two rank-ladder frames, and every Jupiter frame | a render is a function of the geometry, and the geometry moved | regenerated |
| `verify_project` | this is the sweep that would catch a mistake in the carry-forward reasoning | run in full |
| the independent blind review | an old review is never proof of a new correction | run fresh, unprimed |

## The wall-clock, against the source run's own figure

The archive's `make_round` logs each begin with the wall-clock the
tool took -- `(2.6s, exit 0)` -- so the source run's own figure is
readable rather than estimated. All 24 component-round HISTORIES carry
forward, but the gate time saved is only the 20 parts whose reports
carried too: summed over their archive rounds, the source run spent
**717 seconds**, or **12.0 minutes**, on work this run did not repeat.
The four board panels' directories are deliberately left out of that
figure, because two of the rounds in each are this run's own and the
directory is no longer a pure archive number.

Set against what this run actually spent on the geometry it could
not carry, measured the same way:

| work | wall-clock |
|---|---:|
| carried: the 20 parts' component rounds, from the archive's logs | 717 s |
| not carried: rebuilding all 24 printed parts | 22 s |
| not carried: re-measuring the four panels' gates | 71 s |
| not carried: `production.py`, 220 colour bodies | 266 s |
| not carried: `gen antisol.step.py`, the whole set | 268 s |
| not carried: the renders, the assembled round and `verify_project` | see `measure/verification-pipeline.md` |

**On the part count this IS the maximum-saving case: all 24 printed
geometries came out byte-identical, and every one of the 24
component-round histories is still exactly true of the file it
describes.** The brief expected that and it is what happened -- a
marking is a flush colour inlay, so moving one moves no surface.
What the brief did not expect, and what this file has to say
plainly, is that the byte-identity of four of them was not
ESTABLISHED until the last command of the run, which is why their
reports were written fresh rather than carried.

**And in WALL-CLOCK terms it is not the maximum-saving case at all.**
The saving is a few minutes against a run whose cost is dominated by
three things quick mode never scopes
-- rebuilding the 220 colour bodies, rebuilding the 52 MB assembly,
and the final verifier. That is a property of this product rather
than of this correction: a set whose printed parts are cheap and
whose assembly is enormous is the shape of project quick mode helps
least.

## Verdict

All 24 printed parts are byte-identical to the published set and
all 24 carry their component round history forward on the sha256
named above. 20 of them also carry their two print-gate reports;
the 4 board panels do not, because their bytes did not match
until the final verifier regenerated the whole set in one process,
and by then their gates had already been re-measured. **Nothing
was carried on a hash that does not match the file beside it**,
and every carried report still hashes to the value the archive's
own sanitization record gives it.

Written by `measure/quick_fix_carry.py` from the exact STEPs in this
tree and `make/made.json`, `SANITIZATION.json` in the source archive.

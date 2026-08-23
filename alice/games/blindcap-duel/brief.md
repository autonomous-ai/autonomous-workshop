# Blindcap: Duel — build brief

Blindcap: Duel is a two-player hidden-information game whose reader is made entirely from printed geometry. Every species shares the same cap-and-shank silhouette above the loam; one or two visible bites still identify the owner. Species exists only in the presence or absence of two hidden, parallel routes inside the keyed shank.

## Product bill

- 2 loam tiles, each 144 × 144 × 30mm overall, joined into one 6 × 3 field.
- 12 mushrooms, approximately 34 × 34 × 49mm: for each player, 2 deadheads, 2 brackets, 1 inkcap and 1 hollow.
- 6 crowns, 24 × 24 × 6mm.
- 6 probes, 11.8 × 11.8 × 34mm.
- 2 screened trays, 154 × 150 × 40mm.
- 1 first-print coupon set: socket, four species, two owner probes, male and female dovetails, plus admitted and blocked reference assemblies.
- 1 A5 landscape scoring aid, 210 × 148mm.

All 15 unique production families fit a 160 × 160mm bed envelope in their supplied orientation. The two trays are the largest parts. Slicer clearance is digital evidence only; a coupon print remains mandatory.

## Load-bearing constraints

1. **Species shares a silhouette; ownership remains visible.** Cap, growth rings, gills, boss, neck, shoulder, D-flat and shank envelope are common to all four species. Only the hidden route cuts vary. One or two cap bites identify the player without disclosing species.
2. **The shank cannot rotate.** A Ø21.4mm D-keyed shank enters a Ø21.8mm matching bore. Nominal diametral allowance is 0.4mm. The shank flat is at Y = −6.0mm and the bore flat at Y = −6.2mm, giving 0.2mm keyed-face allowance.
3. **The channels are independent.** Both channels are Ø6.8mm × 31mm and share one axis 70° from vertical. Their centres remain 12.6mm apart. Relative to each socket centre, mouth A is at `(6.363961, 15.273506)`mm and mouth B at `(15.273506, 6.363961)`mm. The paths remain parallel and never cross; an absent route meets solid shank.
4. **The board holds evidence until harvest.** An admitted probe rests at 3.0mm proud. A blocked probe clears at 27.632812mm proud and contacts at 27.625mm; the digital reference is 27.628906mm, approximately 28mm for table instruction. Before anything moves at harvest, players record all four public probe counts. They then withdraw every probe completely to 34mm proud, remove it, and only then lift the mushrooms.
5. **Identity is never color-only.** One or two physical marks identify each player's caps, crowns, probes and tray. One or two raised dots identify the two channel mouths.

## Interface evidence

`project/fit_checks.py` tests every species against both channels. The intended read matrix is:

| Species | One-dot path | Two-dot path |
| --- | ---: | ---: |
| deadhead | blocked | blocked |
| bracket | admitted | blocked |
| inkcap | blocked | admitted |
| hollow | admitted | admitted |

Both admitted poses clear the tile and their intended shank routes. At the blocked boundary, 27.632812mm proud clears and 27.625mm makes contact. At the blind stop, 3.1mm proud clears and 2.9mm collides; 3.0mm is the reference. These are digital solid checks, not printer evidence.

Other nominal fits:

- Crown bore to boss: 0.8mm diametral allowance.
- Tile dovetail: 0.4mm allowance per side.
- Probe: 4mm across-flats hex shaft in a Ø6.8mm channel, with a 0.9mm-radius blunt tip.
- Trays: shallow 3mm cradles and exact 5mm crown pockets, leaving a 1mm floor.

## Harvest contract

1. Before touching any probe, agree and record for each player: rival mushrooms tested in both channels, distinct rival mushrooms probed, probes beneath mushrooms bearing that player's crown, and probes resting low.
2. Pull all six probes completely clear—34mm proud—and return them to their owners.
3. Lift each mushroom and place it cap-down in its original cell so the shank points upward.
4. Rest any crown flat on the upward shank, preserving its owner and cell.
5. Identify maximal orthogonally connected same-species groves, then score the largest uncontested grove and the recorded probe counts if a tiebreak is needed.

## Build order

1. Generate and print the complete coupon set first.
2. Confirm that low and high are unmistakable from both seats, one route never leaks into the other, every keyed variant inserts and lifts without damaging force, and full probe withdrawal permits clean harvest inversion.
3. Print and test the dovetail pair.
4. Only then print the two tiles, twelve mushrooms, six crowns, six probes and two trays.
5. Run the blind two-player protocol in `content/playtest-script.md` before making any public-sale claim.

`physical_fit_verified` remains `false`. The digital gate earns a coupon print, not a public listing.

# Host inspection-batch rejection repair

- Current Make checkpoint: `1257c72104f7b75197a3f0464f9b54280343610ac58666e28fa4af7b14077f5c`
- Current Make subject: `9b712607dee2f587d239d7b9482d4da3cca7fc68f7326999db127404a4c6f4b1`
- Authoritative rejection: `c7fc2d326fc649efe10e91797dc15f0c92cf5e048601d74bad31f1a38329cd86`
- Failure code: `verifier-nonzero`
- Exact failure: `inspect batch returned 2 response(s), expected 11`
- Rejected assembly STEP SHA-256: `c5b591165c8e380faffcd359e5cbc5c11020819e16f548d018a3f4b4d21ec7ef`

## Focused repair

The host's isolated `--fresh --exports --strict-fit` run passed layout, all
five source generations, strict print fit, the 21-check paired-fit audit, the
24-check sealed-dimension audit, and all 10 motion conditions.  Its inspection
batch emitted successful assembly refs and validity responses, then its process
ended before any per-part response.  The rejected source represented both the
54 mm shell perimeter and 12-lobe reel control perimeter with 144 planar
vertices; the complete assembly exposed 1,206 B-rep faces to the long-lived
inspection process.

The repair introduces one shared `PLANAR_CURVE_FACETS = 72` parameter and uses
it for those two dense near-circular perimeters.  Seventy-two samples retain six
vertices per authored 30-degree reel scallop, preserve the exact 114 mm reel
extrema, and keep the 54 mm shell polygon chord error below a 0.4 mm nozzle.
No portal, creature profile, fit surface, detent, latch, stand, or optical
state parameter changed.

## Fresh evidence

The host-equivalent command ran against a cache-free isolated copy:

```text
verify_project <isolated-project> --fresh --exports --strict-fit
```

It returned zero in 205.84 seconds.  The formerly rejected batch emitted all
11 responses and passed assembly/part refs, every validity check, and assembly
interference.  The rest of the same run passed strict print fit, all local fit
and specification assertions, all 10 motion conditions, every exported mesh,
and every 0.8 mm thickness gate.  The exact report is
`measure/verification-pipeline.md` with SHA-256
`8c27421ce349c1c0b00ad37948fd3a5d7921b83ba09e359165c96478ad28203d`.

Topology changed as intended:

| Entry | Rejected faces | Repaired faces |
|---|---:|---:|
| assembled | 1,206 | 954 |
| front shell | 386 | 294 |
| kickstand | 48 | 48 |
| rear shell | 459 | 371 |
| shadow reel | 313 | 241 |

The primary assembly STEP changed from the rejected
`c5b591165c8e380faffcd359e5cbc5c11020819e16f548d018a3f4b4d21ec7ef`
to `3e0243306c97e5b29975107e93c6f399af5f8ef9f81415dda497bfb4e60a6b0b`.
The regenerated combined STL is
`69632ce86ea4cdbbf88981ea3332c830cfa866cbeb128fbebd8a3ea5aa557bff`.
These are digital geometry checks only; they do not prove physical printing,
fit, strength, detent feel, brightness, recognition, or durability.

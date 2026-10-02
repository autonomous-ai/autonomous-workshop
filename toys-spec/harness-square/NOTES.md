# Harness Square — working notes

Seven shell directions for the Harness device with a 3.5" square screen
(design-a-toy, Inventor Rowan Vale). `REPORT.html` is the selection page; each
`<option>/CONTRACT.md` sits beside its reference images.

## How the images were made

AI image generation via OpenRouter (`openai/gpt-5.4-image-2`), credentials read
from the main checkout's `.env` and never logged. No web imagery was used, so
there are no source URLs. The rejected prototypes in `harness-new-prototype/`
were looked at for what to avoid and were not passed to the generator.

Post-processing: flat background keyed to alpha by border flood fill, crop,
square pad with an 18% margin, resize to 800x800. Three component images got an
anisotropic aspect correction of 20% or less: m1 pod-housing (x 1.20),
m2 tile-housing (x 1.06), m3 swivel-base (height x 1.09).
`x1-swap/lineup-illustration.png` is a family illustration, not a reference.

## Status (Stage 3b partial)

Options S1–S3 and M1–M3 had two generation rounds and were measured: silhouette
aspect, bezel window ratio, slot, cheek gap, post and hole counts, and for each
assembly a camera fit against the contract's projected part boxes. Where the
image was better, the contract followed it (M1 base 124 -> 113 mm with a 12 mm bar,
M2 flap 56 mm, M3 post 13 mm, S1 slot opening 20 mm in plan). The remaining
differences are listed per option in `REPORT.html`.

X1 has had one generation round and has not been measured.

Not done yet for any option: the full per-feature table, the Stage 3c print
check, and the Stage 3d motion check. They run on the option chosen, before
handoff to build-a-toy.

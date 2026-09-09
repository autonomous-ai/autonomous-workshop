- Render every sealed Make revision on the trusted host with a pinned
  three.js renderer under headless Chromium (`tools/render/`, installed per
  machine with `npm ci`; `workshop doctor` reports it under `render`). The
  hero, each `product.json` `presentation.states` mesh, and a fixed-camera
  signature strip are rendered from sealed bytes in the sealed part colours,
  bound to the Made product hash in `artifacts/make/rNNNN/renders/renders.json`
  with a private host copy, citable in `MANUAL-DESIGN.json` as
  `renders/<name>.png`, and shipped to the Factory as the listing cover. A
  missing or failing renderer records `unavailable` and never blocks a run.

# Host product renderer

The trusted Workshop host renders every sealed Make revision with three.js
under headless Chromium (swiftshader, no GPU, no network). Outputs are bound in
`artifacts/make/rNNNN/renders/renders.json`; the Release manual may cite them
and the Factory import ships the hero as the listing cover.

Install once per machine (Node 22 or newer):

```bash
cd tools/render
npm ci
npx playwright install chromium
```

`workshop doctor` reports the renderer under the `render` check by rendering a
built-in cube. Without it every Release still succeeds: the manual falls back
to Make's own snaps and the shop renders its own cover.

`render_scene.mjs <scene.json> <out_dir>` renders one scene file; the Python
side (`workshop.release.renders`) writes that file from sealed bytes only.
Set `WORKSHOP_NODE_BIN` to point at a specific Node binary.
Set `WORKSHOP_HOST_RENDERER=off` to skip rendering entirely (CI, or a host
that must not launch a browser); every consumer then takes the fallback path.

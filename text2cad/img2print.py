#!/root/text2cad/.venv/bin/python
"""img2print — image → TRELLIS 2 → printable mesh → gate → gcode → draft.

    ./img2print.py <image> --slug <slug> [--title "..."] [--resolution 1024]
                   [--seed N] [--backend hf|fal] [--no-publish] [--no-slice]

Sibling lane to the CAD pipeline: same out/<slug>/ layout (concept.png,
brief.md, run.json, <slug>.stl, gate.json, <slug>.gcode) and the same
publish.py draft flow at the end. TRELLIS returns ONE fused visual mesh, so
this is a figurine/display lane — no fe_parts/, no .step, no mechanism.

Backends: hf (default) = the free microsoft/TRELLIS.2 Space via gradio_client
(HF_TOKEN in .env optional, raises the ZeroGPU quota); partpacker = NVIDIA
PartPacker Space (free, lower fidelity, but emits SEPARATE PARTS -> real
fe_parts/*.stl + part_colors.json); fal = fal.ai paid API (FAL_KEY in .env,
$0.25-0.35/run).
"""
import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
FAL_QUEUE = "https://queue.fal.run/fal-ai/trellis-2"
# A1-mini gate limits: 160mm footprint hard-fail, 180mm machine height.
FOOTPRINT_MM = 150.0
HEIGHT_MM = 165.0
COST_USD = {512: 0.25, 1024: 0.30, 1536: 0.35}
PALETTE = ["#37414d", "#e0592a", "#b9c0ca", "#f2b134", "#1f8a8a"]


def load_env():
    for line in (HERE / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"'))


def fal_call(url: str, key: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(url, headers={"Authorization": f"Key {key}",
                                               "Content-Type": "application/json"},
                                 data=json.dumps(body).encode() if body else None)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def trellis_hf(image: Path, resolution: int, seed, glb_out: Path) -> dict:
    """Free path: the official Space, session API start_session ->
    preprocess_image -> image_to_3d -> extract_glb."""
    from gradio_client import Client, handle_file
    space = os.environ.get("TRELLIS_SPACE", "microsoft/TRELLIS.2")
    t0 = time.time()
    c = Client(space, token=os.environ.get("HF_TOKEN", "").strip() or None)
    c.predict(api_name="/start_session")
    pre = c.predict(input=handle_file(str(image)), api_name="/preprocess_image")
    pre_path = pre if isinstance(pre, str) else pre["path"]
    c.predict(image=handle_file(pre_path), seed=int(seed or 0),
              resolution=str(resolution), api_name="/image_to_3d")
    glb, _ = c.predict(api_name="/extract_glb")
    shutil.copy(glb, glb_out)
    print(f"trellis[hf]: {glb_out.name} {glb_out.stat().st_size // 1024}KB in "
          f"{int(time.time() - t0)}s")
    return {"backend": space, "seconds": int(time.time() - t0), "cost_usd": 0}


def trellis_partpacker(image: Path, resolution: int, seed, glb_out: Path) -> dict:
    """Part-level generation: each part is a separate sub-mesh in the GLB.
    resolution is unused (the Space has its own grid_res)."""
    from gradio_client import Client, handle_file
    space = os.environ.get("PARTPACKER_SPACE", "cpuai/PartPacker")
    t0 = time.time()
    c = Client(space, token=os.environ.get("HF_TOKEN", "").strip() or None)
    pre = c.predict(image_path=handle_file(str(image)), api_name="/process_image")
    pre_path = pre if isinstance(pre, str) else pre["path"]
    glb = c.predict(input_image=handle_file(pre_path), seed=int(seed or 0),
                    api_name="/process_3d")
    shutil.copy(glb, glb_out)
    print(f"trellis[partpacker]: {glb_out.name} {glb_out.stat().st_size // 1024}KB "
          f"in {int(time.time() - t0)}s")
    return {"backend": space, "seconds": int(time.time() - t0), "cost_usd": 0}


def trellis_fal(image: Path, resolution: int, seed, glb_out: Path) -> dict:
    key = os.environ.get("FAL_KEY", "").strip()
    if not key:
        raise SystemExit("img2print: set FAL_KEY in .env (fal.ai dashboard)")
    mime = "image/png" if image.suffix.lower() == ".png" else "image/jpeg"
    data_uri = f"data:{mime};base64," + base64.b64encode(image.read_bytes()).decode()
    body = {"image_url": data_uri, "resolution": resolution}
    if seed is not None:
        body["seed"] = seed
    sub = fal_call(FAL_QUEUE, key, body)
    rid = sub["request_id"]
    print(f"trellis: submitted {rid} (resolution={resolution})")
    t0 = time.time()
    while True:
        if time.time() - t0 > 900:
            raise SystemExit("trellis: timed out after 15min")
        st = fal_call(f"{FAL_QUEUE}/requests/{rid}/status", key)
        if st.get("status") == "COMPLETED":
            break
        if st.get("status") not in ("IN_QUEUE", "IN_PROGRESS"):
            raise SystemExit(f"trellis: {st}")
        time.sleep(5)
    res = fal_call(f"{FAL_QUEUE}/requests/{rid}", key)
    glb_url = res["model_glb"]["url"]
    urllib.request.urlretrieve(glb_url, glb_out)
    print(f"trellis: {glb_out.name} {glb_out.stat().st_size // 1024}KB in "
          f"{int(time.time() - t0)}s")
    return {"backend": "fal-ai/trellis-2", "request_id": rid,
            "seconds": int(time.time() - t0), "glb_url": glb_url,
            "cost_usd": COST_USD.get(resolution)}


def color_of(g) -> str | None:
    try:
        c = g.visual.material.baseColorFactor
        return "#%02x%02x%02x" % tuple(int(round(v * 255)) if v <= 1 else int(v)
                                       for v in c[:3])
    except Exception:
        pass
    try:
        c = g.visual.vertex_colors[0]
        return "#%02x%02x%02x" % (int(c[0]), int(c[1]), int(c[2]))
    except Exception:
        return None


def emit_parts(parts, hexes, parts_dir: Path, stl_out: Path, part_gap: float):
    """fe_parts/*.stl in assembled pose + part_colors.json + the gapped
    viewer-only assembled variant (erode + per-part Fibonacci micro-shift so
    nothing survives the FE's 1e-4 weld)."""
    shutil.rmtree(parts_dir, ignore_errors=True)
    parts_dir.mkdir()
    part_colors = {}
    for j, (g, hx) in enumerate(zip(parts, hexes)):
        name = f"part_{j:02d}.stl"
        g.export(str(parts_dir / name))
        part_colors[name] = hx
    (parts_dir.parent / "part_colors.json").write_text(
        json.dumps(part_colors, indent=2), encoding="utf-8")
    if part_gap > 0:
        shrunk = []
        for j, g in enumerate(parts):
            v = g.copy()
            v.vertices = v.vertices - np.nan_to_num(v.vertex_normals) * part_gap
            th = j * 2.399963  # golden angle
            z = 1 - 2 * (j + 0.5) / max(len(parts), 1)
            r = (1 - z * z) ** 0.5
            v.apply_translation(np.array([r * np.cos(th), r * np.sin(th), z])
                                * part_gap)
            shrunk.append(v)
        viewer = stl_out.with_name(stl_out.stem + "_viewer.stl")
        trimesh.util.concatenate(shrunk).export(str(viewer))
        print(f"mesh: viewer variant {viewer.name} (part gap {part_gap}mm)")


def to_print_stl(glb: Path, stl_out: Path, parts_dir: Path | None = None,
                 part_gap: float = 0.0) -> dict:
    scene = trimesh.load(str(glb))
    geoms = scene.dump() if isinstance(scene, trimesh.Scene) else [scene]
    colors = [color_of(g) for g in geoms]
    # Geometry only — carrying PBR textures through split/concatenate OOMs a
    # 15GB box on a 300k-tri shell soup.
    geoms = [trimesh.Trimesh(vertices=g.vertices, faces=g.faces, process=False)
             for g in geoms]
    m = trimesh.util.concatenate(geoms) if len(geoms) > 1 else geoms[0].copy()
    # glTF is Y-up; the bed is Z-up.
    rot = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
    m.apply_transform(rot)
    m.merge_vertices()
    m.update_faces(m.nondegenerate_faces())
    m.remove_unreferenced_vertices()
    # TRELLIS shell soup: drop floating debris (first run carried ~4,700
    # single-triangle shells into the gcode). Relative threshold — units are
    # still arbitrary here.
    comps = m.split(only_watertight=False)
    if len(comps) > 1:
        keep = [c for c in comps if len(c.faces) >= 50
                and max(c.extents) >= 0.02 * max(m.extents)]
        if keep:
            m = trimesh.util.concatenate(keep)
    if not m.is_watertight:
        trimesh.repair.fill_holes(m)
    trimesh.repair.fix_normals(m)
    # Fill the printable envelope: model units are arbitrary.
    ext = m.extents
    scale = min(FOOTPRINT_MM / max(ext[0], ext[1]), HEIGHT_MM / ext[2])
    m.apply_scale(scale)
    shift = [-m.bounds[0][0] - m.extents[0] / 2,
             -m.bounds[0][1] - m.extents[1] / 2, -m.bounds[0][2]]
    m.apply_translation(shift)
    m.export(str(stl_out))
    d = m.extents
    n_parts = 1
    if parts_dir is not None and len(geoms) > 1:
        # Per-part STLs in ASSEMBLED pose under the same transform, so
        # fe_colors.py's geometric ownership against assembled.stl holds.
        for g in geoms:
            g.apply_transform(rot)
            g.apply_scale(scale)
            g.apply_translation(shift)
        # Real parts only: PartPacker pads its output with debris (first run:
        # 23 of 27 "parts" were 1-4 triangles under 1mm).
        real = [i for i, g in enumerate(geoms)
                if len(g.faces) >= 50 and max(g.extents) >= 3.0]
        if len(real) > 1:
            emit_parts([geoms[i] for i in real],
                       [colors[i] or PALETTE[j % len(PALETTE)]
                        for j, i in enumerate(real)],
                       parts_dir, stl_out, part_gap)
            n_parts = len(real)
    print(f"mesh: {len(m.faces)} tris, {n_parts} part(s), "
          f"{d[0]:.0f}x{d[1]:.0f}x{d[2]:.0f}mm, watertight={m.is_watertight}")
    return {"tris": int(len(m.faces)), "n_parts": n_parts,
            "bbox_mm": [round(float(x), 1) for x in d],
            "watertight": bool(m.is_watertight)}


def to_print_stl_color(glb: Path, stl_out: Path, parts_dir: Path,
                       part_gap: float, k: int = 10, max_parts: int = 24) -> dict:
    """Color-split: TRELLIS bakes the input image's colors into the texture,
    so faces cluster by baked color (k-means) + adjacency into parts whose
    color IS the image's color. For inputs where each component has a distinct
    color; texture noise/weathering is absorbed into large neighbors."""
    MIN_FACES, MIN_MM = 300, 4.0
    scene = trimesh.load(str(glb))
    geoms = scene.dump() if isinstance(scene, trimesh.Scene) else [scene]
    plain = []
    for g in geoms:
        try:
            vc = np.asarray(g.visual.to_color().vertex_colors)[:, :3]
            # TRELLIS.2 writes its baseColor map in LINEAR space (stored
            # pixels are dark; renderers apply the sRGB transfer on display).
            # Convert so clusters and hex colors match what the eye sees.
            vc = (255.0 * (vc / 255.0) ** (1 / 2.2)).astype(np.uint8)
        except Exception:
            vc = np.full((len(g.vertices), 3), 200, np.uint8)
        plain.append(trimesh.Trimesh(vertices=g.vertices, faces=g.faces,
                                     vertex_colors=vc, process=False))
    m = trimesh.util.concatenate(plain) if len(plain) > 1 else plain[0]
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    ext = m.extents
    scale = min(FOOTPRINT_MM / max(ext[0], ext[1]), HEIGHT_MM / ext[2])
    m.apply_scale(scale)
    m.apply_translation([-m.bounds[0][0] - m.extents[0] / 2,
                         -m.bounds[0][1] - m.extents[1] / 2, -m.bounds[0][2]])
    m.export(str(stl_out))

    fc = np.asarray(m.visual.face_colors)[:, :3].astype(np.float64)
    rng = np.random.default_rng(0)
    cent = fc[rng.choice(len(fc), min(k, len(fc)), replace=False)]
    for _ in range(25):
        lab = ((fc[:, None, :] - cent[None, :, :]) ** 2).sum(-1).argmin(1)
        for j in range(len(cent)):
            if (lab == j).any():
                cent[j] = fc[lab == j].mean(0)
    # collapse near-identical centroids (weathering makes shades, not colors)
    for a in range(len(cent)):
        for b in range(a + 1, len(cent)):
            if np.linalg.norm(cent[a] - cent[b]) < 40:
                lab[lab == b] = a
    adj = m.face_adjacency
    comps = trimesh.graph.connected_components(
        adj[lab[adj[:, 0]] == lab[adj[:, 1]]], nodes=np.arange(len(m.faces)),
        min_len=1)
    comp = np.zeros(len(m.faces), np.int64)
    for i, c in enumerate(comps):
        comp[c] = i
    # absorb small components into their most-shared neighbor
    for _ in range(4):
        sizes = np.bincount(comp)
        small = sizes < MIN_FACES
        if not small[comp[adj[:, 0]]].any() and not small[comp[adj[:, 1]]].any():
            break
        ca, cb = comp[adj[:, 0]], comp[adj[:, 1]]
        votes = {}
        for a, b in zip(ca[ca != cb], cb[ca != cb]):
            if small[a] and sizes[b] > sizes[a]:
                votes.setdefault(a, {}).setdefault(b, 0)
                votes[a][b] += 1
            if small[b] and sizes[a] > sizes[b]:
                votes.setdefault(b, {}).setdefault(a, 0)
                votes[b][a] += 1
        if not votes:
            break
        remap = np.arange(sizes.size)
        for s, nb in votes.items():
            remap[s] = max(nb, key=nb.get)
        comp = remap[comp]
    # cap: absorb the smallest remaining component into its most-shared
    # neighbor until only max_parts survive (shading on same-color surfaces
    # over-segments — 320 comps on an all-gray test mesh)
    while True:
        ids, sizes = np.unique(comp, return_counts=True)
        if len(ids) <= max_parts and (sizes >= MIN_FACES).all():
            break
        order = np.argsort(sizes)
        target = ids[order[0]]
        ca, cb = comp[adj[:, 0]], comp[adj[:, 1]]
        mask = (ca == target) ^ (cb == target)
        nb = np.where(ca[mask] == target, cb[mask], ca[mask])
        if len(nb):
            vals, cnts = np.unique(nb, return_counts=True)
            comp[comp == target] = vals[np.argmax(cnts)]
        else:  # floating island with no adjacency: fold into the biggest
            comp[comp == target] = ids[order[-1]]
    keep = [c for c in np.unique(comp)
            if (comp == c).sum() >= MIN_FACES]
    import colorsys

    def vivid_hex(rgb):
        # weathering desaturates the median — take the most-saturated
        # quartile (the actual paint) and lift it toward what the eye reads
        a = rgb / 255.0
        s = (a.max(1) - a.min(1)) / np.maximum(a.max(1), 1e-6)
        sel = s >= np.quantile(s, 0.75)
        base = np.median(a[sel] if sel.any() else a, axis=0)
        h, s0, v = colorsys.rgb_to_hsv(*base)
        r, g, b = colorsys.hsv_to_rgb(h, min(1.0, s0 * 1.5 + 0.05),
                                      min(0.95, max(0.3, v * 1.15)))
        return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))

    parts, hexes = [], []
    for c in sorted(keep, key=lambda c: -(comp == c).sum()):
        sub = m.submesh([np.where(comp == c)[0]], append=True)
        if max(sub.extents) < MIN_MM:
            continue
        parts.append(sub)
        hexes.append(vivid_hex(fc[comp == c]))
    n_parts = 1
    if len(parts) > 1:
        emit_parts(parts, hexes, parts_dir, stl_out, part_gap)
        n_parts = len(parts)
    d = m.extents
    print(f"mesh: {len(m.faces)} tris, color-split -> {n_parts} part(s), "
          f"{d[0]:.0f}x{d[1]:.0f}x{d[2]:.0f}mm")
    return {"tris": int(len(m.faces)), "n_parts": n_parts,
            "bbox_mm": [round(float(x), 1) for x in d],
            "watertight": bool(m.is_watertight), "split": "color"}


def slice_gcode(out_dir: Path, slug: str) -> dict:
    """Same Orca CLI + profile as gate.py, but keeps the gcode and turns on
    tree supports — organic TRELLIS meshes rarely print supportless."""
    cli = os.environ.get("ORCASLICER_CLI", "").strip()
    profile = [p.strip() for p in os.environ.get("ORCA_PROFILE", "").split(";") if p.strip()]
    if not cli or len(profile) != 3:
        return {"gcode": None, "note": "no ORCA config"}
    gdir = out_dir / "gcode"
    shutil.rmtree(gdir, ignore_errors=True)
    gdir.mkdir()
    # A second process-type settings file is rejected as a duplicate, so the
    # supports switch rides a renamed clone of the process profile instead.
    proc = json.loads(Path(profile[1]).read_text(encoding="utf-8"))
    proc.update({"name": proc["name"] + " img2print-supports", "from": "User",
                 "enable_support": "1", "support_type": "tree(auto)"})
    supported = gdir / "process_supports.json"
    supported.write_text(json.dumps(proc), encoding="utf-8")
    for settings in (f"{profile[0]};{supported}",
                     f"{profile[0]};{profile[1]}"):  # retry supportless if clone rejected
        r = subprocess.run([cli, "--load-settings", settings,
                            "--load-filaments", profile[2], "--slice", "0",
                            "--outputdir", str(gdir), str(out_dir / f"{slug}.stl")],
                           capture_output=True, text=True, timeout=600)
        gcodes = sorted(gdir.glob("*.gcode"))
        if r.returncode == 0 and gcodes:
            dst = out_dir / f"{slug}.gcode"
            shutil.move(str(gcodes[0]), dst)
            raw = dst.read_bytes()
            head = raw[:16000].decode(errors="ignore")
            tail = raw[-16000:].decode(errors="ignore")  # filament stats sit at EOF
            t = re.search(r"(?:estimated printing time.*?=|total estimated time:|model printing time:)"
                          r"\s*(?:(\d+)d)?\s*(?:(\d+)h)?\s*(?:(\d+)m)?", head, re.I)
            mins = (int(t.group(1) or 0) * 1440 + int(t.group(2) or 0) * 60
                    + int(t.group(3) or 0)) if t else None
            # this profile reports [cm3] only — grams via PLA density
            f = re.search(r"filament used \[g\]\s*=\s*([\d.]+)", tail, re.I) or \
                re.search(r"filament used \[cm3\]\s*=\s*([\d.]+)", tail, re.I)
            grams = float(f.group(1)) * (1.0 if "[g]" in f.group(0) else 1.24) if f else None
            info = {"gcode": dst.name, "supports": "process_supports" in settings,
                    "print_min": mins,
                    "filament_g": round(grams, 1) if grams else None}
            print(f"slice: {dst.name} print_min={info['print_min']} "
                  f"filament_g={info['filament_g']} supports={info['supports']}")
            return info
    return {"gcode": None, "note": (r.stderr or r.stdout)[-200:]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--title", default="")
    ap.add_argument("--resolution", type=int, default=1024, choices=(512, 1024, 1536))
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--backend", choices=("hf", "partpacker", "fal"), default="hf")
    ap.add_argument("--part-gap", type=float, default=0.05,
                    help="viewer-only shrink per part (mm) so the FE colors "
                         "every part separately; 0 disables")
    ap.add_argument("--split", choices=("none", "color"), default="none",
                    help="color: segment the (textured) mesh into parts by "
                         "baked image color — for inputs colored per part")
    ap.add_argument("--colors", type=int, default=10,
                    help="k-means color count for --split color")
    ap.add_argument("--max-parts", type=int, default=24,
                    help="part cap for --split color; smallest regions are "
                         "absorbed into neighbors")
    ap.add_argument("--no-publish", action="store_true")
    ap.add_argument("--no-slice", action="store_true")
    args = ap.parse_args()
    load_env()
    image = Path(args.image).resolve()
    if not image.is_file():
        raise SystemExit(f"img2print: no such image: {image}")
    out_dir = HERE / "out" / args.slug
    out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(image, out_dir / "concept.png")
    shutil.copy(image, out_dir / "hero.png")

    run = {"pipeline": "img2print", "source_image": image.name,
           "prompt": f"img2print: {args.slug} — photo concept lifted to a printable "
                     f"figurine via TRELLIS 2 image-to-3D"}
    gen = {"hf": trellis_hf, "partpacker": trellis_partpacker,
           "fal": trellis_fal}[args.backend]
    run["trellis"] = gen(image, args.resolution, args.seed, out_dir / "trellis.glb")
    if args.split == "color":
        run["mesh"] = to_print_stl_color(out_dir / "trellis.glb",
                                         out_dir / f"{args.slug}.stl",
                                         out_dir / "fe_parts", args.part_gap,
                                         args.colors, args.max_parts)
    else:
        run["mesh"] = to_print_stl(out_dir / "trellis.glb", out_dir / f"{args.slug}.stl",
                                   out_dir / "fe_parts" if args.backend == "partpacker" else None,
                                   args.part_gap)

    title = args.title or args.slug.replace("-", " ").title()
    if not (out_dir / "brief.md").is_file():
        (out_dir / "brief.md").write_text(
            f"# {title}\n\n## Concept\n\nA display print lifted straight from a "
            f"single concept photo by TRELLIS 2 image-to-3D — the photographed "
            f"object as a solid, bed-ready figurine ({run['mesh']['n_parts']} "
            f"part(s), {run['mesh']['bbox_mm'][0]:.0f}mm wide).\n\n## Provenance\n\n"
            f"- source: {image.name} (concept.png)\n"
            f"- TRELLIS 2 via {run['trellis']['backend']}, "
            f"resolution={args.resolution}, seed={args.seed}\n",
            encoding="utf-8")

    g = subprocess.run([str(HERE / ".venv/bin/python"), str(HERE / "gate.py"),
                        str(out_dir), "--no-slice"], capture_output=True, text=True)
    print(g.stdout.strip()[-300:])
    run["gate_pass"] = g.returncode == 0  # informational: organic meshes fail CAD rules
    if not args.no_slice:
        run["slice"] = slice_gcode(out_dir, args.slug)
    (out_dir / "run.json").write_text(json.dumps(run, indent=2), encoding="utf-8")

    if not args.no_publish:
        p = subprocess.run([sys.executable, str(HERE / "publish.py"), args.slug],
                           capture_output=True, text=True, cwd=HERE)
        print((p.stdout + p.stderr).strip()[-500:])
        if p.returncode != 0:
            return 1
        viewer = out_dir / f"{args.slug}_viewer.stl"
        if viewer.is_file() and (out_dir / "published.json").is_file():
            # publish.py uploaded the fused print STL; swap the CDN copy for
            # the gapped viewer variant so the FE colors every part.
            purl = json.loads((out_dir / "published.json").read_text())["project_url"]
            r = subprocess.run(["/root/gcsvenv/bin/python",
                                str(HERE / "gcs_upload_project.py"), str(viewer),
                                purl, str(out_dir / "fe_parts")],
                               capture_output=True, text=True, timeout=600)
            print(r.stdout.strip().splitlines()[-1] if r.returncode == 0
                  else f"viewer upload FAILED: {r.stderr[-200:]}")
    print(f"img2print DONE: out/{args.slug}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())

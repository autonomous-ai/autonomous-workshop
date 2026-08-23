#!/usr/bin/env python3
"""Key a published multi-part design's colors the way the FE actually resolves
them, and store the result on its thumbnail job — the automated version of the
f14 repair (2026-08-13).

    /root/.local/bin/uv run --with trimesh --with numpy python fe_colors.py <slug> [--dry-run]

Reads  out/<slug>/published.json          (design id from publish.py)
       out/<slug>/fe_parts/*.stl            (per-part meshes, uploaded as
                                           assembled_<name>.stl siblings)
       out/<slug>/part_colors.json        ({"assembled_foo.stl": "#hex"} —
                                           authored by the design phase;
                                           missing parts default #ffffff)
Steps  1. stage /root/aibatch/<id>/model.stl and run render_three43_fe.mjs
          FE_DUMP_GROUPS=1 -> fe_groups.json: the FE part numbering (slivers
          shed at contact faces take part numbers too — ecm-website known bug,
          so filename keys alone MISKEY any fragmented assembly).
       2. own each FE group geometrically (bbox + nearest part vertices).
       3. build assembly_parts (order = FE group, part = FE color key,
          color = owner's color) + part_colors, upsert the history's
          thumbnail job (a real queued render job when none exists).
       4. re-run the dump FE_STRICT=1 against the final colors — exit 4 if
          any real part would still render white.
Exit   0 ok (or single-mesh design: nothing to key), 2 bad input, 4 verify failed.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
RENDER = "/root/aibatch/render_three43_fe.mjs"
SLIVER_TRIS = 50  # matches REAL_PART_MIN_TRIS in the renderer


def env_of(path):
    out = {}
    for line in open(path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip().strip(chr(34))
    return out


def main():
    slug = sys.argv[1]
    dry = "--dry-run" in sys.argv
    # --dir lets another pipeline reuse this: text2game's out/ lives in its own
    # repo, and re-implementing the FE group ownership there would duplicate the
    # one piece of logic that stops a fragmented assembly being miskeyed.
    out_dir = HERE / "out" / slug
    if "--dir" in sys.argv:
        out_dir = Path(sys.argv[sys.argv.index("--dir") + 1]).resolve()
    pub = out_dir / "published.json"
    if not pub.is_file():
        print("fe_colors: no published.json — publish first"); return 2
    info = json.loads(pub.read_text())
    did = info["id"]

    parts_dir = out_dir / "fe_parts"
    if not (parts_dir.is_dir() and list(parts_dir.glob("*.stl"))):
        print("fe_colors: single-mesh design (no parts dir) — nothing to key"); return 0
    uploaded = {}   # uploaded sibling name -> local path
    for p in sorted(parts_dir.glob("*.stl")):
        name = p.name if p.name.startswith("assembled_") else "assembled_" + p.name
        uploaded[name] = p

    colors_file = out_dir / "part_colors.json"
    palette = {}
    if colors_file.is_file():
        for k, v in json.loads(colors_file.read_text()).items():
            k = k if k.startswith("assembled_") else "assembled_" + k
            palette[k] = v
    else:
        print("fe_colors: WARNING no part_colors.json — all parts default #ffffff")
    for name in uploaded:
        palette.setdefault(name, "#ffffff")

    from pymongo import MongoClient
    from bson import ObjectId
    senv = env_of("/root/panda-secrets/.env")
    db = MongoClient(senv["MONGODB_URI"])[senv.get("MONGODB_DBNAME", "pandasocial")]
    D = ObjectId(did)
    hist = db.design_history.find_one({"design_id": D})
    if not hist or not hist.get("project_url"):
        print("fe_colors: design_history/project_url missing — bridge the project first"); return 2
    purl = hist["project_url"].rstrip("/")

    # 1. FE group dump via the shared renderer (the FE-parity authority).
    stage = Path("/root/aibatch") / did
    stage.mkdir(parents=True, exist_ok=True)
    if not (stage / "model.stl").exists():
        # The staged mesh must MATCH the uploaded assembled.stl — img2print's
        # gapped viewer variant, when present, is what actually sits on the CDN.
        stl = out_dir / f"{slug}_viewer.stl"
        if not stl.is_file():
            stl = out_dir / f"{slug}.stl"
        if not stl.is_file():
            stl = out_dir / "main.stl"
        if not stl.is_file():
            stl = out_dir / "assembled.stl"   # text2game names it this
        if not stl.is_file():
            print("fe_colors: no assembled STL in out dir"); return 2
        os.symlink(stl, stage / "model.stl")
    if not (stage / "assembly_colors.json").exists():
        (stage / "assembly_colors.json").write_text(json.dumps({"colors": {}}))
    r = subprocess.run(["node", RENDER, did],
                       env={**os.environ, "PROJECT_URL": purl, "FE_DUMP_GROUPS": "1"},
                       cwd="/root/aibatch", capture_output=True, text=True, timeout=600)
    if r.returncode != 0 or not (stage / "fe_groups.json").is_file():
        print("fe_colors: group dump failed:", (r.stdout + r.stderr)[-300:]); return 2
    groups = json.loads((stage / "fe_groups.json").read_text())
    print(f"fe_colors: {len(groups)} FE groups, {len(uploaded)} part files")

    # 2. Own each group: bbox candidates, nearest part vertices tie-break.
    meshes = {}
    for name, p in uploaded.items():
        m = trimesh.load(str(p), force="mesh")
        meshes[name] = (m.bounds.copy(), m.vertices.view(np.ndarray))
    def owner_of(centroid):
        c = np.asarray(centroid)
        cands = [n for n, (b, _) in meshes.items()
                 if np.all(c >= b[0] - 0.5) and np.all(c <= b[1] + 0.5)] or list(meshes)
        if len(cands) == 1:
            return cands[0]
        return min(cands, key=lambda n: float(np.min(np.linalg.norm(meshes[n][1] - c, axis=1))))

    ap, pc = [], {}
    for g in groups:
        # 2026-08-16: when the FE group key IS a sibling part filename, the
        # match is exact by NAME — the geometric fallback mis-owned all 14
        # one-way-newsreel groups to l_frame because the frame's bbox spans
        # the whole machine and swallowed every centroid. Geometry is only
        # for merged single-mesh groups (keys like "assembled.stl#26").
        own = g["key"] if g["key"] in uploaded else owner_of(g["centroid"])
        stem = own[:-4]
        ap.append({"order": g["order"], "part": g["key"], "color": palette[own],
                   "mesh_name": stem if g["faces"] >= SLIVER_TRIS else stem + "_sliver"})
        pc[own] = palette[own]
    for e in ap[:6] + [x for x in ap if x["order"] >= len(uploaded)][:6]:
        print("  ", e["order"], e["part"], "->", e["mesh_name"], e["color"])

    # Degenerate-map guard: a multi-color palette resolving to ONE color means
    # the owner matching failed wholesale (every part painted like the frame,
    # everything else white in the viewer) — refuse to write it.
    if len(set(pc.values())) == 1 and len(set(palette[n] for n in uploaded)) > 1:
        print("fe_colors: DEGENERATE MAP — multi-color palette collapsed to a "
              "single color; owner matching failed. Refusing to write.")
        return 5

    if dry:
        print("fe_colors: DRY RUN — no DB write")
    else:
        now = datetime.now(timezone.utc)
        res = db.thumbnail_jobs.update_one(
            {"design_id": D, "history_id": hist["_id"]},
            {"$set": {"assembly_parts": ap, "part_colors": pc,
                      "project_url": hist["project_url"], "updated_at": now},
             # uniq_generation_job is unique but NOT sparse, and the lone null
             # slot was consumed by the eclipse inert doc (2026-08-13) — every
             # later insert needs its own id.
             # Contract (models/thumbnail_job.go:57-60): a new render job
             # carries design_id, history_id, generation_job_id, project_url,
             # status "queued" — nothing else. status afterwards belongs to the
             # Blender worker; superseded/image_published/video_published are
             # Go's publication acks and must never be written from here.
             "$setOnInsert": {"generation_job_id": ObjectId(),
                              "created_at": now, "status": "queued"}},
            upsert=True)
        print(f"fe_colors: job {'updated' if res.matched_count else 'inserted'}")

    # 4. Strict verify against the exact map the FE will resolve.
    (stage / "assembly_colors.json").write_text(
        json.dumps({"colors": {e["part"]: e["color"] for e in ap}}))
    r = subprocess.run(["node", RENDER, did],
                       env={**os.environ, "PROJECT_URL": purl,
                            "FE_DUMP_GROUPS": "1", "FE_STRICT": "1"},
                       cwd="/root/aibatch", capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        print("fe_colors: STRICT VERIFY FAILED:", (r.stdout + r.stderr)[-300:]); return 4
    print("fe_colors: verified — every real part keyed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

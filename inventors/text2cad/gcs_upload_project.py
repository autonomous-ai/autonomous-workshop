#!/usr/bin/env python3
"""Upload a single-mesh FE project to a design-history CDN prefix so the
platform viewer has files to load: assembled.stl + _tree.json (+ params.py if
present next to the STL). Run with /root/gcsvenv/bin/python (needs
google-cloud-storage). Multi-part designs still need a hand-written bridge
(pattern: out/eclipse-v2/gcs_project.py) for per-part shells and colors.

    gcs_upload_project.py <path/to/model.stl> <project_url> [parts_dir]

parts_dir (e.g. out/<slug>/fe_parts) uploads every *.stl as an
assembled_<name>.stl sibling and lists it in _tree.json — the FE needs the
siblings in the tree to build part slides and color keys (fe_colors.py).
"""
import json
import os
import sys
import tempfile

env = {}
for line in open("/root/panda-secrets/.env"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip().strip('"')

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/root/panda-secrets/gcs-sa.json"
from google.cloud import storage

stl, purl = sys.argv[1], sys.argv[2]
parts_dir = sys.argv[3] if len(sys.argv) > 3 else ""
cdn_base = env["GCS_CDN_URL"].rstrip("/")
assert purl.startswith(cdn_base + "/"), (purl, cdn_base)
prefix = purl[len(cdn_base) + 1:].rstrip("/")

tree = [{"type": "directory", "name": ".", "contents": [
    {"type": "file", "name": "assembled.stl"},
]}]
uploads = [("assembled.stl", stl, "application/octet-stream")]
if parts_dir and os.path.isdir(parts_dir):
    for f in sorted(os.listdir(parts_dir)):
        if not f.lower().endswith(".stl"):
            continue
        name = f if f.startswith("assembled_") else "assembled_" + f
        tree[0]["contents"].append({"type": "file", "name": name})
        uploads.append((name, os.path.join(parts_dir, f), "application/octet-stream"))
params = os.path.join(os.path.dirname(stl), "params.py")
if os.path.exists(params):
    tree[0]["contents"].append({"type": "file", "name": "params.py"})
    uploads.append(("params.py", params, "text/x-python"))
with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
    json.dump(tree, f)
uploads.append(("_tree.json", f.name, "application/json"))

bkt = storage.Client().bucket(env["GCS_BUCKET"])
for name, path, ctype in uploads:
    bkt.blob(prefix + "/" + name).upload_from_filename(path, content_type=ctype)
    print("uploaded", prefix + "/" + name)
os.unlink(f.name)

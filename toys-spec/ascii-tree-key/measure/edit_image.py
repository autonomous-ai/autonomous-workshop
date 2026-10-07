"""Edit an image with OpenRouter: base image(s) as image_url parts + a text prompt.
Usage: edit_image.py --prompt-file P --out OUT --image IMG [--image IMG2] [--env .env]"""
import argparse, base64, json, mimetypes, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / ".claude/skills/brainstorm-trend/scripts")
import generate_image as g

ap = argparse.ArgumentParser()
ap.add_argument("--prompt-file", type=Path, required=True)
ap.add_argument("--out", type=Path, required=True)
ap.add_argument("--image", type=Path, action="append", required=True)
ap.add_argument("--env", type=Path, default=Path(".env"))
a = ap.parse_args()
parts = []
for p in a.image:
    mt = mimetypes.guess_type(str(p))[0] or "image/png"
    parts.append({"type": "image_url", "image_url": {"url": f"data:{mt};base64," + base64.b64encode(p.read_bytes()).decode()}})

def transport(url, headers, body):
    d = json.loads(body)
    text = d["messages"][0]["content"]
    d["messages"][0]["content"] = [{"type": "text", "text": text}] + parts
    return g._urllib_transport(url, headers, json.dumps(d).encode())

cfg = g.load_openrouter_config(a.env) if hasattr(g, "load_openrouter_config") else None
r = g.generate_image(a.prompt_file.read_text(), a.out, config=cfg, transport=transport)
print(r.path, r.width, r.height, r.size)

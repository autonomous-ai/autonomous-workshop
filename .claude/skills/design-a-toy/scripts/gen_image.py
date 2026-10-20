"""Generate or edit one image through OpenRouter.

usage: python3 gen_image.py PROMPT_FILE OUT_PNG [INPUT_IMAGE ...]

The input images are sent as references: an edit when IMAGE 1 is the image to change.
The model is $IMAGE_MODEL, else OPENROUTER_IMAGE_MODEL from the main checkout's .env.
That .env also holds OPENROUTER_API_KEY, which this script never prints.
- Image-only models (the id contains "gpt-image", e.g. openai/gpt-image-2.5-sunburst) are called
  through POST /images with input_references. Through chat/completions they answer 404.
  $IMAGE_ASPECT (e.g. 3:2 for a three-view turnaround) sets aspect_ratio.
- Multimodal models (openai/gpt-5.4-image-2, google/gemini-3-pro-image) go through
  chat/completions with modalities ["image", "text"].
On a transient failure (KeyError 'choices', HTTP 5xx) run it again.
"""
import base64, json, os, subprocess, sys, urllib.request

common = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
                        capture_output=True, text=True, check=True).stdout.strip()
env = {}
for line in open(os.path.join(os.path.dirname(common), ".env")):
    if "=" in line and not line.startswith("#"):
        k, v = line.strip().split("=", 1); env[k] = v.strip().strip('"')
base = (env.get("OPENROUTER_API_BASE") or "https://openrouter.ai/api/v1").rstrip("/")
model = os.environ.get("IMAGE_MODEL") or env.get("OPENROUTER_IMAGE_MODEL") or "openai/gpt-5.4-image-2"
prompt = open(sys.argv[1]).read()
refs = [{"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(open(p, "rb").read()).decode()}}
        for p in sys.argv[3:]]
hdr = {"Authorization": "Bearer " + env["OPENROUTER_API_KEY"], "Content-Type": "application/json"}

def post(path, body):
    req = urllib.request.Request(base + path, data=json.dumps(body).encode(), headers=hdr)
    return json.load(urllib.request.urlopen(req, timeout=600))

if "gpt-image" in model:
    body = {"model": model, "prompt": prompt, "n": 1}
    if os.environ.get("IMAGE_ASPECT"):
        body["aspect_ratio"] = os.environ["IMAGE_ASPECT"]
    if refs:
        body["input_references"] = refs
    r = post("/images", body)
    data = (r.get("data") or [{}])[0].get("b64_json")
else:
    r = post("/chat/completions", {"model": model, "modalities": ["image", "text"],
                                   "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}] + refs}]})
    imgs = r["choices"][0]["message"].get("images") or []
    data = imgs[0]["image_url"]["url"].split(",", 1)[1] if imgs else None
if not data:
    print("NO IMAGE", json.dumps(r)[:800]); sys.exit(1)
open(sys.argv[2], "wb").write(base64.b64decode(data))
print("ok", sys.argv[2], model)

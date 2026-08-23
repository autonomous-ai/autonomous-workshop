#!/usr/bin/env python3
"""Concept image for the DISCOVER winner — the quality bar the build aims at.

    ./concept_image.py <out_dir> [--telegram]

DISCOVER picks a product from text, and until now the first picture arrived
from DRAFT ~45min and $8.50 later. This renders the panel's own product
description in ~15s so the human can answer the only question that matters at
this point: is this the quality I want? The approved image then stays in the
output dir as the visual target DRAFT and BUILD chase.

Backend is the self-hosted media gateway (hunyuan t2i), which has its own key
and does not touch the OpenRouter budget.
"""
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

GATEWAY = "https://2x4090-9091.eternalai.org"
SECRETS = Path("/root/panda-secrets/media-gateway.env")
T2C_ENV = Path("/root/text2cad/.env")
UA = "curl/8.7.1"  # the gateway's CDN 1010s a default python-urllib UA
POLL_S, POLL_EVERY = 240, 10

STYLE = (
    "Premium studio product photograph, single object on a seamless warm-neutral "
    "backdrop, soft directional light, shallow depth of field, crisp focus on the "
    "mechanism. The object is a multi-part 3D-printed mechanical device: matte "
    "filament surfaces with fine layer lines, precise tolerances, parts that "
    "visibly move against each other. Industrial-design quality, the kind of "
    "object a design magazine would photograph. No text, no logo, no watermark, "
    "no hands, no clutter.")


def env(path: Path) -> dict:
    out = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, _, v = line.partition("=")
                out[k.strip()] = v.strip().strip('"')
    return out


def get(url: str, key: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Authorization": "Bearer " + key})
    return json.load(urllib.request.urlopen(req, timeout=30))


def build_prompt(text: str) -> str:
    """The panel already wrote the product description — that IS the brief."""
    def grab(pat):
        m = re.search(pat, text, re.M)
        return m.group(1).strip() if m else ""

    subject = grab(r"^PROMPT:\s*(.+)$")
    mech = grab(r"^Mechanism:\s*(.+?)\s*—")
    parts = grab(r"^Mechanism:.*?—\s*(\d+)")
    if not subject:
        raise SystemExit("no PROMPT: line in discover.md")
    bits = [subject]
    if mech:
        bits.append(f"The mechanism to show: {mech}")
    if parts:
        bits.append(f"It has {parts} separate printed parts, all visible.")
    return " ".join(bits) + "\n\n" + STYLE


def generate(prompt: str, out: Path, key: str) -> None:
    body = {"model": "hunyuan-image-3-t2i", "type": "text-to-image",
            "prompt": prompt, "image_size": "landscape_4_3", "num_images": 1,
            "output_format": "jpeg", "enable_safety_checker": True}
    req = urllib.request.Request(f"{GATEWAY}/media/generations",
                                 data=json.dumps(body).encode(),
                                 headers={"User-Agent": UA, "Content-Type": "application/json",
                                          "Authorization": "Bearer " + key})
    t0 = time.time()
    rid = json.load(urllib.request.urlopen(req, timeout=60))["request_id"]
    while time.time() - t0 < POLL_S:
        time.sleep(POLL_EVERY)
        r = get(f"{GATEWAY}/media/generations/{rid}", key)
        if r.get("status") == "completed":
            url = (r.get("result_files") or [{}])[0].get("file_url")
            if not url:
                raise SystemExit(f"completed with no file: {json.dumps(r)[:200]}")
            img = urllib.request.Request(url, headers={"User-Agent": UA})
            out.write_bytes(urllib.request.urlopen(img, timeout=120).read())
            print(f"concept: {out} ({out.stat().st_size // 1024}KB, "
                  f"{round(time.time()-t0)}s)")
            return
        if r.get("status") == "failed":
            raise SystemExit(f"gateway failed: {json.dumps(r)[:200]}")
    raise SystemExit(f"gateway still {r.get('status')} after {POLL_S}s — giving up")


def main() -> int:
    out_dir = Path(sys.argv[1])
    text = (out_dir / "discover.md").read_text(encoding="utf-8")
    prompt = build_prompt(text)
    print("--- prompt ---\n" + prompt + "\n--------------")
    img = out_dir / "concept.png"
    key = env(SECRETS).get("MEDIA_GATEWAY_API_KEY", "")
    if not key:
        raise SystemExit("no MEDIA_GATEWAY_API_KEY in panda-secrets/media-gateway.env")
    generate(prompt, img, key)

    if "--telegram" in sys.argv:
        e = env(T2C_ENV)
        tok, chat = e.get("TELEGRAM_BOT_TOKEN", ""), e.get("TELEGRAM_CHAT_DM", "")
        slug = re.search(r"^WINNER:\s*(\S+)", text, re.M)
        slug = slug.group(1) if slug else out_dir.name
        cap = f"{slug} — concept: đây là chất lượng BUILD sẽ nhắm tới"
        if tok and chat:
            os.system(f'curl -s "https://api.telegram.org/bot{tok}/sendPhoto" '
                      f'-F chat_id={chat} -F photo=@{img} '
                      f'-F caption="{cap}" > /dev/null')
            print("telegram: concept sent")
    return 0


if __name__ == "__main__":
    sys.exit(main())

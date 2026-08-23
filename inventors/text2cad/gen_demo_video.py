#!/usr/bin/env python3
"""Fire-and-forget demo video for a drafted design (MiniMax-H3 fl2va).

    ./gen_demo_video.py <slug>

Spawned DETACHED by text2cad right after the draft proposal goes out to
Telegram — the H3 gateway can cold-start for 35+ minutes, so the cycle must
NEVER await this. The script polls on its own, telegrams the finished video
(or a failure note) itself, and writes logs/video-<slug>.log.

Retry policy per /root/docs/minimax-h3-gateway.md §3: poll 5s; queued >40min
or progress stalled >10min while processing -> resubmit; 3 attempts total
(6s clip first, 4s fallbacks). Output out/<slug>/demo_draft.mp4, verified to
carry both avc1 (video) and mp4a (audio) atoms before sending.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
GATEWAY = "https://2x4090-9091.eternalai.org"
ADMINDASH = "http://localhost:8090"


def env_file(path) -> dict:
    d = {}
    p = Path(path)
    if not p.is_file():
        return d
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            d[k.strip()] = v.strip().strip('"')
    return d


def curl_json(args, timeout=60) -> dict:
    r = subprocess.run(["curl", "-s", *args], capture_output=True, text=True,
                       timeout=timeout)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {}


def main() -> int:
    slug = sys.argv[1]
    out_dir = HERE / "out" / slug
    env = env_file(HERE / ".env")
    tok = env.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat = env.get("TELEGRAM_CHAT_DM", "").strip()

    def tg_text(text):
        if tok and chat:
            subprocess.run(["curl", "-s",
                            f"https://api.telegram.org/bot{tok}/sendMessage",
                            "-d", f"chat_id={chat}",
                            "--data-urlencode", f"text={text}"],
                           capture_output=True, timeout=30)

    gw_key = env_file("/root/panda-secrets/media-gateway.env").get(
        "MEDIA_GATEWAY_API_KEY", "")
    admin = env_file("/root/panda-secrets/admindash.env").get("ADMIN_TOKEN", "")
    frame = next((p for p in (out_dir / "hero.png", out_dir / "concept.png")
                  if p.is_file()), None)
    if not (gw_key and admin and frame):
        print("video: missing gateway key / admin token / frame — skip")
        return 1

    up = curl_json(["-H", f"Authorization: Bearer {admin}",
                    "-F", f"file=@{frame}", f"{ADMINDASH}/api/uploads"], 120)
    img_url = up.get("url")
    if not img_url:
        tg_text(f"{slug}: demo video SKIPPED — frame upload to CDN failed")
        return 1

    run = {}
    if (out_dir / "run.json").is_file():
        run = json.loads((out_dir / "run.json").read_text(encoding="utf-8"))
    mech = (run.get("prompt") or slug.replace("-", " "))[:600]
    prompt = (
        "The 3D-printed product shown in the reference image at 0.00 seconds, "
        "demonstrated in operation on a warm neutral studio backdrop. "
        f"The product: {mech} "
        "Show its mechanism actually moving the way it is designed to work — "
        "cranks turning, gears meshing, moving parts visibly doing their job — "
        "in one slow, confident 30-degree orbit with a gentle push-in, shallow "
        "depth of field. Exact color fidelity to the reference image, matte "
        "3D-printed plastic with fine layer lines. No hands, no text, no logo. "
        "Soundscape: the real mechanical sounds of the moving parts, quiet "
        "room ambience. No music.")

    for attempt in range(3):
        dur = 6 if attempt == 0 else 4
        body = {"model": "minimax/minimax-h3-fl2va", "type": "image-to-video",
                "image_url": img_url, "prompt": prompt, "duration": dur,
                "aspect_ratio": "16:9", "resolution": "480p"}
        j = curl_json(["-X", "POST", f"{GATEWAY}/media/generations",
                       "-H", f"Authorization: Bearer {gw_key}",
                       "-H", "Content-Type: application/json",
                       "-d", json.dumps(body)])
        rid, st = j.get("request_id"), j.get("status")
        print(f"[submit#{attempt + 1} {dur}s] id={rid} status={st}", flush=True)
        if not rid or st == "failed":
            continue
        start = last_change = time.time()
        last_prog = None
        while True:
            time.sleep(5)
            j = curl_json([f"{GATEWAY}/media/generations/{rid}",
                           "-H", f"Authorization: Bearer {gw_key}"])
            st, prog = j.get("status"), j.get("progress")
            now = time.time()
            if prog != last_prog:
                last_prog, last_change = prog, now
                print(f"[{int(now - start)}s] {st} {prog}", flush=True)
            if st == "completed":
                url = j["result_files"][0]["file_url"]
                out = out_dir / "demo_draft.mp4"
                subprocess.run(["curl", "-s", "-o", str(out), url], timeout=300)
                data = out.read_bytes() if out.is_file() else b""
                if b"avc1" in data and b"mp4a" in data:
                    subprocess.run(
                        ["curl", "-s", "-F", f"chat_id={chat}",
                         "-F", f"video=@{out}",
                         "-F", f"caption=🎬 {slug} — auto demo: how it works "
                               "(from the draft hero). GO/NO commands are in "
                               "the proposal above.",
                         f"https://api.telegram.org/bot{tok}/sendVideo"],
                        capture_output=True, timeout=120)
                    print("video: sent", flush=True)
                    return 0
                print("video: mp4 missing streams, retrying", flush=True)
                break
            if st == "failed":
                print(f"video: job failed: {j}", flush=True)
                break
            if st == "queued" and now - start > 2400:
                print("video: queued >40min, resubmit", flush=True)
                break
            if st == "processing" and now - last_change > 600:
                print(f"video: stalled >10min at {prog}, resubmit", flush=True)
                break
    tg_text(f"{slug}: demo video FAILED after 3 attempts — gateway slow or "
            "dark; the proposal renders above still stand.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

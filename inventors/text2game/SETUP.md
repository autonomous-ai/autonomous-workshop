# Setting up text2game on a fresh machine

Goal: `git clone` + the owner's `.env` = the full flow runs. What the repo
cannot carry (secrets, a sibling toolchain, two CLIs that need a login) is
listed here once, and `./doctor.py` checks every line of it.

```bash
git clone https://github.com/nohope88/text2game.git && cd text2game
cp /path/to/owner.env .env          # section A of .env.example, filled in
./doctor.py                         # red rows = your to-do list, in order
./doctor.py --phase discover,1      # the rules half needs far less than the CAD half
```

## 1. What the owner hands you

| item | goes where | used by |
|---|---|---|
| `.env` (section A of `.env.example`: Telegram, `MEDIA_GATEWAY_KEY`, and for publish `ADMIN_TOKEN`, `PANDA_OWNER_ID`, `MONGODB_URI`, `GCS_*`) | `text2game/.env` | every phase reads it via `harness.load_env()` |
| `gcs-sa.json` (GCS service account) | `/root/panda-secrets/gcs-sa.json` — this exact path; text2cad's uploader hardcodes it | publish |
| a `claude` login (Claude Code subscription) and, unless you set `CODEX_JOBS=none`, a `codex` login (ChatGPT Pro) | `~/.claude/`, `~/.codex/` | every LLM phase |

Everything else below is public tooling or a sibling repo from the same org.

## 2. The rules half: DISCOVER + phase 1

```bash
npm i -g @anthropic-ai/claude-code && claude        # sign in once
pip install -r requirements.txt
./doctor.py --phase discover,1
./discover.py                                        # panel -> winner -> concept video -> Telegram
./text2game --slug <winner>                          # phase 1 -> checkpoint
```

Optional, and the doctor says so: the `second-brain` MCP server in
`~/.claude.json` (the proposers read the day's X/HN digests through it; without
it the panel reads the local wiki/google-trends digests only), the
`gamevault` checkout (`GAMEVAULT=…`, critic leads), a web dir for
`SHARED_REPORTS`. The concept video needs `MEDIA_GATEWAY_KEY`; without it the
panel still finishes (`CONCEPT_VIDEO=off` to silence the warning).

## 3. The CAD half: phase 2 + phase 3

text2game does not carry a CAD toolchain of its own. It drives **text2cad**,
a sibling checkout, through `TEXT2CAD_DIR` / `TEXT2CAD_PY`:

```bash
cd .. && git clone https://github.com/nohope88/text2cad.git && cd text2cad
curl -LsSf https://astral.sh/uv/install.sh | sh                  # uv
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python cadquery trimesh numpy manifold3d matplotlib pillow
mkdir -p ~/.claude/skills && ln -s "$PWD/skills/cadcode" ~/.claude/skills/cadcode
sudo apt install prusa-slicer nodejs ffmpeg                      # 3: slice, renders, video
cd ../text2game && echo "TEXT2CAD_DIR=$PWD/../text2cad" >> .env  # or edit the line
./doctor.py --phase 2,3
```

Phase 2 and 3 run on **codex** by default on the panda box (`CODEX_JOBS=phase23`
in the owner's `.env`): `npm i -g @openai/codex && codex login`. No ChatGPT
Pro? `CODEX_JOBS=none` runs them on claude — the build prompts then name the
cadcode skill, which is why the symlink above exists.

The slicer profile `profiles/petg.ini` ships in this repo; `SLICER_PROFILE`
points at another. Plate/bed sizes are dials in `.env`.

## 4. Publish (Panda Social DRAFT) — hand-run

`./publish.py <slug>` is deliberately the most box-bound step, because it
touches production data. On top of the CAD half it needs:

- `bin/importdesign` inside the text2cad checkout — a Go binary built from the
  private `panda-social-backend` repo (`go build -o ../text2cad/bin/importdesign
  ./cmd/importdesign`), and that backend checkout at `BACKEND_DIR`;
- a venv with `google-cloud-storage` at `GCS_PY` (default `/root/gcsvenv/bin/python`);
- `admindash` reachable at `ADMINDASH_URL` for thumbnails/product page;
- the secrets from section A and `gcs-sa.json` at its fixed path.

`./doctor.py --phase publish --probe` checks all of it, including that
admindash answers. publish.py only ever writes `status=draft`; flipping to
public stays a person's click in admindash.

## 5. Read this before your first paid run

- `./doctor.py --probe` once: it makes one tiny `claude -p` call and pings the
  gateways, so a dead login surfaces here and not 40 minutes into a panel.
- Phases skip when their artifact exists; `--force` reruns. `out/` and `logs/`
  are gitignored — a fresh clone starts with no designs, and that is fine:
  `catalog.json` and `evidence.jsonl` (committed) are the pipeline's memory.
- Costs on this box's config: a DISCOVER panel ≈ $14 / 30 min; phase 1 ≈
  $15–25 over 1–2 h; concept videos are free (self-hosted gateway).
- The gateway facts in `/root/docs/minimax-h3-gateway.md` (cold start 35+ min,
  no cancel) are panda-box notes; on another machine keep `CONCEPT_VIDEO=on`
  and accept that the first video of the day may take that long.

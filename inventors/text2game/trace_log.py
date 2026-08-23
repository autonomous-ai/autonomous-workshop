"""Every prompt in, every reply out, on disk.

text2cad keeps run.json (what a phase COST) and the CLI keeps its own session
transcripts, but nothing keeps the prompt a phase was actually given. That gap
is why "the reviser refused to fix it" arguments could not be settled: the
prompt was reconstructed from the source at the time of reading, not from the
source at the time of running. These files are the record.

    out/<slug>/trace/0003-build-p2.in.md    the exact prompt sent
    out/<slug>/trace/0003-build-p2.out.md   the exact reply returned
    out/<slug>/trace/index.jsonl            one row per call
"""
import json
import re
import time
from pathlib import Path

_SAFE = re.compile(r"[^a-z0-9._-]+")


def _slugify(name: str) -> str:
    return _SAFE.sub("-", name.lower()).strip("-") or "phase"


def write(out_dir: Path, seq: int, name: str, prompt: str, reply: str,
          entry: dict) -> None:
    d = out_dir / "trace"
    d.mkdir(parents=True, exist_ok=True)
    stem = f"{seq:04d}-{_slugify(name)}"
    (d / f"{stem}.in.md").write_text(prompt, encoding="utf-8")
    (d / f"{stem}.out.md").write_text(reply or "(no output)", encoding="utf-8")
    row = {"seq": seq, "phase": name, "stem": stem,
           "prompt_chars": len(prompt), "reply_chars": len(reply or ""),
           "provider": entry.get("provider", "claude"),
           "model": entry.get("model"), "wall_s": entry.get("wall_s"),
           "num_turns": entry.get("num_turns"), "subtype": entry.get("subtype"),
           "cost_usd": entry.get("cost_usd"), "is_error": entry.get("is_error"),
           "t": round(time.time(), 1)}
    with (d / "index.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def next_seq(out_dir: Path) -> int:
    idx = out_dir / "trace" / "index.jsonl"
    if not idx.exists():
        return 1
    n = 0
    for line in idx.read_text(encoding="utf-8").splitlines():
        if line.strip():
            n += 1
    return n + 1

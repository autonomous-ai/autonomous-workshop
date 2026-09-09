#!/usr/bin/env python3
"""So sánh nhiều run Workshop: token, chi phí, artifact, kết quả gate.

    python3 compare_runs.py <wish-id> [<wish-id> ...]
    python3 compare_runs.py --all          # mọi run có state

Chi phí lấy từ transcript của từng run, không lấy tổng của OpenRouter — nên
vẫn tách được khi nhiều run chạy song song trên cùng một key.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path

HOME = Path.home()
STATE = HOME / "Library/Application Support/Autonomous Workshop/state"
RUNS = HOME / "Library/Application Support/Autonomous Workshop/runs"
PROJECTS = HOME / ".claude/projects"

# $/1M: (input, output, cache_read, cache_write). Cache read/write suy từ giá
# input theo tỷ lệ chuẩn của Anthropic (0.1x đọc, 1.25x ghi) khi nhà cung cấp
# không công bố riêng.
PRICING = {
    "meta/muse-spark-1.3": (1.25, 4.25, 0.125, 1.5625),
    "moonshotai/kimi-k3": (3.00, 15.00, 0.30, 3.75),
    "claude-sonnet-5": (2.00, 10.00, 0.20, 2.50),
    "claude-opus-5": (5.00, 25.00, 0.50, 6.25),
    "claude-haiku-4-5-20251001": (1.00, 5.00, 0.10, 1.25),
}


def transcript(wish_id: str) -> Path | None:
    directory = PROJECTS / (
        "-Users-macmini-Library-Application-Support-Autonomous-Workshop-runs-"
        "%s-workspace" % wish_id
    )
    files = sorted(
        glob.glob(str(directory / "*.jsonl")), key=os.path.getmtime, reverse=True
    )
    return Path(files[0]) if files else None


def usage(path: Path) -> dict:
    """Sum per-model token usage across one session transcript."""

    per_model: dict[str, dict[str, int]] = {}
    messages = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        message = record.get("message")
        if not isinstance(message, dict):
            continue
        counts = message.get("usage")
        model = message.get("model")
        if not isinstance(counts, dict) or not model:
            continue
        messages += 1
        bucket = per_model.setdefault(
            model, {"in": 0, "out": 0, "cache_read": 0, "cache_write": 0}
        )
        bucket["in"] += counts.get("input_tokens") or 0
        bucket["out"] += counts.get("output_tokens") or 0
        bucket["cache_read"] += counts.get("cache_read_input_tokens") or 0
        bucket["cache_write"] += counts.get("cache_creation_input_tokens") or 0
    return {"messages": messages, "models": per_model}


def cost(per_model: dict) -> float:
    total = 0.0
    for model, b in per_model.items():
        rates = PRICING.get(model)
        if rates is None:
            continue
        p_in, p_out, p_cr, p_cw = rates
        total += (
            b["in"] * p_in
            + b["out"] * p_out
            + b["cache_read"] * p_cr
            + b["cache_write"] * p_cw
        ) / 1e6
    return total


def thickness_trail(path: Path) -> list[str]:
    """Every `thinnest N mm` the run measured, in order."""

    found = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        for match in re.finditer(r"thinnest ([0-9.]+) mm", line):
            found.append(match.group(1))
    return found


def describe(wish_id: str) -> None:
    state = STATE / wish_id
    workspace = RUNS / wish_id / "workspace"
    artifacts = workspace / "artifacts"

    gates = sorted(p.name for p in (state / "gates").glob("*.json")) if (
        state / "gates"
    ).is_dir() else []
    wish_text = ""
    wish_file = workspace / "WISH.json"
    if wish_file.is_file():
        try:
            wish_text = json.loads(wish_file.read_text())["objective"]
        except (KeyError, ValueError, OSError):
            pass

    stl = list(artifacts.rglob("*.stl"))
    manual = artifacts / "release/package/MANUAL.pdf"

    print("=" * 78)
    print("%s" % wish_id)
    print("  wish     : %s" % wish_text[:66])
    print("  gates    : %s" % (" ".join(g.replace(".json", "") for g in gates) or "—"))
    print("  artifact : %d file | STL %d | MANUAL.pdf %s"
          % (sum(1 for _ in artifacts.rglob("*") if _.is_file()),
             len(stl), "CÓ" if manual.is_file() else "chưa"))

    path = transcript(wish_id)
    if path is None:
        print("  (chưa có transcript)")
        return
    u = usage(path)
    print("  messages : %d" % u["messages"])
    for model, b in u["models"].items():
        print("    %-26s in=%-9d cr=%-10d cw=%-8d out=%d"
              % (model, b["in"], b["cache_read"], b["cache_write"], b["out"]))
    c = cost(u["models"])
    unpriced = [m for m in u["models"] if m not in PRICING]
    print("  ≈ chi phí: $%.2f%s"
          % (c, "  (chưa có giá: %s)" % ", ".join(unpriced) if unpriced else ""))
    trail = thickness_trail(path)
    if trail:
        print("  độ dày   : %d lần đo | %s" % (len(trail), " ".join(trail[-8:])))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wish_ids", nargs="*", metavar="WISH_ID")
    parser.add_argument("--all", action="store_true", help="mọi run có state")
    arguments = parser.parse_args()

    ids = arguments.wish_ids
    if arguments.all or not ids:
        ids = sorted(p.name for p in STATE.iterdir() if p.is_dir())
    for wish_id in ids:
        describe(wish_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())

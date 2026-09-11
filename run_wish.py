#!/usr/bin/env python3
"""Run Workshop through its current CLI.

python run_wish.py --dry-run
python run_wish.py --wish 'a minecraft sword' --agent claude --model sonnet --yes
python run_wish.py --resume <wish-id> --yes

New runs use CONFIG. Resume uses the runtime frozen by the host, not CONFIG.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shlex
import subprocess
import sys

CONFIG = {
    "wish": "a minecraft sword",
    "agent": "claude",
    "model": "sonnet",
    "workflow": "spark",
    "effort": "high",
    "max_tokens": None,  # New Codex runs default to 10M; resume keeps saved cap.
    "turn_minutes": None,  # None keeps the frozen boundary; "none" removes the clock.
}
REPOSITORY = Path(__file__).resolve().parent
# Isolated native executable installed for this Apple Silicon workstation.
# Use the native binary directly so sandbox helpers do not need the npm wrapper.
PINNED_CODEX_BINARY = (
    Path.home() / ".local/share/workshop/codex-0.153.4/node_modules/@openai/"
    "codex-darwin-arm64/vendor/aarch64-apple-darwin/bin/codex"
)
FACTORY_CREDENTIALS = (
    Path.home() / "Library/Application Support/Autonomous Workshop/credentials/factory.env"
)


class SetupError(RuntimeError):
    """Invalid runner configuration."""


def build_command(config: dict, resume_id: str | None) -> list[str]:
    if config.get("use_openrouter"):
        raise SetupError("CLI mới không có provider override; không hỗ trợ --openrouter.")
    project_python = REPOSITORY / ".venv/bin/python"
    prefix = [str(project_python) if project_python.is_file() else sys.executable, "-m", "cli"]
    limit = config.get("max_tokens")
    budget = []
    if limit is not None:
        if type(limit) is not int or not 1_000 <= limit <= 100_000_000:
            raise SetupError("max_tokens phải là số nguyên từ 1.000 đến 100.000.000.")
        budget = ["--max-tokens", str(limit)]
    turn = config.get("turn_minutes")
    boundary = []
    if turn is not None:
        if not (turn == "none" or (type(turn) is int and 1 <= turn <= 360)):
            raise SetupError("turn_minutes phải là số phút từ 1 đến 360, hoặc 'none'.")
        boundary = ["--turn-minutes", str(turn)]
    if resume_id:
        return [*prefix, "resume", resume_id, "--strict", *budget, *boundary]
    agent = config["agent"]
    if agent not in ("codex", "claude", "grok"):
        raise SetupError("agent phải là codex, claude hoặc grok.")
    if limit is not None and agent != "codex":
        raise SetupError("Budget token hiện chỉ được host thực thi cho Codex.")
    workflow = config["workflow"]
    if workflow not in ("spark", "forge", "quest"):
        raise SetupError("workflow phải là spark, forge hoặc quest.")
    command = [*prefix, "wish", config["wish"], "--strict", "--agent", agent,
               "--workflow", workflow, "--model", config["model"]]
    effort = config.get("effort")
    if effort is not None:
        if agent == "grok" or effort not in ("low", "medium", "high", "xhigh"):
            raise SetupError("effort chỉ hỗ trợ Codex/Claude: low, medium, high, xhigh.")
        command += ["--effort", effort]
    return [*command, *budget, *boundary]


def runtime_environment() -> dict[str, str]:
    environment = dict(os.environ)
    if not environment.get("WORKSHOP_CODEX_BIN") and PINNED_CODEX_BINARY.is_file():
        environment["WORKSHOP_CODEX_BIN"] = str(PINNED_CODEX_BINARY)
    return environment


def confirm_publication_risk() -> None:
    if not FACTORY_CREDENTIALS.is_file():
        return
    print("Có Factory credentials: host có thể publish khi Release đạt.")
    try:
        input("Enter để tiếp tục, Ctrl-C để dừng: ")
    except (EOFError, KeyboardInterrupt):
        raise SetupError("Đã hủy.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="in lệnh, không chạy")
    parser.add_argument("--resume", metavar="WISH_ID")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--wish")
    parser.add_argument("--agent", "--manager", dest="agent", choices=("codex", "claude", "grok"))
    parser.add_argument("--model")
    parser.add_argument("--workflow", choices=("spark", "forge", "quest"))
    parser.add_argument("--effort", "--reasoning-effort", dest="effort", choices=("low", "medium", "high", "xhigh"))
    parser.add_argument("--max-tokens", type=int, help="tổng token cap; resume không reset usage")
    parser.add_argument("--turn-minutes",
                        help="số phút cho mỗi native turn (1-360), hoặc 'none' để bỏ hẳn wall clock")
    gateway = parser.add_mutually_exclusive_group()
    gateway.add_argument("--openrouter", action="store_true", help="không được CLI mới hỗ trợ")
    gateway.add_argument("--no-openrouter", action="store_true", help="tương thích lệnh cũ; dùng native runtime")
    args = parser.parse_args()
    selection_keys = ("wish", "agent", "model", "workflow", "effort")
    if args.resume and any(getattr(args, key) is not None for key in selection_keys):
        parser.error("Resume dùng cấu hình đã đóng băng; không nhận wish/agent/model/workflow/effort mới.")
    config = dict(CONFIG)
    for key in selection_keys:
        value = getattr(args, key)
        if value is not None:
            config[key] = value
    # Never apply CONFIG's token override to an existing product implicitly.
    config["max_tokens"] = args.max_tokens if args.resume or args.max_tokens is not None else CONFIG.get("max_tokens")
    if args.turn_minutes is not None:
        raw = args.turn_minutes.strip().lower()
        config["turn_minutes"] = raw if raw == "none" else int(raw)
    if args.agent == "grok" and args.effort is None:
        config["effort"] = None
    config["use_openrouter"] = args.openrouter
    try:
        command = build_command(config, args.resume)
        environment = runtime_environment()
        if environment.get("WORKSHOP_CODEX_BIN"):
            print("WORKSHOP_CODEX_BIN=" + shlex.quote(environment["WORKSHOP_CODEX_BIN"]))
        print(shlex.join(command))
        if args.dry_run:
            return 0
        if not args.yes:
            confirm_publication_risk()
    except SetupError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return subprocess.run(command, cwd=str(REPOSITORY), env=environment).returncode


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Fail CI on secret-shaped tracked paths or high-confidence credentials.

Only file names and rule names are printed. Secret values never enter logs.
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SAFE_ENV_NAMES = frozenset((".env.example", ".env.sample", ".env.template"))
BAD_SUFFIXES = (".pem", ".key", ".p12", ".pfx")
CONTENT_RULES = {
    "private-key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github-token": re.compile(rb"gh[pousr]_[A-Za-z0-9]{20,}"),
    "anthropic-key": re.compile(rb"sk-ant-[A-Za-z0-9_-]{20,}"),
    "openai-key": re.compile(rb"sk-(?:proj-)?[A-Za-z0-9_-]{32,}"),
    "google-api-key": re.compile(rb"AIza[0-9A-Za-z_-]{30,}"),
    "telegram-token": re.compile(rb"(?<![A-Za-z0-9])[0-9]{7,12}:[A-Za-z0-9_-]{30,}"),
    "credentialed-mongodb-uri": re.compile(rb"mongodb(?:\+srv)?://[^\s:/]+:[^\s/@]+@"),
}


def repository_files():
    result = subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
        ],
        check=True,
        stdout=subprocess.PIPE,
    )
    return [Path(item.decode("utf-8")) for item in result.stdout.split(b"\0") if item]


def path_problem(path):
    name = path.name.lower()
    if name.startswith(".env") and name not in SAFE_ENV_NAMES:
        return "tracked-environment-file"
    if ".bak" in name:
        return "tracked-backup-file"
    if name.endswith(BAD_SUFFIXES):
        return "tracked-private-material"
    return None


def main():
    findings = []
    for relative in repository_files():
        rule = path_problem(relative)
        if rule:
            findings.append((relative, rule))
            continue
        absolute = ROOT / relative
        try:
            if absolute.stat().st_size > 5 * 1024 * 1024:
                continue
            content = absolute.read_bytes()
        except OSError:
            continue
        if b"\0" in content:
            continue
        for rule_name, pattern in CONTENT_RULES.items():
            if pattern.search(content):
                findings.append((relative, rule_name))
    for path, rule in findings:
        print("secret-scan: %s: %s" % (path.as_posix(), rule), file=sys.stderr)
    if findings:
        print("secret-scan: %d finding(s); values suppressed" % len(findings), file=sys.stderr)
        return 1
    print("secret-scan: clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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
CREDENTIAL_FILENAMES = frozenset(("panda-auth.json", "portal-auth.json"))
CONTENT_RULES = {
    "private-key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github-token": re.compile(rb"gh[pousr]_[A-Za-z0-9]{20,}"),
    "anthropic-key": re.compile(rb"sk-ant-[A-Za-z0-9_-]{20,}"),
    "openai-key": re.compile(rb"sk-(?:proj-)?[A-Za-z0-9_-]{32,}"),
    "google-api-key": re.compile(rb"AIza[0-9A-Za-z_-]{30,}"),
    "telegram-token": re.compile(rb"(?<![A-Za-z0-9])[0-9]{7,12}:[A-Za-z0-9_-]{30,}"),
    "credentialed-mongodb-uri": re.compile(rb"mongodb(?:\+srv)?://[^\s:/]+:[^\s/@]+@"),
}
SCAN_CHUNK_BYTES = 1024 * 1024
SCAN_OVERLAP_BYTES = 64 * 1024


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
    if name in CREDENTIAL_FILENAMES:
        return "tracked-credential-file"
    if name.startswith(".env") and name not in SAFE_ENV_NAMES:
        return "tracked-environment-file"
    if ".bak" in name:
        return "tracked-backup-file"
    if name.endswith(BAD_SUFFIXES):
        return "tracked-private-material"
    return None


def content_problems(path):
    """Return matching rules while streaming every file, including CAD/binary data.

    The overlap is deliberately much larger than the credentials recognized by
    these high-confidence rules, so a value split across read boundaries is not
    missed. Values are never returned or logged.
    """

    matches = set()
    carry = b""
    with path.open("rb") as handle:
        while True:
            block = handle.read(SCAN_CHUNK_BYTES)
            if not block:
                break
            window = carry + block
            for rule_name, pattern in CONTENT_RULES.items():
                if rule_name not in matches and pattern.search(window):
                    matches.add(rule_name)
            carry = window[-SCAN_OVERLAP_BYTES:]
    return sorted(matches)


def main():
    findings = []
    for relative in repository_files():
        rule = path_problem(relative)
        if rule:
            findings.append((relative, rule))
            continue
        absolute = ROOT / relative
        try:
            content_rules = content_problems(absolute)
        except OSError:
            continue
        for rule_name in content_rules:
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

"""Bounded structured-output calls through an installed authenticated Codex CLI."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Mapping, Optional

from .errors import ContractError
from .execution_env import codex_subprocess_environment


ALLOWED_WORKSHOP_MODELS = frozenset(("gpt-5.6-terra", "gpt-5.6-luna"))

# Structured Workshop calls are classifiers/generators, not coding-agent
# sessions.  Every required byte is serialized into the prompt, so none of
# these calls needs a shell, a browser, plugins, skills, or access to the
# product workspace.  Keep this list explicit and use ``--strict-config`` so
# an incompatible Codex CLI fails closed instead of silently restoring a tool.
_DISABLED_STRUCTURED_CALL_FEATURES = (
    "apps",
    "browser_use",
    "browser_use_external",
    "browser_use_full_cdp_access",
    "code_mode_host",
    "computer_use",
    "goals",
    "hooks",
    "image_generation",
    "in_app_browser",
    "multi_agent",
    "plugins",
    "remote_plugin",
    "shell_snapshot",
    "shell_tool",
    "skill_search",
    "tool_suggest",
    "unified_exec",
    "view_image",
    "workspace_dependencies",
)


def structured_call_hardening_args() -> tuple[str, ...]:
    """Return the fail-closed, tool-free Codex CLI boundary."""

    arguments = ["--ignore-user-config", "--strict-config"]
    for feature in _DISABLED_STRUCTURED_CALL_FEATURES:
        arguments.extend(("--disable", feature))
    arguments.extend(
        (
            "--config",
            "shell_environment_policy.inherit=none",
            "--config",
            "shell_environment_policy.ignore_default_excludes=false",
        )
    )
    return tuple(arguments)


class CodexInvocationError(RuntimeError):
    pass


class CodexStructuredRunner:
    def __init__(
        self,
        *,
        model: str,
        reasoning_effort: str,
        binary: Optional[str] = None,
        timeout_seconds: int = 600,
        runner: Any = subprocess.run,
        cli_version: Optional[str] = None,
    ) -> None:
        if model not in ALLOWED_WORKSHOP_MODELS:
            raise ContractError(
                "Workshop Codex model must be gpt-5.6-terra or gpt-5.6-luna"
            )
        if reasoning_effort not in ("low", "medium", "high", "xhigh"):
            raise ValueError("unsupported Codex reasoning effort")
        self.binary = binary or os.environ.get("WORKSHOP_CODEX_BIN") or shutil.which("codex")
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.timeout_seconds = timeout_seconds
        self._runner = runner
        self.cli_version = cli_version or self._read_cli_version()

    def _read_cli_version(self) -> str:
        if not self.binary:
            return "0.0.0"
        try:
            completed = self._runner(
                [self.binary, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
                env=codex_subprocess_environment(),
            )
        except (OSError, subprocess.SubprocessError):
            return "0.0.0"
        output = completed.stdout if isinstance(completed.stdout, str) else ""
        match = re.search(r"\d+(?:\.\d+){1,3}(?:[-+][A-Za-z0-9.-]+)?", output)
        return match.group(0) if match else "0.0.0"

    def invoke(
        self,
        *,
        prompt: str,
        schema: Mapping[str, Any],
        workspace: Optional[Path] = None,
    ) -> Mapping[str, Any]:
        if not self.binary:
            raise CodexInvocationError("Codex CLI is not installed or on PATH")
        try:
            with tempfile.TemporaryDirectory(prefix="workshop-codex-") as temporary:
                control_root = Path(temporary)
                schema_path = control_root / "output.schema.json"
                output_path = control_root / "output.json"
                schema_path.write_text(
                    json.dumps(schema, sort_keys=True), encoding="utf-8"
                )
                # The API keeps ``workspace`` for worker compatibility, but a
                # structured call never receives filesystem access to it.  Its
                # complete observation is already present in ``prompt``.
                del workspace
                cwd = control_root
                command = [
                    self.binary,
                    "exec",
                    "--ephemeral",
                    "--ignore-rules",
                    "--skip-git-repo-check",
                    *structured_call_hardening_args(),
                    "--sandbox",
                    "read-only",
                    "--color",
                    "never",
                    "--config",
                    'model_reasoning_effort="%s"' % self.reasoning_effort,
                    "--output-schema",
                    str(schema_path),
                    "--output-last-message",
                    str(output_path),
                    "-C",
                    str(cwd),
                    "--model",
                    self.model,
                    "-",
                ]
                completed = self._runner(
                    command,
                    input=prompt,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    check=False,
                    env=codex_subprocess_environment(),
                )
                if completed.returncode != 0 or not output_path.is_file():
                    raise CodexInvocationError("Codex did not complete the structured call")
                payload = json.loads(output_path.read_text(encoding="utf-8"))
        except CodexInvocationError:
            raise
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            raise CodexInvocationError("Codex returned no valid structured result") from exc
        if not isinstance(payload, dict):
            raise CodexInvocationError("Codex structured result must be an object")
        return payload


__all__ = [
    "ALLOWED_WORKSHOP_MODELS",
    "CodexInvocationError",
    "CodexStructuredRunner",
    "structured_call_hardening_args",
]

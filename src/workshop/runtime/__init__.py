"""Native session, receipt, and narrow durable effect contracts."""

from workshop.runtime.agent_assets import (
    inventor_agent_bytes,
    inventor_custom_agent_bytes,
)
from workshop.runtime.claude import (
    MINIMUM_CLAUDE_NATIVE_RUNTIME_VERSION,
    ClaudeInvocationError,
    ClaudeNativeSessionBinding,
    ClaudeNativeSessionLauncher,
    ClaudeNativeSessionOutcome,
    claude_supports_native_workshop,
)
from workshop.runtime.contracts import Receipt
from workshop.runtime.codex import (
    CODEX_PERMISSION_PROFILE,
    MINIMUM_CODEX_NATIVE_RUNTIME_VERSION,
    CodexInvocationError,
    CodexNativeSessionBinding,
    CodexNativeSessionLauncher,
    CodexNativeSessionOutcome,
    codex_supports_native_workshop,
)
from workshop.runtime.effects import EffectIntent, EffectLedger
from workshop.runtime.managers import (
    DEFAULT_MANAGER_ID,
    SUPPORTED_MANAGER_IDS,
    NativeManagerInvocationError,
    NativeSessionLauncher,
    manager_launcher,
    manager_spec,
)
from workshop.runtime.credentials import (
    factory_credential_environment,
    factory_credential_file,
)

__all__ = [
    "CodexInvocationError",
    "ClaudeInvocationError",
    "CODEX_PERMISSION_PROFILE",
    "MINIMUM_CODEX_NATIVE_RUNTIME_VERSION",
    "MINIMUM_CLAUDE_NATIVE_RUNTIME_VERSION",
    "DEFAULT_MANAGER_ID",
    "SUPPORTED_MANAGER_IDS",
    "NativeManagerInvocationError",
    "NativeSessionLauncher",
    "ClaudeNativeSessionBinding",
    "ClaudeNativeSessionLauncher",
    "ClaudeNativeSessionOutcome",
    "CodexNativeSessionBinding",
    "CodexNativeSessionLauncher",
    "CodexNativeSessionOutcome",
    "EffectIntent",
    "EffectLedger",
    "Receipt",
    "codex_supports_native_workshop",
    "claude_supports_native_workshop",
    "factory_credential_environment",
    "factory_credential_file",
    "inventor_agent_bytes",
    "inventor_custom_agent_bytes",
    "manager_launcher",
    "manager_spec",
]

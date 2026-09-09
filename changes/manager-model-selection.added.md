- Add `--model`, `--model-provider`, and `--model-provider-base-url` to
  `workshop wish`, `workshop start`, and `workshop resume` so one run can
  select the Manager CLI's model. The selection is launch-time rather than
  frozen into the checkpoint, so the same run may be resumed against another
  model to compare two models over identical durable state.
- Replace the fixed Codex and Grok model lists with shared argv-safe shape
  validation in `workshop.runtime.managers.manager_model`; the selected Manager
  CLI now owns model availability. `ALLOWED_WORKSHOP_MODELS` remains exported as
  the documented default set and is no longer a gate.
- Pass `--model` to Claude Code, which previously received no model argument.
- Allow an explicitly selected model provider with a validated `https` (or
  loopback `http`) base URL for the two Managers that can honour one: Codex
  through `-c model_provider=<id>`, and Claude Code through `ANTHROPIC_BASE_URL`
  with `ANTHROPIC_AUTH_TOKEN` set from `OPENROUTER_API_KEY` and
  `ANTHROPIC_API_KEY` emptied so a stale vendor key cannot silently serve the
  run. Grok Build rejects the option rather than ignoring it, because a
  silently dropped gateway would let a run report one endpoint while another
  served it.
- Forward `OPENROUTER_API_KEY` to Codex, and `ANTHROPIC_API_KEY` /
  `ANTHROPIC_AUTH_TOKEN` to Claude Code, through their existing subprocess
  allowlists. Factory credentials remain excluded from every Manager
  subprocess.

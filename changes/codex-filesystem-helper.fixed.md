- Let native Codex file tools such as `apply_patch` and `view_image` re-execute
  their built-in sandboxed filesystem helper through an identity-bound,
  read-only grant to the exact launched Codex binary without exposing Codex
  home, network access, or any writable path outside the product root.

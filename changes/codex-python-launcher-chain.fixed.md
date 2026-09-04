- Let sandboxed native sessions actually start the Workshop Python. The Codex
  read-only runtime grant now trusts every real directory on the launcher's
  symlink chain (Homebrew's `opt/<formula>` link and its keg `bin`, pyenv or
  uv launchers behind a link) and, for macOS framework builds, the framework
  version root that holds the `Python` shared library. Before this, the
  Daydream and stage finalizers and CAD tools failed with `Operation not
  permitted` or a dyld load error on such hosts. Hosts whose launcher chain
  adds nothing keep their exact policy identity; others resume older
  checkpoints through the bound predecessor policy.

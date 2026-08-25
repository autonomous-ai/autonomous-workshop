# Contributors

Owns Taste, inventor manifests, discovery, contribution checks, scaffolding,
and the installed snapshot of runnable inventor profiles.

Public API: `workshop.contributors`.

Contributor policy, identity validation, Taste loading, and scaffolding are
available from that package boundary. Contributors never imports Match or the
Workflow engine; applications ask Match to route only after an identity is
published.

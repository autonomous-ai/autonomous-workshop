- A design vault that is up but useless no longer ends a run: a 200 without a
  JSON object (a proxy's maintenance page) counts as the vault being away, an
  export the host cannot seal bypasses the checkpoint like an outage, and a
  write-back the vault refuses with a 400 is set aside under host state as
  `vault/pending/<name>.rejected` instead of aborting after a durable gate.

- Give every Inventor its own shop account. `workshop start <inventor-id>`
  now checks for that account before it dreams anything, prompts once for the
  username and password, and stores them in
  `$WORKSHOP_HOME/credentials/inventors/<id>.env` (0600 inside a 0700
  directory, never inside a run workspace and never given to an agent).
  Release resolves the publishing pair for the run's selected Inventor and
  falls back to the host-wide file, so existing hosts keep publishing.
- `workshop login <inventor-id>` stores that account: it prompts in a
  terminal and reads the password from stdin when one is piped, so a password
  never reaches shell history or the process table.
- `workshop create inventor` prints the sign-up link and the next command.
  `WORKSHOP_SHOP_SIGNUP_URL` overrides the link.

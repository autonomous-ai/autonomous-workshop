- Give every Inventor its own shop account. The first time you create or start
  an Inventor, Workshop opens
  `https://www.autonomous.ai/toys/inventor/login` in your browser. Choose an
  Autonomous account and approve **Connect Inventor**; Workshop then continues
  in the terminal.
- Store the generated publishing credential and canonical Inventor id in
  `$WORKSHOP_HOME/credentials/inventors/<id>.env` (0600 inside a 0700
  directory). The browser redirects a short-lived authorization code to the
  local callback; Workshop exchanges it directly with the API using PKCE. The
  publishing credential never enters browser JavaScript, a URL, a run
  workspace, or a coding-agent process.
- `workshop login <inventor-id>` repeats the browser flow to choose a different
  account. Existing host-wide Factory credentials remain supported.

- `tools/publish_direct.py --live` waits up to 2 minutes for Factory's shop
  listing after publishing, so a normal direct publication no longer ends
  with exit 3 and a reconcile run. It only re-reads a publication whose
  ledger intent is `unknown` and never repeats the publish request. A
  refused publication is not retried.

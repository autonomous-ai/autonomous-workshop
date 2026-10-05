- Every `make_round` round now renders nine views, including side and
  tilted three-quarter views, plus one labelled `sheet.png`; the packet binds
  the sheet with front, top and iso. Assembly visual feedback and every
  Component Review record `matches_plan` and `matches_reference` separately,
  and a pass or an agreeing review needs both. `make_round --preview-assembly` renders the rough whole
  once before component loops; it is never a round or a pass (ADR 0087).
- `render_review` now moves the vendored `cadgen` to the front of the import
  path even when an editable install already lists it, so an older `cadgen`
  on `PYTHONPATH` can no longer be imported first.

- `make_round` re-searches a +/-30 degree pose window when the replayed
  camera scores under the likeness floor and keeps the better score, marked
  `(re-searched)`; replay alone scored a moved neck at 0.49 where a fresh
  search found 0.75. See ADR 0059.

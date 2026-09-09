Give the isolated CAD gate a rejection budget. It was the most expensive gate
in the run and the only one with no bound: its record was overwritten in place,
so a Make or Playtest that could not satisfy it resubmitted until a token cap
ended the invocation. Each distinct isolated verification now advances a
counter, so resubmitting unchanged geometry costs the budget, while
reprocessing one verification after a crash does not. At eight consecutive
rejections the stage records a truthful failure naming the last failure code
instead of attempting again. Records written before the counter existed still
read, and count as the first rejection.

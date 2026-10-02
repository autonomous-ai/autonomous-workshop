- Spark Make: a Component's passing round must now be reviewed before its
  geometry may change, and a Shape Round is only the first change after a
  disagreeing review, so the five repairs are spent on the reviewer's
  feedback (ADR 0081). An agreed or accepted Component stays locked unless a
  Shared Helper it imports changes or an assembly round needs it changed; a
  rerun that rebuilds the reviewed geometry keeps its review. Editing a shared
  file no longer stales Components that do not import it, and a round that
  fails its checks is no longer rendered.

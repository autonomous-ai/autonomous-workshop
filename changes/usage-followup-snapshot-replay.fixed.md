- Accept an exact replay of the preceding Codex task's cumulative and
  last-request token counters at a follow-up boundary without charging it
  again. Keep the boundary pending until fresh usage proves continuation or
  reset. Changed counters or models still fail closed; `total == last` keeps
  its reset meaning. Offline replay recovered the affected run's existing
  9,425,297-token observation without changing run state or resuming work.

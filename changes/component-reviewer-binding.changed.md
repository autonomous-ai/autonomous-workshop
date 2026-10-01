- Spark Make on Claude Code: every Component Review must now come from that
  Component's one Component Reviewer. The review names the reviewer's native
  agent id, the first review binds it, and the host refuses Make output whose
  review names an agent that was not started as the Component Reviewer or
  never read the packet it judged (issue #77). The reviewer knows the print
  stance and the printing limits, so it asks only for printable detail; the
  Manager sends it a fixed request and the worker reads the recorded review
  itself.

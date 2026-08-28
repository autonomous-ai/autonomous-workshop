- Reject literal quote-wrapped Factory credential values and make `workshop
  doctor` verify one complete host-owned service-account pair without exposing
  credential values. One legacy scoped Alice-style username is normalized only
  as a migration alias; ambiguous multi-account configuration is rejected.

Make print preflight now checks unsupported overhangs before visual review,
using the same default profile as final verification. Previously a part could
pass early mesh and thickness checks, consume a review round, and then fail
final verification solely because its print orientation needs supports.
The bound preflight must cover every printable at the standard profile.

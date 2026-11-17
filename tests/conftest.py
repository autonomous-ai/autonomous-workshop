"""Suite-wide test isolation.

The timing ledger (ADR 0106) appends a row for every timed tool run. The
suite runs those tools many times, so it writes to a throwaway ledger, never
the owner's ``$WORKSHOP_HOME/timing/ledger.jsonl``. A test that checks the
ledger sets ``WORKSHOP_TIMING_LEDGER`` itself.
"""

import os
import tempfile

os.environ["WORKSHOP_TIMING_LEDGER"] = os.path.join(
    tempfile.mkdtemp(prefix="workshop-test-timing-"), "ledger.jsonl")

# End-to-end acceptance

This directory owns acceptance checks that cross every Workshop component.

The committed suite uses deterministic local providers and must be safe in CI.
Production acceptance additionally runs the installed wheel from an unrelated
working directory, starts with `workshop wish`, verifies the durable event and
artifact chains, and confirms the authenticated Factory page. Production
credentials and run receipts belong only in ignored local runtime storage.

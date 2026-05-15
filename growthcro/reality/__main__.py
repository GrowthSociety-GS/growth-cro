"""Package entrypoint — defers to the poller CLI (Task 011).

`python3 -m growthcro.reality --client weglot` is equivalent to
`python3 -m growthcro.reality.poller --client weglot`. The worker dispatcher
calls the latter explicitly, but this entrypoint exists for parity with
`growthcro.geo` and the canonical `-m <package>` convention.
"""
from __future__ import annotations

import sys

from growthcro.reality.poller import main

if __name__ == "__main__":
    sys.exit(main())

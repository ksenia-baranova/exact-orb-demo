"""Independent, deterministic data for correlation and lifecycle logging tests."""

from datetime import datetime, timezone
from uuid import UUID


STARTED_AT = datetime(2026, 9, 16, tzinfo=timezone.utc)
RUN_ID = UUID(int=1, version=4)
RUN_ID_B = UUID(int=2, version=4)
FORBIDDEN_PAYLOAD = "synthetic payload that must not be logged"

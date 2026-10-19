import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable

from app.core.config import settings


class SlidingWindowLimiter:
    """In-memory limiter. Per-process: fine for one backend container, not for horizontal scale."""

    def __init__(
        self, limit: int, window_seconds: float, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self._limit = limit
        self._window = window_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = self._clock()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] >= self._window:
                hits.popleft()
            if len(hits) >= self._limit:
                return False
            hits.append(now)
            return True


# Connection tests make the server open outbound network connections, so they are rate limited.
connection_test_limiter = SlidingWindowLimiter(settings.connection_test_rate_per_minute, 60)
"""Basic per-client sliding-window rate limiter.

This is process-local: it protects a single instance from casual abuse. Running several
instances in production requires a shared limiter (API gateway, Redis, Cloudflare...).
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from app.core.errors import RateLimitedError


class SlidingWindowRateLimiter:
    def __init__(self, max_requests: int, window_seconds: float = 60.0, clock=time.monotonic):
        self._max = max_requests
        self._window = window_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> None:
        now = self._clock()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] >= self._window:
                hits.popleft()
            if len(hits) >= self._max:
                retry_after = int(self._window - (now - hits[0])) + 1
                raise RateLimitedError(
                    "Too many identification requests. Please wait and try again.",
                    details={"retry_after_seconds": retry_after},
                )
            hits.append(now)

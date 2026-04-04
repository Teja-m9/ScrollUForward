"""
Simple async circuit breaker for inter-service HTTP calls.
States: CLOSED (normal) → OPEN (failing) → HALF-OPEN (testing recovery)
"""
import time, asyncio, logging
from enum import Enum
from typing import Callable, Any

log = logging.getLogger("circuit_breaker")


class State(Enum):
    CLOSED    = "closed"
    OPEN      = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        success_threshold: int = 2,
    ):
        self.name              = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout  = recovery_timeout
        self.success_threshold = success_threshold
        self._state            = State.CLOSED
        self._failures         = 0
        self._successes        = 0
        self._last_failure_time: float = 0.0

    @property
    def state(self) -> State:
        if self._state == State.OPEN:
            if time.monotonic() - self._last_failure_time >= self.recovery_timeout:
                self._state    = State.HALF_OPEN
                self._successes = 0
                log.info(f"[CB:{self.name}] OPEN → HALF_OPEN")
        return self._state

    def _on_success(self):
        if self.state == State.HALF_OPEN:
            self._successes += 1
            if self._successes >= self.success_threshold:
                self._state    = State.CLOSED
                self._failures = 0
                log.info(f"[CB:{self.name}] HALF_OPEN → CLOSED (recovered)")
        else:
            self._failures = 0

    def _on_failure(self):
        self._failures += 1
        self._last_failure_time = time.monotonic()
        if self._failures >= self.failure_threshold or self.state == State.HALF_OPEN:
            self._state = State.OPEN
            log.warning(f"[CB:{self.name}] CLOSED → OPEN ({self._failures} failures)")

    async def call(self, func: Callable, *args, fallback: Any = None, **kwargs):
        if self.state == State.OPEN:
            log.warning(f"[CB:{self.name}] Circuit OPEN — returning fallback")
            return fallback
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            log.error(f"[CB:{self.name}] Call failed: {e}")
            if fallback is not None:
                return fallback
            raise


# ── Pre-built breakers for each service ──────────────────────────────────────
breakers: dict[str, CircuitBreaker] = {
    "auth":       CircuitBreaker("auth"),
    "content":    CircuitBreaker("content"),
    "discussion": CircuitBreaker("discussion"),
    "user":       CircuitBreaker("user"),
    "chat":       CircuitBreaker("chat"),
    "ai_worker":  CircuitBreaker("ai_worker"),
}

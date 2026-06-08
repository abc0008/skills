"""
_core.py — foundation utilities shared by every script: typed exceptions,
structured logging, and a retry decorator for transient API failures.

================================================================================
AI AGENT ORIENTATION
================================================================================
Import this first. It deliberately has NO databricks dependency so it can be
unit-tested in isolation and imported safely anywhere. Everything here is pure
Python stdlib.

Three things live here:
  1. Typed exceptions  -> so callers can distinguish "your setup is wrong"
     (ConfigError) from "the API hiccuped" (TransientError) from "the API said
     no and will keep saying no" (PermanentError). Exit codes map to these.
  2. get_logger()      -> structured, level-controlled logging. Use this instead
     of print() in new code. Honors LOG_LEVEL env (DEBUG/INFO/WARNING/ERROR).
  3. @retry            -> exponential backoff w/ jitter for TransientError and a
     configurable set of exception types. Used to wrap flaky network calls.
================================================================================
"""

from __future__ import annotations

import functools
import logging
import os
import random
import sys
import time
from typing import Callable, Type, TypeVar


# ------------------------------------------------------------------------------
# Typed exceptions. Exit-code mapping lives in each script's main(), but the
# semantics are defined here so they're consistent everywhere.
# ------------------------------------------------------------------------------
class DriftDefenseError(Exception):
    """Base for all errors this toolkit raises intentionally."""


class ConfigError(DriftDefenseError):
    """The repo/config/environment is set up wrong. Not retryable. The fix is a
    human editing config.yaml, env vars, or file layout. Maps to exit code 2."""


class TransientError(DriftDefenseError):
    """A probably-temporary failure (network blip, 429 rate limit, 503). Safe to
    retry. If it survives all retries it is escalated by the caller."""


class PermanentError(DriftDefenseError):
    """The API answered and the answer is a hard no (404 space not found, 403
    permission denied, malformed request). Retrying will not help."""


# ------------------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------------------
def get_logger(name: str) -> logging.Logger:
    """Return a configured logger. Level from LOG_LEVEL env (default INFO).
    Format is compact and CI-friendly (no timestamps by default since CI adds
    its own; set LOG_TIMESTAMPS=1 to include them)."""
    logger = logging.getLogger(name)
    if logger.handlers:  # already configured (idempotent across imports)
        return logger

    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    handler = logging.StreamHandler(sys.stdout)
    if os.environ.get("LOG_TIMESTAMPS") == "1":
        fmt = "%(asctime)s %(levelname)-7s %(name)s | %(message)s"
    else:
        fmt = "%(levelname)-7s %(name)s | %(message)s"
    handler.setFormatter(logging.Formatter(fmt))
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, level, logging.INFO))
    logger.propagate = False
    return logger


_log = get_logger("drift._core")

T = TypeVar("T")


# ------------------------------------------------------------------------------
# Retry with exponential backoff + jitter
# ------------------------------------------------------------------------------
def retry(
    attempts: int = 4,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retry_on: tuple[Type[BaseException], ...] = (TransientError,),
    jitter: float = 0.3,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator: retry a function on transient failures with exponential
    backoff and jitter.

    attempts  : total tries (not just retries). 4 -> 1 try + 3 retries.
    base_delay: seconds before the first retry; doubles each time.
    max_delay : cap on any single sleep.
    retry_on  : exception types that trigger a retry. Anything else propagates
                immediately (we do NOT retry PermanentError or ConfigError).
    jitter    : +/- fraction randomization to avoid thundering-herd retries.

    Designed to be testable: inject a fake clock by monkeypatching time.sleep,
    and a flaky function, to assert it retries the right number of times. The
    test suite does exactly this.
    """
    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> T:
            delay = base_delay
            last_exc: BaseException | None = None
            for attempt in range(1, attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except retry_on as e:  # type: ignore[misc]
                    last_exc = e
                    if attempt == attempts:
                        _log.error("%s failed after %d attempts: %s",
                                   fn.__name__, attempts, e)
                        raise
                    sleep_for = min(delay, max_delay)
                    sleep_for *= 1 + random.uniform(-jitter, jitter)
                    sleep_for = max(0.0, sleep_for)
                    _log.warning("%s attempt %d/%d failed (%s); retrying in %.1fs",
                                 fn.__name__, attempt, attempts, e, sleep_for)
                    time.sleep(sleep_for)
                    delay *= 2
            # Unreachable, but satisfies type-checkers.
            assert last_exc is not None
            raise last_exc
        return wrapper
    return decorator


def classify_http_error(status_code: int, message: str = "") -> DriftDefenseError:
    """Map an HTTP status to the right typed exception so retry logic and exit
    codes behave correctly. Used by the REST fallback and SDK error adapters."""
    if status_code in (429, 500, 502, 503, 504):
        return TransientError(f"HTTP {status_code} (transient): {message}")
    if status_code in (400, 401, 403, 404, 409, 422):
        return PermanentError(f"HTTP {status_code} (permanent): {message}")
    # Unknown 4xx -> permanent; unknown 5xx -> transient.
    if 500 <= status_code < 600:
        return TransientError(f"HTTP {status_code}: {message}")
    return PermanentError(f"HTTP {status_code}: {message}")

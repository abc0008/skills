"""Tests for _core: retry behavior and HTTP error classification."""
from __future__ import annotations

import pytest

import _core
from _core import (ConfigError, PermanentError, TransientError,
                   classify_http_error, retry)


def test_retry_succeeds_after_transient(monkeypatch):
    sleeps = []
    monkeypatch.setattr(_core.time, "sleep", lambda s: sleeps.append(s))
    calls = {"n": 0}

    @retry(attempts=4, base_delay=1.0, jitter=0.0)
    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise TransientError("blip")
        return "ok"

    assert flaky() == "ok"
    assert calls["n"] == 3
    assert sleeps == [1.0, 2.0]  # exponential backoff, no jitter


def test_retry_exhausts_and_raises(monkeypatch):
    monkeypatch.setattr(_core.time, "sleep", lambda s: None)

    @retry(attempts=3, base_delay=0.1, jitter=0.0)
    def always_fail():
        raise TransientError("nope")

    with pytest.raises(TransientError):
        always_fail()


def test_retry_does_not_retry_permanent(monkeypatch):
    calls = {"n": 0}
    monkeypatch.setattr(_core.time, "sleep", lambda s: None)

    @retry(attempts=5)
    def perm():
        calls["n"] += 1
        raise PermanentError("404")

    with pytest.raises(PermanentError):
        perm()
    assert calls["n"] == 1  # never retried


@pytest.mark.parametrize("code,expected", [
    (429, TransientError), (500, TransientError), (503, TransientError),
    (504, TransientError), (400, PermanentError), (401, PermanentError),
    (403, PermanentError), (404, PermanentError), (409, PermanentError),
    (422, PermanentError), (418, PermanentError), (599, TransientError),
])
def test_classify_http_error(code, expected):
    assert isinstance(classify_http_error(code), expected)

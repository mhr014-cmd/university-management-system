"""
Unit tests: app.middleware.rate_limit.enforce_login_rate_limit (Milestone 11).

Verifies the fixed-window, per-client-IP login rate limit in isolation,
without a database or live server.
"""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.middleware import rate_limit as rate_limit_module
from app.middleware.rate_limit import enforce_login_rate_limit


def make_request(ip: str = "127.0.0.1"):
    request = MagicMock()
    request.client.host = ip
    return request


@pytest.fixture(autouse=True)
def reset_attempts():
    rate_limit_module._attempts.clear()
    yield
    rate_limit_module._attempts.clear()


def test_allows_up_to_the_configured_max_attempts():
    request = make_request()
    for _ in range(rate_limit_module._MAX_ATTEMPTS):
        enforce_login_rate_limit(request)  # should not raise


def test_rejects_the_attempt_beyond_the_max():
    request = make_request()
    for _ in range(rate_limit_module._MAX_ATTEMPTS):
        enforce_login_rate_limit(request)

    with pytest.raises(HTTPException) as exc:
        enforce_login_rate_limit(request)
    assert exc.value.status_code == 429


def test_different_clients_are_tracked_independently():
    request_a = make_request("10.0.0.1")
    request_b = make_request("10.0.0.2")

    for _ in range(rate_limit_module._MAX_ATTEMPTS):
        enforce_login_rate_limit(request_a)

    enforce_login_rate_limit(request_b)  # different IP, should not raise


def test_window_expiry_allows_new_attempts(monkeypatch):
    request = make_request()
    current_time = [1000.0]
    monkeypatch.setattr(rate_limit_module.time, "monotonic", lambda: current_time[0])

    for _ in range(rate_limit_module._MAX_ATTEMPTS):
        enforce_login_rate_limit(request)

    current_time[0] += rate_limit_module._WINDOW_SECONDS + 1
    enforce_login_rate_limit(request)  # old attempts have expired, should not raise

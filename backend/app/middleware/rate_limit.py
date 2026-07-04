"""
Rate limiting: POST /auth/login (Milestone 11 — see docs/System_Architecture.md
§11 and docs/Requirement_Analysis.md §14 item 13, a gap the proposal never
specifies a policy for).

Reasonable default chosen and documented here, per CLAUDE.md's own guidance
for this exact gap: 5 attempts per 60 seconds, keyed by client IP, fixed
window. Not distributed — state is held in this process's memory only, so
it does not coordinate across multiple worker processes/instances (see
PROJECT_PROGRESS.md's Milestone 11 Known Issues). Acceptable for this
project's documented single-instance deployment target
(System_Architecture.md §8); a production deployment that scales the API
tier horizontally would need a shared store (e.g. Redis) instead.
"""

import time

from fastapi import HTTPException, Request, status

_WINDOW_SECONDS = 60
_MAX_ATTEMPTS = 5

_attempts: dict[str, list[float]] = {}


def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def enforce_login_rate_limit(request: Request) -> None:
    now = time.monotonic()
    key = _client_key(request)
    window_start = now - _WINDOW_SECONDS

    recent = [t for t in _attempts.get(key, []) if t > window_start]
    if len(recent) >= _MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )

    recent.append(now)
    _attempts[key] = recent

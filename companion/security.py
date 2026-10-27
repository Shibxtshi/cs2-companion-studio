"""Small, dependency-free security helpers for the V1P LAN-only application."""
from __future__ import annotations

import json
import math
import secrets
from collections import deque
from urllib.parse import urlsplit


def same_origin(origin: str | None, host: str | None, *, secure: bool = False) -> bool:
    """Reject cross-site browser WebSockets; a same-origin page may connect.

    Never rely on this instead of the PIN. Non-browser WS clients must set
    Origin explicitly, which also makes test behavior predictable.
    """
    if not origin or not host or origin == 'null':
        return False
    try:
        parsed = urlsplit(origin)
    except ValueError:
        return False
    return parsed.scheme == ('https' if secure else 'http') and parsed.netloc.lower() == host.lower() and not parsed.path.strip('/') and not parsed.query and not parsed.fragment


class LoginLimiter:
    """Per-peer failed-login throttling without persistent personal logs."""
    def __init__(self, limit: int = 5, window: int = 300, lockout: int = 900):
        self.limit = limit
        self.window = window
        self.lockout = lockout
        self._tries: dict[str, deque[float]] = {}
        self._locked: dict[str, float] = {}

    def _prune(self, now: float) -> None:
        for ip in tuple(self._tries):
            q = self._tries[ip]
            while q and q[0] <= now - self.window:
                q.popleft()
            if not q:
                self._tries.pop(ip, None)
        for ip in tuple(self._locked):
            if self._locked[ip] <= now:
                self._locked.pop(ip, None)
        # Bound memory even if a misconfigured reverse proxy floods us.
        if len(self._tries) > 512:
            self._tries.clear()

    def allowed(self, ip: str, now: float) -> bool:
        self._prune(now)
        return now >= self._locked.get(ip, 0)

    def fail(self, ip: str, now: float) -> None:
        self._prune(now)
        q = self._tries.setdefault(ip, deque())
        q.append(now)
        if len(q) >= self.limit:
            self._locked[ip] = now + self.lockout
            self._tries.pop(ip, None)

    def success(self, ip: str) -> None:
        self._tries.pop(ip, None)
        self._locked.pop(ip, None)


def credential_matches(provided, expected):
    """Reject malformed/non-ASCII inputs before constant-time comparison."""
    return (isinstance(provided, str) and len(provided) <= 256 and provided.isascii()
            and secrets.compare_digest(provided, expected))


def decode_message(raw):
    """Bound nested structures and reject non-standard JSON numeric constants."""
    def invalid_constant(value):
        raise ValueError('Non-finite JSON number')
    try:
        document = json.loads(raw, parse_constant=invalid_constant)
    except RecursionError as exc:
        raise ValueError('JSON nesting limit') from exc
    pending = [(document, 0)]
    visited = 0
    while pending:
        value, depth = pending.pop()
        visited += 1
        if depth > 32 or visited > 20000:
            raise ValueError('JSON complexity limit')
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError('Non-finite JSON number')
        children = value.values() if isinstance(value, dict) else value if isinstance(value, list) else ()
        pending.extend((child, depth + 1) for child in children)
    return document

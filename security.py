"""Small, dependency-free security helpers for the V1P LAN-only application."""
from __future__ import annotations

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

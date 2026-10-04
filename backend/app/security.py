import threading
import time
from collections import deque
from collections.abc import Callable
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.config import get_settings

_hasher = PasswordHasher()


def hash_password(senha: str) -> str:
    return _hasher.hash(senha)


def verify_password(hash_: str, senha: str) -> bool:
    try:
        return _hasher.verify(hash_, senha)
    except (VerificationError, InvalidHashError):
        return False


def create_token(user_id: int) -> str:
    settings = get_settings()
    expira = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode({"sub": str(user_id), "exp": expira}, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


class SlidingWindowLimiter:
    """In-memory limiter (per process). Enough for v1; use Redis when scaling out."""

    def __init__(
        self,
        max_events: int,
        window_seconds: float,
        clock: Callable[[], float] = time.monotonic,
        sweep_threshold: int = 10_000,
    ):
        self._max = max_events
        self._window = window_seconds
        self._clock = clock
        self._sweep_threshold = sweep_threshold
        self._events: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        with self._lock:
            return self._allow(key)

    def _allow(self, key: str) -> bool:
        agora = self._clock()
        if len(self._events) > self._sweep_threshold:
            self._sweep(agora)
        eventos = self._events.get(key)
        if eventos is not None:
            while eventos and agora - eventos[0] >= self._window:
                eventos.popleft()
            if not eventos:
                del self._events[key]
                eventos = None
        if eventos is not None and len(eventos) >= self._max:
            return False
        if self._max <= 0:
            return False
        self._events.setdefault(key, deque()).append(agora)
        return True

    def _sweep(self, agora: float) -> None:
        self._events = {
            k: v for k, v in self._events.items() if v and agora - v[-1] < self._window
        }

    def reset(self) -> None:
        with self._lock:
            self._events.clear()


login_limiter = SlidingWindowLimiter(max_events=5, window_seconds=60)
login_ip_limiter = SlidingWindowLimiter(max_events=20, window_seconds=60)
question_limiter = SlidingWindowLimiter(max_events=6, window_seconds=60)
register_ip_limiter = SlidingWindowLimiter(max_events=10, window_seconds=3600)

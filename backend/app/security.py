import time
from collections import defaultdict, deque
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

    def __init__(self, max_events: int, window_seconds: float, clock: Callable[[], float] = time.monotonic):
        self._max = max_events
        self._window = window_seconds
        self._clock = clock
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        agora = self._clock()
        eventos = self._events[key]
        while eventos and agora - eventos[0] >= self._window:
            eventos.popleft()
        if len(eventos) >= self._max:
            return False
        eventos.append(agora)
        return True

    def reset(self) -> None:
        self._events.clear()


login_limiter = SlidingWindowLimiter(max_events=5, window_seconds=60)

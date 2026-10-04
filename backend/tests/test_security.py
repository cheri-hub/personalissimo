from app.security import (
    SlidingWindowLimiter,
    create_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_roundtrip():
    h = hash_password("senha-segura-1")
    assert h != "senha-segura-1"
    assert verify_password(h, "senha-segura-1") is True
    assert verify_password(h, "outra") is False


def test_verify_password_with_garbage_hash_is_false():
    assert verify_password("nao-e-um-hash", "x") is False


def test_token_roundtrip_and_tamper():
    token = create_token(42)
    assert decode_token(token) == 42
    assert decode_token(token + "x") is None
    assert decode_token("lixo") is None


def test_sliding_window_limiter():
    agora = [0.0]
    limiter = SlidingWindowLimiter(2, 60, clock=lambda: agora[0])
    assert limiter.allow("k") is True
    assert limiter.allow("k") is True
    assert limiter.allow("k") is False
    assert limiter.allow("outro") is True
    agora[0] = 61.0
    assert limiter.allow("k") is True

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


def test_limiter_does_not_leak_keys():
    agora = [0.0]
    limiter = SlidingWindowLimiter(1, 60, clock=lambda: agora[0])
    assert limiter.allow("k") is True
    assert limiter.allow("k") is False
    assert limiter.allow("k") is False
    assert list(limiter._events) == ["k"]
    assert len(limiter._events["k"]) == 1
    agora[0] = 61.0
    assert limiter.allow("k") is True
    assert list(limiter._events) == ["k"]
    assert len(limiter._events["k"]) == 1


def test_limiter_denied_unknown_key_creates_no_entry():
    limiter = SlidingWindowLimiter(0, 60)
    assert limiter.allow("k") is False
    assert limiter._events == {}


def test_limiter_sweeps_many_one_shot_keys():
    agora = [0.0]
    limiter = SlidingWindowLimiter(2, 60, clock=lambda: agora[0], sweep_threshold=5)
    for i in range(50):
        assert limiter.allow(f"k{i}") is True
    agora[0] = 100.0
    assert limiter.allow("novo") is True
    assert len(limiter._events) <= 2


def test_limiter_sweep_keeps_keys_inside_window():
    agora = [0.0]
    limiter = SlidingWindowLimiter(1, 60, clock=lambda: agora[0], sweep_threshold=3)
    assert limiter.allow("preso") is True
    agora[0] = 50.0
    for i in range(5):
        limiter.allow(f"k{i}")
    assert limiter.allow("preso") is False

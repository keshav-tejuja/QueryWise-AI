from app.security.rate_limit import SlidingWindowLimiter


def test_blocks_after_limit_then_recovers():
    now = [0.0]
    limiter = SlidingWindowLimiter(2, 60, clock=lambda: now[0])
    assert limiter.allow("user")
    assert limiter.allow("user")
    assert not limiter.allow("user")
    now[0] = 61.0
    assert limiter.allow("user")


def test_keys_are_independent():
    limiter = SlidingWindowLimiter(1, 60)
    assert limiter.allow("a")
    assert limiter.allow("b")
    assert not limiter.allow("a")
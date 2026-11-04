"""Compare painted pixels without amplifying low-alpha canvas quantization."""


def assert_painted_rgba(actual, expected):
    """Check alpha and composites on both dark and light opaque backgrounds."""
    actualAlpha = actual[3] / 255
    expectedAlpha = expected[3] / 255
    assert abs(actual[3] - expected[3]) <= 1, (actual, expected)
    for background in (0, 255):
        for actualChannel, expectedChannel in zip(actual[:3], expected[:3]):
            painted = actualChannel * actualAlpha + background * (1 - actualAlpha)
            wanted = expectedChannel * expectedAlpha + background * (1 - expectedAlpha)
            # Reading an 8-bit premultiplied canvas can round both color and alpha.
            assert abs(painted - wanted) <= 1.5, (actual, expected, background)

"""Color measurement must tolerate quantization without accepting wrong surfaces."""
import pytest

from tests.browser.rendering_checks import assert_painted_rgba


def test_low_alpha_round_trip_keeps_the_same_painted_color():
    assert_painted_rgba([40, 26, 20, 38], [39, 30, 20, 38])
    assert_painted_rgba([255, 0, 0, 153], [255, 0, 0, 153])


@pytest.mark.parametrize('actual', [[0, 255, 0, 38], [39, 30, 20, 100], [200, 30, 20, 255]])
def test_wrong_color_or_opacity_is_still_rejected(actual):
    with pytest.raises(AssertionError):
        assert_painted_rgba(actual, [39, 30, 20, 38])

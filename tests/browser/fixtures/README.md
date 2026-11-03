# Widget characterization fixtures

`widgets-en.json` and `widgets-fr.json` preserve synthetic expected UI output captured from main `38cb111c5790166e9f82fe87e98710762add9b11` before P1 extraction. They are historical references, not personal profiles or raw packets. Complete/missing/zero/estimated states and bomb/demo observations describe that baseline.

The old editor and its original recording runner were removed in V1-01. There is no current instruction to regenerate these files with `--record`. Do not rewrite them from a candidate to hide a regression. Current synthetic state builders live in `widget_fixtures.py`; current behavior is checked by the widget-preview, rendering and production suites listed in [tests/README.md](../../README.md).

Chrome 156 with UTC and fixed synthetic dates/timer anchors produced the original references. Their historical authenticated-to-demo behavior was subsequently replaced by deliberate private-surface clearing. Old captures/test results are not proof for current source or every browser.

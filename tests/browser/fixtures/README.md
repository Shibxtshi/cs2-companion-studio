# Widget characterization fixtures

widgets-en.json and widgets-fr.json contain only synthetic expected UI output captured from unchanged main 38cb111c5790166e9f82fe87e98710762add9b11 before P1 extraction. They contain no PIN, token, personal profile or raw game packet.

Each locale records a complete 29-widget reference and changed fields for other states. Cases cover missing/zero values, reported/history economy labels, all supported bomb timer states and the existing demo transitions. Custom labels and player text use synthetic strings.

The default runner compares without updating these files. Use --record only against an explicitly reviewed reference, never to hide a regression. Chrome 156 with UTC and frozen synthetic dates/timer anchors produced the initial fixtures; CI checks all three browsers. The historical authenticated-to-demo board behavior is recorded as observed and can be revised only with an approved functional change.

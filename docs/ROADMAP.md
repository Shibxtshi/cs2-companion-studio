# V1P publication roadmap

- [x] **1 — Stabilize V3**: snapshot compatibility, separate static assets, baseline tests.
- [x] **2 — Remove shipped secrets**: ignore rules, setup generator, examples, secret hygiene check.
- [x] **3 — Initial LAN/API hardening**: origin check, PIN throttling, request caps, security headers, safer Docker default. (Further security audit before release remains required.)
- [x] **4 — Harden GSI state lifecycle (V1P-B)**: reconnects, map/round/player changes, stale-data handling, confidence-labelled economy with conservative missing-value behavior and tests. Windows/CS2 user validation still needed.
- [x] **5 — Installer (V1P-C, Windows validation pending)**: guided detection of CS2/Steam, secret generation/reuse, safe GSI backup/restore, LAN opt-in, diagnostics and onboarding.
- [x] **6 — Widget UX (V1P-D)**: direct snapping resize on desktop, per-widget backgrounds/styles/opacity, five layout templates, mobile-friendly controls, backward-compatible profile migration.
- [x] **7 — User experience (V1P-E / V1P-E.1)**: bilingual guided start, help, authenticated live diagnostics, reconnect status, mobile layout and accessibility, followed by server-side shared profiles, demo isolation and sanitized support logs.
- [x] **8 — V1P-F CI/test suite implemented**: Windows/Linux regressions, 3-browser E2E, Docker smoke, dependency audit and SBOM pipeline, security coverage. **CI validated on GitHub runners; retain the final fresh-build release gate.**
- [x] **9 — Source-available release docs**: license checks, proper SECURITY, CONTRIBUTING, changelog and screenshots.
- [ ] **10 — Tag/publish v1.0.0**: final review, versioned GitHub release and support instructions.

No public publication is implied by this development snapshot.

**V1P-E.1 corrections completed:** server-side profile storage and cross-device synchronization, multilingual widget search, rename, demo isolation, sanitized diagnostics and independent-project disclaimer. No automatic browser profile migration.


## v1.0.0 preparation — final step

The public-facing README, AI disclosure, code of conduct, support instructions, issue/PR templates, custom no-resale source-available license draft and publication checklist are drafted. This is **not yet a public release**; the license holder/private contact and all CI release gates must be completed before step 10. See [`PUBLIC_RELEASE_CHECKLIST.md`](PUBLIC_RELEASE_CHECKLIST.md).

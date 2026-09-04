# Contributing

Bug fixes, translations, tests and UI improvements are welcome.

1. Fork the repository and create a focused branch.
2. Keep the exact model/firmware validation intact.
3. Run `make test`.
4. Explain hardware-impacting changes and how they were validated.
5. Open a pull request without logs containing tokens or personal data.

New laptop support must be reviewed separately and backed by upstream
`msi-ec` support. A similar model name is not evidence of register
compatibility.

Shell code uses `set -Eeuo pipefail`; Python targets Python 3.11 or later.
Changes to game detection should include a synthetic `/proc` test.
Backend changes should extend the fake-sysfs integration test.

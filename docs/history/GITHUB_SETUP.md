# Setting up the GitHub repository

This document is for the personal project maintainer preparing the **first public V1P release**. This archive is not itself a published GitHub repository.

## Suggested repository metadata

- **Name:** `cs2-companion-studio` (subject to availability)
- **Description:** `Unofficial, AI-assisted personal CS2 GSI dashboard with customizable widgets and multi-device layouts.`
- **Topics:** `counter-strike-2`, `cs2`, `gsi`, `dashboard`, `docker`, `fastapi`, `open-source`
- **About links:** only verified URLs after publishing (do not invent links).

## First upload safely

1. Start from a **clean copy** of this public candidate, **not** the installed folder that contains `.env`, live profiles and logs.
2. Historical note: the initial MIT proposal was superseded. Review the current non-effective no-resale draft and public release checklist.
3. Configure a private security reporting route and a private code-of-conduct contact.
4. Make a **private repository** on GitHub first; avoid pushing real secrets or machine-local data.
5. Inspect `git status --ignored` and `git ls-files` to confirm secrets are not staged or tracked.
6. Commit and push the source; let GitHub Actions run. Investigate every failing check and dependency-audit advisory.
7. Test Docker and installer on a Windows machine, as in [PUBLIC_RELEASE_CHECKLIST.md](../releases/checklist.md).
8. When ready, add up-to-date screenshots, publish the repository and create the first tagged release.

This project is explicitly independent and developed with ChatGPT assistance; maintain visible attribution in README and AI_DISCLOSURE.md.

For example, from a *clean directory* only:

```powershell
git init
git add .
git status --short
python scripts/check_secrets.py
# Inspect files staged for commit before continuing.
git commit -m "Prepare V1P public repository"
```

Do not commit `.env` or `data/` even when using `git add .`. `check_secrets.py` rejects tracked secrets but is not a substitute for reviewing the Git index and full history.

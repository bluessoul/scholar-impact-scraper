# Security Policy

## Sensitive Files

Do not publish, commit, upload, or paste contents from:

- `.env`
- `.env.*` except `.env.example`
- `config.json`
- `.playwright_profile/`
- browser caches
- generated screenshots
- captured HTML pages
- generated CSV, JSON, Markdown, and log outputs

## Credentials

Use environment variables or local ignored files for credentials.

If a credential is accidentally committed or shared:

1. Rotate or revoke it immediately.
2. Remove it from the repository history before publishing.
3. Re-run the release checklist in `RELEASE_CHECKLIST.md`.

## Browser Profiles

The `.playwright_profile/` directory may contain cookies, login state, and institutional access traces. Treat it as a secret.

## Responsible Use

Use this project only with accounts, subscriptions, and data you are authorized to access. Respect service terms, rate limits, copyright restrictions, institutional policies, and privacy obligations.

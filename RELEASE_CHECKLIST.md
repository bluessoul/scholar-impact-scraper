# Release Checklist

Use this checklist before publishing this skill to GitHub.

## Must Not Publish

- `config.json`
- `.env` and `.env.*` except `.env.example`
- `.playwright_profile/`
- `.agent/`
- `node/`
- `node_modules/`
- generated `*.csv`, `*.json`, `*.html`, `*.png`, `*.jpg`, `*.jpeg`, `*.log`
- screenshots, captured pages, and raw scraping outputs

## Current Clean Copy

This `public-release/` folder intentionally contains only:

- source code
- dependency manifests
- placeholder environment example
- public documentation
- the JCR fetch script moved to `scripts/fetch.js`
- one mock-based ORCID test file

## Before GitHub Push

Run these checks from inside `public-release/`:

```powershell
rg -n -i "password|passwd|pwd|token|secret|api[_-]?key|client[_-]?secret|cookie|session|authorization|bearer|email|username|login"
rg -n -i "xiang|imdea|PFr\\+iW4Q|u8ZwRT4|carlos"
git status --short
git diff --cached
```

Keyword matches in documentation or placeholder examples are acceptable only after manual review. Real emails, passwords, tokens, cookies, account identifiers, and generated research data are not acceptable.

## Credential Rotation

Because the source folder contained a real `config.json` with an email and password, rotate that password before publishing anything derived from this project.

## Compliance Note

Use the tool only with accounts, subscriptions, and data that the user is authorized to access. Respect Google Scholar, Web of Science, Clarivate JCR, ORCID, institutional policies, rate limits, privacy obligations, and copyright restrictions.

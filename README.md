# Scholar Impact Scraper

Scholar Impact Scraper is a QClaw/OpenClaw skill and standalone toolkit for collecting academic impact signals from public or subscription-backed scholar services.

It currently includes:

- Google Scholar publication and citation scraping with Playwright.
- Web of Science citation lookups when the user has legitimate access.
- ORCID publication extraction through the ORCID Public API.
- Clarivate JCR journal category, quartile, ranking, and impact-factor extraction through Playwright.

## Safety First

Do not commit real credentials, browser profiles, generated result files, screenshots, or captured HTML pages.

This repository is designed to keep secrets outside Git:

- Use environment variables or a local `.env` file for credentials.
- Keep `config.json` local only.
- Keep `.playwright_profile/` local only; it can contain cookies and institutional login state.
- Review generated CSV/JSON/HTML/PNG files before sharing them.

## Install

Python dependencies:

```bash
pip install -r requirements.txt
playwright install chromium
```

Node dependencies for the JCR fetcher:

```bash
npm install
```

## ORCID Setup

Copy `.env.example` to `.env` and fill in only local credentials:

```bash
cp .env.example .env
```

Example variables:

```env
ORCID_CLIENT_ID=APP-XXXXXXXXXXXXXXXX
ORCID_CLIENT_SECRET=00000000-0000-0000-0000-000000000000
TARGET_ORCID_ID=0000-0002-1825-0097
OUTPUT_CSV=orcid_publications.csv
```

Run:

```bash
python orcid_extractor.py
```

## Scholar And Web Of Science

Run:

```bash
python scholar_playwright.py --user-id <Scholar_ID> --wos-id <WoS_ID> --output output.csv --max-clicks 5
```

If Web of Science needs institutional login, open a persistent browser profile locally:

```bash
python launch_browser_for_login.py
```

The resulting `.playwright_profile/` directory must stay local and must never be committed.

## JCR Fetcher

Install Node dependencies first:

```bash
npm install
```

Run with an input JSON file:

```bash
npm run fetch -- --input input.json --output jcr_results.md
```

Input format:

```json
[
  {
    "journal_name_or_issn": "IEEE Transactions on Pattern Analysis and Machine Intelligence",
    "publication_year": 2021
  }
]
```

For Clarivate credentials, prefer local environment variables:

```powershell
$env:CLARIVATE_EMAIL="your_email@institution.edu"
$env:CLARIVATE_PASSWORD="your_password"
```

You may also use `config.json` locally, but it is ignored by Git and must not be published.

## Tests

```bash
python tests/test_orcid_extractor.py
```

## Compliance

Use this tool only with accounts and subscriptions you are authorized to use. Respect service terms, rate limits, copyright restrictions, institutional policies, and privacy obligations.

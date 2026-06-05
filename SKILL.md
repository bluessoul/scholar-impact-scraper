---
name: scholar-impact-scraper
description: "Academic impact scraping toolkit for Google Scholar, Web of Science, ORCID, and Clarivate JCR. Uses Python and Playwright/Node helpers. Credentials and browser sessions must stay local."
version: "1.0.0"
author: "Antigravity"
metadata:
  openclaw:
    requires:
      env:
        - ORCID_CLIENT_ID (optional)
        - ORCID_CLIENT_SECRET (optional)
        - CLARIVATE_EMAIL (optional)
        - CLARIVATE_PASSWORD (optional)
---

# Scholar Impact Scraper

Use this skill when the user needs to collect or reconcile academic impact data from Google Scholar, Web of Science, ORCID, or Clarivate JCR.

## Privacy And Secrets

- Never publish or commit `config.json`, `.env`, `.playwright_profile/`, generated CSV/JSON/HTML files, screenshots, or browser caches.
- Ask the user to provide credentials through local environment variables or local ignored files only.
- Treat `.playwright_profile/` as sensitive because it may contain cookies and institutional access state.
- Do not display passwords, access tokens, cookies, or full credential-bearing config files in chat.

## Python Tools

Install dependencies:

```bash
pip install -r {baseDir}/requirements.txt
playwright install chromium
```

Run Scholar/Web of Science extraction:

```bash
python {baseDir}/scholar_playwright.py --user-id <Scholar_ID> --wos-id <WoS_ID> --output <Output_CSV> --max-clicks <Max_Clicks>
```

Optional flags include `--fetch-doi`, `--fetch-wos-ut`, and `--no-wos-ut`.

Run ORCID extraction:

```bash
python {baseDir}/orcid_extractor.py
```

## Login Helper

If Web of Science or JCR requires institutional login, open a local persistent browser profile:

```bash
python {baseDir}/launch_browser_for_login.py
```

Keep the generated `.playwright_profile/` directory local.

## JCR Tools

Install Node dependencies:

```bash
npm install
```

Run JCR extraction:

```bash
npm run fetch -- --input <Input_JSON_Path> --output <Output_MD_Path>
```

Input JSON format:

```json
[
  {
    "journal_name_or_issn": "1007-9211",
    "publication_year": 2022
  }
]
```

## Output Handling

Generated CSV, JSON, Markdown, HTML, and screenshot files should be considered local artifacts until reviewed and explicitly approved for sharing.

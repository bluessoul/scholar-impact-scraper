中文说明：[QUICKSTART.md](QUICKSTART.md)

# Quickstart

## 1. Install Base Tools

Install:

- Python 3.10 or newer.
- Node.js 18 or newer.
- Git.

## 2. Install Project Dependencies

Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m playwright install chromium
npm install
```

macOS/Linux:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m playwright install chromium
npm install
```

## 3. Configure Local Credentials

Windows:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Fill in only the credentials required by the workflow you plan to use:

- ORCID: `ORCID_CLIENT_ID` and `ORCID_CLIENT_SECRET`
- OpenAlex: optional `OPENALEX_API_KEY`
- JCR: `CLARIVATE_EMAIL` and `CLARIVATE_PASSWORD`
- Web of Science: usually requires manual institutional login

Do not commit `.env`, `config.json`, or `.playwright_profile/`.

## 4. Run Tests

Windows:

```powershell
.\.venv\Scripts\python tests\test_orcid_extractor.py
```

macOS/Linux:

```bash
./.venv/bin/python tests/test_orcid_extractor.py
```

## 5. First Run: Save Web Login State

If you plan to use live Web of Science or JCR lookup, run a login helper first:

```bash
python launch_browser_for_login.py
```

Windows JCR login helper:

```powershell
.\launch_jcr_login.bat
```

After login succeeds, close the browser. State is saved under `.playwright_profile/`. Do not commit or share that directory. If a core script detects that `.playwright_profile/` does not exist yet, it creates a `FIRST_RUN_LOGIN_SETUP.md` reminder file.

## 6. Run ORCID

Windows:

```powershell
.\.venv\Scripts\python orcid_extractor.py
```

macOS/Linux:

```bash
./.venv/bin/python orcid_extractor.py
```

## 7. Run JCR

There are two JCR usage paths: use your own single-year or multi-year JCR quartile raw-data files as an offline reference, or use your authorized Clarivate/JCR account with a Playwright automated browser to query live information from the website. The current scripts default to a visible browser window for login and verification; you can adapt the browser mode to headless in your own environment if appropriate. The public release does not bundle complete JCR raw files by default; local files can be placed under `data/jcr-local/`, but should not be committed unless redistribution is clearly allowed.

```bash
npm run fetch -- --input examples/jcr_input.example.json --output jcr_results.md
```

The script first asks whether you want to pause and use/find a local JCR offline file. For unattended runs, skip the prompt:

```bash
npm run fetch -- --input examples/jcr_input.example.json --output jcr_results.md --skip-offline-reminder
```

`jcr_results.md` is a generated local artifact and should be reviewed before sharing.

## 8. Run Scholar/WoS

```bash
python scholar_playwright.py --user-id <Scholar_ID> --wos-id <WoS_ID> --output output.csv --max-clicks 5
```

Default publication-enrichment run:

```bash
python scholar_playwright.py --user-id <Scholar_ID> --output output.csv --max-clicks 5 --output-sort publication-date
```

The script defaults to Google Scholar detail panels, OpenAlex, and Crossref in order to enrich DOI and metadata, and it attempts corresponding-author extraction. `--output-sort publication-date` makes CSV and reference outputs newest-first; omit it to keep the default citation-count sort.

Common optional flags:

```text
--citation-format apa,gbt
--target-author "Author Name"
--target-author-position 3
--author-highlight both
--corresponding-author "Author Name"
--corresponding-author-position 5
--openalex-max-records 20
--no-fetch-doi
--no-openalex-enrich
--no-fetch-corresponding
--output-sort citations|publication-date|year|none
```

If Web of Science needs login:

```bash
python launch_browser_for_login.py
```

`.playwright_profile/` stores local login state. Do not commit or share it.

## 9. License

This project uses the Apache License 2.0. Copyright © 2026 bluessoul. If you use, modify, or redistribute this project, keep the `LICENSE`, `NOTICE`, and copyright notice, and provide attribution to the original project.

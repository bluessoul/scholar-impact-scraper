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

For Google Scholar extraction, use DOI resolution, OpenAlex enrichment, and corresponding-author lookup by default. The script defaults to `--fetch-doi`, `--openalex-enrich`, and `--fetch-corresponding`; use `--no-fetch-doi`, `--no-openalex-enrich`, or `--no-fetch-corresponding` only for fast, offline, or minimal runs. Optional Web of Science flags include `--fetch-wos-ut` and `--no-wos-ut`.
Use `--refine auto` or `--refine all` to open Google Scholar detail panels and enrich rows with `Journal`, `Conference`, `Volume`, `Issue`, `Pages`, `Publisher`, `Description`, and raw `Scholar Detail Fields JSON` when those fields are visible.
DOI resolution is multi-source. DOI values visible in Google Scholar detail panels are used first. When `--fetch-doi` is enabled with the default `--refine auto`, the script opens Scholar detail panels up to `--refine-limit` before querying Crossref. Only records that still have no DOI are queried against Crossref by title. CSV output records `DOI Source`, `DOI Confidence`, and `DOI Evidence JSON` for downstream verification.
OpenAlex metadata enrichment is enabled by default before Crossref fallback. It uses DOI exact lookup when a DOI is already available, otherwise title search with confidence scoring. Optional controls are `--openalex-api-key` (or `OPENALEX_API_KEY`), `--openalex-max-records <N>`, and `--openalex-min-confidence <score>`. The enrichment can fill missing DOI, complete authors when Scholar authors are truncated, corresponding authors, source, publisher, volume, issue, and pages. CSV output adds `OpenAlex ID`, `OpenAlex DOI`, `OpenAlex Match Confidence`, `OpenAlex Match Method`, `OpenAlex Authors`, `OpenAlex Author Count`, `OpenAlex Corresponding Authors`, `OpenAlex Corresponding Author Positions`, `OpenAlex Source`, `OpenAlex Publisher`, `OpenAlex Volume`, `OpenAlex Issue`, `OpenAlex Pages`, `OpenAlex Evidence JSON`, `Metadata Enrichment Source`, and `Metadata Enrichment Confidence`.
CSV output is always saved. By default, the script asks whether to also export references as APA, MLA, Chicago, Harvard, LaTeX/BibTeX, AMA/Numeric, GB/T 7714, GB/T 7714-2025, or all formats. For automation, pass `--citation-format none`, `--citation-format apa`, `--citation-format gbt2025`, or comma-separated values such as `--citation-format apa,latex,gbt2025`.
Output sorting is user-selectable with `--output-sort citations`, `publication-date`, `year`, or `none`. The default remains `citations`; use `--output-sort publication-date` when the user wants newest publications first.
Use `--target-author "<Name>"` or `--target-author-position <N>` to add target-author columns (`Target Author Position`, `Target Author Matched Name`, `Highlighted Authors`) and highlight that author in reference exports. Highlight styles are `--author-highlight bold`, `underline`, `both`, or `none`.
Corresponding-author support has two layers. First, a user can provide `--corresponding-author "<Name>"` or `--corresponding-author-position <N>`, which takes priority. Second, default corresponding-author lookup reuses OpenAlex enrichment first and uses Crossref as a no-guess fallback when structured corresponding-author data is unavailable. CSV output adds `Corresponding Author Position`, `Corresponding Author Matched Name`, `Is Target Author Corresponding`, `Highlighted Corresponding Authors`, `Corresponding Evidence Source`, `Corresponding Confidence`, and `Corresponding Evidence JSON`.

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

Run JCR / partition extraction:

```bash
npm run fetch -- --input <Input_JSON_Path> --output <Output_MD_Path>
```

If the user does not clearly specify which partition system they want, ask whether they want local CAS partition data, local JCR data, live JCR lookup, or no partition lookup. For CAS partition lookup, instruct the user to place their own legally obtained CSV/TSV/JSON files under `data/cas-local/` or pass `--local-partition-file <path>`.

Common options:

```bash
npm run fetch -- --input <Input_JSON_Path> --output cas_results.md --partition-source cas-local
npm run fetch -- --input <Input_JSON_Path> --output jcr_local_results.md --partition-source jcr-local
npm run fetch -- --input <Input_JSON_Path> --output jcr_live_results.md --partition-source jcr-live
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

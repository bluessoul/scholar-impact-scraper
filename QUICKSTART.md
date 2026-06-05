# Quickstart

This guide is for users and coding agents that want to run the project after cloning it.

## 1. Install Python Dependencies

Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m playwright install chromium
```

macOS/Linux:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m playwright install chromium
```

## 2. Install Node Dependencies

```bash
npm install
```

## 3. Configure Local Credentials

Copy `.env.example` to `.env` and fill in only local values.

Do not commit `.env`, `config.json`, or `.playwright_profile/`.

## 4. Run A Test

Windows:

```powershell
.\.venv\Scripts\python tests\test_orcid_extractor.py
```

macOS/Linux:

```bash
./.venv/bin/python tests/test_orcid_extractor.py
```

## 5. Run ORCID

```bash
python orcid_extractor.py
```

## 6. Run JCR

```bash
npm run fetch -- --input examples/jcr_input.example.json --output jcr_results.md
```

`jcr_results.md` is a generated local artifact and should be reviewed before sharing.

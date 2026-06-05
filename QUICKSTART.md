中文说明在前，English version is provided in the second half of this file.

# Quickstart 快速开始

## 中文快速开始

### 1. 安装基础环境

请先安装：

- Python 3.10 或更新版本。
- Node.js 18 或更新版本。
- Git。

### 2. 安装项目依赖

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

### 3. 配置本地凭据

Windows:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

只填写你要使用的功能需要的凭据：

- ORCID：`ORCID_CLIENT_ID` 和 `ORCID_CLIENT_SECRET`
- JCR：`CLARIVATE_EMAIL` 和 `CLARIVATE_PASSWORD`
- Web of Science：通常需要手动登录机构账号

不要提交 `.env`、`config.json` 或 `.playwright_profile/`。

### 4. 运行测试

Windows:

```powershell
.\.venv\Scripts\python tests\test_orcid_extractor.py
```

macOS/Linux:

```bash
./.venv/bin/python tests/test_orcid_extractor.py
```

### 5. 运行 ORCID

Windows:

```powershell
.\.venv\Scripts\python orcid_extractor.py
```

macOS/Linux:

```bash
./.venv/bin/python orcid_extractor.py
```

### 6. 运行 JCR

```bash
npm run fetch -- --input examples/jcr_input.example.json --output jcr_results.md
```

`jcr_results.md` 是本地生成文件，分享前需要人工检查。

### 7. 运行 Scholar/WoS

```bash
python scholar_playwright.py --user-id <Scholar_ID> --wos-id <WoS_ID> --output output.csv --max-clicks 5
```

如果需要登录 Web of Science：

```bash
python launch_browser_for_login.py
```

`.playwright_profile/` 会保存本地登录状态，不能提交或分享。

---

# Quickstart

English version. The Chinese version is provided above.

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

## 5. Run ORCID

Windows:

```powershell
.\.venv\Scripts\python orcid_extractor.py
```

macOS/Linux:

```bash
./.venv/bin/python orcid_extractor.py
```

## 6. Run JCR

```bash
npm run fetch -- --input examples/jcr_input.example.json --output jcr_results.md
```

`jcr_results.md` is a generated local artifact and should be reviewed before sharing.

## 7. Run Scholar/WoS

```bash
python scholar_playwright.py --user-id <Scholar_ID> --wos-id <WoS_ID> --output output.csv --max-clicks 5
```

If Web of Science needs login:

```bash
python launch_browser_for_login.py
```

`.playwright_profile/` stores local login state. Do not commit or share it.

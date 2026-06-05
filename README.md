中文说明在前，English version is provided in the second half of this README.

# Scholar Impact Scraper 学术影响力抓取工具

## 这是什么

Scholar Impact Scraper 是一个面向 QClaw/OpenClaw、Codex、Claude Code、Cloud Code 以及其他 Agentic IDE 的学术影响力抓取工具仓库。它也可以作为普通命令行项目使用。

它目前包含：

- Google Scholar 论文列表和引用数据抓取。
- Web of Science 引用数据查询，前提是用户拥有合法访问权限。
- ORCID Public API 论文成果提取。
- Clarivate JCR 期刊学科类别、分区、排名和影响因子提取。

## 开始之前

请先确认你已经安装：

- Python 3.10 或更新版本。
- Node.js 18 或更新版本，包含 `npm`。
- Git。
- 可以正常打开浏览器的桌面环境，因为 Playwright 可能需要弹出浏览器完成登录或验证。

你不一定需要配置所有账号。只使用哪个功能，就配置哪个功能需要的凭据：

- ORCID：需要 ORCID Public API Client ID 和 Client Secret。
- Google Scholar：通常不需要账号，但可能触发验证码或访问限制。
- Web of Science：需要你自己拥有合法的机构订阅或个人访问权限。
- Clarivate JCR：需要你自己拥有合法的 Clarivate/JCR 访问权限。

## 安全规则

不要提交、上传、粘贴或公开以下内容：

- `.env`
- `.env.*`，除了 `.env.example`
- `config.json`
- `.playwright_profile/`
- 浏览器缓存
- 截图
- 抓取下来的 HTML 页面
- 生成的 CSV、JSON、Markdown 和日志文件

`.playwright_profile/` 可能包含 cookie、登录状态和机构访问痕迹，请把它当作秘密文件处理。

如果你曾经把真实账号、密码、token 或 cookie 提交到了 Git 历史里，仅删除文件是不够的。请先轮换或撤销凭据，再清理 Git 历史。

## 安装环境

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

## 配置本地账号和凭据

复制环境变量模板：

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

然后只在本地 `.env` 中填写你需要的功能对应的值：

```env
ORCID_CLIENT_ID=APP-XXXXXXXXXXXXXXXX
ORCID_CLIENT_SECRET=00000000-0000-0000-0000-000000000000
TARGET_ORCID_ID=0000-0002-1825-0097
OUTPUT_CSV=orcid_publications.csv

CLARIVATE_EMAIL=your_email@institution.edu
CLARIVATE_PASSWORD=your_password
```

建议优先使用 `.env` 或系统环境变量。`config.json` 只适合本地临时使用，已经被 `.gitignore` 忽略，不能发布。

## 先跑一个测试

Windows:

```powershell
.\.venv\Scripts\python tests\test_orcid_extractor.py
```

macOS/Linux:

```bash
./.venv/bin/python tests/test_orcid_extractor.py
```

如果测试通过，说明 Python 依赖和基础环境基本正常。

## 运行 ORCID 提取

确认 `.env` 中已经配置 ORCID 信息后运行：

Windows:

```powershell
.\.venv\Scripts\python orcid_extractor.py
```

macOS/Linux:

```bash
./.venv/bin/python orcid_extractor.py
```

也可以通过命令行参数覆盖 `.env`：

```bash
python orcid_extractor.py --orcid 0000-0002-1825-0097 --client-id APP-YOURID --client-secret YOURSECRET --output my_publications.csv
```

## 运行 Google Scholar 和 Web of Science

```bash
python scholar_playwright.py --user-id <Scholar_ID> --wos-id <WoS_ID> --output output.csv --max-clicks 5
```

如果 Web of Science 需要机构登录，先打开本地持久化浏览器：

```bash
python launch_browser_for_login.py
```

在弹出的浏览器中手动登录你的机构或个人账号。关闭浏览器后，登录状态会保存在本地 `.playwright_profile/` 中。这个目录不能提交或分享。

## 运行 JCR 提取

先准备输入文件。可以参考：

```text
examples/jcr_input.example.json
```

输入格式：

```json
[
  {
    "journal_name_or_issn": "IEEE Transactions on Pattern Analysis and Machine Intelligence",
    "publication_year": 2021
  }
]
```

运行：

```bash
npm run fetch -- --input examples/jcr_input.example.json --output jcr_results.md
```

如果你使用 Clarivate/JCR 自动登录，请只在本地 `.env` 或系统环境变量中配置：

```powershell
$env:CLARIVATE_EMAIL="your_email@institution.edu"
$env:CLARIVATE_PASSWORD="your_password"
```

## 输出文件

常见输出包括：

- `*.csv`
- `*.json`
- `*.md`
- `*.html`
- `*.png`
- `*.log`

这些默认都是本地产物。分享或提交前请人工检查，确认没有个人信息、机构访问痕迹、账号信息、cookie、受版权保护的页面内容或不该公开的数据。

## Agentic IDE 支持

这个仓库尽量兼容多种 Agentic IDE 和 coding agent：

- `SKILL.md`：给支持 skill 工作流的工具使用。
- `AGENTS.md`：给通用 coding agent 使用。
- `CLAUDE.md`：给 Claude Code 使用。
- `GEMINI.md`：给 Gemini 或其他代理客户端使用。
- `QUICKSTART.md`：更短的安装和运行步骤。
- `SECURITY.md` 和 `RELEASE_CHECKLIST.md`：安全和发布检查。

## 合规说明

请只在你拥有合法授权的账号、订阅和数据范围内使用本工具。使用时请遵守 Google Scholar、Web of Science、Clarivate JCR、ORCID 的服务条款、访问频率限制、版权要求、机构政策和隐私义务。

---

# Scholar Impact Scraper

English version. The Chinese version is provided above.

## What This Is

Scholar Impact Scraper is an academic impact extraction toolkit for QClaw/OpenClaw, Codex, Claude Code, Cloud Code, and other agentic IDEs. It can also be used as a normal command-line project.

It currently includes:

- Google Scholar publication and citation scraping.
- Web of Science citation lookups when the user has legitimate access.
- ORCID publication extraction through the ORCID Public API.
- Clarivate JCR journal category, quartile, ranking, and impact-factor extraction.

## Before You Start

Make sure you have:

- Python 3.10 or newer.
- Node.js 18 or newer, including `npm`.
- Git.
- A desktop environment that can open a browser, because Playwright may need a visible browser for login or verification.

You do not need every account for every workflow. Configure only the credentials required by the feature you plan to use:

- ORCID: requires an ORCID Public API Client ID and Client Secret.
- Google Scholar: usually does not require an account, but may trigger verification or rate limits.
- Web of Science: requires legitimate institutional or personal access.
- Clarivate JCR: requires legitimate Clarivate/JCR access.

## Safety Rules

Do not commit, upload, paste, or publish:

- `.env`
- `.env.*` except `.env.example`
- `config.json`
- `.playwright_profile/`
- browser caches
- screenshots
- captured HTML pages
- generated CSV, JSON, Markdown, and log files

Treat `.playwright_profile/` as sensitive because it may contain cookies, login state, and institutional access traces.

If real credentials, tokens, or cookies were ever committed to Git history, deleting the file is not enough. Rotate or revoke the credential first, then clean the Git history.

## Install

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

## Configure Local Credentials

Copy the environment template:

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Then fill in only the values required by the workflow you plan to run:

```env
ORCID_CLIENT_ID=APP-XXXXXXXXXXXXXXXX
ORCID_CLIENT_SECRET=00000000-0000-0000-0000-000000000000
TARGET_ORCID_ID=0000-0002-1825-0097
OUTPUT_CSV=orcid_publications.csv

CLARIVATE_EMAIL=your_email@institution.edu
CLARIVATE_PASSWORD=your_password
```

Prefer `.env` or environment variables. `config.json` is supported only for local use, is ignored by Git, and must not be published.

## Run A Smoke Test

Windows:

```powershell
.\.venv\Scripts\python tests\test_orcid_extractor.py
```

macOS/Linux:

```bash
./.venv/bin/python tests/test_orcid_extractor.py
```

If the test passes, your Python dependencies and base environment are working.

## Run ORCID Extraction

After configuring ORCID values in `.env`, run:

Windows:

```powershell
.\.venv\Scripts\python orcid_extractor.py
```

macOS/Linux:

```bash
./.venv/bin/python orcid_extractor.py
```

You can also override `.env` with command-line arguments:

```bash
python orcid_extractor.py --orcid 0000-0002-1825-0097 --client-id APP-YOURID --client-secret YOURSECRET --output my_publications.csv
```

## Run Google Scholar And Web Of Science

```bash
python scholar_playwright.py --user-id <Scholar_ID> --wos-id <WoS_ID> --output output.csv --max-clicks 5
```

If Web of Science needs institutional login, open a local persistent browser profile first:

```bash
python launch_browser_for_login.py
```

Log in manually in the browser window. After closing the browser, login state is stored locally in `.playwright_profile/`. Never commit or share that directory.

## Run JCR Extraction

Prepare an input file. See:

```text
examples/jcr_input.example.json
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

Run:

```bash
npm run fetch -- --input examples/jcr_input.example.json --output jcr_results.md
```

If you use Clarivate/JCR automatic login, configure credentials only through local `.env` or environment variables:

```powershell
$env:CLARIVATE_EMAIL="your_email@institution.edu"
$env:CLARIVATE_PASSWORD="your_password"
```

## Output Files

Common outputs include:

- `*.csv`
- `*.json`
- `*.md`
- `*.html`
- `*.png`
- `*.log`

These are local artifacts by default. Before sharing or committing them, manually check that they do not contain personal information, institutional access traces, account data, cookies, copyrighted page content, or data that should not be public.

## Agentic IDE Support

This repository is designed to be friendly to multiple coding agents and agentic IDEs:

- `SKILL.md`: for tools that support skill workflows.
- `AGENTS.md`: for general coding agents.
- `CLAUDE.md`: for Claude Code.
- `GEMINI.md`: for Gemini or other agent clients.
- `QUICKSTART.md`: shorter setup and run instructions.
- `SECURITY.md` and `RELEASE_CHECKLIST.md`: security and release checks.

## Compliance

Use this tool only with accounts, subscriptions, and data you are authorized to access. Respect the terms of service, rate limits, copyright restrictions, institutional policies, and privacy obligations of Google Scholar, Web of Science, Clarivate JCR, and ORCID.

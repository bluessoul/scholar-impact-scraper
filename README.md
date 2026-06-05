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

### JCR 数据来源和实时查询能力

目前公开仓库的使用说明只覆盖两类 JCR 使用方式：

- 离线参考：如果你手头有网上公开分享的 JCR 2024 分区原始文件，可以把它作为本地参考数据使用。请注意，这类文件不是本仓库生成的官方实时数据，也可能存在滞后、缺项或版权/再分发限制，使用前需要自行核验来源和授权。
- 实时查询：如果你拥有合法的 Clarivate/JCR 访问权限，可以通过本项目的 Playwright 自动化浏览器登录 JCR 网站，查询当前页面可见的最新信息。当前脚本默认使用可视化浏览器窗口，便于手动处理机构登录、验证码或安全验证；在你自己的环境中也可以按需要改成无头模式。

实时查询不会绕过访问控制。你仍然需要使用自己有权使用的机构或个人账号。

默认 public release 不附带完整的 JCR 2024 原始分区文件。原因是网上分享的数据文件可能有版权、数据库权利、平台条款或再分发限制。如果你只是本地使用，可以把自己的文件放在 `data/jcr2024/` 或其他本地路径中；如果你确实要把数据文件发布到 GitHub，请先确认来源允许公开再分发，并在 `data/jcr2024/README.md` 中记录来源、许可证、下载日期和校验信息。

运行 JCR 脚本时，它会先主动提醒你可以寻找公开分享的 JCR 2024 分区原始文件来节省实时查询时间。如果你选择不使用离线文件，脚本会继续打开 Playwright 浏览器进行实时查询。自动化运行时可以添加 `--skip-offline-reminder` 跳过这个提醒。

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

自动化或无人值守运行时：

```bash
npm run fetch -- --input examples/jcr_input.example.json --output jcr_results.md --skip-offline-reminder
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

### JCR Data Sources And Live Lookup

The public release currently documents two JCR usage paths:

- Offline reference: if you already have a publicly shared JCR 2024 quartile raw-data file, you can use it as a local reference source. This kind of file is not official live data generated by this repository, may be incomplete or outdated, and may have copyright or redistribution restrictions. Verify the source and permission before using it.
- Live lookup: if you have legitimate Clarivate/JCR access, this project can use a Playwright automated browser to log in to the JCR website and query the latest information visible to your account. The current scripts default to a visible browser window so that institutional login, CAPTCHA, or security checks can be handled manually; you can adapt the browser mode to headless in your own environment if appropriate.

Live lookup does not bypass access control. You still need to use an institutional or personal account that you are authorized to use.

By default, the public release does not bundle the full JCR 2024 raw quartile file. Publicly shared data files may be subject to copyright, database rights, platform terms, or redistribution restrictions. For local-only use, place your own file under `data/jcr2024/` or another local path. If you decide to publish a data file to GitHub, first confirm that the source allows public redistribution and document the source, license, download date, and checksum in `data/jcr2024/README.md`.

When the JCR script starts, it first reminds you that a publicly shared JCR 2024 quartile raw-data file may save live lookup time. If you choose not to use an offline file, the script continues with the Playwright browser workflow. For automated runs, pass `--skip-offline-reminder` to skip this prompt.

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

For automated or unattended runs:

```bash
npm run fetch -- --input examples/jcr_input.example.json --output jcr_results.md --skip-offline-reminder
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

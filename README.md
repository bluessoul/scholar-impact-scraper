English version: [README.en.md](README.en.md)

# Scholar Impact Scraper 学术影响力抓取工具

## 它解决什么问题

科研人员、研究助理和科研管理人员经常需要反复整理同一批信息：某位学者在 Google Scholar 的论文和引用、Web of Science 的引用与他引数据、ORCID 成果列表，以及期刊在 JCR 中的分区、排名和影响因子。这些信息分散在不同平台，复制粘贴耗时，也很容易漏项或格式不一致。

这个项目把这些重复工作整理成一套可由命令行或 Agentic IDE 协助运行的流程：你准备 Scholar ID、WoS ID、ORCID iD 或期刊列表，工具负责把抓取、登录提醒、验证码人工接管、结果导出和安全注意事项串起来。它尤其适合做学者影响力初筛、简历/基金材料前的数据整理、期刊分区核查、论文列表补全，以及让 Codex、Claude Code、OpenClaw 等客户端接手半自动化科研数据任务。

本项目不会绕过任何平台访问控制。需要账号或机构订阅的功能，仍然要求你使用自己有权访问的账号。

## 典型使用场景

- **基金申请和简历整理**：批量整理某位学者的论文、引用、作者顺序、通讯作者线索、DOI、卷期页码，并按 APA、MLA、Chicago、Harvard、LaTeX/BibTeX、AMA/Numeric 或 GB/T 7714 导出参考文献，减少手工改格式的时间。
- **学者影响力初筛**：快速汇总 Google Scholar 与 Web of Science 的引用指标，辅助评估候选人、合作对象、课题组成员或项目团队的科研产出。
- **论文清单补全**：从 Google Scholar 列表页出发，打开详情页补全作者、期刊/会议、卷、期、页码、出版社、DOI 等字段；缺失 DOI 时再用 Crossref 进行补充校验。
- **期刊投稿和成果归档**：查询 JCR 分区、排名和影响因子，或把用户自己下载的多年份 JCR 本地数据作为参考，服务投稿选择、成果登记和年度统计。
- **Agentic IDE 自动化任务**：让 Codex、Claude Code、OpenClaw 等客户端读取 `SKILL.md`/`AGENTS.md`，在本地凭据和浏览器会话范围内协助执行半自动化科研数据整理流程。

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

## 首次运行：保存浏览器登录状态

如果你要使用 Web of Science 或 Clarivate/JCR 的实时查询，建议第一次先通过登录助手保存本地浏览器会话：

```bash
python launch_browser_for_login.py
```

Windows 下也可以为 JCR 运行：

```powershell
.\launch_jcr_login.bat
```

在打开的浏览器中登录你有权使用的机构或个人账号，确认平台可访问后关闭浏览器。登录状态会保存在 `.playwright_profile/` 中。这个目录是敏感本地文件，不能提交或分享。

如果你直接运行核心脚本但还没有 `.playwright_profile/`，脚本会在终端中提醒你先完成登录设置，并生成 `FIRST_RUN_LOGIN_SETUP.md` 给 Codex、Claude Code、OpenClaw 等客户端读取。该提醒文件已被 `.gitignore` 忽略。

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

- 离线参考：如果你手头有自己下载或整理的某一年 JCR 分区原始文件，可以把它作为本地参考数据使用。请注意，这类文件不是本仓库生成的官方实时数据，也可能存在滞后、缺项或版权/再分发限制，使用前需要自行核验来源和授权。
- 实时查询：如果你拥有合法的 Clarivate/JCR 访问权限，可以通过本项目的 Playwright 自动化浏览器登录 JCR 网站，查询当前页面可见的最新信息。当前脚本默认使用可视化浏览器窗口，便于手动处理机构登录、验证码或安全验证；在你自己的环境中也可以按需要改成无头模式。

实时查询不会绕过访问控制。你仍然需要使用自己有权使用的机构或个人账号。

默认 public release 不附带任何完整的 JCR 原始分区文件。原因是这类数据文件可能有版权、数据库权利、平台条款、机构授权或再分发限制。如果你只是本地使用，可以把自己的多年份 JCR 文件放在 `data/jcr-local/` 或其他本地路径中；如果你确实要把数据文件发布到 GitHub，请先确认来源允许公开再分发，并在 `data/jcr-local/README.md` 中记录年份、来源、许可证、下载日期和校验信息。

运行 JCR 脚本时，它会先主动提醒你可以使用自己准备的本地 JCR 数据文件来节省实时查询时间。如果你选择不使用离线文件，脚本会继续打开 Playwright 浏览器进行实时查询。自动化运行时可以添加 `--skip-offline-reminder` 跳过这个提醒。

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

## 许可证

本项目采用 Apache License 2.0。版权所有 © 2026 bluessoul。使用、修改或分发本项目时，请保留 `LICENSE`、`NOTICE` 和版权声明，并注明原项目来源。

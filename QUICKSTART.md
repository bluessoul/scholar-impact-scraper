English version: [QUICKSTART.en.md](QUICKSTART.en.md)

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
- OpenAlex：可选 `OPENALEX_API_KEY`
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

### 5. 首次运行：保存网页登录状态

如果你要使用 Web of Science 或 JCR 实时查询，建议先运行登录助手：

```bash
python launch_browser_for_login.py
```

Windows 下的 JCR 登录助手：

```powershell
.\launch_jcr_login.bat
```

登录成功后关闭浏览器，状态会保存在 `.playwright_profile/`。不要提交或分享这个目录。核心脚本如果发现还没有 `.playwright_profile/`，会生成 `FIRST_RUN_LOGIN_SETUP.md` 提醒文件。

### 6. 运行 ORCID

Windows:

```powershell
.\.venv\Scripts\python orcid_extractor.py
```

macOS/Linux:

```bash
./.venv/bin/python orcid_extractor.py
```

### 7. 运行 JCR / 中科院分区

分区数据有三种使用方式：使用你自己准备的中科院分区本地文件、使用你自己准备的 JCR 本地文件，或使用你自己的 Clarivate/JCR 合法账号通过 Playwright 浏览器查询实时信息。默认 public release 不附带完整 JCR 或中科院分区原始文件；本地 JCR 文件可以放在 `data/jcr-local/`，本地中科院分区文件可以放在 `data/cas-local/`，但除非确认允许再分发，否则不要提交。

```bash
npm run fetch -- --input examples/jcr_input.example.json --output jcr_results.md
```

使用中科院本地分区：

```bash
npm run fetch -- --input examples/jcr_input.example.json --output cas_results.md --partition-source cas-local
```

使用 JCR 本地分区：

```bash
npm run fetch -- --input examples/jcr_input.example.json --output jcr_local_results.md --partition-source jcr-local
```

如果没有指定 `--partition-source`，交互式运行会主动询问使用中科院本地分区、JCR 本地分区、JCR 实时查询，还是跳过分区查询。无人值守运行时可显式指定来源：

```bash
npm run fetch -- --input examples/jcr_input.example.json --output jcr_results.md --partition-source jcr-live --skip-offline-reminder
```

`jcr_results.md` 是本地生成文件，分享前需要人工检查。

### 8. 运行 Scholar/WoS

```bash
python scholar_playwright.py --user-id <Scholar_ID> --wos-id <WoS_ID> --output output.csv --max-clicks 5
```

默认论文补全命令：

```bash
python scholar_playwright.py --user-id <Scholar_ID> --output output.csv --max-clicks 5 --output-sort publication-date
```

脚本默认会按顺序使用 Google Scholar 详情页、OpenAlex 和 Crossref 补全 DOI 与元数据，并尝试提取通讯作者。`--output-sort publication-date` 会让 CSV 和参考文献按最新发表日期优先排序；如果想保持原来的按引用数排序，可以省略它。

常用可选项：

```text
--citation-format apa,gbt2025
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

如果需要登录 Web of Science：

```bash
python launch_browser_for_login.py
```

`.playwright_profile/` 会保存本地登录状态，不能提交或分享。

### 9. 许可证

本项目使用 Apache License 2.0。版权所有 © 2026 bluessoul。使用、修改或分发本项目时，请保留 `LICENSE`、`NOTICE` 和版权声明，并注明原项目来源。

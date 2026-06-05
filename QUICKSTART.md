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

### 7. 运行 JCR

JCR 有两种使用方式：一种是使用你自己准备的网上公开分享的 JCR 2024 分区原始文件作为离线参考；另一种是使用你自己的 Clarivate/JCR 合法账号，通过 Playwright 自动化浏览器登录网站查询实时信息。当前脚本默认打开可视化浏览器，便于处理登录和验证码；如果你的环境适合，也可以自行改成无头模式。默认 public release 不附带完整 JCR 2024 原始文件；本地文件可以放在 `data/jcr2024/`，但除非确认允许再分发，否则不要提交。

```bash
npm run fetch -- --input examples/jcr_input.example.json --output jcr_results.md
```

脚本会先提醒你是否要暂停并寻找/使用本地 JCR 2024 离线文件。无人值守运行时可跳过提醒：

```bash
npm run fetch -- --input examples/jcr_input.example.json --output jcr_results.md --skip-offline-reminder
```

`jcr_results.md` 是本地生成文件，分享前需要人工检查。

### 8. 运行 Scholar/WoS

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

There are two JCR usage paths: use your own publicly shared JCR 2024 quartile raw-data file as an offline reference, or use your authorized Clarivate/JCR account with a Playwright automated browser to query live information from the website. The current scripts default to a visible browser window for login and verification; you can adapt the browser mode to headless in your own environment if appropriate. The public release does not bundle the full JCR 2024 raw file by default; local files can be placed under `data/jcr2024/`, but should not be committed unless redistribution is clearly allowed.

```bash
npm run fetch -- --input examples/jcr_input.example.json --output jcr_results.md
```

The script first asks whether you want to pause and use/find a local JCR 2024 offline file. For unattended runs, skip the prompt:

```bash
npm run fetch -- --input examples/jcr_input.example.json --output jcr_results.md --skip-offline-reminder
```

`jcr_results.md` is a generated local artifact and should be reviewed before sharing.

## 8. Run Scholar/WoS

```bash
python scholar_playwright.py --user-id <Scholar_ID> --wos-id <WoS_ID> --output output.csv --max-clicks 5
```

If Web of Science needs login:

```bash
python launch_browser_for_login.py
```

`.playwright_profile/` stores local login state. Do not commit or share it.

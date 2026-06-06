const fs = require('fs');
const path = require('path');
const readline = require('readline');
const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();

// Apply stealth evasions
chromium.use(stealth);

// Parse CLI arguments
const args = process.argv.slice(2);
const options = {
  input: null,
  journal: null,
  year: null,
  chromeData: null,
  profile: 'JCR Scraper', // Changed default to 'JCR Scraper'
  output: 'jcr_results.md',
  timeout: 30000,
  skipOfflineReminder: false,
  skipLoginReminder: false,
};

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--input' && args[i + 1]) {
    options.input = args[i + 1];
    i++;
  } else if (args[i] === '--journal' && args[i + 1]) {
    options.journal = args[i + 1];
    i++;
  } else if (args[i] === '--year' && args[i + 1]) {
    options.year = args[i + 1];
    i++;
  } else if (args[i] === '--chrome-data' && args[i + 1]) {
    options.chromeData = args[i + 1];
    i++;
  } else if (args[i] === '--profile' && args[i + 1]) {
    options.profile = args[i + 1];
    i++;
  } else if (args[i] === '--output' && args[i + 1]) {
    options.output = args[i + 1];
    i++;
  } else if (args[i] === '--timeout' && args[i + 1]) {
    options.timeout = parseInt(args[i + 1], 10);
    i++;
  } else if (args[i] === '--skip-offline-reminder' || args[i] === '--use-live-jcr') {
    options.skipOfflineReminder = true;
  } else if (args[i] === '--skip-login-reminder') {
    options.skipLoginReminder = true;
  }
}

// Auto-resolve --chrome-data if not specified
if (!options.chromeData && process.env.LOCALAPPDATA) {
  options.chromeData = path.join(process.env.LOCALAPPDATA, 'Google', 'Chrome', 'User Data');
}

// Verification artifact path (for CAPTCHA notification)
// Adapted for QClaw: Output to workspace root for easy access
const workspaceRoot = process.cwd();
const verificationArtifactPath = path.join(workspaceRoot, 'captcha_verification.md');
const jcrOfflineReminderPath = path.join(workspaceRoot, 'JCR_OFFLINE_DATA_OPTION.md');
const firstRunLoginSetupPath = path.join(workspaceRoot, 'FIRST_RUN_LOGIN_SETUP.md');

function isProfileLikelyInitialized(profileDir) {
  if (!fs.existsSync(profileDir)) return false;
  try {
    const entries = fs.readdirSync(profileDir);
    return entries.length > 0;
  } catch (err) {
    return false;
  }
}

function writeFirstRunLoginSetupArtifact(profileDir) {
  const content = `# First Run Login Setup\n\n` +
    `This project uses a local Playwright profile to save browser login state.\n\n` +
    `Profile directory:\n\n` +
    `\`${profileDir}\`\n\n` +
    `Recommended setup before live JCR or Web of Science lookup:\n\n` +
    `1. Run \`launch_jcr_login.bat\` for Clarivate/JCR login, or run \`python launch_browser_for_login.py\` for Web of Science login.\n` +
    `2. In the opened browser, log in with an institutional or personal account you are authorized to use.\n` +
    `3. Verify that the target platform works.\n` +
    `4. Close the browser window so cookies and session state are saved locally.\n\n` +
    `Do not commit or share \`.playwright_profile/\`, \`.env\`, or \`config.json\`.\n\n` +
    `To suppress this reminder, pass \`--skip-login-reminder\` where supported.\n\n` +
    `Timestamp: ${new Date().toLocaleString()}\n`;

  try {
    fs.writeFileSync(firstRunLoginSetupPath, content, 'utf8');
    console.log(`[First Run] Login setup artifact written to: ${firstRunLoginSetupPath}`);
  } catch (err) {
    console.error('[First Run] Failed to write login setup artifact:', err.message);
  }
}

function remindFirstRunLoginSetup(profileDir) {
  if (options.skipLoginReminder || process.env.SKIP_LOGIN_REMINDER === '1') {
    return;
  }
  if (isProfileLikelyInitialized(profileDir)) {
    return;
  }

  console.log('\n' + '='.repeat(80));
  console.log('[First Run Login Setup]');
  console.log('No existing .playwright_profile was detected.');
  console.log('For live JCR or Web of Science lookup, log in once through the browser');
  console.log('so cookies and session state can be saved locally.');
  console.log('');
  console.log('Recommended helpers:');
  console.log('  - JCR: launch_jcr_login.bat');
  console.log('  - Web of Science: python launch_browser_for_login.py');
  console.log('');
  console.log('The current script can still continue and will open a browser if needed.');
  console.log('Do not commit or share .playwright_profile/.');
  console.log('='.repeat(80) + '\n');

  writeFirstRunLoginSetupArtifact(profileDir);
}

function writeJcrOfflineReminderArtifact() {
  const content = `# Local JCR Data Option\n\n` +
    `Before launching Playwright for live Clarivate/JCR lookup, you may be able to save time by using a user-provided local JCR quartile raw-data file for the relevant year.\n\n` +
    `Suggested workflow:\n\n` +
    `1. Prepare a JCR quartile/partition raw-data file for the year you need.\n` +
    `2. Verify that the source allows your intended use and redistribution, if any.\n` +
    `3. Place the local file under \`data/jcr-local/\` or another local path.\n` +
    `4. Do not commit the raw data file unless redistribution is clearly allowed.\n\n` +
    `If you do not want to use an offline file, continue with live lookup. The script will open a Playwright browser and use your authorized Clarivate/JCR access.\n\n` +
    `To skip this reminder in automation, pass \`--skip-offline-reminder\` or set \`JCR_SKIP_OFFLINE_REMINDER=1\`.\n\n` +
    `Timestamp: ${new Date().toLocaleString()}\n`;

  try {
    fs.writeFileSync(jcrOfflineReminderPath, content, 'utf8');
    console.log(`[JCR Offline Option] Reminder artifact written to: ${jcrOfflineReminderPath}`);
  } catch (err) {
    console.error('[JCR Offline Option] Failed to write reminder artifact:', err.message);
  }
}

async function promptJcrOfflineDataOption() {
  if (options.skipOfflineReminder || process.env.JCR_SKIP_OFFLINE_REMINDER === '1') {
    return true;
  }

  console.log('\n' + '='.repeat(80));
  console.log('[Local JCR Data Option]');
  console.log('You may save time by using a local JCR quartile/partition raw-data file.');
  console.log('Prepare a file for the target JCR year, verify permission,');
  console.log('then place it under data/jcr-local/ or another local path.');
  console.log('');
  console.log('If you choose live lookup, this script will continue with Playwright and your');
  console.log('authorized Clarivate/JCR account. Live lookup does not bypass access control.');
  console.log('='.repeat(80) + '\n');

  writeJcrOfflineReminderArtifact();

  if (!process.stdin.isTTY || !process.stdout.isTTY) {
    console.log('[JCR Offline Option] Non-interactive terminal detected; continuing with live Playwright lookup.');
    console.log('[JCR Offline Option] Use --skip-offline-reminder to suppress this message.\n');
    return true;
  }

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  const answer = await new Promise(resolve => {
    rl.question('Do you want to pause now and use/find a local JCR data file? (y/N): ', resolve);
  });
  rl.close();

  const normalized = String(answer || '').trim().toLowerCase();
  if (normalized === 'y' || normalized === 'yes') {
    console.log('\n[JCR Offline Option] Stopping before browser launch.');
    console.log('[JCR Offline Option] Put your local JCR data file under data/jcr-local/ or another local path.');
    console.log('[JCR Offline Option] Re-run with --skip-offline-reminder when you want to proceed with live lookup.\n');
    return false;
  }

  console.log('\n[JCR Offline Option] Continuing with live Playwright lookup.\n');
  return true;
}

function writeVerificationArtifact() {
  // Console output - eye-catching alert for QClaw userr
  console.log('\n' + '='.repeat(80));
  console.log('[⚠️ 待办提示] CAPTCHA 验证 required！');
  console.log('='.repeat(80) + '\n');
  
  const content = `# ⚠️ CAPTCHA Verification Required ⚠️\n\n` +
    `Clarivate JCR has presented a security challenge (CAPTCHA, Geetest, or Cloudflare verification).\n\n` +
    `### Instructions:\n` +
    `1. Look at the opened Google Chrome browser window.\n` +
    `2. **Manually complete the CAPTCHA slider, checkbox, or challenge** on the page.\n` +
    `3. Do not close the browser window.\n` +
    `4. Once completed and you are redirected to the JCR page, **this script will automatically detect the success state and resume!**\n\n` +
    `*Timestamp: ${new Date().toLocaleString()}*\n` +
    `*Status: Waiting for user completion...*\n`;
  try {
    fs.writeFileSync(verificationArtifactPath, content, 'utf8');
    console.log(`[Human-in-the-Loop] Verification artifact created at: ${verificationArtifactPath}`);
    console.log(`[⚠️ 待办提示] 请在打开的 Chrome 浏览器窗口中完成 CAPTCHA 验证！`);
    console.log(`[⚠️ 待办提示] 验证文件已保存到: ${verificationArtifactPath}\n`);
  } catch (err) {
    console.error('Failed to write verification artifact:', err.message);
  }
}

function removeVerificationArtifact() {
  try {
    if (fs.existsSync(verificationArtifactPath)) {
      fs.unlinkSync(verificationArtifactPath);
      console.log('[Human-in-the-Loop] CAPTCHA solved! Verification artifact removed.');
    }
  } catch (err) {
    console.error('Failed to remove verification artifact:', err.message);
  }
}

function loadConfigJson() {
  const configPath = path.join(process.cwd(), 'config.json');
  if (fs.existsSync(configPath)) {
    try {
      const content = fs.readFileSync(configPath, 'utf8');
      const config = JSON.parse(content);
      if (config.CLARIVATE_EMAIL) {
        process.env.CLARIVATE_EMAIL = config.CLARIVATE_EMAIL;
      } else if (config.email) {
        process.env.CLARIVATE_EMAIL = config.email;
      }
      if (config.CLARIVATE_PASSWORD) {
        process.env.CLARIVATE_PASSWORD = config.CLARIVATE_PASSWORD;
      } else if (config.password) {
        process.env.CLARIVATE_PASSWORD = config.password;
      }
      console.log('[Config] Loaded credentials from config.json successfully.');
    } catch (e) {
      console.error('[Config] Error reading config.json file:', e.message);
    }
  }
}

function loadEnvFile() {
  const envPath = path.join(process.cwd(), '.env');
  if (fs.existsSync(envPath)) {
    try {
      const content = fs.readFileSync(envPath, 'utf8');
      const lines = content.split('\n');
      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed && !trimmed.startsWith('#') && trimmed.includes('=')) {
          const firstEquals = trimmed.indexOf('=');
          const key = trimmed.substring(0, firstEquals).trim();
          const value = trimmed.substring(firstEquals + 1).trim().replace(/^['"]|['"]$/g, '');
          process.env[key] = value;
        }
      }
      console.log('[Config] Loaded environment variables from .env file successfully.');
    } catch (e) {
      console.error('[Config] Error reading .env file:', e.message);
    }
  }
}

function normalizeJournalName(name) {
  if (!name) return '';
  if (/^\d{4}-\d{3}[\dX]$/i.test(name.trim())) {
    return name.trim();
  }
  return name
    .toUpperCase()
    .replace(/:\s*/g, '-')      // replace colon and following spaces with hyphen
    .replace(/\s+&\s+/g, ' AND ') // replace & with AND
    .replace(/\s+/g, ' ')       // compress whitespace
    .trim();
}

function getSearchCandidates(name) {
  if (!name) return [];
  const trimmed = name.trim();
  if (/^\d{4}-\d{3}[\dX]$/i.test(trimmed)) {
    return [trimmed];
  }
  
  const candidates = [];
  const normalized = normalizeJournalName(trimmed);
  candidates.push(normalized);
  
  const upperRaw = trimmed.toUpperCase();
  if (upperRaw !== normalized) {
    candidates.push(upperRaw);
  }
  
  if (trimmed !== upperRaw && trimmed !== normalized) {
    candidates.push(trimmed);
  }
  
  if (trimmed.includes(':')) {
    const prefix = trimmed.split(':')[0].trim().toUpperCase();
    if (prefix.length >= 6) {
      candidates.push(prefix);
    }
  } else if (trimmed.includes('-')) {
    const prefix = trimmed.split('-')[0].trim().toUpperCase();
    if (prefix.length >= 6) {
      candidates.push(prefix);
    }
  }
  
  return Array.from(new Set(candidates));
}

function isMatchingJournalText(linkText, queryCandidates) {
  if (!linkText) return false;
  const normalizedLink = linkText.toUpperCase()
    .replace(/[^A-Z0-9]/g, '')
    .trim();
    
  for (const candidate of queryCandidates) {
    const normalizedCandidate = candidate.toUpperCase()
      .replace(/[^A-Z0-9]/g, '')
      .trim();
      
    if (normalizedLink === normalizedCandidate) return true;
    
    if (normalizedCandidate.length >= 10 && (normalizedLink.startsWith(normalizedCandidate) || normalizedCandidate.startsWith(normalizedLink))) {
      return true;
    }
  }
  return false;
}

async function dismissOneTrust(page) {
  try {
    await page.evaluate(() => {
      const sdk = document.getElementById('onetrust-consent-sdk');
      if (sdk) sdk.remove();
      const banner = document.getElementById('onetrust-banner-sdk');
      if (banner) banner.remove();
      const filter = document.querySelector('.onetrust-pc-dark-filter');
      if (filter) filter.remove();
      document.body.classList.remove('onetrust-hide-scroll');
    });
  } catch (e) {}
}

async function handleCaptcha(page) {
  try {
    await dismissOneTrust(page);
    let isCloudflare = false;
    let isGeetest = false;

    try {
      isCloudflare = await page.evaluate(() => {
        return document.title.includes('Just a moment') || 
               document.body.innerText.includes('Verify you are human') ||
               !!document.querySelector('iframe[src*="turnstile"]') ||
               !!document.querySelector('#challenge-stage');
      });
    } catch (e) {
      // Ignored: Navigation destroyed context during check
    }

    try {
      isGeetest = await page.evaluate(() => {
        return !!document.querySelector('.geetest_holder') || 
               !!document.querySelector('.captcha') ||
               document.body.innerText.includes('security check');
      });
    } catch (e) {
      // Ignored: Navigation destroyed context during check
    }

    if (isCloudflare || isGeetest) {
      console.log('\n[⚠️ WARNING] Cloudflare or Geetest CAPTCHA detected!');
      writeVerificationArtifact();
      
      let solved = false;
      const startTime = Date.now();
      
      while (!solved) {
        let hasDashboard = false;
        try {
          hasDashboard = await page.evaluate(() => {
            return !!document.querySelector('input[placeholder*="Search"]') || 
                   !!document.querySelector('.search-input') ||
                   !!document.querySelector('#search-input') ||
                   !!document.querySelector('.journal-profile-header') ||
                   document.body.innerText.includes('Journal Citation Reports');
          });
        } catch (e) {
          // Ignored: Navigation context changed
        }

        if (hasDashboard) {
          solved = true;
          break;
        }

        if (page.isClosed()) {
          console.log('[Error] Browser page was closed by the user.');
          process.exit(1);
        }

        await page.waitForTimeout(2000);
        const elapsedMinutes = ((Date.now() - startTime) / 60000).toFixed(1);
        console.log(`[Human-in-the-Loop] Still waiting for captcha completion... (${elapsedMinutes}m elapsed)`);
      }

      removeVerificationArtifact();
      console.log('[Success] CAPTCHA successfully bypassed!');
    }
  } catch (err) {
    // Ignored: Context destroyed globally during navigation
  }
}

async function handleLogin(page) {
  // ⚠️ 安全提示：请从环境变量读取凭据，不要硬编码！
  // 设置方法 (PowerShell):
  //   $env:CLARIVATE_EMAIL="your_email@institution.edu"
  //   $env:CLARIVATE_PASSWORD="your_password"
  const CREDENTIALS = {
    email: process.env.CLARIVATE_EMAIL || '',
    password: process.env.CLARIVATE_PASSWORD || ''
  };

  // 检查是否配置了凭据
  if (!CREDENTIALS.email || !CREDENTIALS.password) {
    console.log('\n' + '='.repeat(80));
    console.log('[⚠️ 待办提示] Clarivate 登录页面检测到，但未配置自动登录凭据！');
    console.log('='.repeat(80));
    console.log('\n请在打开的 Chrome 浏览器窗口中手动完成登录：');
    console.log('  1. 输入您的 Clarivate 账号和密码');
    console.log('  2. 完成可能的 CAPTCHA 验证');
    console.log('  3. 登录成功后，脚本将自动继续\n');
    console.log('[提示] 如需自动登录，请设置环境变量：');
    console.log('  $env:CLARIVATE_EMAIL="your_email@institution.edu"');
    console.log('  $env:CLARIVATE_PASSWORD="your_password"\n');
  }

  let isLoginPage = false;
  try {
    isLoginPage = await page.evaluate(() => {
      const url = window.location.href;
      return url.includes('clarivate.com') && (
        url.includes('login') || 
        url.includes('signin') || 
        !!document.querySelector('input[type="password"]')
      );
    });
  } catch (e) {
    // Ignored: Navigation context destroyed during page transition
  }

  if (isLoginPage) {
    if (CREDENTIALS.email && CREDENTIALS.password) {
      console.log('[Login Detector] Clarivate Login page detected! Attempting automatic login...');
    }
    
    try {
      await page.screenshot({ path: 'jcr_login_page.png' });
      console.log('[Diagnostic] Login page screenshot saved as "jcr_login_page.png".');
    } catch (e) {}

    try {
      await page.waitForSelector('input[type="password"]', { timeout: 15000 });
    } catch (e) {
      console.log('[Login Detector] Warning: Password input not found yet. Proceeding with scan...');
    }

    if (CREDENTIALS.email && CREDENTIALS.password) {
      // 自动登录流程
      try {
        let emailInput = null;
        const emailSelectors = [
          'input[type="email"]',
          'input[name="email"]',
          'input#email',
          'input#emailAddress',
          'input[name="emailAddress"]',
          'input[name="username"]',
          'input#username',
          'input[formcontrolname="username"]',
          'input[formcontrolname="email"]',
          'input[placeholder*="email" i]',
          'input[placeholder*="username" i]',
          'input[placeholder*="Email" i]',
          'input[placeholder*="Sign in" i]',
          'input[type="text"]'
        ];

        for (const sel of emailSelectors) {
          const el = await page.$(sel);
          if (el && await el.isVisible()) {
            emailInput = el;
            console.log(`[Login] Found email input using selector: "${sel}"`);
            break;
          }
        }

        if (!emailInput) {
          try {
            emailInput = page.getByLabel(/Email address/i).first();
            if (await emailInput.count() > 0) {
              console.log('[Login] Found email input via getByLabel');
            } else {
              emailInput = null;
            }
          } catch (e) {
            emailInput = null;
          }
        }

        let passwordInput = null;
        const passwordSelectors = [
          'input[type="password"]',
          'input[name="password"]',
          'input#password',
          'input[formcontrolname="password"]',
          'input[placeholder*="password" i]'
        ];

        for (const sel of passwordSelectors) {
          const el = await page.$(sel);
          if (el && await el.isVisible()) {
            passwordInput = el;
            console.log(`[Login] Found password input using selector: "${sel}"`);
            break;
          }
        }

        if (!passwordInput) {
          try {
            passwordInput = page.getByLabel(/Password/i).first();
            if (await passwordInput.count() > 0) {
              console.log('[Login] Found password input via getByLabel');
            } else {
              passwordInput = null;
            }
          } catch (e) {
            passwordInput = null;
          }
        }

        if (emailInput && passwordInput) {
          console.log('[Login] Filling credentials...');
          
          await emailInput.click();
          await emailInput.fill(CREDENTIALS.email);
          await page.waitForTimeout(500);

          await passwordInput.click();
          await passwordInput.fill(CREDENTIALS.password);
          await page.waitForTimeout(500);

          let signInBtn = null;
          try {
            const loc = page.locator('button, input[type="submit"], [role="button"]').filter({ hasText: /Sign in|SignIn|Log in|登录/i }).first();
            if (await loc.count() > 0 && await loc.isVisible()) {
              signInBtn = loc;
              console.log('[Login] Found sign-in button using filter on buttons/inputs');
            }
          } catch (e) {
            console.log('[Login] Button filter check note:', e.message);
          }

          if (!signInBtn) {
            const btnSelectors = [
              'button[type="submit"]',
              'button.mat-flat-button',
              'input[type="submit"]',
              '.signin-btn',
              'button',
              'input'
            ];

            for (const sel of btnSelectors) {
              try {
                const btns = await page.$$(sel);
                for (const btn of btns) {
                  const txt = (await btn.innerText()).trim();
                  const val = (await btn.getAttribute('value') || '').trim();
                  const combined = (txt + ' ' + val).toLowerCase();
                  if (combined.includes('sign in') || combined.includes('signin') || combined.includes('log in') || combined.includes('登录')) {
                    signInBtn = btn;
                    console.log(`[Login] Found sign-in button using selector: "${sel}" with text/value: "${txt || val}"`);
                    break;
                  }
                }
                if (signInBtn) break;
              } catch (e) {}
            }
          }

          if (!signInBtn) {
            try {
              signInBtn = page.getByRole('button', { name: /Sign in/i }).first();
              if (await signInBtn.count() > 0) {
                console.log('[Login] Found sign-in button via getByRole');
              } else {
                signInBtn = null;
              }
            } catch (e) {
              signInBtn = null;
            }
          }

          if (signInBtn) {
            console.log('[Login] Clicking sign-in button...');
            await signInBtn.click();
            await page.waitForTimeout(5000);
            await handleCaptcha(page);
          } else {
            console.error('[Login] Error: Could not find sign-in button!');
          }
        } else {
          console.error('[Login] Error: Email or password inputs not found!');
          try {
            await page.screenshot({ path: 'jcr_login_failed_diagnostic.png' });
            console.log('[Diagnostic] Login failed screenshot saved as "jcr_login_failed_diagnostic.png".');
          } catch (e) {}
        }

      } catch (loginErr) {
        console.error('[Login] Error during automatic login execution:', loginErr.message);
      }
    } else {
      // 手动登录流程（未配置凭据时）
      console.log('\n[Login] 未配置自动登录凭据，等待手动登录...\n');
      
      const startTime = Date.now();
      const maxWaitTime = 300000; // 最多等待 5 分钟
      
      while (Date.now() - startTime < maxWaitTime) {
        let isLoggedIn = false;
        try {
          isLoggedIn = await page.evaluate(() => {
            const url = window.location.href;
            return !url.includes('login') && !url.includes('signin') &&
                   (!!document.querySelector('input[placeholder*="Search"]') || 
                    !!document.querySelector('.search-input') ||
                    !!document.querySelector('#search-input') ||
                    !!document.querySelector('.journal-profile-header'));
          });
        } catch (e) {
          // Ignored: Navigation context destroyed during page transition, retry on next loop
        }
        
        if (isLoggedIn) {
          console.log('\n[Success] 登录成功检测！脚本将继续执行...\n');
          return;
        }
        
        if (page.isClosed()) {
          console.log('[Error] 浏览器页面已被用户关闭。');
          process.exit(1);
        }
        
        await page.waitForTimeout(2000);
        const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
        if (elapsedSeconds % 10 === 0) {
          console.log(`[Login] 仍在等待登录完成... (已等待 ${elapsedSeconds} 秒)`);
        }
      }
      
      console.log('\n[Warning] 登录等待超时。继续执行，但可能会失败...\n');
    }
  } else {
    console.log('[Login Detector] No active login page detected. Proceeding...');
  }
}

function writeMarkdownOutput(outputPath, results) {
  let markdown = '# JCR Historical Fetcher Results\n\n';
  markdown += 'Generated on: **' + new Date().toLocaleString() + '**\n\n';
  markdown += '| Journal Name / ISSN | JCR Year | Subject Category | Rank in Category | JIF Quartile | JIF Percentile | Journal Impact Factor (JIF) | 5-Year Impact Factor | Status |\n';
  markdown += '| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n';

  for (const item of results) {
    if (item.error) {
      markdown += '| ' + item.journal + ' | ' + item.year + ' | N/A | N/A | N/A | N/A | N/A | N/A | ❌ Error: ' + item.error + ' |\n';
      continue;
    }

    const categories = (item.categories || 'N/A').split('; ').map(s => s.trim());
    const ranks = (item.rank || 'N/A').split('; ').map(s => s.trim());
    const quartiles = (item.quartile || 'N/A').split('; ').map(s => s.trim());
    const percentiles = (item.percentile || 'N/A').split('; ').map(s => s.trim());
    const jif = item.journalImpactFactor || 'N/A';
    const fiveYearJif = item.fiveYearJIF || 'N/A';

    const rowCount = Math.max(categories.length, ranks.length, quartiles.length, percentiles.length);

    for (let i = 0; i < rowCount; i++) {
      const cleanField = (s) => (s || '').replace(/\s*[\r\n]+\s*/g, ' ').trim();
      const category = cleanField(categories[i] || 'N/A');
      const rank = cleanField(ranks[i] || 'N/A');
      const quartile = cleanField(quartiles[i] || 'N/A');
      const percentile = cleanField(percentiles[i] || 'N/A');
      
      let displayQuartile = quartile;
      const pctValue = parseFloat(percentile.replace('%', '').trim());
      if (!isNaN(pctValue) && pctValue >= 90.00) {
        if (displayQuartile.toUpperCase() === 'Q1') {
          displayQuartile = 'Q1 (D1)';
        } else {
          displayQuartile = displayQuartile + ' (D1)';
        }
      }
      
      markdown += '| ' + item.journal + ' | ' + item.year + ' | ' + category + ' | ' + rank + ' | ' + displayQuartile + ' | ' + percentile + ' | ' + jif + ' | ' + fiveYearJif + ' | Success |\n';
    }
  }

  try {
    fs.writeFileSync(outputPath, markdown, 'utf8');
    console.log('[Success] Results successfully saved to: ' + path.resolve(outputPath));
  } catch (err) {
    console.error('Failed to write output results: ' + err.message);
  }
}

async function fetchSingleJournal(page, context, journal_name_or_issn, publication_year, options) {
  let profilePage = page;
  
  // Go to JCR Home
  console.log(`Navigating to JCR Home: https://jcr.clarivate.com/jcr/home ...`);
  await page.goto('https://jcr.clarivate.com/jcr/home', { waitUntil: 'load', timeout: options.timeout });
  
  // Save diagnostic screenshot
  try {
    await page.screenshot({ path: 'jcr_home_loaded.png' });
    console.log('[Diagnostic] Screenshot saved as "jcr_home_loaded.png".');
  } catch (e) {
    console.log('[Diagnostic] Failed to save homepage screenshot:', e.message);
  }

  // Wait for either search interface or login page to appear
  console.log('Waiting for JCR home page or login page to load...');
  const startWaitTime = Date.now();
  let mode = 'unknown'; // 'home', 'login', or 'timeout'
  
  while (Date.now() - startWaitTime < 45000) { // wait up to 45 seconds
    let state = 'waiting';
    try {
      state = await page.evaluate(() => {
        const url = window.location.href;
        if (url.includes('clarivate.com') && (url.includes('login') || url.includes('signin') || !!document.querySelector('input[type="password"]'))) {
          return 'login';
        }
        const searchInput = document.querySelector('input[placeholder*="Journal"], input[placeholder*="Search"], input.search-input, input#search-input');
        if (searchInput && searchInput.offsetWidth > 0 && searchInput.offsetHeight > 0) {
          return 'home';
        }
        return 'waiting';
      });
    } catch (e) {
      // Ignored: Navigation context destroyed during page transition, retry on next loop
    }

    if (state === 'login') {
      mode = 'login';
      break;
    } else if (state === 'home') {
      mode = 'home';
      break;
    }
    
    // Handle CAPTCHA if it appears
    await handleCaptcha(page);
    
    await page.waitForTimeout(1500);
  }

  console.log(`[Detector] Initial page state determined as: "${mode}"`);

  if (mode === 'login') {
    await handleLogin(page);
    
    // After login, wait again for home page to load
    console.log('Waiting for JCR home page to load after login...');
    const postLoginStart = Date.now();
    while (Date.now() - postLoginStart < 45000) {
      let isHome = false;
      try {
        isHome = await page.evaluate(() => {
          const searchInput = document.querySelector('input[placeholder*="Journal"], input[placeholder*="Search"], input.search-input, input#search-input');
          return !!(searchInput && searchInput.offsetWidth > 0 && searchInput.offsetHeight > 0);
        });
      } catch (e) {
        // Ignored: Navigation context destroyed during page transition, retry on next loop
      }
      if (isHome) {
        mode = 'home';
        break;
      }
      
      // Check for CAPTCHA if it appears during/after login redirection
      await handleCaptcha(page);
      
      await page.waitForTimeout(1500);
    }
  }

  // Check if search input is visible on home page
  let searchInput = null;
  const searchSelectors = [
    'input[placeholder*="Journal"]:visible',
    'input[placeholder*="ISSN"]:visible',
    'input[placeholder*="category"]:visible',
    'input[placeholder*="Search"]:visible',
    'input.search-input:visible',
    'input#search-input:visible',
    'input[type="search"]:visible',
    'input[role="combobox"]:visible'
  ];

  const combinedSearchSelector = searchSelectors.join(', ');
  try {
    await page.waitForSelector(combinedSearchSelector, { state: 'visible', timeout: 15000 });
    for (const selector of searchSelectors) {
      const el = await page.$(selector);
      if (el && await el.isVisible()) {
        searchInput = el;
        console.log(`[Success] Found visible search input using selector: "${selector}"`);
        break;
      }
    }
  } catch (e) {
    console.log('[Diagnostic] Timeout waiting for search interface to become visible.');
  }

  if (!searchInput) {
    console.error('[Error] Search box is not accessible. Skipping this journal.');
    return {
      journal: journal_name_or_issn,
      year: publication_year,
      categories: 'N/A',
      rank: 'N/A',
      quartile: 'N/A',
      percentile: 'N/A',
      journalImpactFactor: 'N/A',
      fiveYearJIF: 'N/A',
      error: 'Search box not found/inaccessible'
    };
  }

  // Enter search term with multi-stage JCR candidate support
  const searchCandidates = getSearchCandidates(journal_name_or_issn);
  console.log(`[Search Engine] Generated search candidates: ${JSON.stringify(searchCandidates)}`);
  
  let suggestionFound = false;

  for (let c = 0; c < searchCandidates.length; c++) {
    const candidate = searchCandidates[c];
    console.log(`[Search Step] Attempt ${c + 1}/${searchCandidates.length}: Typing "${candidate}"...`);
    
    await searchInput.click({ force: true });
    await page.keyboard.press('Control+A');
    await page.keyboard.press('Backspace');
    
    // Type candidate sequentially to trigger JCR input events reliably
    await page.keyboard.type(candidate, { delay: 10 });
    await page.waitForTimeout(3000); // Allow autocompletion and network requests to finish
    
    // Attempt evaluation inside browser context to click suggestion elements (handles custom structures)
    try {
      const clicked = await page.evaluate((candidates) => {
        const elements = Array.from(document.querySelectorAll('span, div, a, li, mat-option, [role="option"]'));
        
        // 1. Look specifically for "See 1 result" or similar link first, as it is the most reliable navigation trigger!
        const seeResult = elements.find(el => {
          const rect = el.getBoundingClientRect();
          if (rect.width === 0 || rect.height === 0) return false;
          const text = (el.innerText || '').trim().toLowerCase();
          return text.includes('see') && text.includes('result');
        });
        
        if (seeResult) {
          const eventOpts = { bubbles: true, cancelable: true, view: window };
          seeResult.dispatchEvent(new MouseEvent('mousedown', eventOpts));
          seeResult.dispatchEvent(new MouseEvent('mouseup', eventOpts));
          seeResult.dispatchEvent(new MouseEvent('click', eventOpts));
          return { success: true, method: 'seeResultLink', text: seeResult.innerText };
        }
        
        // 2. Look for the actual autocomplete option container (e.g. mat-option or parent list item)
        const targets = elements.filter(el => {
          const rect = el.getBoundingClientRect();
          if (rect.width === 0 || rect.height === 0) return false;
          if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') return false;
          
          const text = (el.innerText || '').trim();
          if (!text || text.length > 150) return false;
          
          const upperText = text.toUpperCase();
          return candidates.some(c => {
            const upperCand = c.toUpperCase();
            return upperText === upperCand || 
                   (upperText.includes(upperCand) && upperText.length < upperCand.length + 30);
          });
        });
        
        if (targets.length > 0) {
          targets.sort((a, b) => {
            const rectA = a.getBoundingClientRect();
            const rectB = b.getBoundingClientRect();
            return (rectA.width * rectA.height) - (rectB.width * rectB.height);
          });
          
          // Let's traverse up to 4 levels to find a mat-option or option container
          let bestEl = targets[0];
          let parent = targets[0];
          for (let i = 0; i < 4 && parent; i++) {
            const tag = parent.tagName.toLowerCase();
            const role = parent.getAttribute('role') || '';
            const className = parent.className || '';
            if (tag === 'mat-option' || role === 'option' || className.includes('option') || className.includes('item') || className.includes('result')) {
              bestEl = parent;
              break;
            }
            parent = parent.parentElement;
          }
          
          const eventOpts = { bubbles: true, cancelable: true, view: window };
          bestEl.dispatchEvent(new MouseEvent('mousedown', eventOpts));
          bestEl.dispatchEvent(new MouseEvent('mouseup', eventOpts));
          bestEl.dispatchEvent(new MouseEvent('click', eventOpts));
          return { success: true, method: 'nameMatch', text: bestEl.innerText };
        }
        
        return { success: false };
      }, searchCandidates);
      
      if (clicked && clicked.success) {
        console.log(`[Success] Suggestion matched and clicked inside browser via ${clicked.method}: "${clicked.text}"`);
        suggestionFound = true;
        break;
      }
    } catch (evalErr) {
      console.log(`[Warning] Suggestion click evaluator error: ${evalErr.message}`);
    }
    
    // Selector-based backup option
    const suggestionSelectors = [
      '.mat-option',
      'mat-option',
      '.autocomplete-result',
      '[role="option"]',
      '.suggestion-item'
    ];
    for (const selector of suggestionSelectors) {
      try {
        const suggestions = await page.$$(selector);
        if (suggestions.length > 0) {
          let bestSuggestion = null;
          for (const suggestion of suggestions) {
            const sugText = (await suggestion.innerText()).trim();
            if (isMatchingJournalText(sugText, searchCandidates)) {
              bestSuggestion = suggestion;
              break;
            }
          }
          if (!bestSuggestion && c === searchCandidates.length - 1) {
            bestSuggestion = suggestions[0];
          }
          if (bestSuggestion) {
            console.log(`[Success] Clicking selector-based suggestion: "${await bestSuggestion.innerText()}"`);
            await bestSuggestion.click({ force: true });
            suggestionFound = true;
            break;
          }
        }
      } catch (e) {}
    }
    
    if (suggestionFound) {
      break;
    } else {
      console.log(`[Search Step] Candidate "${candidate}" did not yield a matching suggestion.`);
    }
  }

  // Ultimate Navigation Check: if suggestion clicked but didn't trigger navigation, force search!
  await page.waitForTimeout(3000);
  const postClickUrl = page.url();
  const dropdownStillOpen = await page.evaluate(() => {
    const dropdown = document.querySelector('.mat-autocomplete-panel, .autocomplete-panel, .dropdown-menu, .suggestion-box, [role="listbox"]');
    if (dropdown) {
      const rect = dropdown.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0;
    }
    const seeResult = Array.from(document.querySelectorAll('*')).find(el => {
      return (el.innerText || '').toLowerCase().includes('see') && (el.innerText || '').toLowerCase().includes('result');
    });
    if (seeResult) {
      const rect = seeResult.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0;
    }
    return false;
  });

  if (suggestionFound && (postClickUrl.includes('/jcr/home') && !postClickUrl.includes('search-results') && !postClickUrl.includes('journal-profile') || dropdownStillOpen)) {
    console.log('[Warning] Suggestion click executed but page did not navigate and dropdown is still open. Trying keyboard ArrowDown + Enter fallback...');
    try {
      await searchInput.click({ force: true });
      await page.keyboard.press('ArrowDown');
      await page.waitForTimeout(500);
      await page.keyboard.press('Enter');
      console.log('[Keyboard Fallback] Dispatched ArrowDown and Enter keypresses to force autocomplete selection!');
      await page.waitForTimeout(4000);
    } catch (keyErr) {
      console.log(`[Warning] Keyboard fallback failed: ${keyErr.message}`);
    }
    
    // Check again if we navigated
    const newUrl = page.url();
    if (newUrl.includes('/jcr/home') && !newUrl.includes('search-results') && !newUrl.includes('journal-profile')) {
      console.log('[Warning] Keyboard fallback did not trigger navigation. Bypassing click block to force search...');
      suggestionFound = false; // Reset to false to trigger the fallback search force!
    } else {
      console.log('[Success] Keyboard fallback successfully triggered navigation!');
      suggestionFound = true;
    }
  }

  if (!suggestionFound) {
    const defaultSearchTerm = searchCandidates[0] || journal_name_or_issn;
    console.log(`[Fallback] Suggestion dropdown not detected or failed to navigate. Pressing Enter to force search for "${defaultSearchTerm}"...`);
    await searchInput.click({ force: true });
    await page.keyboard.press('Control+A');
    await page.keyboard.press('Backspace');
    await page.keyboard.type(defaultSearchTerm, { delay: 10 });
    await page.waitForTimeout(1000);
    await searchInput.press('Enter');
    
    // Proactively click any search button / magnifying glass icon nearby if we remain on the same page
    await page.waitForTimeout(2000);
    const currentUrl = page.url();
    if (currentUrl.includes('/jcr/home') && !currentUrl.includes('search-results') && !currentUrl.includes('journal-profile')) {
      console.log('[Fallback] Search still pending on homepage. Finding nearby magnifying glass button...');
      await page.evaluate(() => {
        const input = document.querySelector('input[placeholder*="Journal"], input[placeholder*="Search"]');
        if (input) {
          let sibling = input.nextElementSibling;
          while (sibling) {
            if (sibling.tagName === 'BUTTON' || sibling.querySelector('svg') || sibling.innerText.includes('search') || sibling.className.includes('search')) {
              sibling.click();
              return;
            }
            sibling = sibling.nextElementSibling;
          }
          const parent = input.parentElement;
          if (parent) {
            const btns = Array.from(parent.querySelectorAll('button, [role="button"], mat-icon'));
            const searchBtn = btns.find(b => {
              const rect = b.getBoundingClientRect();
              return rect.width > 0 && rect.height > 0 && (b.innerText.toLowerCase().includes('search') || b.querySelector('svg') || b.className.includes('search') || b.className.includes('icon'));
            });
            if (searchBtn) {
              searchBtn.click();
              return;
            }
          }
        }
      });
    }
  }

  await page.waitForTimeout(4000);

  // Check if we landed on search results page instead of directly on the profile
  if (page.url().includes('search-results')) {
    console.log('Search results page detected. Waiting for table or results to render...');
    
    // Wait up to 15 seconds for a cell or table to appear
    const searchResultsSelectors = [
      '.table-cell-journalName:visible',
      'mat-cell.mat-column-journalName:visible',
      'mat-table:visible',
      'table:visible',
      '[role="grid"]:visible',
      '.mat-row:visible',
      'mat-row:visible'
    ];
    
    const combinedSearchResultsSelector = searchResultsSelectors.join(', ');
    try {
      await page.waitForSelector(combinedSearchResultsSelector, { state: 'visible', timeout: 15000 });
      console.log('[Success] Search results table loaded!');
    } catch (e) {
      console.log('[Warning] Timeout waiting for search results table to load. Scanning DOM anyway...');
    }
    
    try {
      await page.screenshot({ path: 'jcr_search_results.png' });
      console.log('[Diagnostic] Screenshot of search results saved as "jcr_search_results.png".');
    } catch (e) {
      console.log('[Diagnostic] Failed to save search results screenshot:', e.message);
    }

    // Diagnostic DOM Dump
    try {
      const domDump = await page.evaluate(() => {
        const container = document.querySelector('app-search-results, mat-table, table, .mat-table, [role="grid"], body');
        if (!container) return 'No search results container found';
        const elements = Array.from(container.querySelectorAll('a, button, span, div, mat-cell, .mat-cell, td, th'));
        return elements.map(el => {
          const text = (el.innerText || '').trim();
          if (text.length > 0 && text.length < 80) {
            return `<${el.tagName} class="${el.className}" role="${el.getAttribute('role') || ''}" href="${el.getAttribute('href') || ''}">${text}</${el.tagName}>`;
          }
          return null;
        }).filter(x => x !== null).slice(0, 120);
      });
      console.log('[Diagnostic DOM Dump]:', JSON.stringify(domDump, null, 2));
    } catch (err) {
      console.log('[Diagnostic] Failed to get DOM dump:', err.message);
    }

    // Query multiple possible link selectors inside the grid or page
    const journalLinkSelectors = [
      '.table-cell-journalName a:visible',
      'mat-cell.mat-column-journalName a:visible',
      '.mat-column-journalName a:visible',
      'a[href*="journal-profile"]:visible',
      'mat-row a:visible',
      '.mat-row a:visible',
      '.mat-table a:visible',
      '[role="row"] a:visible',
      '[role="gridcell"] a:visible',
      'td a:visible',
      'table a:visible',
      'main a:visible',
      'a:visible',
      '.table-cell-journalName:visible',
      'span.table-cell-journalName:visible',
      'mat-cell.mat-column-journalName:visible',
      '.mat-column-journalName:visible'
    ];

    let linkClicked = false;
    
    // Setup listener for a new tab (Clarivate JCR often opens journal details in a new tab)
    const newPagePromise = context.waitForEvent('page', { timeout: 10000 }).catch(() => null);
    
    // Navigation / header text exclusion list to avoid clicking nav links
    const excludeWords = [
      'journals', 'categories', 'publishers', 'countries', 'regions',
      'compare', 'favorites', 'export', 'see all', 'journal name',
      'issn', 'eissn', 'edition', 'jcr year', 'legal center', 'privacy',
      'cookie', 'terms', 'copyright', 'accessibility', 'help'
    ];

    for (const selector of journalLinkSelectors) {
      try {
        const links = await page.$$(selector);
        for (const link of links) {
          const text = (await link.innerText()).trim();
          const textLower = text.toLowerCase();
          const href = await link.getAttribute('href');
          
          const isExcluded = excludeWords.some(word => textLower.includes(word));
          
          if (text && text.length > 3 && !isExcluded) {
            // Check if it matches our candidates to avoid wrong journal clicks on search result page
            const matchesQuery = isMatchingJournalText(text, searchCandidates);
            if (matchesQuery) {
              console.log(`[Success] Found matching journal link in table: "${text}" with href: "${href}".`);
              if (href && (href.includes('journal-profile') || href.includes('journalProfile'))) {
                // Direct URL navigation bypass: 100% immune to click blocking/intercepting!
                const targetUrl = href.startsWith('http') ? href : new URL(href, 'https://jcr.clarivate.com').href;
                console.log(`[Direct Navigation] Direct routing to journal profile: ${targetUrl}`);
                await page.goto(targetUrl, { waitUntil: 'load', timeout: options.timeout });
                linkClicked = true;
              } else {
                console.log('[Fallback] No direct href found. Performing native click...');
                await link.click({ force: true });
                linkClicked = true;
              }
              break;
            } else {
              console.log(`[Search Results] Skipping non-matching journal link: "${text}"`);
            }
          }
        }
        if (linkClicked) break;
      } catch (e) {}
    }

    if (!linkClicked) {
      console.log('[Warning] Could not find journal link using selectors. Trying to click the first cell link...');
      try {
        const firstCellLink = await page.$('.table-cell-journalName a, mat-cell.mat-column-journalName a, table tbody tr td a, .mat-row a, mat-row a');
        if (firstCellLink) {
          const href = await firstCellLink.getAttribute('href');
          if (href && (href.includes('journal-profile') || href.includes('journalProfile'))) {
            const targetUrl = href.startsWith('http') ? href : new URL(href, 'https://jcr.clarivate.com').href;
            console.log(`[Direct Navigation Fallback] Direct routing to first cell: ${targetUrl}`);
            await page.goto(targetUrl, { waitUntil: 'load', timeout: options.timeout });
            linkClicked = true;
          } else {
            console.log('Clicking the first cell link...');
            await firstCellLink.click({ force: true });
            linkClicked = true;
          }
        }
      } catch (e) {
        console.error('Failed to click first cell link:', e.message);
      }
    }

    if (linkClicked) {
      // Wait to see if a new tab was opened
      const newPageOpened = await newPagePromise;
      if (newPageOpened) {
        console.log('[Tab Detector] A new browser tab was opened! Switching context to the new tab...');
        profilePage = newPageOpened;
        await profilePage.waitForLoadState('load');
        await profilePage.waitForTimeout(2000);
      } else {
        console.log('[Tab Detector] No new tab opened. Continuing on the same tab.');
        await page.waitForTimeout(3000);
      }
    } else {
      console.error('[Error] Failed to click journal link on search results page.');
    }
  }

  // Wait for Journal Profile page load
  console.log('Waiting for Journal Profile page to load...');
  const profileSelectors = [
    '.journal-profile-header',
    '.journal-profile',
    'h1.journal-title',
    'text="Journal\'s performance"',
    'text="Journal information"',
    'text="Journal Impact Factor"',
    '.selected-year',
    'mat-select[name*="year"]',
    'h1'
  ];
  let profileLoaded = false;

  for (const selector of profileSelectors) {
    try {
      console.log(`Checking profile selector: "${selector}"`);
      await profilePage.waitForSelector(selector, { timeout: 5000 });
      profileLoaded = true;
      console.log(`[Success] Profile page loaded using selector: "${selector}"`);
      break;
    } catch (e) {}
  }

  if (!profileLoaded) {
    console.error('[Error] Journal Profile page failed to load.');
    console.log(`[Diagnostic] Current URL: ${profilePage.url()}`);
    try {
      await profilePage.screenshot({ path: `jcr_profile_failed_${journal_name_or_issn}.png` });
      console.log(`[Diagnostic] Saved screenshot for failed load to: jcr_profile_failed_${journal_name_or_issn}.png`);
    } catch (e) {
      console.log('[Diagnostic] Failed to take failed-load screenshot:', e.message);
    }
    
    if (profilePage !== page) {
      console.log('[Tab Manager] Closing failed profile tab...');
      await profilePage.close().catch(() => {});
    }
    
    return {
      journal: journal_name_or_issn,
      year: publication_year,
      categories: 'N/A',
      rank: 'N/A',
      quartile: 'N/A',
      percentile: 'N/A',
      journalImpactFactor: 'N/A',
      fiveYearJIF: 'N/A',
      error: 'Journal profile page failed to load'
    };
  }

  await handleCaptcha(profilePage);
  await profilePage.waitForTimeout(2000);

  // Scroll page down to load lazy-loaded elements
  console.log('Scrolling page to ensure lazy-loaded content resolves...');
  try {
    await profilePage.evaluate(() => window.scrollTo(0, document.body.scrollHeight / 2));
    await profilePage.waitForTimeout(1000);
    await profilePage.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await profilePage.waitForTimeout(1500);
    await profilePage.evaluate(() => window.scrollTo(0, 0)); // Scroll back to top
    await profilePage.waitForTimeout(1000);
  } catch (scrollErr) {
    console.log('Note on scrolling:', scrollErr.message);
  }

  // Handle Year Selection
  // Check the currently selected JCR Year
  let currentYear = '';
  try {
    const yearElementSelectors = ['.jcr-year-select', 'mat-select[name*="year"]', '.selected-year', '#year-select'];
    for (const selector of yearElementSelectors) {
      const el = await profilePage.$(selector);
      if (el && await el.isVisible()) {
        currentYear = (await el.innerText()).trim();
        if (currentYear) break;
      }
    }
  } catch (e) {}

  if (!currentYear) {
    const urlMatch = profilePage.url().match(/[?&]year=(\d{4})/);
    if (urlMatch) {
      currentYear = urlMatch[1];
      console.log(`[Year Detector] Resolved current JCR year from URL: "${currentYear}"`);
    }
  }

  console.log(`Current page year: ${currentYear || 'Unknown'}. Target year: ${publication_year}`);

  // If year is different, navigate to target year or change dropdown
  if (currentYear && !currentYear.includes(publication_year.toString())) {
    console.log(`Attempting to switch to target JCR Year: ${publication_year}...`);
    
    const currentUrl = profilePage.url();
    if (currentUrl.includes('journal-profile') && currentUrl.includes('year=')) {
      const newUrl = currentUrl.replace(/year=\d{4}/, `year=${publication_year}`);
      console.log(`Directly navigating to year URL: ${newUrl}`);
      await profilePage.goto(newUrl, { waitUntil: 'load', timeout: options.timeout });
    } else {
      // Fallback: Click dropdown to select the year
      try {
        const selectDropdown = await profilePage.$('mat-select[name*="year"]');
        if (selectDropdown) {
          await selectDropdown.click({ force: true });
          await profilePage.waitForSelector('.mat-option');
          const optionsList = await profilePage.$$('.mat-option');
          for (const optionEl of optionsList) {
            const text = await optionEl.innerText();
            if (text.includes(publication_year.toString())) {
              await optionEl.click({ force: true });
              break;
            }
          }
        }
      } catch (e) {
        console.error('Failed to change year dropdown:', e.message);
      }
    }
    await profilePage.waitForTimeout(3000);
    await handleCaptcha(profilePage);
    
    // Re-extract 5-Year Impact Factor after year switch
    console.log('Re-extracting 5-Year Impact Factor after year switch...');
    const reExtractResult = await profilePage.evaluate(() => {
      // Extract 5 Year Impact Factor
      let fiveYearJIF = 'N/A';
      try {
        const elements = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, div, span, p, a'));
        let targetEl = null;
        for (const el of elements) {
          const text = (el.innerText || '').trim();
          if (text === '5 Year Impact Factor' || (text.toLowerCase().includes('5 year impact factor') && text.length < 40)) {
            targetEl = el;
            break;
          }
        }

        if (targetEl) {
          let cardContainer = targetEl;
          for (let i = 0; i < 4; i++) {
            if (!cardContainer.parentElement) break;
            const parentText = cardContainer.parentElement.innerText || '';
            if (parentText.includes('View Calculation')) {
              cardContainer = cardContainer.parentElement;
              break;
            }
            cardContainer = cardContainer.parentElement;
          }

          if (cardContainer) {
            const cardText = cardContainer.innerText || '';
            const lines = cardText.split('\n').map(l => l.trim()).filter(l => l.length > 0);
            const idx = lines.findIndex(l => l === '5 Year Impact Factor' || l.toLowerCase().includes('5 year impact factor'));
            if (idx !== -1 && idx + 1 < lines.length) {
              const possibleValue = lines[idx + 1];
              if (/^(?:[\d.]+|N\/A|n\/a)$/.test(possibleValue) && possibleValue !== '5') {
                fiveYearJIF = possibleValue;
              }
            }
          }
        }
      } catch (e) {}
      return fiveYearJIF;
    });

    if (reExtractResult !== 'N/A') {
      fiveYearJIFValue = reExtractResult;
      console.log(`[Re-extract] Successfully updated 5-Year JIF to: ${fiveYearJIFValue}`);
    } else {
      console.log('[Re-extract] Failed to re-extract 5-Year JIF, keeping previous value.');
    }
  }

  // Expand "Rank" or "Rank by Journal Impact Factor" section if collapsed
  console.log('Locating ranking and category table...');
  try {
    const rankHeaderSelectors = [
      '//h3[contains(text(),"Rank by Journal Impact Factor")]',
      '//span[contains(text(),"Rank by Journal Impact Factor")]',
      '//div[contains(text(),"Rank by Journal Impact Factor")]',
      'text="Rank by Journal Impact Factor"',
      'text="Rank"'
    ];
    
    for (const selector of rankHeaderSelectors) {
      const isXPath = selector.startsWith('//');
      let headerElement = null;
      if (isXPath) {
        headerElement = await profilePage.$(selector);
      } else {
        const loc = profilePage.locator(selector).first();
        if (await loc.count() > 0) {
          headerElement = await loc.elementHandle();
        }
      }

      if (headerElement) {
        console.log(`Found Rank section header: "${selector}"`);
        
        // Check if section is expanded
        const isTableVisible = await profilePage.evaluate(() => {
          const tbls = Array.from(document.querySelectorAll('table.rank-table, .rank-by-jif-table table, .jif-ranking-table table, table'));
          return tbls.some(tbl => {
            const text = tbl.innerText || '';
            return text.includes('Category') && (text.includes('Rank') || text.includes('Quartile')) && tbl.offsetWidth > 0 && tbl.offsetHeight > 0;
          });
        });

        if (!isTableVisible) {
          console.log('Expanding Rank section via click since JIF Rank table is not visible...');
          try {
            await headerElement.scrollIntoViewIfNeeded();
          } catch(e) {}
          await headerElement.click({ force: true });
          await profilePage.waitForTimeout(2000);
        }
        break;
      }
    }
  } catch (e) {
    console.log('Note on Rank section expansion:', e.message);
  }

  // Extract Table Data
  let dataExtracted = false;
  let finalResult = null;
  console.log('Extracting JIF Ranking history and 5-Year Impact Factor using comprehensive DOM and Text scanning...');
  try {
    const evaluationResults = await profilePage.evaluate(() => {
      const headers = Array.from(document.querySelectorAll('h3, span, div, h2, h4, a'));
      let rankSection = null;
      for (const h of headers) {
        const text = (h.innerText || '').trim();
        if (text === 'Rank by Journal Impact Factor' || text.includes('Rank by Journal Impact Factor')) {
          rankSection = h.closest('.mat-expansion-panel') || h.closest('mat-expansion-panel') || h.parentElement;
          break;
        }
      }

      if (!rankSection) {
        rankSection = document.body;
      }

      const results = [];
      const tables = Array.from(rankSection.querySelectorAll('table, mat-table, [role="grid"], .mat-table, .rank-table'));
      
      // Extract all clean uppercase category names from tabs inside the rankSection
      const tabElements = Array.from(rankSection.querySelectorAll('.mat-tab-label-content, .mat-tab-label, [role="tab"], div, span, a'));
      const tabCategories = [];
      for (const el of tabElements) {
        const text = (el.innerText || '').trim();
        // Match uppercase JCR category name pattern (allow uppercase, spaces, commas, ampersands, hyphens, and parentheses)
        if (/^[A-Z\s,&()\-]{4,}$/.test(text) && 
            !['CATEGORY', 'JCR YEAR', 'QUARTILE', 'RANK', 'JIF PERCENTILE', 'JCR YEARS', 'JIF PERCENTILE IN CATEGORY', 'EXPORT', 'SCIE', 'SSCI', 'ESCI', 'VIEW CALCULATION'].includes(text.toUpperCase())) {
          if (!tabCategories.includes(text)) {
            tabCategories.push(text);
          }
        }
      }

      for (let tableIndex = 0; tableIndex < tables.length; tableIndex++) {
        const table = tables[tableIndex];
        const tableText = (table.innerText || '').toLowerCase();
        if (!tableText.includes('year') && !tableText.includes('rank') && !tableText.includes('quartile')) {
          continue;
        }

        const rows = Array.from(table.querySelectorAll('tr, mat-row, .mat-row, [role="row"]'));
        for (const row of rows) {
          const cells = Array.from(row.querySelectorAll('td, mat-cell, .mat-cell, [role="gridcell"], th, mat-header-cell'));
          if (cells.length === 0) continue;

          const cellTexts = cells.map(c => (c.innerText || '').trim());
          
          let year = '';
          let rank = '';
          let quartile = '';
          let percentile = '';

          for (const text of cellTexts) {
            if (/^\d{4}$/.test(text)) {
              year = text;
            } else if (/^\d+\s*\/\s*\d+$/.test(text)) {
              rank = text.replace(/\s+/g, '');
            } else if (/^Q[1-4]$/i.test(text)) {
              quartile = text.toUpperCase();
            } else if (/^(?:\d{1,2}(?:\.\d+)?|100(?:\.0+)?)\s*%?$/.test(text)) {
              percentile = text;
            }
          }

          if (year && (rank || quartile)) {
            // Determine category for this specific table
            let category = tabCategories[tableIndex] || '';

            if (!category) {
              // Fallback: search siblings/parents for uppercase category name
              let current = table;
              while (current && current !== rankSection && !category) {
                const siblings = Array.from(current.parentElement?.querySelectorAll('div, span, p, h4, h3, a') || []);
                for (const sib of siblings) {
                  const sibText = (sib.innerText || '').trim();
                  if (/^[A-Z\s,&()\-]{5,}$/.test(sibText) && 
                      !['CATEGORY', 'JCR YEAR', 'QUARTILE', 'RANK', 'JIF PERCENTILE', 'JCR YEARS', 'JIF PERCENTILE IN CATEGORY', 'EXPORT', 'SCIE', 'SSCI', 'ESCI', 'VIEW CALCULATION'].includes(sibText.toUpperCase())) {
                    category = sibText;
                    break;
                  }
                }
                current = current.parentElement;
              }
            }

            if (!category) {
              category = 'Unknown Category';
            }

            results.push({ year, rank, quartile, percentile: percentile || 'N/A', category });
          }
        }
      }

      // Extract Journal Impact Factor (Layer 1: Visual innerText Flow & Backups)
      let journalImpactFactor = 'N/A';
      try {
        const elements = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, div, span, p, a'));
        let targetEl = null;
        for (const el of elements) {
          const text = (el.innerText || '').trim();
          if (text === 'Journal Impact Factor' || (text.toLowerCase().includes('journal impact factor') && !text.toLowerCase().includes('5 year') && text.length < 40)) {
            targetEl = el;
            break;
          }
        }

        if (targetEl) {
          // Walk up to card level
          let cardContainer = targetEl;
          for (let i = 0; i < 4; i++) {
            if (!cardContainer.parentElement) break;
            const parentText = cardContainer.parentElement.innerText || '';
            if (parentText.includes('View Calculation')) {
              cardContainer = cardContainer.parentElement;
              break;
            }
            cardContainer = cardContainer.parentElement;
          }

          if (cardContainer) {
            const cardText = cardContainer.innerText || '';
            const lines = cardText.split('\n').map(l => l.trim()).filter(l => l.length > 0);
            const idx = lines.findIndex(l => l === 'Journal Impact Factor' || (l.toLowerCase().includes('journal impact factor') && !l.toLowerCase().includes('5 year')));
            if (idx !== -1 && idx + 1 < lines.length) {
              const possibleValue = lines[idx + 1];
              if (/^(?:[\d.]+|N\/A|n\/a)$/.test(possibleValue) && possibleValue !== '5') {
                journalImpactFactor = possibleValue;
              }
            }
          }
        }

        // Selector Fallback if index search failed
        if (journalImpactFactor === 'N/A' && targetEl) {
          let parent = targetEl.parentElement;
          let foundValue = false;
          for (let i = 0; i < 4; i++) {
            if (!parent || foundValue) break;
            const descendants = Array.from(parent.querySelectorAll('div, span, p, h1, h2, h3, h4, h5, .jif-value, .value, .metric-value'));
            for (const desc of descendants) {
              const valText = (desc.innerText || '').trim();
              if (/^\d+(\.\d+)?$/.test(valText) && valText !== '5') {
                journalImpactFactor = valText;
                foundValue = true;
                break;
              }
            }
            parent = parent.parentElement;
          }
        }
      } catch (e) {}

      // Page-wide Regex fallback
      if (journalImpactFactor === 'N/A') {
        try {
          const bodyText = document.body.innerText || '';
          const regexes = [
            /Journal\s*Impact\s*Factor\s*[\r\n]+\s*([\d.]+)/i,
            /Journal\s*Impact\s*Factor\s*([\d.]+)/i
          ];
          for (const regex of regexes) {
            const match = bodyText.match(regex);
            if (match && match[1] && match[1] !== '5') {
              journalImpactFactor = match[1];
              break;
            }
          }
        } catch (e) {}
      }

      // Extract 5 Year Impact Factor (Layer 1: Visual innerText Flow & Backups)
      let fiveYearJIF = 'N/A';
      try {
        const elements = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, div, span, p, a'));
        let targetEl = null;
        for (const el of elements) {
          const text = (el.innerText || '').trim();
          if (text === '5 Year Impact Factor' || (text.toLowerCase().includes('5 year impact factor') && text.length < 40)) {
            targetEl = el;
            break;
          }
        }

        if (targetEl) {
          // Walk up to card level
          let cardContainer = targetEl;
          for (let i = 0; i < 4; i++) {
            if (!cardContainer.parentElement) break;
            const parentText = cardContainer.parentElement.innerText || '';
            if (parentText.includes('View Calculation')) {
              cardContainer = cardContainer.parentElement;
              break;
            }
            cardContainer = cardContainer.parentElement;
          }

          if (cardContainer) {
            const cardText = cardContainer.innerText || '';
            const lines = cardText.split('\n').map(l => l.trim()).filter(l => l.length > 0);
            const idx = lines.findIndex(l => l === '5 Year Impact Factor' || l.toLowerCase().includes('5 year impact factor'));
            if (idx !== -1 && idx + 1 < lines.length) {
              const possibleValue = lines[idx + 1];
              if (/^(?:[\d.]+|N\/A|n\/a)$/.test(possibleValue) && possibleValue !== '5') {
                fiveYearJIF = possibleValue;
              }
            }
          }
        }

        // Selector Fallback if index search failed
        if (fiveYearJIF === 'N/A' && targetEl) {
          let parent = targetEl.parentElement;
          let foundValue = false;
          for (let i = 0; i < 4; i++) {
            if (!parent || foundValue) break;
            const descendants = Array.from(parent.querySelectorAll('div, span, p, h1, h2, h3, h4, h5, .jif-value, .value, .metric-value'));
            for (const desc of descendants) {
              const valText = (desc.innerText || '').trim();
              if (/^\d+(\.\d+)?$/.test(valText) && valText !== '5') {
                fiveYearJIF = valText;
                foundValue = true;
                break;
              }
            }
            parent = parent.parentElement;
          }
        }
      } catch (e) {}

      // Page-wide Regex fallback
      if (fiveYearJIF === 'N/A') {
        try {
          const bodyText = document.body.innerText || '';
          const regexes = [
            /5\s*Year\s*Impact\s*Factor\s*[\r\n]+\s*([\d.]+)/i,
            /5\s*Year\s*Impact\s*Factor\s*([\d.]+)/i,
            /5-Year\s*Impact\s*Factor\s*[\r\n]+\s*([\d.]+)/i,
            /5-Year\s*Impact\s*Factor\s*([\d.]+)/i
          ];
          for (const regex of regexes) {
            const match = bodyText.match(regex);
            if (match && match[1] && match[1] !== '5') {
              fiveYearJIF = match[1];
              break;
            }
          }
        } catch (e) {}
      }

      return {
        history: results,
        journalImpactFactor: journalImpactFactor,
        fiveYearJIF: fiveYearJIF
      };
    });

    const extractedHistory = evaluationResults.history;
    let journalImpactFactorValue = evaluationResults.journalImpactFactor;
    let fiveYearJIFValue = evaluationResults.fiveYearJIF;

    console.log(`Successfully compiled JIF rank history:`, extractedHistory);
    console.log(`Successfully extracted Journal Impact Factor (Initial):`, journalImpactFactorValue);
    console.log(`Successfully extracted 5 Year Impact Factor (Initial):`, fiveYearJIFValue);

    // Layer 2 Fallback: CSV Download Strategy
    if (fiveYearJIFValue === 'N/A' || !/^\d+(\.\d+)?$/.test(fiveYearJIFValue)) {
      console.log('[Fallback] 5-Year JIF is not a valid number. Attempting CSV Download Strategy...');
      try {
        const cardLocator = profilePage.locator('div, section, mat-card, .card, mat-expansion-panel').filter({ hasText: /5 Year Impact Factor/i }).first();
        if (await cardLocator.count() > 0) {
          // Look for any clickable button/icon representing download inside the card
          let downloadBtn = cardLocator.locator('button, a, [role="button"]').filter({ has: profilePage.locator('mat-icon, i, svg, [class*="download"]') }).first();
          if (await downloadBtn.count() === 0) {
            downloadBtn = cardLocator.locator('button').filter({ hasText: /download|export/i }).first();
          }
          if (await downloadBtn.count() === 0) {
            downloadBtn = cardLocator.locator('button').first();
          }

          if (await downloadBtn.count() > 0) {
            console.log('Found download button/icon in card. Clicking...');
            await downloadBtn.click();
            await profilePage.waitForTimeout(1500);
            
            // Click CSV option in the menu dropdown (menu is global popup, wait up to 5s)
            const csvOption = profilePage.locator('.mat-menu-item, [role="menuitem"], a, button').filter({ hasText: /^CSV$/i }).first();
            if (await csvOption.count() > 0) {
              console.log('Triggering CSV download...');
              const [ download ] = await Promise.all([
                profilePage.waitForEvent('download', { timeout: 10000 }),
                csvOption.click()
              ]);
              
              const tempDownloadPath = path.join(process.cwd(), 'temp_jif_download.csv');
              await download.saveAs(tempDownloadPath);
              console.log(`CSV successfully downloaded to: ${tempDownloadPath}`);
              
              if (fs.existsSync(tempDownloadPath)) {
                const csvContent = fs.readFileSync(tempDownloadPath, 'utf8');
                fs.unlinkSync(tempDownloadPath); // Clean up immediately
                
                const csvLines = csvContent.split(/[\r\n]+/).map(l => l.trim()).filter(l => l.length > 0);
                if (csvLines.length > 0) {
                  const headerParts = csvLines[0].replace(/"/g, '').split(',').map(p => p.trim().toLowerCase());
                  let yearColIndex = headerParts.findIndex(h => h.includes('year') || h.includes('date'));
                  let jifColIndex = headerParts.findIndex(h => h.includes('factor') || h.includes('jif') || h.includes('impact'));
                  
                  if (yearColIndex === -1) yearColIndex = 0;
                  if (jifColIndex === -1) jifColIndex = 1;
                  
                  for (let idx = 1; idx < csvLines.length; idx++) {
                    const parts = csvLines[idx].replace(/"/g, '').split(',').map(p => p.trim());
                    if (parts.length > Math.max(yearColIndex, jifColIndex)) {
                      const yearVal = parts[yearColIndex];
                      const jifVal = parts[jifColIndex];
                      if (yearVal === publication_year.toString() || yearVal.includes(publication_year.toString())) {
                        console.log(`[CSV Parser] Matched JCR Year ${publication_year} -> 5-Year JIF: ${jifVal}`);
                        fiveYearJIFValue = jifVal;
                        break;
                      }
                    }
                  }
                }
              }
            } else {
              console.log('CSV option not found in export dropdown.');
            }
          } else {
            console.log('Download button not found in card container.');
          }
        } else {
          console.log('Card container for 5 Year Impact Factor not found.');
        }
      } catch (downloadErr) {
        console.log('CSV Download Strategy failed/noted:', downloadErr.message);
      }
    }

    if (extractedHistory.length > 0) {
      const categoriesMap = {};
      
      for (const item of extractedHistory) {
        const cat = item.category || 'Unknown Category';
        if (!categoriesMap[cat]) {
          categoriesMap[cat] = [];
        }
        categoriesMap[cat].push(item);
      }

      const finalCategories = [];
      const finalRanks = [];
      const finalQuartiles = [];
      const finalPercentiles = [];

      for (const [cat, history] of Object.entries(categoriesMap)) {
        let targetEntry = history.find(h => h.year === publication_year.toString());
        
        if (!targetEntry) {
          // "有新用新，无新用前"原则：优先使用目标年份，若无则使用目标年份之前最近的一年
          const sorted = [...history]
            .filter(h => parseInt(h.year) <= publication_year)
            .sort((a, b) => parseInt(b.year) - parseInt(a.year));
          if (sorted.length > 0) {
            targetEntry = sorted[0];
            console.log(`[Year Fallback] Target year ${publication_year} not found in history for "${cat}". Falling back to previous available year: ${targetEntry.year}`);
          }
        }

        if (targetEntry) {
          finalCategories.push(cat);
          finalRanks.push(targetEntry.rank || 'N/A');
          finalQuartiles.push(targetEntry.quartile || 'N/A');
          finalPercentiles.push(targetEntry.percentile || 'N/A');
        }
      }

      if (finalCategories.length > 0) {
        finalResult = {
          journal: journal_name_or_issn,
          year: publication_year,
          categories: finalCategories.join('; '),
          rank: finalRanks.join('; '),
          quartile: finalQuartiles.join('; '),
          percentile: finalPercentiles.join('; '),
          journalImpactFactor: journalImpactFactorValue,
          fiveYearJIF: fiveYearJIFValue
        };
        dataExtracted = true;
      }
    }
  } catch (err) {
    console.error(`Error during JIF Ranking history extraction:`, err.message);
  }

  // Close profilePage tab if it's a new tab to restore state
  if (profilePage !== page) {
    console.log('[Tab Manager] Closing profile tab to return to search/home tab...');
    await profilePage.close().catch(() => {});
  }

  if (dataExtracted && finalResult) {
    return finalResult;
  } else {
    console.error('[Error] Failed to extract ranking table data.');
    return {
      journal: journal_name_or_issn,
      year: publication_year,
      categories: 'N/A',
      rank: 'N/A',
      quartile: 'N/A',
      percentile: 'N/A',
      journalImpactFactor: 'N/A',
      fiveYearJIF: 'N/A',
      error: 'Could not parse ranking table structure'
    };
  }
}

function parseBatchLine(line, defaultYear = 2026) {
  const trimmed = line.trim();
  if (!trimmed) return null;
  
  // Regex to check if the line ends with a space followed by a 4-digit year (e.g., 1879-1069 2026)
  const match = trimmed.match(/\s+(\d{4})$/);
  if (match) {
    const journal = trimmed.substring(0, match.index).trim();
    const year = parseInt(match[1], 10);
    return { journal, year };
  } else {
    return { journal: trimmed, year: defaultYear };
  }
}

async function startInteractiveConsole(page, context, options, results) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  const ask = (query) => new Promise(resolve => rl.question(query, resolve));

  console.log('\n==================================================');
  console.log('🤖 JCR Historical Fetcher - Interactive Console');
  console.log('==================================================');
  
  try {
    console.log('Select Input Mode:');
    console.log('1. Single Journal Query (Step-by-step)');
    console.log('2. Batch Paste Mode (Paste multiple journals at once) [RECOMMENDED]');
    console.log('3. Exit');
    const choiceInput = await ask('\nEnter choice (1, 2, or 3, default: 2): ');
    const choice = choiceInput.trim() || '2';

    if (choice === '3' || choice.toLowerCase() === 'exit') {
      console.log('Exiting interactive console...');
      return;
    }

    if (choice === '1') {
      console.log('\n--------------------------------------------------');
      console.log('ℹ️ Single Journal Mode Active');
      console.log('--------------------------------------------------');
      console.log('Instructions:');
      console.log('1. Enter the ISSN or Journal Name at the prompt.');
      console.log('2. Enter the target JCR publication year (e.g., 2026).');
      console.log('3. The script will automatically query the already-opened Chrome.');
      console.log('4. Results are displayed instantly and appended to "jcr_results.md".');
      console.log('Type "exit" at any prompt to quit the interactive console.\n');

      while (true) {
        console.log('\n--- Ready for Next Journal ---');
        const journalInput = await ask('Journal Name or ISSN (type "exit" to quit): ');
        const journal = journalInput.trim();
        
        if (journal.toLowerCase() === 'exit') {
          console.log('Exiting interactive console...');
          break;
        }
        if (!journal) {
          console.log('Error: Journal input cannot be empty.');
          continue;
        }

        const yearInput = await ask('Target Year (e.g. 2026, default: 2026, type "exit" to quit): ');
        let yearStr = yearInput.trim();
        
        if (yearStr.toLowerCase() === 'exit') {
          console.log('Exiting interactive console...');
          break;
        }
        
        if (!yearStr) {
          yearStr = '2026';
        }
        
        const year = parseInt(yearStr, 10);
        if (isNaN(year) || !/^\d{4}$/.test(yearStr)) {
          console.log('Error: Invalid year format. Please enter a 4-digit number.');
          continue;
        }

        console.log(`\n[Info] Processing: "${journal}" for JCR Year: ${year}...`);
        
        const result = await fetchSingleJournal(page, context, journal, year, options);
        
        console.log('\n---------------- RESULT ----------------');
        if (result.error) {
          console.log(`❌ Error: ${result.error}`);
        } else {
          console.log(`✨ Journal:    ${result.journal}`);
          console.log(`📅 Year:       ${result.year}`);
          console.log(`📚 Categories: ${result.categories}`);
          console.log(`📈 Rank:       ${result.rank}`);
          console.log(`🏆 Quartile:   ${result.quartile}`);
          console.log(`📊 Percentile: ${result.percentile}`);
          console.log(`📊 5-Year JIF: ${result.fiveYearJIF || 'N/A'}`);
        }
        console.log('----------------------------------------\n');

        results.push(result);
        writeMarkdownOutput(options.output, results);
      }
    } else if (choice === '2') {
      console.log('\n--------------------------------------------------');
      console.log('📋 JCR Batch Paste Mode Active');
      console.log('--------------------------------------------------');
      
      const defaultYearInput = await ask('Default JCR Year for journals without a specified year (default: 2026): ');
      let defaultYearStr = defaultYearInput.trim();
      if (!defaultYearStr) {
        defaultYearStr = '2026';
      }
      
      const defaultYear = parseInt(defaultYearStr, 10);
      if (isNaN(defaultYear) || !/^\d{4}$/.test(defaultYearStr)) {
        console.log('Invalid year format. Defaulting to 2026.');
      }
      const finalDefaultYear = isNaN(defaultYear) ? 2026 : defaultYear;

      console.log('\nPlease paste your list of journals and optional target years below.');
      console.log('Format: [Journal Name or ISSN] [Year] (one journal per line)');
      console.log('Examples:');
      console.log('  1879-1069 2026');
      console.log('  0266-3538 2025');
      console.log('  Nature Materials');
      console.log('\n👉 Press Enter on an EMPTY line to finish pasting and start query!');
      console.log('--------------------------------------------------');

      const batchTargets = [];
      while (true) {
        const line = await ask('> ');
        const trimmed = line.trim();
        if (trimmed === '') {
          break;
        }
        const target = parseBatchLine(line, finalDefaultYear);
        if (target) {
          batchTargets.push(target);
          console.log(`   Added to queue: "${target.journal}" for Year: ${target.year}`);
        }
      }

      if (batchTargets.length === 0) {
        console.log('No journals entered. Returning to menu.');
        return;
      }

      console.log(`\nReady to process ${batchTargets.length} journals. Starting batch execution...`);
      
      for (let i = 0; i < batchTargets.length; i++) {
        const target = batchTargets[i];
        console.log(`\n==================================================`);
        console.log(`[Batch ${i + 1}/${batchTargets.length}] Processing: "${target.journal}" for JCR Year: ${target.year}`);
        console.log(`==================================================`);
        
        try {
          const result = await fetchSingleJournal(page, context, target.journal, target.year, options);
          
          console.log('\n---------------- RESULT ----------------');
          if (result.error) {
            console.log(`❌ Error: ${result.error}`);
          } else {
            console.log(`✨ Journal:    ${result.journal}`);
            console.log(`📅 Year:       ${result.year}`);
            console.log(`📚 Categories: ${result.categories}`);
            console.log(`📈 Rank:       ${result.rank}`);
            console.log(`🏆 Quartile:   ${result.quartile}`);
            console.log(`📊 Percentile: ${result.percentile}`);
            console.log(`📊 5-Year JIF: ${result.fiveYearJIF || 'N/A'}`);
          }
          console.log('----------------------------------------\n');

          results.push(result);
          writeMarkdownOutput(options.output, results);
        } catch (err) {
          console.error(`Error processing "${target.journal}":`, err.message);
          const errorResult = {
            journal: target.journal,
            year: target.year,
            categories: 'N/A',
            rank: 'N/A',
            quartile: 'N/A',
            percentile: 'N/A',
            journalImpactFactor: 'N/A',
            fiveYearJIF: 'N/A',
            error: err.message
          };
          results.push(errorResult);
          writeMarkdownOutput(options.output, results);
        }
      }
      
      console.log('\nBatch processing complete! All results saved to jcr_results.md.');
    } else {
      console.log('Invalid choice. Exiting interactive console.');
    }
  } finally {
    rl.close();
  }
}

(async () => {
  // Load local credentials if available in workspace
  loadConfigJson();
  loadEnvFile();

  if (!options.chromeData) {
    console.error('Error: --chrome-data path is required or could not be auto-resolved.');
    console.log('Usage 1 (Interactive): node fetch.js [--chrome-data <path>] [--profile <profile>]');
    console.log('Usage 2 (Single Input): node fetch.js --journal "1879-1069" --year 2026 [--chrome-data <path>]');
    console.log('Usage 3 (Batch File):  node fetch.js --input <input.json> [--chrome-data <path>]');
    console.log('Optional: pass --skip-offline-reminder to skip the local JCR data prompt.');
    console.log('Optional: pass --skip-login-reminder to skip the first-run login setup reminder.');
    process.exit(1);
  }

  const shouldContinueLiveLookup = await promptJcrOfflineDataOption();
  if (!shouldContinueLiveLookup) {
    process.exit(0);
  }

  const hasFileInput = !!options.input;
  const hasSingleInput = !!(options.journal && options.year);
  const isInteractive = !hasFileInput && !hasSingleInput;

  let payload = [];
  if (hasFileInput) {
    try {
      const rawData = fs.readFileSync(options.input, 'utf8');
      payload = JSON.parse(rawData);
      if (!Array.isArray(payload)) {
        throw new Error('Input must be a JSON array of objects.');
      }
    } catch (err) {
      console.error(`Failed to read input payload: ${err.message}`);
      process.exit(1);
    }
    console.log(`Loaded payload containing ${payload.length} journal query targets from input file.`);
  } else if (hasSingleInput) {
    payload = [{
      journal_name_or_issn: options.journal,
      publication_year: options.year
    }];
    console.log(`Loaded single target: "${options.journal}" for Year ${options.year}.`);
  } else {
    console.log('\n==================================================');
    console.log('🤖 JCR Historical Fetcher - Launching Interactive Mode');
    console.log('==================================================');
  }

  const localUserDataDir = path.resolve('.playwright_profile');
  remindFirstRunLoginSetup(localUserDataDir);
  console.log(`[Unified Profile Setup] Launching JCR Fetcher using local dedicated profile: ${localUserDataDir}`);
  console.log(`[Unified Profile Setup] No file copying is needed. 100% immune to Chrome locks!`);

  let context;
  try {
    context = await chromium.launchPersistentContext(localUserDataDir, {
      headless: false,
      viewport: null,
      args: [
        '--disable-blink-features=AutomationControlled',
        '--test-type',
        '--profile-directory=Default'
      ],
      timeout: options.timeout,
    });
  } catch (err) {
    console.error('\n[❌ ERROR] Failed to launch Chrome with persistent context!');
    console.error(err.message);
    process.exit(1);
  }

  let page = null;
  for (let i = 0; i < 50; i++) {
    if (context.pages().length > 0) {
      page = context.pages()[0];
      break;
    }
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  if (!page) {
    console.log('[Info] Creating a new browser tab...');
    page = await context.newPage();
  } else {
    console.log('[Info] Successfully connected and reusing default browser tab.');
  }

  const results = [];

  try {
    if (isInteractive) {
      // Execute the interactive console loop!
      await startInteractiveConsole(page, context, options, results);
    } else {
      // Execute the non-interactive batch/single loop with clean tab isolation
      if (page) {
        // Keep the default page open but navigate to about:blank to keep it lightweight.
        // This prevents the persistent browser context from closing or crashing.
        await page.goto('about:blank').catch(() => {});
      }
      for (const target of payload) {
        const { journal_name_or_issn, publication_year } = target;
        console.log(`\n--------------------------------------------------`);
        console.log(`Processing: "${journal_name_or_issn}" for Year: ${publication_year}`);
        
        const freshPage = await context.newPage();
        try {
          const result = await fetchSingleJournal(freshPage, context, journal_name_or_issn, publication_year, options);
          results.push(result);
          writeMarkdownOutput(options.output, results);
        } catch (loopErr) {
          console.error(`Error processing "${journal_name_or_issn}":`, loopErr.message);
          results.push({
            journal: journal_name_or_issn,
            year: publication_year,
            categories: 'N/A',
            rank: 'N/A',
            quartile: 'N/A',
            percentile: 'N/A',
            journalImpactFactor: 'N/A',
            fiveYearJIF: 'N/A',
            error: loopErr.message
          });
          writeMarkdownOutput(options.output, results);
        } finally {
          await freshPage.close().catch(() => {});
          // Gentle cooling delay to mimic human behavior and allow JCR backend recovery
          await new Promise(r => setTimeout(r, 3000));
        }
      }
    }
  } catch (err) {
    console.error(`Fatal script loop error: ${err.message}`);
    try {
      if (page) {
        await page.screenshot({ path: 'jcr_crash_diagnostic.png' });
        console.log('[Diagnostic] Crash screenshot saved as "jcr_crash_diagnostic.png".');
      }
    } catch (e) {
      console.log('[Diagnostic] Failed to save crash screenshot:', e.message);
    }
  } finally {
    await context.close();
  }

  console.log('\n==================================================');
  console.log('JCR Historical Fetcher execution finished.');
  console.log('==================================================');
})();

import asyncio
import sys
import os
import logging
import re
from playwright.async_api import async_playwright

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def handle_wos_captcha_if_needed(page) -> None:
    block_keywords = [
        "verify you are human", 
        "unusual activity", 
        "security check", 
        "机器人", 
        "验证码", 
        "unusual activity coming from your institution",
        "access denied",
        "strictly necessary cookies"
    ]
    
    logger.info("Checking if Web of Science has triggered security CAPTCHA or blocking...")
    while True:
        try:
            body_text = await page.locator("body").inner_text()
        except Exception as e:
            logger.warning(f"Failed to read page body text: {e}")
            body_text = ""
            
        body_text_lower = body_text.lower()
        is_blocked = any(kw.lower() in body_text_lower for kw in block_keywords)
        
        if not is_blocked:
            break
            
        logger.warning("="*80)
        logger.warning("⚠️  [警告] Web of Science 触发了安全验证 / 流量拦截保护！")
        logger.warning("Web of Science has triggered a security verification / BOT check.")
        logger.warning("请在弹出的浏览器窗口中【手动完成验证 / 点击同意Cookie】以恢复执行。")
        logger.warning("Please manually solve the verification / Accept Cookies in the open browser window.")
        logger.warning("="*80)
        
        await asyncio.sleep(5)
    logger.info("Web of Science security check passed or not detected. Proceeding...")

async def main():
    async with async_playwright() as p:
        # Use the exact same persistent profile as the main script
        user_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".playwright_profile"))
        logger.info(f"Launching visible Chromium with persistent profile: {user_data_dir}...")
        
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            args=["--start-maximized"]
        )
        
        pages = context.pages
        page = pages[0] if pages else await context.new_page()
        
        url = "https://www.webofscience.com/wos/author/record/GPW-7178-2022"
        logger.info(f"Navigating to {url}...")
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            logger.info("Waiting 5 seconds for page content to settle before checking CAPTCHA...")
            await asyncio.sleep(5)
            
            # Check if initially blocked
            block_keywords = [
                "verify you are human", "unusual activity", "security check", 
                "机器人", "验证码", "unusual activity coming from your institution",
                "access denied", "strictly necessary cookies"
            ]
            try:
                body_text = await page.locator("body").inner_text()
            except Exception:
                body_text = ""
            was_blocked = any(kw.lower() in body_text.lower() for kw in block_keywords)
            
            if was_blocked:
                await handle_wos_captcha_if_needed(page)
                # Re-navigate
                logger.info(f"Re-navigating to {url} after captcha solving...")
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(6)
            else:
                logger.info("No initial Web of Science block detected. Proceeding...")
            
            logger.info("Sleeping 15 seconds to let dynamic content render...")
            await asyncio.sleep(15)
            
            # Save screenshot
            await page.screenshot(path="wos_success_screenshot.png")
            logger.info("Screenshot saved to wos_success_screenshot.png")
            
            # Save HTML content
            content = await page.content()
            with open("wos_success_page.html", "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("HTML content saved to wos_success_page.html")
            
            # Print page body text length and preview
            body_text = await page.locator("body").inner_text()
            logger.info(f"Success page body text length: {len(body_text)}")
            logger.info("First 1000 characters of body text:")
            print(body_text[:1000])
            
        except Exception as e:
            logger.error(f"Error occurred: {e}")
            
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())

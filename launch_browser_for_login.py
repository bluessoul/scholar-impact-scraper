import asyncio
import os
import sys
import logging
from playwright.async_api import async_playwright

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    async with async_playwright() as p:
        user_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".playwright_profile"))
        logger.info("="*80)
        logger.info("🚀 启动机构订阅登录浏览器 / Launching Persistent Browser for Subscription Login...")
        logger.info(f"保存路径 / Profile Directory: {user_data_dir}")
        logger.info("="*80)
        
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            args=["--start-maximized"]
        )
        
        pages = context.pages
        page = pages[0] if pages else await context.new_page()
        
        # Go to Web of Science login page or main page
        url = "https://www.webofscience.com/wos/author/record/GPW-7178-2022"
        logger.info(f"正在导航至学者页面 / Navigating to: {url}")
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            
            print("\n" + "="*90)
            print("💡  [提示 / INSTRUCTIONS]")
            print("1. 如果页面提示 'Author record was not found'，这是因为您当前处于 Web of Science 免费版视图。")
            print("2. 请在浏览器窗口中【登录您的机构/大学订阅账号】(例如通过右上角 Sign In 或机构校外访问 VPN 登录)。")
            print("3. 登录成功后，请重新刷新此学者页面以确认能正常显示其文献和引用数据。")
            print("4. 登录完成后，请直接【关闭浏览器窗口】。脚本会自动保存您的机构登录 Cookie！")
            print("="*90 + "\n")
            
            # Keep browser open until the user manually closes it
            while True:
                await asyncio.sleep(2)
                # Check if browser context is still active by trying to get pages
                if not context.pages:
                    break
        except Exception as e:
            logger.error(f"发生错误 / Error: {e}")
        finally:
            logger.info("浏览器已关闭，登录 Cookie 已被持久化保存！")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("已通过 Ctrl+C 退出。")

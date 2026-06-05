import asyncio
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
        logger.info("Launching browser...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        url = "https://www.webofscience.com/wos/author/record/GPW-7178-2022"
        logger.info(f"Navigating to {url}...")
        
        try:
            await page.goto(url, wait_until="commit", timeout=30000)
            logger.info("Committed. Sleeping 15 seconds to let dynamic content render...")
            await asyncio.sleep(15)
            
            # Save screenshot
            await page.screenshot(path="wos_dump_screenshot.png")
            logger.info("Screenshot saved to wos_dump_screenshot.png")
            
            # Save HTML content
            content = await page.content()
            with open("wos_page.html", "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("HTML content saved to wos_page.html")
            
            # Print page body text
            body_text = await page.locator("body").inner_text()
            logger.info(f"Body text length: {len(body_text)}")
            logger.info("First 1000 characters of body text:")
            print(body_text[:1000])
            
        except Exception as e:
            logger.error(f"Error occurred: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

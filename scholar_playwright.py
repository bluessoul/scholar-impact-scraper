#!/usr/bin/env python3
"""
Google Scholar Profile Scraper (Playwright Async Version)
Extracts publication records defensively with non-headless human emulation and manual CAPTCHA recovery.
"""

import os
import re
import sys
import csv
import random
import asyncio
import logging
import argparse
import urllib.parse
import requests
import pandas as pd
from playwright.async_api import async_playwright

def is_profile_likely_initialized(profile_dir: str) -> bool:
    return os.path.isdir(profile_dir) and bool(os.listdir(profile_dir))


def write_first_run_login_setup(profile_dir: str) -> None:
    artifact_path = os.path.join(os.getcwd(), "FIRST_RUN_LOGIN_SETUP.md")
    content = f"""# First Run Login Setup

This project uses a local Playwright profile to save browser login state.

Profile directory:

`{profile_dir}`

Recommended setup before live Web of Science lookup:

1. Run `python launch_browser_for_login.py`.
2. In the opened browser, log in with an institutional or personal account you are authorized to use.
3. Verify that Web of Science works for your target profile.
4. Close the browser window so cookies and session state are saved locally.

For Clarivate/JCR login, run `launch_jcr_login.bat`.

Do not commit or share `.playwright_profile/`, `.env`, or `config.json`.

Timestamp: {__import__('datetime').datetime.now().isoformat(timespec='seconds')}
"""
    try:
        with open(artifact_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"First-run login setup artifact written to: {artifact_path}")
    except Exception as exc:
        logger.warning(f"Failed to write first-run login setup artifact: {exc}")


def remind_first_run_login_setup(profile_dir: str, uses_wos: bool) -> None:
    if os.getenv("SKIP_LOGIN_REMINDER") == "1":
        return
    if is_profile_likely_initialized(profile_dir):
        return

    print("\n" + "=" * 80)
    print("[First Run Login Setup]")
    print("No existing .playwright_profile was detected.")
    print("The script can continue, but Web of Science/JCR access may require a saved browser login.")
    print("")
    print("Recommended setup:")
    print("  - Web of Science: python launch_browser_for_login.py")
    print("  - JCR: launch_jcr_login.bat")
    print("")
    if uses_wos:
        print("Because --wos-id was provided, logging in once before extraction is recommended.")
    print("Do not commit or share .playwright_profile/.")
    print("=" * 80 + "\n")

    write_first_run_login_setup(profile_dir)


def fetch_doi_via_crossref(title: str) -> str:
    """
    Queries Crossref API to find the DOI of a paper by its title (Option 2).
    Returns 'https://doi.org/{doi}' if found, else 'N/A'.
    """
    if not title or title == "N/A":
        return "N/A"
        
    encoded_title = urllib.parse.quote_plus(title)
    url = f"https://api.crossref.org/works?query.title={encoded_title}&rows=1"
    headers = {
        "User-Agent": "ScholarScraper/1.0 (mailto:scholar_scraper@example.com)"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            items = data.get("message", {}).get("items", [])
            if items:
                primary = items[0]
                doi = primary.get("DOI")
                if doi:
                    return f"https://doi.org/{doi}"
        return "N/A"
    except Exception as e:
        logger.warning(f"Crossref lookup failed for '{title[:40]}...': {e}")
        raise

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def handle_captcha_if_needed(page) -> None:
    """
    Checks if Google has triggered a CAPTCHA or blocked the request (sorry page).
    If triggered, pauses execution until the user manually solves it in the opened browser.
    """
    # Google Scholar redirects to a URL containing "sorry/index" when a CAPTCHA is triggered
    sorry_selector = "iframe[src*='sorry']"
    
    while "sorry" in page.url or await page.is_visible(sorry_selector):
        print("\n" + "="*80)
        print("⚠️  [警告] 谷歌学术触发了人机验证码 (CAPTCHA) 阻断保护！")
        print("Google Scholar has triggered a CAPTCHA. The script is PAUSED.")
        print("请在弹出的浏览器窗口中【手动完成验证码验证】以恢复执行。")
        print("Please manually solve the CAPTCHA in the open Chromium browser window.")
        print("="*80 + "\n")
        
        # Log status every 5 seconds while waiting
        await asyncio.sleep(5)
        
    # Once solved, ensure the profile elements are visible before continuing
    try:
        await page.wait_for_selector("#gsc_prf", timeout=10000)
    except Exception:
        pass

async def handle_wos_captcha_if_needed(page) -> None:
    """
    Checks if Web of Science has triggered a security verification or bot block.
    Pauses execution until the user manually solves it in the opened browser window.
    """
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

async def scrape_wos_citations(orcid_id: str, page, fetch_wos_ut: bool = False) -> dict:
    """
    Queries Web of Science public profile using Playwright to extract WoS citation counts
    and optional Accession Numbers.
    Returns a dictionary mapping {normalized_title: {"citations": citation_count, "accession_number": ut_number}}.
    """
    clean_id = orcid_id.strip().split('/')[-1]
    url = f"https://www.webofscience.com/wos/author/record/{clean_id}"
    logger.info(f"Navigating to Web of Science Profile: {url}...")
    
    wos_citations = {}
    
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        # Give some time for initial load or redirects
        await asyncio.sleep(5)
        
        # Check if initially blocked by Captcha or cookie overlay
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
            logger.warning("Web of Science profile page is BLOCKED initially. Entering CAPTCHA wait...")
            await handle_wos_captcha_if_needed(page)
            
            # Re-navigate to the original URL now that the session is authenticated and has cookies!
            logger.info(f"Re-navigating to Web of Science Profile after solving block: {url}...")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(6)
        else:
            logger.info("No initial Web of Science block detected. Proceeding...")
        logger.info("Waiting for Web of Science publication items to load...")
        
        # Dismiss onboarding 'Got it' overlay guide if visible
        try:
            got_it_btn = page.locator("button:has-text('Got it')")
            if await got_it_btn.count() > 0 and await got_it_btn.first.is_visible():
                logger.info("Found onboarding 'Got it' guide popup. Clicking to dismiss...")
                await got_it_btn.first.click()
                await asyncio.sleep(2)
        except Exception as e:
            logger.debug(f"Failed to dismiss onboarding guide: {e}")
            
        # Stepwise scroll down to trigger lazy loading of publications
        logger.info("Scrolling down step-by-step to trigger Web of Science publications lazy loading...")
        for scroll_offset in [800, 1600, 2400, 3200, 4000]:
            await page.evaluate(f"window.scrollTo(0, {scroll_offset})")
            # Dynamic buffer sleep
            await asyncio.sleep(2.0)
            
        try:
            await page.wait_for_selector("app-record, .publication-item, [class*='publication-item'], app-record-list-item", timeout=20000)
        except Exception:
            # Check for Captcha again if wait times out
            await handle_wos_captcha_if_needed(page)
            # Re-navigate if blocked again
            try:
                body_text2 = await page.locator("body").inner_text()
            except Exception:
                body_text2 = ""
            if any(kw.lower() in body_text2.lower() for kw in block_keywords):
                logger.info(f"Re-navigating to Web of Science Profile after solving secondary block: {url}...")
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(6)
            
        # Extract author-level metrics (H-Index, Citations, 他引)
        wos_h_index = "N/A"
        wos_sum_cited = "N/A"
        wos_sum_cited_without_self = "N/A"
        try:
            logger.info("Extracting Web of Science author-level metrics (H-Index, Citations, 他引)...")
            descriptors = page.locator(".wat-author-metric-descriptor")
            desc_count = await descriptors.count()
            for i in range(desc_count):
                desc_el = descriptors.nth(i)
                desc_text = (await desc_el.inner_text()).strip()
                parent = desc_el.locator("..")
                value_el = parent.locator(".wat-author-metric")
                if await value_el.count() > 0:
                    val_text = (await value_el.nth(0).inner_text()).strip()
                    
                    sub_desc_el = parent.locator(".wat-author-metric-sub-descriptor")
                    sub_desc_text = ""
                    if await sub_desc_el.count() > 0:
                        sub_desc_text = (await sub_desc_el.inner_text()).strip().lower()
                    
                    if desc_text.lower() == "h-index":
                        wos_h_index = val_text
                    elif desc_text.lower() == "sum of times cited":
                        if "without self-citations" in sub_desc_text:
                            wos_sum_cited_without_self = val_text
                        else:
                            wos_sum_cited = val_text
            logger.info(f"Web of Science Metrics: H-Index={wos_h_index}, Citations={wos_sum_cited}, 他引={wos_sum_cited_without_self}")
        except Exception as e:
            logger.warning(f"Failed to extract Web of Science author metrics: {e}")

        # Get all publication cards
        items = await page.locator("app-record, .publication-item, [class*='publication-item'], app-record-list-item").all()
        logger.info(f"Located {len(items)} publication records on Web of Science page.")
        
        for item in items:
            try:
                # Title: Check primary audited selectors, then fallback
                title_el = item.locator("a.title, a.title-link, .publication-title")
                title = ""
                if await title_el.count() > 0:
                    title = (await title_el.nth(0).inner_text()).strip()
                
                # Citations: Check primary audited selectors, then fallback
                citations = 0
                citations_el = item.locator("a[data-ta='stat-number-citation-related-count'], div.citations a.stat-number, .times-cited-value, [class*='times-cited']")
                if await citations_el.count() > 0:
                    cit_text = (await citations_el.nth(0).inner_text()).strip()
                    clean_cit = re.sub(r'\D', '', cit_text)
                    citations = int(clean_cit) if clean_cit else 0
                
                # WoS Accession Number (UT)
                ut_number = "N/A"
                if fetch_wos_ut:
                    links = await item.locator("a[href]").all()
                    for link in links:
                        href = await link.get_attribute("href")
                        if href:
                            match = re.search(r'WOS:[A-Z0-9]+', href, re.IGNORECASE)
                            if match:
                                ut_number = match.group(0).upper()
                                break
                
                if title:
                    # Normalize title (lowercase, alphanumeric only)
                    norm_title = re.sub(r'[^a-z0-9]', '', title.lower())
                    wos_citations[norm_title] = {
                        "citations": citations,
                        "accession_number": ut_number
                    }
                    logger.info(f"WoS Scraped: '{title[:45]}...' | Citations: {citations} | UT: {ut_number}")
            except Exception as e:
                logger.debug(f"Error parsing WoS item: {e}")
                
    except Exception as e:
        logger.error(f"Failed to scrape Web of Science citations: {e}")
        
    return {
        "citations_map": wos_citations,
        "h_index": wos_h_index,
        "sum_cited": wos_sum_cited,
        "sum_cited_without_self": wos_sum_cited_without_self
    }

async def scrape_scholar_profile(profile_url: str, output_csv: str, max_clicks: int, refine_mode: str = "auto", refine_limit: int = 10, fetch_doi: bool = False, wos_id: str = None, fetch_wos_ut: bool = False) -> None:
    """
    Launches a non-headless Playwright Chromium instance, navigates to the Scholar profile,
    handles dynamic pagination with "Show more", pauses for manual CAPTCHA solving,
    extracts complete publication metadata (including optional deep modal refinement),
    and saves sorted CSVs, integrating Web of Science citation counts and Accession Numbers.
    """
    logger.info("Initializing Playwright Async Engine...")
    
    async with async_playwright() as p:
        # Define a persistent user data directory inside the workspace
        user_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".playwright_profile"))
        remind_first_run_login_setup(user_data_dir, uses_wos=bool(wos_id))
        logger.info(f"Launching visible Chromium with persistent profile: {user_data_dir}...")
        
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            args=["--start-maximized"]
        )
        
        # Get already opened page or open a new one
        pages = context.pages
        page = pages[0] if pages else await context.new_page()
        
        logger.info(f"Navigating to Scholar Profile: {profile_url}...")
        try:
            await page.goto(profile_url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            logger.warning(f"Initial navigation warning (timeout/other): {e}. Proceeding anyway...")
        
        # Check for CAPTCHA immediately upon loading
        await handle_captcha_if_needed(page)
        
        # Click reject cookies if the consent dialog appears to clean the viewport
        try:
            reject_cookies = page.locator("button:has-text('Reject Unnecessary Cookies')")
            if await reject_cookies.is_visible():
                await reject_cookies.click()
                logger.info("Cookie consent dialog dismissed.")
        except Exception:
            pass
            
        show_more_selector = "#gsc_bpf_more"
        
        # ==========================================
        # Dynamic Pagination Loop ("Show more")
        # ==========================================
        # Enhanced pagination loop with human‑like evasion tactics
        click_count = 0  # Track number of "Show more" clicks
        while True:
            # Check for CAPTCHA before each interaction
            await handle_captcha_if_needed(page)

            show_more_button = page.locator(show_more_selector)

            # Verify button presence
            if await show_more_button.count() == 0:
                logger.info("Show more button is no longer present. Reached the end of the profile.")
                break

            # Verify button enabled state
            if await show_more_button.get_attribute("disabled") is not None:
                logger.info("Show more button is disabled. All publications are successfully expanded.")
                break

            # Human‑like delay using Gaussian distribution (mean 4.5s, sigma 1.2s)
            raw_delay = random.gauss(4.5, 1.2)
            delay = max(2.0, min(8.0, raw_delay))  # clamp between 2‑8 seconds
            logger.info(f"Human‑like pacing delay: waiting {delay:.2f}s before click #{click_count + 1}.")
            await asyncio.sleep(delay)

            # Capture current row count for later comparison
            initial_row_count = await page.locator("tr.gsc_a_tr").count()

            # Ensure button is in view
            await show_more_button.scroll_into_view_if_needed()

            # Randomized click within button's bounding box
            bbox = await show_more_button.bounding_box()
            if bbox is None:
                logger.warning("Unable to obtain button bounding box; falling back to default click.")
                await show_more_button.click(timeout=10000)
            else:
                # Choose a random point inside the box, avoiding edges (5% margin)
                margin_x = bbox["width"] * 0.05
                margin_y = bbox["height"] * 0.05
                x_offset = random.uniform(margin_x, bbox["width"] - margin_x)
                y_offset = random.uniform(margin_y, bbox["height"] - margin_y)
                click_x = bbox["x"] + x_offset
                click_y = bbox["y"] + y_offset
                logger.info(f"Moving mouse to ({click_x:.1f}, {click_y:.1f}) and clicking within button.")
                # Human‑like mouse movement (smooth steps)
                await page.mouse.move(click_x, click_y, steps=30)
                await page.mouse.click(click_x, click_y)
                logger.info("Clicked 'Show more' button.")

            click_count += 1

            # Stop if reached max clicks limit
            if click_count >= max_clicks:
                logger.info(f"Reached maximum of {max_clicks} 'Show more' clicks; stopping pagination.")
                break

            # Random micro‑scrolling with 25‑30% probability after a click
            if random.random() < 0.27:
                scroll_amount = random.randint(100, 300)
                logger.info(f"Performing micro‑scroll of {scroll_amount}px to mimic reading behavior.")
                await page.mouse.wheel(0, scroll_amount)
                await asyncio.sleep(random.uniform(0.5, 1.5))

            # Periodic "reading" pause every 5‑7 clicks
            pause_interval = random.randint(5, 7)
            if click_count % pause_interval == 0:
                read_pause = max(6.0, random.gauss(12.0, 3.0))
                logger.info(f"Simulated reading pause after {click_count} clicks: waiting {read_pause:.2f}s.")
                await asyncio.sleep(read_pause)

            # Wait for new rows to load (max ~5 seconds)
            rows_loaded = False
            for _ in range(25):
                await asyncio.sleep(0.2)
                await handle_captcha_if_needed(page)
                new_row_count = await page.locator("tr.gsc_a_tr").count()
                if new_row_count > initial_row_count:
                    logger.info(f"Loaded new rows. Row count increased from {initial_row_count} to {new_row_count}.")
                    rows_loaded = True
                    break

            if not rows_loaded:
                logger.info("No new rows detected after click. Checking if we reached the end...")
                if await show_more_button.count() == 0 or await show_more_button.get_attribute("disabled") is not None:
                    break
                    
        # ==========================================
        # Publication Data Extraction
        # ==========================================
        logger.info("All publications expanded. Beginning data extraction...")

        # Extract Google Scholar author stats
        scholar_citations = "N/A"
        scholar_h_index = "N/A"
        try:
            logger.info("Extracting Google Scholar author-level metrics...")
            rows_stats = await page.locator("tr:has(.gsc_rsb_f)").all()
            for r in rows_stats:
                label_el = r.locator(".gsc_rsb_f")
                val_els = r.locator("td.gsc_rsb_std")
                if await label_el.count() > 0 and await val_els.count() > 0:
                    label = (await label_el.nth(0).inner_text()).strip().lower()
                    val_all = (await val_els.nth(0).inner_text()).strip()
                    if "citations" in label:
                        scholar_citations = val_all
                    elif "h-index" in label:
                        scholar_h_index = val_all
            logger.info(f"Google Scholar Metrics: Citations={scholar_citations}, H-Index={scholar_h_index}")
        except Exception as e:
            logger.warning(f"Failed to extract Google Scholar author stats: {e}")
        
        rows = await page.locator("tr.gsc_a_tr").all()
        total_rows = len(rows)
        logger.info(f"Total publication rows identified: {total_rows}")
        
        extracted_data = []
        
        for idx, row in enumerate(rows, 1):
            title = "N/A"
            authors = "N/A"
            venue = "N/A"
            citations = 0
            year = "N/A"
            
            try:
                # 1. Extract Title
                title_loc = row.locator(".gsc_a_t a")
                if await title_loc.count() > 0:
                    title = (await title_loc.inner_text()).strip()
                    
                # 2. Extract Authors (first .gs_gray inside .gsc_a_t)
                gray_locs = row.locator(".gsc_a_t .gs_gray")
                if await gray_locs.count() > 0:
                    authors = (await gray_locs.nth(0).inner_text()).strip()
                    
                # 3. Extract Venue/Journal (second .gs_gray inside .gsc_a_t)
                if await gray_locs.count() > 1:
                    venue = (await gray_locs.nth(1).inner_text()).strip()
                    
                # 4. Extract Citations (.gsc_a_c a)
                citations_loc = row.locator(".gsc_a_c a")
                if await citations_loc.count() > 0:
                    cit_text = (await citations_loc.inner_text()).strip()
                    if cit_text:
                        # Clean and convert citations to integer
                        try:
                            # Replace any non-digit character like "*" or ","
                            clean_cit = re.sub(r'\D', '', cit_text)
                            citations = int(clean_cit) if clean_cit else 0
                        except ValueError:
                            citations = 0
                            
                # 5. Extract Year (.gsc_a_y span)
                year_loc = row.locator(".gsc_a_y span")
                if await year_loc.count() > 0:
                    year = (await year_loc.inner_text()).strip()
                else:
                    # Fallback to direct .gsc_a_y if span is absent
                    year_loc_direct = row.locator(".gsc_a_y")
                    if await year_loc_direct.count() > 0:
                        year = (await year_loc_direct.inner_text()).strip()
                        
            except Exception as e:
                logger.error(f"Row {idx}: Failed to extract columns cleanly: {e}")
                
            extracted_data.append({
                "Title": title,
                "Authors": authors,
                "Journal/Venue": venue,
                "Citations": citations,
                "WoS Citations": "N/A",  # Default to N/A
                "Year": year,
                "Publication Date": year,  # Default to Year
                "DOI": "N/A",  # Default to N/A
                "Scholar Author Citations": scholar_citations,
                "Scholar Author H-Index": scholar_h_index,
                "WoS Author Citations": "N/A",
                "WoS Author Citations (Non-Self)": "N/A",
                "WoS Author H-Index": "N/A"
            })


        # ==========================================
        # Secondary Refinement ("Refined Crawl")
        # ==========================================
        refine_indices = []
        if refine_mode == "auto":
            # Auto-detect papers with truncated authors
            for idx, data in enumerate(extracted_data):
                if "..." in data["Authors"]:
                    refine_indices.append(idx)
            logger.info(f"Auto-detected {len(refine_indices)} papers with truncated author lists for refinement.")
        elif refine_mode == "all":
            refine_indices = list(range(len(extracted_data)))
            logger.info(f"Selected all {len(refine_indices)} papers for refinement.")
        elif refine_mode != "none":
            # Parse comma-separated list of 1-based indices
            try:
                parts = [int(p.strip()) - 1 for p in refine_mode.split(",") if p.strip().isdigit()]
                refine_indices = [p for p in parts if 0 <= p < len(extracted_data)]
                logger.info(f"Parsed manual refinement indices: {[p + 1 for p in refine_indices]}")
            except Exception as e:
                logger.error(f"Failed to parse refine indices '{refine_mode}': {e}")

        # Limit refinement to avoid anti-bot blocks
        if refine_indices:
            refined_count = 0
            to_refine = refine_indices[:refine_limit]
            logger.info(f"Refining top {len(to_refine)} selected papers (limited by --refine-limit={refine_limit}) to evade bot detection...")

            for idx in to_refine:
                paper = extracted_data[idx]
                logger.info(f"[{refined_count + 1}/{len(to_refine)}] Refining paper #{idx + 1}: '{paper['Title']}'")

                try:
                    # Check for CAPTCHA before clicking
                    await handle_captcha_if_needed(page)

                    # Locate the paper's title link. The link has index `idx` in the table rows
                    title_locator = page.locator("tr.gsc_a_tr a.gsc_a_at").nth(idx)
                    if await title_locator.count() == 0:
                        logger.warning(f"Could not locate title link in DOM for paper #{idx + 1}; skipping.")
                        continue

                    # Scroll link into view
                    await title_locator.scroll_into_view_if_needed()

                    # Human-like delay before click (Gaussian, mean 4.0s, sigma 1.0s)
                    raw_delay = random.gauss(4.0, 1.0)
                    delay = max(1.5, min(7.0, raw_delay))
                    logger.info(f"Waiting {delay:.2f}s before opening details...")
                    await asyncio.sleep(delay)

                    # Get bounding box for randomized click coordinates
                    bbox = await title_locator.bounding_box()
                    if bbox is None:
                        await title_locator.click(timeout=10000)
                    else:
                        margin_x = bbox["width"] * 0.05
                        margin_y = bbox["height"] * 0.05
                        x_offset = random.uniform(margin_x, bbox["width"] - margin_x)
                        y_offset = random.uniform(margin_y, bbox["height"] - margin_y)
                        click_x = bbox["x"] + x_offset
                        click_y = bbox["y"] + y_offset
                        # Smooth mouse move and click
                        await page.mouse.move(click_x, click_y, steps=25)
                        await page.mouse.click(click_x, click_y)

                    # Wait for detail modal to load
                    await page.wait_for_selector("#gsc_oci_table", timeout=12000)
                    await handle_captcha_if_needed(page)

                    # Extract full authors list and publication date
                    fields = await page.locator(".gsc_oci_field").all_inner_texts()
                    values = await page.locator(".gsc_oci_value").all_inner_texts()

                    full_authors = None
                    pub_date = None
                    for f, v in zip(fields, values):
                        field_name = f.strip().lower()
                        if field_name == "authors":
                            full_authors = v.strip()
                        elif field_name == "publication date":
                            pub_date = v.strip()

                    if full_authors:
                        # Success! Update the author list
                        logger.info(f"Successfully refined author list: {full_authors}")
                        extracted_data[idx]["Authors"] = full_authors
                    else:
                        logger.warning("Could not locate 'Authors' field in detail page.")

                    if pub_date:
                        # Success! Update the publication date
                        logger.info(f"Successfully refined publication date: {pub_date}")
                        extracted_data[idx]["Publication Date"] = pub_date
                    else:
                        logger.warning("Could not locate 'Publication date' field in detail page.")

                    # Close details by clicking the back button #gs_hdr_bck
                    back_btn = page.locator("#gs_hdr_bck")
                    if await back_btn.count() > 0:
                        # Human-like delay before going back
                        raw_back_delay = random.gauss(2.5, 0.5)
                        back_delay = max(1.0, min(5.0, raw_back_delay))
                        await asyncio.sleep(back_delay)

                        back_bbox = await back_btn.bounding_box()
                        if back_bbox:
                            x_offset = random.uniform(back_bbox["width"] * 0.1, back_bbox["width"] * 0.9)
                            y_offset = random.uniform(back_bbox["height"] * 0.1, back_bbox["height"] * 0.9)
                            await page.mouse.move(back_bbox["x"] + x_offset, back_bbox["y"] + y_offset, steps=20)
                            await page.mouse.click(back_bbox["x"] + x_offset, back_bbox["y"] + y_offset)
                        else:
                            await back_btn.click()

                        # Wait for profile page to restore
                        await page.wait_for_selector("#gsc_prf", timeout=10000)
                    else:
                        logger.warning("Could not find back button to return to profile.")

                    refined_count += 1

                except Exception as e:
                    logger.error(f"Failed to refine paper #{idx + 1}: {e}")
                    # Try to force return to main profile page if stuck
                    try:
                        if await page.locator("#gs_hdr_bck").is_visible():
                            await page.click("#gs_hdr_bck")
                            await page.wait_for_selector("#gsc_prf", timeout=10000)
                    except Exception:
                        pass
            
        # ==========================================
        # Web of Science Citations Extraction
        # ==========================================
        if wos_id:
            logger.info("Initializing Web of Science Core Collection citation extraction...")
            try:
                wos_res = await scrape_wos_citations(wos_id, page, fetch_wos_ut=fetch_wos_ut)
                wos_citations_map = wos_res.get("citations_map", {})
                wos_sum_cited = wos_res.get("sum_cited", "N/A")
                wos_sum_cited_without_self = wos_res.get("sum_cited_without_self", "N/A")
                wos_h_index = wos_res.get("h_index", "N/A")
                
                logger.info(f"Web of Science extraction finished. Retrieved {len(wos_citations_map)} matching records.")
                for idx, data in enumerate(extracted_data):
                    title = data["Title"]
                    norm_title = re.sub(r'[^a-z0-9]', '', title.lower())
                    wos_info = wos_citations_map.get(norm_title, {"citations": "N/A", "accession_number": "N/A"})
                    extracted_data[idx]["WoS Citations"] = wos_info.get("citations", "N/A")
                    extracted_data[idx]["WoS Author Citations"] = wos_sum_cited
                    extracted_data[idx]["WoS Author Citations (Non-Self)"] = wos_sum_cited_without_self
                    extracted_data[idx]["WoS Author H-Index"] = wos_h_index
                    if fetch_wos_ut:
                        extracted_data[idx]["WoS Accession Number"] = wos_info.get("accession_number", "N/A")
            except Exception as e:
                logger.error(f"Error matching Web of Science citations: {e}")

        # Close persistent context safely
        logger.info("Closing persistent browser context...")
        await context.close()

        # ==========================================
        # Fetching DOIs via Crossref (Option 2)
        # ==========================================
        if fetch_doi and extracted_data:
            logger.info("Fetching DOIs via Crossref API (Option 2)...")
            import time
            try:
                for idx, data in enumerate(extracted_data):
                    title = data["Title"]
                    logger.info(f"[{idx+1}/{len(extracted_data)}] Querying Crossref DOI for: '{title[:50]}...'")
                    doi = fetch_doi_via_crossref(title)
                    extracted_data[idx]["DOI"] = doi
                    # Polite rate-limiting delay for Crossref API
                    time.sleep(0.3)
            except Exception as e:
                logger.error(f"Crossref DOI fetching failed/interrupted: {e}")
                print("\n" + "="*70)
                print("⚠️  [警告] Crossref DOI 查询 (方案二) 失败或被限制。")
                print("建议采用【方案一】：")
                print("使用 orcid_extractor.py 脚本拉取该学者的 ORCID 记录。")
                print("ORCID 记录包含完美的、官方认证的原始 DOI 链接！")
                print("命令示例: python orcid_extractor.py --orcid [学者ORCID]")
                print("="*70)
        
        # ==========================================
        # Sorting and Saving CSV & Stats Summary
        # ==========================================
        if extracted_data:
            df = pd.DataFrame(extracted_data)
            
            # Sort by Citations descending
            df_sorted = df.sort_values(by="Citations", ascending=False)
            
            # Save to CSV (using utf-8-sig for perfect Windows Excel encoding)
            df_sorted.to_csv(output_csv, index=False, encoding="utf-8-sig")
            logger.info(f"Scraped data successfully saved to: {os.path.abspath(output_csv)}")
            logger.info(f"Total records saved: {len(df_sorted)}")
            
            # Extract stats metrics for JSON & terminal card
            first_row = extracted_data[0]
            wos_sum_cited_val = first_row.get("WoS Author Citations", "N/A")
            wos_sum_cited_without_self_val = first_row.get("WoS Author Citations (Non-Self)", "N/A")
            wos_h_index_val = first_row.get("WoS Author H-Index", "N/A")
            
            stats_summary = {
                "Google Scholar": {
                    "Total Citations": scholar_citations,
                    "H-Index": scholar_h_index
                },
                "Web of Science": {
                    "Total Citations": wos_sum_cited_val,
                    "Total Citations (Without Self-Citations)": wos_sum_cited_without_self_val,
                    "H-Index": wos_h_index_val
                }
            }
            
            # Save stats companion JSON file
            base_path, _ = os.path.splitext(output_csv)
            stats_json_path = f"{base_path}_stats.json"
            try:
                import json
                with open(stats_json_path, "w", encoding="utf-8") as f:
                    json.dump(stats_summary, f, indent=4, ensure_ascii=False)
                logger.info(f"Stats summary successfully saved to: {os.path.abspath(stats_json_path)}")
            except Exception as je:
                logger.warning(f"Failed to save companion stats JSON: {je}")
                
            # Print beautiful Author Impact Metrics Card
            print("\n" + "="*60)
            print("📊  【学者影响力指标汇总 / AUTHOR IMPACT METRICS SUMMARY】")
            print("="*60)
            print(f"  Google Scholar:")
            print(f"    - 被引总数 (Total Citations): {scholar_citations}")
            print(f"    - H-Index:                   {scholar_h_index}")
            if wos_id:
                print(f"  Web of Science (ID: {wos_id}):")
                print(f"    - 被引总数 (Total Citations): {wos_sum_cited_val}")
                print(f"    - 他引总数 (Non-Self Citations): {wos_sum_cited_without_self_val}")
                print(f"    - H-Index:                   {wos_h_index_val}")
            else:
                print(f"  Web of Science:")
                print(f"    - 被引总数 (Total Citations): N/A (未提供 --wos-id)")
                print(f"    - 他引总数 (Non-Self Citations): N/A (未提供 --wos-id)")
                print(f"    - H-Index:                   {wos_h_index_val}")
            print("="*60 + "\n")
        else:
            logger.warning("No records extracted. CSV was not generated.")

def main():
    parser = argparse.ArgumentParser(
        description="Scrape Google Scholar profiles securely using Playwright with CAPTCHA self-healing wait."
    )
    parser.add_argument(
        "--user-id",
        default="SQdUxqYAAAAJ",
        help="Google Scholar user profile ID (default: SQdUxqYAAAAJ)."
    )
    parser.add_argument(
        "--output",
        default="google_scholar_scraped.csv",
        help="Output CSV filepath (default: google_scholar_scraped.csv)."
    )
    parser.add_argument(
        "--max-clicks",
        type=int,
        default=5,
        help="Maximum number of 'Show more' clicks to perform (default 5) to reduce data load."
    )
    parser.add_argument(
        "--refine",
        default="none",
        help="Secondary refinement mode: 'auto' (truncations), 'none', 'all', or comma-separated indices (e.g. '1,2,5')."
    )
    parser.add_argument(
        "--refine-limit",
        type=int,
        default=10,
        help="Maximum number of papers to refine (default 10) to avoid bot detection."
    )
    parser.add_argument(
        "--fetch-doi",
        action="store_true",
        help="Query Crossref API to fetch and store DOI links for each publication."
    )
    parser.add_argument(
        "--wos-id",
        default=None,
        help="Web of Science ResearcherID or ORCID iD for citation mapping (e.g., 0000-0002-0499-6138)."
    )
    parser.add_argument(
        "--fetch-wos-ut",
        dest="fetch_wos_ut",
        action="store_true",
        help="Explicitly enable extraction of Web of Science Accession Numbers (UT)."
    )
    parser.add_argument(
        "--no-wos-ut",
        dest="fetch_wos_ut",
        action="store_false",
        help="Explicitly disable extraction of Web of Science Accession Numbers (UT)."
    )
    parser.set_defaults(fetch_wos_ut=None)
    
    args = parser.parse_args()
    
    fetch_wos_ut = args.fetch_wos_ut
    if args.wos_id and fetch_wos_ut is None:
        print("\n" + "="*80)
        print("📋  [提示 / PROMPT]")
        print("是否需要为每篇论文提取 Web of Science 入藏号 (Accession Number, UT)？")
        print("Do you want to extract and include Web of Science Accession Numbers (UT) in the CSV?")
        print("="*80)
        try:
            choice = input("请输入 Y (需要) 或 N (不需要)，默认 [N]: ").strip().lower()
            fetch_wos_ut = choice == 'y'
        except Exception:
            fetch_wos_ut = False
            
    # Standard profile URL format
    profile_url = f"https://scholar.google.com/citations?hl=en&user={args.user_id.strip()}"
    
    # Run Async scraping loop - Default Highest Success Rate Method (Playwright + Human Evasion)
    try:
        asyncio.run(scrape_scholar_profile(
            profile_url, 
            args.output, 
            args.max_clicks, 
            args.refine, 
            args.refine_limit, 
            args.fetch_doi,
            wos_id=args.wos_id,
            fetch_wos_ut=fetch_wos_ut
        ))
    except KeyboardInterrupt:
        logger.info("Process interrupted by user. Exiting.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Google Scholar Playwright extraction failed: {e}")
        print("\n" + "="*70)
        print("⚠️  [警告] Google Scholar Playwright (防封锁人类模拟) 抓取失败或被中断。")
        print("您可以选择运行以下备用方法：")
        print("1. 使用 scholarly 开源库 (简单 API 封装，不使用浏览器，但极易被谷歌封锁)")
        print("2. 使用 免费代理 / 代理 API 方式 (需配置代理服务器)")
        print("="*70)
        choice = input("请输入您想尝试的备份方法编号 (1/2)，或按回车退出: ").strip()
        if choice == "1":
            print("\n正在尝试运行 scholarly 备份方案...")
            try:
                from scholarly import scholarly
                print(f"Searching author ID: {args.user_id}...")
                author = scholarly.search_author_id(args.user_id)
                print("Filling publications list...")
                author = scholarly.fill(author, sections=['publications'])
                publications = author.get('publications', [])
                logger.info(f"Found {len(publications)} publications via scholarly.")
                if publications:
                    # Extract H-Index and total citations from scholarly profile
                    scholar_citations = author.get('citedby', 'N/A')
                    scholar_h_index = author.get('hindex', 'N/A')
                    
                    # Save to CSV
                    import pandas as pd
                    extracted = []
                    for pub in publications:
                        bib = pub.get('bib', {})
                        extracted.append({
                            "Title": bib.get('title', 'N/A'),
                            "Authors": bib.get('author', 'N/A'),
                            "Journal/Venue": bib.get('journal', bib.get('venue', 'N/A')),
                            "Citations": pub.get('num_citations', 0),
                            "WoS Citations": "N/A",
                            "Year": bib.get('pub_year', 'N/A'),
                            "Publication Date": bib.get('pub_year', 'N/A'),
                            "DOI": "N/A",
                            "Scholar Author Citations": scholar_citations,
                            "Scholar Author H-Index": scholar_h_index,
                            "WoS Author Citations": "N/A",
                            "WoS Author Citations (Non-Self)": "N/A",
                            "WoS Author H-Index": "N/A"
                        })
                    df = pd.DataFrame(extracted)
                    df_sorted = df.sort_values(by="Citations", ascending=False)
                    df_sorted.to_csv(args.output, index=False, encoding="utf-8-sig")
                    logger.info(f"Successfully saved scholarly fallback data to: {args.output}")
                    
                    # Save stats summary companion JSON
                    stats_summary = {
                        "Google Scholar": {
                            "Total Citations": scholar_citations,
                            "H-Index": scholar_h_index
                        },
                        "Web of Science": {
                            "Total Citations": "N/A",
                            "Total Citations (Without Self-Citations)": "N/A",
                            "H-Index": "N/A"
                        }
                    }
                    base_path, _ = os.path.splitext(args.output)
                    stats_json_path = f"{base_path}_stats.json"
                    try:
                        import json
                        with open(stats_json_path, "w", encoding="utf-8") as f:
                            json.dump(stats_summary, f, indent=4, ensure_ascii=False)
                    except Exception:
                        pass
                        
                    # Print metrics card for fallback
                    print("\n" + "="*60)
                    print("📊  【学者影响力指标汇总 / AUTHOR IMPACT METRICS SUMMARY】")
                    print("="*60)
                    print(f"  Google Scholar (via scholarly fallback):")
                    print(f"    - 被引总数 (Total Citations): {scholar_citations}")
                    print(f"    - H-Index:                   {scholar_h_index}")
                    print(f"  Web of Science:")
                    print(f"    - 被引总数 (Total Citations): N/A")
                    print(f"    - 他引总数 (Non-Self Citations): N/A")
                    print(f"    - H-Index:                   N/A")
                    print("="*60 + "\n")
                else:
                    logger.error("scholarly found no publications.")
                    sys.exit(1)
            except Exception as se:
                logger.critical(f"scholarly fallback also failed: {se}")
                sys.exit(1)
        elif choice == "2":
            print("\n提示：代理旋转方法需要配置海外代理服务端口或购买 ScraperAPI 等服务，请检查您的 .env 代理配置后再试。")
            sys.exit(1)
        else:
            print("退出。")
            sys.exit(1)

if __name__ == "__main__":
    main()

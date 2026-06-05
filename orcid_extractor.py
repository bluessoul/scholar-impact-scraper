#!/usr/bin/env python3
"""
ORCID Publication Extractor (API v3.0)
Extracts all publication records for a specific scholar and saves them to a sorted CSV.
"""

import os
import csv
import sys
import argparse
import logging
import requests
from dotenv import load_dotenv

# Set up logging for professional user feedback
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables if a .env file is present
load_dotenv()

def get_access_token(client_id: str, client_secret: str, use_sandbox: bool = False) -> str:
    """
    Exchanges Client ID and Client Secret for an OAuth access token.
    Uses endpoint: https://orcid.org/oauth/token (or sandbox equivalent)
    """
    base_url = "https://sandbox.orcid.org" if use_sandbox else "https://orcid.org"
    token_url = f"{base_url}/oauth/token"
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "/read-public"
    }
    
    logger.info("Exchanging client credentials for an ORCID OAuth access token...")
    
    try:
        response = requests.post(token_url, headers=headers, data=payload, timeout=15)
        response.raise_for_status()
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise KeyError("The key 'access_token' was not found in the response.")
            
        logger.info("Access token obtained successfully.")
        return access_token
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to authenticate with ORCID API: {e}")
        if response is not None:
            logger.error(f"Response status: {response.status_code}, Response body: {response.text}")
        raise
    except (ValueError, KeyError) as e:
        logger.error(f"Failed to parse OAuth response token: {e}")
        raise

def fetch_orcid_works(orcid_id: str, access_token: str = None, use_sandbox: bool = False) -> dict:
    """
    Fetches all works for a given ORCID iD.
    Uses endpoint: https://pub.orcid.org/v3.0/{orcid}/works (or sandbox equivalent)
    """
    # Clean the ORCID ID format (remove URL prefix if user pasted the full URL)
    clean_orcid = orcid_id.strip().split('/')[-1]
    
    base_url = "https://pub.sandbox.orcid.org" if use_sandbox else "https://pub.orcid.org"
    works_url = f"{base_url}/v3.0/{clean_orcid}/works"
    
    headers = {
        "Accept": "application/vnd.orcid+json"  # Standard content type for ORCID v3.0 JSON schema
    }
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    
    logger.info(f"Fetching publication records for ORCID ID: {clean_orcid}...")
    
    try:
        response = requests.get(works_url, headers=headers, timeout=20)
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data from ORCID works endpoint: {e}")
        if response is not None:
            logger.error(f"Response status: {response.status_code}, Response body: {response.text}")
        raise

def parse_works(works_json: dict) -> list:
    """
    Parses the JSON response from ORCID works endpoint.
    Extracts Title, Publication Year, Journal/Venue name, and External IDs (such as DOI).
    Includes robust try-except blocks to handle missing fields gracefully.
    """
    extracted_works = []
    
    # Retrieve the group list where publication works are clustered by identifiers
    groups = works_json.get("group", [])
    if not groups:
        logger.warning("No publication groups found in the ORCID record.")
        return extracted_works
        
    logger.info(f"Parsing {len(groups)} publication groups from ORCID record...")
    
    for idx, group in enumerate(groups, 1):
        work_summaries = group.get("work-summary", [])
        if not work_summaries:
            continue
            
        # Select the first work-summary in the group as the primary representation
        # ORCID groups multiple source items of the same work together
        primary_summary = work_summaries[0]
        
        parsed_work = {
            "title": "",
            "publication_year": "",
            "journal_venue": "",
            "doi": "",
            "all_external_ids": ""
        }
        
        # 1. Extract Title
        try:
            parsed_work["title"] = primary_summary.get("title", {}).get("title", {}).get("value", "").strip()
        except Exception as e:
            logger.debug(f"Group {idx}: Error parsing title: {e}")
            parsed_work["title"] = "Unknown Title"
            
        # 2. Extract Publication Year
        try:
            year_val = primary_summary.get("publication-date", {}).get("year", {}).get("value", "")
            if year_val:
                parsed_work["publication_year"] = str(year_val).strip()
        except Exception as e:
            logger.debug(f"Group {idx}: Error parsing publication year: {e}")
            parsed_work["publication_year"] = ""
            
        # 3. Extract Journal/Venue name
        try:
            journal_val = primary_summary.get("journal-title", {}).get("value", "")
            if journal_val:
                parsed_work["journal_venue"] = str(journal_val).strip()
        except Exception as e:
            logger.debug(f"Group {idx}: Error parsing journal/venue name: {e}")
            parsed_work["journal_venue"] = ""
            
        # 4. Extract External IDs (DOI & Others)
        try:
            doi_list = []
            other_ids_list = []
            
            # The group object usually contains external-ids representing the group
            # But the individual work summary might also contain them. Let's merge or check both.
            ext_ids_container = group.get("external-ids", {}) or primary_summary.get("external-ids", {})
            ext_ids = ext_ids_container.get("external-id", [])
            
            for ext_id in ext_ids:
                id_type = str(ext_id.get("external-id-type", "")).strip().lower()
                id_val = str(ext_id.get("external-id-value", "")).strip()
                
                if id_type == "doi":
                    doi_list.append(id_val)
                elif id_val:
                    other_ids_list.append(f"{id_type.upper()}:{id_val}")
            
            # Set the primary DOI (take the first if multiple exist)
            if doi_list:
                parsed_work["doi"] = doi_list[0]
            
            # Create a combined string of all external IDs for complete tracking
            all_ids = []
            if doi_list:
                all_ids.extend([f"DOI:{d}" for d in doi_list])
            if other_ids_list:
                all_ids.extend(other_ids_list)
                
            parsed_work["all_external_ids"] = ", ".join(all_ids)
            
        except Exception as e:
            logger.debug(f"Group {idx}: Error parsing external IDs: {e}")
            parsed_work["doi"] = ""
            parsed_work["all_external_ids"] = ""
            
        # Ensure we have at least a title to record the work
        if parsed_work["title"]:
            extracted_works.append(parsed_work)
            
    return extracted_works

def save_to_csv(works: list, filename: str) -> None:
    """
    Cleans, sorts the works by publication year in descending order,
    and writes them to the specified CSV file.
    """
    # Key sorting function: parse year to integer if possible, else 0 (to sort invalid/empty years to the bottom)
    def get_sort_key(w):
        year_str = w.get("publication_year", "")
        try:
            return int(year_str)
        except ValueError:
            return 0

    # Sort works by Publication Year descending
    sorted_works = sorted(works, key=get_sort_key, reverse=True)
    
    headers = [
        "Title",
        "Publication Year",
        "Journal/Venue",
        "DOI",
        "External IDs"
    ]
    
    logger.info(f"Saving {len(sorted_works)} publication records to '{filename}'...")
    
    try:
        # Write directly to the CSV file
        with open(filename, mode='w', encoding='utf-8', newline='') as csv_file:
            writer = csv.writer(csv_file)
            
            # Write header row
            writer.writerow(headers)
            
            # Write data rows
            for w in sorted_works:
                writer.writerow([
                    w["title"],
                    w["publication_year"] if w["publication_year"] else "N/A",
                    w["journal_venue"] if w["journal_venue"] else "N/A",
                    w["doi"] if w["doi"] else "N/A",
                    w["all_external_ids"] if w["all_external_ids"] else "N/A"
                ])
                
        logger.info(f"Data successfully saved to {os.path.abspath(filename)}")
        
    except OSError as e:
        logger.error(f"Failed to write CSV file: {e}")
        raise

def scrape_works_with_playwright(orcid_id: str) -> list:
    """
    Method 2: Playwright Browser Simulation to scrape ORCID public page.
    Does not require API keys or Client ID.
    """
    from playwright.sync_api import sync_playwright
    import time
    import re
    
    clean_orcid = orcid_id.strip().split('/')[-1]
    url = f"https://orcid.org/{clean_orcid}"
    logger.info(f"Launching Playwright to scrape ORCID page: {url}...")
    
    extracted_works = []
    
    try:
        with sync_playwright() as p:
            # Headless browser is enough for ORCID since it is public and fast
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle")
            
            # Dismiss cookies if visible
            try:
                reject_cookies = page.locator("button:has-text('Reject Unnecessary Cookies')")
                if reject_cookies.is_visible():
                    reject_cookies.click()
            except Exception:
                pass
                
            # Wait for works element
            page.wait_for_selector("app-work-stack", timeout=15000)
            work_stacks = page.locator("app-work-stack").all()
            logger.info(f"Playwright successfully located {len(work_stacks)} work cards.")
            
            for idx, work in enumerate(work_stacks, 1):
                try:
                    # Title
                    title_el = work.locator("app-panel-title")
                    title = title_el.inner_text().strip() if title_el.count() > 0 else "Unknown Title"
                    
                    # Panel text containing year/venue
                    panel_text = work.inner_text()
                    
                    # Parse Year (four digits e.g. 2021)
                    year = ""
                    years = re.findall(r'\b(19\d{2}|20\d{2})\b', panel_text)
                    if years:
                        year = years[0]
                        
                    # Journal/Venue is usually in the panel description
                    journal = ""
                    # Simple heuristic: find journal near external ID info
                    # Standard ORCID markup has a specific subtitle or text
                    lines = [line.strip() for line in panel_text.split("\n") if line.strip()]
                    if len(lines) > 1:
                        # Second line or third line is usually the source/journal
                        journal = lines[1]
                        
                    # DOI
                    doi = ""
                    doi_link = work.locator("a[href*='doi.org']")
                    if doi_link.count() > 0:
                        href = doi_link.nth(0).get_attribute("href")
                        if href:
                            doi = href.split("doi.org/")[-1].strip()
                            
                    if title and title != "Unknown Title":
                        extracted_works.append({
                            "title": title,
                            "publication_year": year,
                            "journal_venue": journal,
                            "doi": doi,
                            "all_external_ids": f"DOI:{doi}" if doi else ""
                        })
                except Exception as e:
                    logger.warning(f"Error parsing work stack {idx} with Playwright: {e}")
            
            browser.close()
    except Exception as e:
        logger.error(f"Playwright scraping failed: {e}")
        raise
        
    return extracted_works

def main():
    parser = argparse.ArgumentParser(
        description="Fetch publication records for a scholar using the ORCID Public API v3.0."
    )
    parser.add_argument(
        "--orcid",
        help="Target scholar's ORCID iD (e.g. 0000-0002-1825-0097). Overrides TARGET_ORCID_ID in .env."
    )
    parser.add_argument(
        "--client-id",
        help="ORCID API Client ID. Overrides ORCID_CLIENT_ID in .env."
    )
    parser.add_argument(
        "--client-secret",
        help="ORCID API Client Secret. Overrides ORCID_CLIENT_SECRET in .env."
    )
    parser.add_argument(
        "--output",
        help="Output CSV file path. Overrides OUTPUT_CSV in .env (defaults to orcid_publications.csv)."
    )
    parser.add_argument(
        "--sandbox",
        action="store_true",
        help="Use the ORCID Sandbox API instead of production."
    )
    
    args = parser.parse_args()
    
    # Resolve configuration hierarchy (CLI args -> .env -> defaults/interactive prompts)
    orcid_id = args.orcid or os.getenv("TARGET_ORCID_ID")
    client_id = args.client_id or os.getenv("ORCID_CLIENT_ID")
    client_secret = args.client_secret or os.getenv("ORCID_CLIENT_SECRET")
    output_csv = args.output or os.getenv("OUTPUT_CSV", "orcid_publications.csv")
    use_sandbox = args.sandbox
    
    print("==================================================================")
    print("             ORCID Publication Extractor (v3.0)                   ")
    print("==================================================================")
    
    # Prompt for variables if not provided via environment or CLI
    if not orcid_id:
        orcid_id = input("Enter target ORCID iD (e.g., 0000-0002-1825-0097): ").strip()
        if not orcid_id:
            logger.error("No ORCID ID specified. Exiting.")
            sys.exit(1)
            
    access_token = None
    if client_id and client_secret:
        try:
            # Step 1: Authentication
            access_token = get_access_token(client_id, client_secret, use_sandbox=use_sandbox)
        except Exception as e:
            logger.warning(f"OAuth authentication failed: {e}. Will attempt to proceed anonymously...")
    else:
        logger.info("Missing or incomplete client credentials. Attempting to proceed with anonymous direct API access...")
            
    try:
        # Step 2: Fetch data via Official API (v3.0) - Default Highest Success Rate Method
        works_json = fetch_orcid_works(orcid_id, access_token, use_sandbox=use_sandbox)
        
        # Step 3: Parse details
        publications = parse_works(works_json)
        
        # Step 4: Sort and save to CSV
        save_to_csv(publications, output_csv)
        
        print("==================================================================")
        logger.info("Process finished successfully!")
        print("==================================================================")
        
    except Exception as e:
        logger.error(f"ORCID API extraction failed: {e}")
        print("\n" + "="*70)
        print("⚠️  [警告] ORCID API (方案一) 抓取失败或被限制。")
        print("是否尝试【方案二】使用 Playwright 模拟浏览器抓取？（不需要 API 密钥）")
        print("="*70)
        choice = input("是否运行 Playwright 模拟网页抓取？(Y/N, 默认 Y): ").strip().lower()
        if choice in ("", "y", "yes"):
            try:
                publications = scrape_works_with_playwright(orcid_id)
                if publications:
                    save_to_csv(publications, output_csv)
                    logger.info("Playwright extraction completed successfully!")
                else:
                    logger.error("Playwright extracted no publications.")
                    sys.exit(1)
            except Exception as pe:
                logger.critical(f"Playwright extraction also failed: {pe}")
                sys.exit(1)
        else:
            print("用户放弃尝试其他方法。退出。")
            sys.exit(1)

if __name__ == "__main__":
    main()

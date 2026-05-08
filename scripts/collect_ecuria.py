#!/usr/bin/env python3
"""
EU Regulation — CURIA/ECJ Ruling Collector.
Uses Playwright to scrape ECJ CURIA (React SPA) for recent rulings.
Falls back to DB status if CURIA is unreachable.
"""
import sys, os, json
from datetime import datetime, date
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from eu_regulation_cache import save_ruling, db_stats, get_db

today_str = date.today().isoformat()
NOW = datetime.now().strftime('%Y-%m-%d %H:%M UTC')

CURIA_BASE = 'https://curia.europa.eu'
SEARCH_URL = f'{CURIA_BASE}/juris/liste.jsf?language=en&type=JUR&text=&jur=C,J,T,F&num=&dates=&lg='
DNI_URL = f'{CURIA_BASE}/juris/dnr.jsf?oecd=JUR&lg=en'

# Keywords for relevant rulings (agriculture, pharma, digital, environment, chemicals)
SEARCH_TERMS = [
    'pesticide', 'glyphosate', 'neonicotinoid', 'plant protection',
    'REACH', 'chemical', 'substance',
    'pharmaceutical', 'medicine', 'SPC', 'clinical trial',
    'GDPR', 'data protection', 'AI act',
    'taxonomy', 'sustainable', 'emissions',
    'MDR', 'medical device', 'food safety',
    'environmental', 'nature restoration', 'waste',
]


def try_curia_search(page, captured, term):
    """Try to search CURIA for a specific term and capture data."""
    print(f"  Searching: '{term}'...")
    try:
        page.goto(
            f'{CURIA_BASE}/juris/liste.jsf?language=en&type=JUR&text={term}&jur=C,J,T,F&num=&dates=&lg=',
            wait_until='networkidle', timeout=15000
        )
        body = page.evaluate('() => document.body.innerText') or ''
        # Check if results page has data
        if 'No results' in body or 'no results' in body.lower():
            return None
        # Try to extract table data
        rows_raw = page.evaluate('''() => {
            const tables = document.querySelectorAll('table');
            if (!tables.length) return null;
            const rows = [];
            tables.forEach(t => {
                const trs = t.querySelectorAll('tr');
                trs.forEach(tr => {
                    const cells = tr.querySelectorAll('td, th');
                    if (cells.length) {
                        rows.push(Array.from(cells).map(c => c.innerText.trim()));
                    }
                });
            });
            return rows;
        }''')
        if rows_raw and len(rows_raw) > 1:
            return rows_raw
        return None
    except Exception as e:
        print(f"    Error: {e}")
        return None


def try_dnr_api(page, captured, term):
    """Try the DNI (Document not Registered) search as fallback."""
    try:
        page.goto(
            f'{CURIA_BASE}/juris/dnr.jsf?oecd=JUR&lg=en&texte={term}',
            wait_until='networkidle', timeout=10000
        )
        body = page.evaluate('() => document.body.innerText') or ''
        if term.lower() in body.lower():
            return body[:3000]
        return None
    except:
        return None


def collect_rulings(page):
    """Main collection loop — try all approaches."""
    all_data = []
    
    for term in SEARCH_TERMS:
        # Approach 1: Direct search via liste.jsf
        result = try_curia_search(page, [], term)
        if result:
            all_data.extend(result)
            continue
        
        # Approach 2: Try DNI
        result = try_dnr_api(page, [], term)
        if result:
            all_data.append({'term': term, 'data': result[:1000]})
    
    return all_data


def store_ruling(raw_entry):
    """Parse scraped data and store in DB."""
    try:
        if isinstance(raw_entry, dict):
            case_no = raw_entry.get('case_no', '')
            title = raw_entry.get('title', '')[:300]
            summary = raw_entry.get('summary', '')[:1000]
            keywords = raw_entry.get('keywords', '')
            decision_date = raw_entry.get('date', '')
            sector = raw_entry.get('sector', 'general')
            case_url = raw_entry.get('url', '')

            if case_no:
                save_ruling(
                    case_no=case_no,
                    title=title or f"CURIA case {case_no}",
                    applicant='',
                    respondent='',
                    summary=summary,
                    keywords=keywords,
                    decision_date=decision_date,
                    court='ECJ',
                    url=case_url,
                    sector=sector
                )
                return 1
        return 0
    except Exception as e:
        print(f"    DB error: {e}")
        return 0


def main():
    print(f"⚖️  ECJ/CURIA Ruling Collector")
    print(f"   {NOW}\n")

    # Check DB first
    stats = db_stats()
    existing = stats.get('ecuria_rulings', 0)
    print(f"Existing rulings in DB: {existing}")

    rulings_collected = 0
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = browser.new_page()
        
        # Intercept XHR responses (CURIA is a JSF app with AJAX)
        captured_data = []
        def handle_response(response):
            url = response.url
            if any(x in url for x in ['liste.jsf', 'dnr.jsf', 'FacesServlet', 'javax.faces', 'jakarta.faces']):
                try:
                    ct = response.headers.get('content-type', '')
                    if 'json' in ct or 'xml' in ct:
                        data = response.json()
                        captured_data.append({'url': url, 'data': data})
                except:
                    pass
        
        page.on('response', handle_response)
        
        # First check if CURIA is reachable
        print("Checking CURIA availability...")
        try:
            resp = page.goto(SEARCH_URL, wait_until='domcontentloaded', timeout=10000)
            status = resp.status if resp else 0
            print(f"  CURIA HTTP {status}")
        except PwTimeout:
            print("  ❌ CURIA unreachable (timeout)")
            browser.close()
            print(f"\n⚠️  CURIA scraper unavailable. Status: timeout")
            print(f"Not legal advice. Status: {today_str}")
            return
        except Exception as e:
            print(f"  ❌ CURIA unreachable: {e}")
            browser.close()
            print(f"\n⚠️  CURIA scraper unavailable. Error: {e}")
            print(f"Not legal advice. Status: {today_str}")
            return

        # Try to collect data
        print("\nSearching for rulings...")
        all_results = collect_rulings(page)
        
        browser.close()
    
    # Store results
    if all_results:
        stored = 0
        for entry in all_results:
            stored += store_ruling(entry)
        rulings_collected = stored
        print(f"\n  Stored: {stored} new rulings")
    else:
        print("\n  No rulings scraped from CURIA — HTML-only interface, no structured API available")
    
    # Report
    print()
    print("=" * 60)
    print("ECJ/CURIA RULING COLLECTION REPORT")
    print(f"Checked: {NOW}")
    print("=" * 60)
    print(f"\nScraped: {len(all_results)} | Stored: {rulings_collected}")
    print(f"Total in DB: {existing + rulings_collected}")
    print()
    print("---")
    print("Not legal advice. Status:", today_str)


if __name__ == '__main__':
    main()

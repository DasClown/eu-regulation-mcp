#!/usr/bin/env python3
"""Playwright-based brpapi extraction — fixed with correct field names.
Hourly check for new/changed consultations from EU Have Your Say.
"""
import json, sqlite3, os
from datetime import datetime, date
from playwright.sync_api import sync_playwright

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, '..', 'cache', 'eu_regulation.db')
today_str = date.today().isoformat()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

conn = get_db()
existing_ids = set(r['consultation_id'] for r in conn.execute(
    "SELECT consultation_id FROM eu_consultations").fetchall())
print(f"Existing consultations in DB: {len(existing_ids)}")

new_consultations = []
closing_soon_data = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
    page = browser.new_page()
    captured = []

    def handle_response(response):
        url = response.url
        try:
            data = response.json()
            captured.append({'url': url, 'data': data})
        except:
            pass

    page.on('response', handle_response)
    print("Loading have-your-say page...")
    page.goto('https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives_en',
              wait_until='networkidle', timeout=30000)

    for c in captured:
        if 'closingSoon' in c['url']:
            closing_soon_data = c['data']

    print(f"Closing soon: {len(closing_soon_data)}")

    if not closing_soon_data:
        print("ERROR: No closingSoon data captured")
        browser.close()
        conn.close()
        exit(1)

    # Show all closing soon
    new_ids = []
    for item in closing_soon_data:
        cid = str(item.get('initiativeId', ''))
        days_left = item.get('daysLeft', 0)
        title = item.get('shortTitle', '??')
        end_date = item.get('endDate', '?')
        is_new = cid not in existing_ids
        marker = "NEW" if is_new else "   "
        print(f"  {marker} [{cid}] {title} | {days_left}d | ends {end_date}")
        if is_new:
            new_ids.append(cid)
            new_consultations.append(item)

    # Get urgent IDs (score 4-5, <7 days) for detail fetching
    urgent_cids = set()
    for item in closing_soon_data:
        cid = str(item.get('initiativeId', ''))
        days_left = item.get('daysLeft', 99)
        if days_left < 7 and days_left >= 0:
            urgent_cids.add(cid)

    # Append today's deadline items
    for item in closing_soon_data:
        cid = str(item.get('initiativeId', ''))
        days_left = item.get('daysLeft', 99)
        if days_left == 0:
            urgent_cids.add(cid)

    print(f"\nFetching details for {len(urgent_cids)} urgent initiatives...")

    # To get proper SPAs for detail pages, need to intercept brpapi
    # Let's use the groupInitiatives endpoint instead
    detail_data = {}
    for init_id in sorted(urgent_cids):
        try:
            # For initiative detail, we need to navigate to the SPA and intercept
            detail_captured = []
            def detail_handler(response):
                url = response.url
                if f'initiativeDetail/{init_id}' in url or f'groupInitiatives/{init_id}' in url:
                    try:
                        dd = response.json()
                        detail_captured.append(dd)
                    except:
                        pass
            page.on('response', detail_handler)
            page.goto(f'https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/{init_id}_en',
                      wait_until='networkidle', timeout=15000)
            if detail_captured:
                detail_data[init_id] = json.dumps(detail_captured[0], indent=2)[:2000]
            else:
                # Fallback: body text
                body_text = page.evaluate('() => document.body.innerText')
                # Filter out cookie banner
                lines = [l.strip() for l in body_text.split('\n') if l.strip() and 'cookie' not in l.lower()][:15]
                detail_data[init_id] = ' '.join(lines[:8])[:800]
            print(f"  Got detail for {init_id}")
        except Exception as e:
            print(f"  Error fetching detail for {init_id}: {e}")
            detail_data[init_id] = ""

    # Also fetch groupInitiatives for sector info via brpapi
    # Navigate back to main page once more to capture groupInitiatives
    page.goto('https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives_en',
              wait_until='networkidle', timeout=30000)
    # Check if we got groupInitiatives in the main page load
    for c in captured:
        if 'groupInitiatives' in c['url']:
            gi_data = c['data']
            print(f"  Got groupInitiatives: keys={list(gi_data.keys())[:10] if isinstance(gi_data, dict) else type(gi_data)}")

    browser.close()

# Store new consultations in DB
new_stored = 0
for item in closing_soon_data:
    cid = str(item.get('initiativeId', ''))
    if cid in existing_ids:
        continue
    days_left = int(item.get('daysLeft', 0))
    if days_left < 7:
        score = 5
    elif days_left < 30:
        score = 4
    elif days_left < 60:
        score = 3
    else:
        score = 2

    end_date = item.get('endDate', '')
    title = item.get('shortTitle', '')
    url = f"https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/{cid}_en"

    detail = detail_data.get(cid, '')
    lines = [l.strip() for l in detail.split('\n') if l.strip()][:20]
    detail_text = ' '.join(lines[:10])[:800]

    # Extract sector from detail
    sector = "General"
    for line in lines:
        if 'sector' in line.lower() or 'topic' in line.lower() or 'theme' in line.lower():
            sector = line[:80]
            break

    conn.execute("""
        INSERT OR REPLACE INTO eu_consultations
        (consultation_id, title, sector, summary, deadline, url, relevance_score, status, last_checked, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'open', ?, ?)
    """, (cid, title, sector, detail_text, end_date, url, score, today_str, today_str))
    new_stored += 1

conn.commit()
conn.close()

# ============ REPORT ============
print()
print("=" * 60)
print("EU HAVE YOUR SAY - CONSULTATION CHECK")
print(f"Checked: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
print("=" * 60)

total_display = len(closing_soon_data)
urgent_count = len([i for i in closing_soon_data if i.get('daysLeft', 99) < 7])
print(f"\nClosing soon: {total_display} | New: {new_stored} | Urgent (<7d): {urgent_count}")

# Urgent consultations (< 7 days)
print("\n--- URGENT: < 7 days remaining ---")
for item in closing_soon_data:
    cid = str(item.get('initiativeId', ''))
    days_left = int(item.get('daysLeft', 99))
    if days_left >= 7:
        continue
    title = item.get('shortTitle', '??')
    end_date = item.get('endDate', '?')
    tag = "TODAY!" if days_left == 0 else f"{days_left}d"
    url = f"https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/{cid}_en"
    print(f"\n  [{tag}] {title}")
    print(f"     Deadline: {end_date}")
    print(f"     Link: {url}")
    detail = detail_data.get(cid, '')
    snippet = detail[:300].replace('\n', ' ').strip() if detail else ''
    if snippet:
        print(f"     {snippet}...")

# Non-urgent closing soon
print("\n--- Other closing soon ---")
for item in closing_soon_data:
    days_left = int(item.get('daysLeft', 99))
    if days_left >= 7:
        cid = str(item.get('initiativeId', ''))
        title = item.get('shortTitle', '?')
        end_date = item.get('endDate', '?')
        print(f"  [{days_left}d] {title} — ends {end_date}")

print()
print("---")
print("Not legal advice. Status:", today_str)

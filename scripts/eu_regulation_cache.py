#!/usr/bin/env python3
"""
EU Regulation Intelligence — SQLite Cache Module
Central data store for the EU Regulation early-warning system.
"""
import sqlite3
import json
import os
from datetime import datetime, date

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'cache', 'eu_regulation.db')

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

# ── EUR-Lex ──────────────────────────────────────────────────────────

def save_eurlex_entry(celex, title, legal_type, author, pub_date, eif, deadline, url, raw):
    conn = get_db()
    conn.execute("""
        INSERT INTO eurlex_metadata
        (celex, title, legal_type, author, publication_date, entry_into_force,
         deadline_transposition, url, raw_json, last_checked)
        VALUES (?,?,?,?,?,?,?,?,?,datetime('now'))
        ON CONFLICT(celex) DO UPDATE SET
            title=excluded.title,
            legal_type=excluded.legal_type,
            author=excluded.author,
            publication_date=excluded.publication_date,
            entry_into_force=excluded.entry_into_force,
            deadline_transposition=excluded.deadline_transposition,
            url=excluded.url,
            raw_json=excluded.raw_json,
            last_checked=datetime('now'),
            updated_at=datetime('now')
    """, (celex, title, legal_type, author, pub_date, eif, deadline, url, json.dumps(raw, default=str)))
    conn.commit()
    conn.close()

def search_eurlex(keyword, limit=10):
    conn = get_db()
    # Case-insensitive search across both columns
    cur = conn.execute("""
        SELECT * FROM eurlex_metadata
        WHERE LOWER(title) LIKE ? OR LOWER(celex) LIKE ?
        ORDER BY publication_date DESC
        LIMIT ?
    """, (f'%{keyword.lower()}%', f'%{keyword.lower()}%', limit))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# ── Legislative Procedures ───────────────────────────────────────────

def save_procedure(proc_num, celex, title, stage, stage_label, ep_url, council_url, trilogue, deadline, raw):
    conn = get_db()
    conn.execute("""
        INSERT INTO legislative_procedures
        (procedure_number, celex, title, stage, stage_label, ep_proposal_url,
         council_url, trilogue_dates, next_deadline, raw_json, last_checked)
        VALUES (?,?,?,?,?,?,?,?,?,?,datetime('now'))
        ON CONFLICT(procedure_number) DO UPDATE SET
            celex=excluded.celex, title=excluded.title, stage=excluded.stage,
            stage_label=excluded.stage_label, ep_proposal_url=excluded.ep_proposal_url,
            council_url=excluded.council_url, trilogue_dates=excluded.trilogue_dates,
            next_deadline=excluded.next_deadline, raw_json=excluded.raw_json,
            last_checked=datetime('now'), updated_at=datetime('now')
    """, (proc_num, celex, title, stage, stage_label, ep_url, council_url, trilogue, deadline, json.dumps(raw, default=str)))
    conn.commit()
    conn.close()

def get_procedures_by_keyword(keyword, limit=10):
    conn = get_db()
    cur = conn.execute("""
        SELECT * FROM legislative_procedures
        WHERE LOWER(title) LIKE ? OR LOWER(procedure_number) LIKE ?
        ORDER BY next_deadline ASC
        LIMIT ?
    """, (f'%{keyword.lower()}%', f'%{keyword.lower()}%', limit))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# ── Consultations ────────────────────────────────────────────────────

def save_consultation(cid, title, sector, summary, deadline, url, score=3):
    conn = get_db()
    conn.execute("""
        INSERT INTO eu_consultations
        (consultation_id, title, sector, summary, deadline, url, relevance_score, last_checked)
        VALUES (?,?,?,?,?,?,?,datetime('now'))
        ON CONFLICT(consultation_id) DO UPDATE SET
            title=excluded.title, sector=excluded.sector, summary=excluded.summary,
            deadline=excluded.deadline, url=excluded.url, relevance_score=excluded.relevance_score,
            last_checked=datetime('now')
    """, (cid, title, sector, summary, deadline, url, score))
    conn.commit()
    conn.close()

def get_open_consultations(sector=None, days_remaining=30, limit=10):
    conn = get_db()
    today = date.today().isoformat()
    query = "SELECT * FROM eu_consultations WHERE status='open' AND deadline >= ?"
    params = [today]
    if sector:
        query += " AND sector LIKE ?"
        params.append(f'%{sector}%')
    query += " ORDER BY deadline ASC LIMIT ?"
    params.append(limit)
    cur = conn.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    # Filter by days_remaining
    from datetime import datetime, timedelta
    cutoff = (datetime.now() + timedelta(days=days_remaining)).strftime('%Y-%m-%d')
    return [r for r in rows if r['deadline'] <= cutoff]

# ── ECJ Rulings ──────────────────────────────────────────────────────

def save_ruling(case_no, title, applicant, respondent, summary, keywords, decision_date, court, url, sector):
    conn = get_db()
    conn.execute("""
        INSERT INTO ecuria_rulings
        (case_number, title, applicant, respondent, summary, keywords,
         decision_date, court, url, relevance_sector, last_checked)
        VALUES (?,?,?,?,?,?,?,?,?,?,datetime('now'))
        ON CONFLICT(case_number) DO UPDATE SET
            title=excluded.title, summary=excluded.summary,
            keywords=excluded.keywords, decision_date=excluded.decision_date,
            url=excluded.url, last_checked=datetime('now')
    """, (case_no, title, applicant, respondent, summary, keywords, decision_date, court, url, sector))
    conn.commit()
    conn.close()

def search_rulings(keyword, limit=10):
    conn = get_db()
    cur = conn.execute("""
        SELECT * FROM ecuria_rulings
        WHERE LOWER(title) LIKE ? OR LOWER(keywords) LIKE ? OR LOWER(summary) LIKE ?
        ORDER BY decision_date DESC
        LIMIT ?
    """, (f'%{keyword.lower()}%', f'%{keyword.lower()}%', f'%{keyword.lower()}%', limit))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# ── National Implementation ──────────────────────────────────────────

def save_national_impl(directive_celex, directive_title, member_state, deadline, status, nat_ref, nat_url):
    conn = get_db()
    conn.execute("""
        INSERT INTO national_implementation
        (directive_celex, directive_title, member_state, transposition_deadline,
         status, national_reference, national_url, last_checked)
        VALUES (?,?,?,?,?,?,?,datetime('now'))
        ON CONFLICT(directive_celex, member_state) DO UPDATE SET
            directive_title=excluded.directive_title,
            transposition_deadline=excluded.transposition_deadline,
            status=excluded.status,
            national_reference=excluded.national_reference,
            national_url=excluded.national_url,
            last_checked=datetime('now'),
            updated_at=datetime('now')
    """, (directive_celex, directive_title, member_state, deadline, status, nat_ref, nat_url))
    conn.commit()
    conn.close()

def get_national_impl(directive_keyword, member_state):
    conn = get_db()
    cur = conn.execute("""
        SELECT * FROM national_implementation
        WHERE (LOWER(directive_title) LIKE ? OR LOWER(directive_celex) LIKE ?)
        AND member_state = ?
        ORDER BY transposition_deadline DESC
    """, (f'%{directive_keyword.lower()}%', f'%{directive_keyword.lower()}%', member_state))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# ── Tracking Subscriptions ───────────────────────────────────────────

def subscribe_tracking(keyword, sector, region='EU'):
    conn = get_db()
    conn.execute("""
        INSERT INTO tracking_subscriptions (keyword, sector, region, last_checked)
        VALUES (?,?,?,datetime('now'))
        ON CONFLICT(keyword, sector, region) DO NOTHING
    """, (keyword, sector, region))
    conn.commit()
    conn.close()

def list_active_trackings():
    conn = get_db()
    cur = conn.execute("SELECT * FROM tracking_subscriptions WHERE is_active=1")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def update_tracking_last_checked(track_id):
    conn = get_db()
    conn.execute("UPDATE tracking_subscriptions SET last_checked=datetime('now') WHERE id=?", (track_id,))
    conn.commit()
    conn.close()

# ── Reporting ─────────────────────────────────────────────────────────

def get_pending_deadlines(days_ahead=30, limit=20):
    """Find all pending deadlines within the next days_ahead days."""
    conn = get_db()
    today = date.today()
    from datetime import timedelta
    cutoff = (today + timedelta(days=days_ahead)).isoformat()
    today_str = today.isoformat()
    
    results = []
    
    # Legislative deadlines
    cur = conn.execute("""
        SELECT 'procedure' as source, title, next_deadline as deadline,
               stage_label as detail, procedure_number as ref
        FROM legislative_procedures
        WHERE next_deadline BETWEEN ? AND ?
        ORDER BY next_deadline
    """, (today_str, cutoff))
    results.extend([dict(r) for r in cur.fetchall()])
    
    # Consultation deadlines
    cur = conn.execute("""
        SELECT 'consultation' as source, title, deadline,
               summary as detail, url as ref
        FROM eu_consultations
        WHERE deadline BETWEEN ? AND ? AND status='open'
        ORDER BY deadline
    """, (today_str, cutoff))
    results.extend([dict(r) for r in cur.fetchall()])
    
    # National implementation deadlines
    cur = conn.execute("""
        SELECT 'national' as source, directive_title as title,
               transposition_deadline as deadline,
               'Status: ' || status || ' — ' || member_state as detail,
               national_url as ref
        FROM national_implementation
        WHERE transposition_deadline BETWEEN ? AND ?
        ORDER BY transposition_deadline
    """, (today_str, cutoff))
    results.extend([dict(r) for r in cur.fetchall()])
    
    conn.close()
    return sorted(results, key=lambda x: x['deadline'])[:limit]

def db_stats():
    conn = get_db()
    stats = {}
    for table in ['eurlex_metadata', 'legislative_procedures', 'eu_consultations',
                  'ecuria_rulings', 'national_implementation', 'tracking_subscriptions']:
        cur = conn.execute(f"SELECT COUNT(*) as c FROM {table}")
        stats[table] = cur.fetchone()['c']
    conn.close()
    return stats


if __name__ == '__main__':
    import sys
    if '--stats' in sys.argv:
        s = db_stats()
        for k, v in s.items():
            print(f"{k}: {v}")
    elif '--deadlines' in sys.argv:
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        for r in get_pending_deadlines(days):
            print(f"[{r['source']}] {r['title']} — Deadline: {r['deadline']} — {r['detail']}")

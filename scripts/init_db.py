#!/usr/bin/env python3
"""Initialize the EU Regulation SQLite database schema at the correct path."""
import sqlite3, os

# The database should be at /root/eu-regulation-mcp/cache/eu_regulation.db
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(BASE, 'cache', 'eu_regulation.db')
print(f"DB path: {DB}")

os.makedirs(os.path.dirname(DB), exist_ok=True)

conn = sqlite3.connect(DB)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA foreign_keys=ON")

conn.executescript("""
CREATE TABLE IF NOT EXISTS eurlex_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    celex TEXT UNIQUE NOT NULL,
    title TEXT,
    legal_type TEXT,
    author TEXT,
    publication_date TEXT,
    entry_into_force TEXT,
    deadline_transposition TEXT,
    language TEXT DEFAULT 'en',
    url TEXT,
    raw_json TEXT,
    last_checked TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS legislative_procedures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    procedure_number TEXT UNIQUE NOT NULL,
    celex TEXT,
    title TEXT,
    stage TEXT,
    stage_label TEXT,
    ep_proposal_url TEXT,
    council_url TEXT,
    trilogue_dates TEXT,
    next_deadline TEXT,
    raw_json TEXT,
    last_checked TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS eu_consultations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consultation_id TEXT UNIQUE NOT NULL,
    title TEXT,
    sector TEXT,
    summary TEXT,
    deadline TEXT,
    url TEXT,
    relevance_score INTEGER DEFAULT 3,
    status TEXT DEFAULT 'open',
    raw_json TEXT,
    last_checked TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ecuria_rulings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_number TEXT UNIQUE NOT NULL,
    title TEXT,
    applicant TEXT,
    respondent TEXT,
    summary TEXT,
    keywords TEXT,
    decision_date TEXT,
    court TEXT DEFAULT 'ECJ',
    url TEXT,
    relevance_sector TEXT,
    raw_json TEXT,
    last_checked TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS national_implementation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    directive_celex TEXT NOT NULL,
    directive_title TEXT,
    member_state TEXT NOT NULL,
    transposition_deadline TEXT,
    status TEXT DEFAULT 'not_started',
    national_reference TEXT,
    national_url TEXT,
    raw_json TEXT,
    last_checked TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(directive_celex, member_state)
);

CREATE TABLE IF NOT EXISTS tracking_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    sector TEXT,
    region TEXT DEFAULT 'EU',
    is_active INTEGER DEFAULT 1,
    last_found_ids TEXT,
    last_checked TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(keyword, sector, region)
);
""")

conn.commit()
conn.close()
print(f"✅ Database initialized at: {DB}")
print(f"   Tables: eurlex_metadata, legislative_procedures, eu_consultations, ecuria_rulings, national_implementation, tracking_subscriptions")

# EU Regulation SQLite DB Schema

> Database: `/root/.hermes/profiles/eu_regulation/cache/eu_regulation.db`
> WAL mode for concurrent access.
> Case-insensitive search via `LOWER()` in all `search_*` cache functions.

## Table: `eurlex_metadata` (34 rows)

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | PK |
| celex | TEXT | CELEX number (e.g. 32022R2065) |
| title | TEXT | Full title |
| legal_type | TEXT | regulation, directive, decision, proposal |
| author | TEXT | e.g. "European Parliament and Council" |
| publication_date | TEXT | ISO date |
| entry_into_force | TEXT | ISO date |
| deadline_transposition | TEXT | ISO date — only for directives |
| language | TEXT | Default 'en' |
| url | TEXT | EUR-Lex permalink |
| raw_json | TEXT | Full JSON blob from EUR-Lex |
| last_checked | TEXT | ISO datetime |
| created_at | TEXT | Auto-set |
| updated_at | TEXT | Auto-updated |

## Table: `legislative_procedures` (12 rows)

**⚠️ Column names differ from what you'd expect:**
- `procedure_number` — NOT `procedure_id`
- `celex` — NOT `celex_number`

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | PK |
| procedure_number | TEXT | e.g. "2023/0208(COD)" — **NOT `procedure_id`** |
| celex | TEXT | CELEX — **NOT `celex_number`** |
| title | TEXT | Short title |
| stage | TEXT | Proposal, EP_1st_reading, Council_1st_reading, Trilogue, Adopted |
| stage_label | TEXT | Human-readable stage description |
| ep_proposal_url | TEXT | Link to European Parliament procedure page |
| council_url | TEXT | Link to Council page |
| trilogue_dates | TEXT | Comma-separated dates |
| next_deadline | TEXT | ISO date or partial date |
| raw_json | TEXT | Full JSON blob |
| last_checked | TEXT | ISO datetime |
| created_at | TEXT | Auto-set |
| updated_at | TEXT | Auto-updated |

**Query example:**
```python
cur.execute("""
    SELECT procedure_number, title, stage, next_deadline, celex
    FROM legislative_procedures
    ORDER BY CASE WHEN next_deadline IS NULL THEN 1 ELSE 0 END, next_deadline ASC
""").fetchall()
```

## Table: `national_implementation` (30 rows)

**⚠️ Uses `directive_title` NOT `title`. No `celex_type` column.**

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | PK |
| directive_celex | TEXT | CELEX of the EU directive |
| directive_title | TEXT | — **NOT `title`** |
| member_state | TEXT | DE, FR, IT, ES (2-letter codes) |
| transposition_deadline | TEXT | ISO date |
| status | TEXT | adopted, drafting, not_started, overdue |
| national_reference | TEXT | National law reference (e.g. BGBl. I 2024 Nr. 123) |
| national_url | TEXT | Link to national gazette |
| raw_json | TEXT | Full JSON blob |
| last_checked | TEXT | ISO datetime |
| created_at | TEXT | Auto-set |
| updated_at | TEXT | Auto-updated |

**Query example:**
```python
cur.execute("""
    SELECT directive_title, member_state, directive_celex, transposition_deadline, status
    FROM national_implementation
    WHERE status != 'adopted' AND transposition_deadline < date('now')
    ORDER BY transposition_deadline ASC
""").fetchall()
```

## Table: `eu_consultations` (23 rows)

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | PK |
| consultation_id | TEXT | From brpapi `initiativeId` |
| title | TEXT | Short title |
| sector | TEXT | Tag (agrar, chemie, pharma, digital, umwelt, cross) |
| summary | TEXT | Full summary with details |
| deadline | TEXT | Format includes time: "2026/05/11 23:59:59" |
| url | TEXT | "Have your say" link |
| relevance_score | INTEGER | 1-5 scale |
| status | TEXT | open, closed, closing_soon |
| raw_json | TEXT | Full JSON from brpapi |
| last_checked | TEXT | ISO datetime |
| created_at | TEXT | Auto-set |

**⚠️ Deadline filter pitfall:** The `get_open_consultations()` tool filters via `deadline >= date('now')`. Seed data uses ISO format (`2026-01-31`) while Playwright-collected data uses the brpapi format (`2026/05/11 23:59:59`). Both work with the date comparison but be aware of the format mismatch.

## Table: `ecuria_rulings` (14 rows)

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | PK |
| case_number | TEXT | e.g. "C-528/16" |
| title | TEXT | Case name |
| applicant | TEXT | Who brought the case |
| respondent | TEXT | Defendant |
| summary | TEXT | Full ruling text / tenor |
| keywords | TEXT | Comma-separated search keywords |
| decision_date | TEXT | ISO date |
| court | TEXT | ECJ, GC (General Court) |
| url | TEXT | curia.europa.eu link |
| relevance_sector | TEXT | agrar, chemie, pharma, etc. |
| raw_json | TEXT | Full JSON blob |
| last_checked | TEXT | ISO datetime |
| created_at | TEXT | Auto-set |

## Table: `tracking_subscriptions` (1 row)

**⚠️ Uses `is_active` (INTEGER) NOT `status` (TEXT).**

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER | PK |
| keyword | TEXT | e.g. "REACH" |
| sector | TEXT | e.g. "chemie" |
| region | TEXT | Default "EU" |
| is_active | INTEGER | 1 or 0 — **NOT `status`** |
| last_checked | TEXT | ISO datetime |
| last_found_ids | TEXT | JSON array of found IDs |
| created_at | TEXT | Auto-set |

**Query example:**
```python
cur.execute("SELECT keyword, sector, region FROM tracking_subscriptions WHERE is_active=1").fetchall()
```

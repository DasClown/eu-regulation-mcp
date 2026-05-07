# System Audit — EU Regulation Intelligence MCP

**Datum:** 2026-05-07  
**Auditor:** Hermes Agent (Session deepseek-v4-flash)  
**Status:** 🟢 OPERATIV

## 1. Dateien & Infrastruktur

| Komponente | Pfad | Größe | Vorhanden? |
|-----------|------|-------|-----------|
| MCP Server | `/root/.hermes/profiles/eu_regulation/scripts/mcp_server.py` | 31KB | ✅ |
| Cache Modul | `/root/.hermes/profiles/eu_regulation/scripts/eu_regulation_cache.py` | 12KB | ✅ |
| Seed Daten | `/root/.hermes/profiles/eu_regulation/scripts/seed_database.py` | 30KB | ✅ |
| Health Check | `/root/.hermes/profiles/eu_regulation/scripts/collect_health.py` | 5.6KB | ✅ |
| Playwright Collector | `/root/.hermes/profiles/eu_regulation/scripts/collect_consultations_playwright.py` | 7.8KB | ✅ |
| SOUL.md | `/root/.hermes/profiles/eu_regulation/SOUL.md` | 2KB | ✅ |
| SQLite DB | `/root/.hermes/profiles/eu_regulation/cache/eu_regulation.db` | 131KB | ✅ |
| Cron Jobs | `/root/.hermes/profiles/eu_regulation/cron/jobs.json` | 8KB | ✅ |
| Skill | `/root/.hermes/profiles/eu_regulation/skills/mcp/eu-regulation-mcp/SKILL.md` | 21KB | ✅ |
| Skill Refs: eu-api-status | `skills/.../references/eu-api-status.md` | 3.6KB | ✅ |
| Skill Refs: eu-api-audit | `skills/.../references/eu-api-audit-2026-05-07.md` | 5.2KB | ✅ |
| Skill Refs: brpapi-playwright | `skills/.../references/brpapi-playwright-scraping.md` | 10.6KB | ✅ |
| Shared Wiki: schema | `shared-wiki/eu-regulation-schema.md` | 1.7KB | ✅ |
| Shared Wiki: alerts | `shared-wiki/concepts/eu-regulation-alerts.md` | 16.6KB | ✅ |
| Shared Wiki: synergy | `shared-wiki/concepts/eu-regulation-synergy.md` | 3.3KB | ✅ |
| Shared Wiki: concept | `shared-wiki/concepts/eu-regulation-mcp-concept.md` | 8.5KB | ✅ |

## 2. Datenbank

| Tabelle | Einträge | Letztes Update |
|---------|----------|---------------|
| `eurlex_metadata` | 34 | 2026-05-07 10:38:33 |
| `legislative_procedures` | 12 | 2026-05-07 10:38:33 |
| `national_implementation` | 30 | 2026-05-07 10:38:33 |
| `eu_consultations` | 23 | 2026-05-07 10:38:33 |
| `ecuria_rulings` | 14 | 2026-05-07 10:38:33 |
| `tracking_subscriptions` | 1 | 2026-05-07 10:38:33 |

**DB-Mode:** WAL (Write-Ahead Logging) für concurrent Access  
**Suchmodus:** Case-insensitive via `LOWER()` in allen query-Funktionen

## 3. Cron-Jobs

| Job | Schedule | Letzter Lauf | Status |
|-----|----------|-------------|--------|
| eu-regulation-collecteur | 0 6 * * * | Noch nie | ⏳ Anstehend |
| eu-consultations-hourly | 0 * * * * | 2026-05-07 22:04 | ✅ 16x gelaufen |
| eu-rulings-weekly | 0 7 * * 1 | Noch nie | ⏳ Nächster: Mo 11.5. |
| eu-alert-notifications | 0 8 * * * | 2026-05-07 10:26 | ✅ 2x gelaufen |

## 4. MCP Registration

| Profil | Config | Vorhanden? |
|--------|--------|-----------|
| eu_regulation | `/root/.hermes/profiles/eu_regulation/config.yaml` | ✅ |
| general | `/root/.hermes/profiles/general/config.yaml` | ❌ (nicht nötig) |
| crop-mcp | `/root/.hermes/profiles/crop-mcp/config.yaml` | ❓ Nicht geprüft |
| drug-pipeline | `/root/.hermes/profiles/drug-pipeline/config.yaml` | ❓ Nicht geprüft |

## 5. GitHub Deployment Readiness

| Kriterium | Status |
|-----------|--------|
| SSH Key vorhanden | ✅ `~/.ssh/id_ed25519.pub` (hermes-ai-agent) |
| SSH Key auf GitHub registriert | ❌ Nicht getestet |
| gh CLI installiert | ✅ |
| gh auth status | ❌ Nicht eingeloggt |
| PAT vorhanden | ❌ Nicht gefunden |
| .env vorhanden | ✅ `/root/.hermes/profiles/eu_regulation/.env` (209B) |

## 6. API-Funktionalität

| API | Status | Details |
|-----|--------|---------|
| EUR-Lex SPARQL | ✅ Funktioniert | `publications.europa.eu/webapi/rdf/sparql` |
| EUR-Lex REST/CELLAR | 🔴 WAF-Block | CloudFront HTTP 202 |
| N-Lex | ✅ Funktioniert | Nationale Gesetzblätter via REST |
| EuGH/CURIA | 🔴 React SPA | Kein REST-Endpunkt |
| Have Your Say brpapi | 🟡 Playwright nötig | Angular SPA, interner brpapi-Endpunkt |
| OEIL (EU-Parlament) | 🔴 404 | Alle getesteten Pfade kaputt |

## 7. Bekannte Lücken

- **Keine Live-Daten-Pipeline** — Seed-Daten sind Stand 2025/2026. Konsultationen via Playwright extrahierbar, aber EUR-Lex und EuGH haben keine funktionierenden Collector-Skripte.
- `collect_eurlex.py` — existiert nicht
- `collect_ecuria.py` — existiert nicht
- Seed-Konsultationen alle abgelaufen (Deadlines liegen in 2025)

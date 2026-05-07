# EU Regulation Intelligence MCP

**MCP-Server zur EU-Regulierungs-Frühwarnung** — überwacht EUR-Lex, EU-Parlament, Kommission, EuGH und nationale Gesetzblätter auf regulatorische Änderungen.

> ⚠️ **Keine Rechtsberatung** — dieses System liefert automatische Vorabprüfungen und Informationen. Konsultiere bei rechtlichen Fragen einen Fachanwalt.

## Features

| Tool | Beschreibung |
|------|-------------|
| `track_regulation` | Thema abonnieren (z.B. "Glyphosat", "Pflanzenschutz") + tägliche Updates |
| `get_legislative_status` | Status eines Gesetzgebungsverfahrens (EP, Rat, Trilog) |
| `get_open_consultations` | Offene EU-Kommissionskonsultationen mit Relevanz-Score |
| `get_national_implementation` | Umsetzungsstand von EU-Richtlinien in DE/FR/IT/ES |
| `get_relevant_rulings` | EuGH-Urteile zu einem Thema |
| `regulatory_impact_assessment` | Risikobewertung vor Investition |
| `system_status` | API-Status + DB-Statistiken |
| `alert_check` | Dringende Änderungen prüfen |

## Quickstart

```bash
# 1. Requirements
pip install requests

# 2. Seed-Datenbank initialisieren
python3 scripts/seed_database.py

# 3. MCP Server starten (STDIO — für MCP-Hosts wie Claude Desktop)
python3 scripts/mcp_server.py

# 4. Oder HTTP Mode
python3 scripts/mcp_server.py --http --port 8080
```

## API-Status (Stand Mai 2026)

| Quelle | Status | Bemerkung |
|--------|--------|-----------|
| EUR-Lex SPARQL | ✅ Funktioniert | Limitierte Metadaten |
| EUR-Lex REST (CELLAR) | ❌ WAF-blocked | CloudFront blockiert autom. Requests |
| EU-Parlament (OEIL) | ❌ 404 | Endpunkt nicht mehr verfügbar |
| EuGH (CURIA) | ❌ React SPA | Kein REST-Endpunkt |
| EU-Konsultationen | ❌ Leeres JSON | Endpunkt geändert |
| EU-Durchführungsrecht (HYS) | ❌ 403 | Scraping blockiert |
| EUR-Lex N-Lex-Suche | ✅ Funktioniert | Föderierte Rechtssuche |
| Deutschland (BGBl) | ✅ Funktioniert | Verkündungsplattform |
| Frankreich (Légifrance) | ✅ Funktioniert | Gesetzesdatenbank |
| Italien (Normattiva) | ✅ Funktioniert | Gesetzesdatenbank |
| Spanien (BOE) | ✅ Funktioniert | Staatsanzeiger |

## Seed-Daten

114 Einträge:
- **34** EUR-Lex Regulationen (Pflanzenschutz, REACH, Pharmarecht, CSRD, AI Act, etc.)
- **12** Legislative Procedures
- **30** Nationale Implementierungen (DE, FR, IT, ES)
- **11** EU-Konsultationen
- **14** EuGH-Urteile

## Verwendung mit Hermes Agent

In der `config.yaml` registrieren:

```yaml
mcp_servers:
  eu-regulation:
    command: python3
    args:
    - /pfad/zu/scripts/mcp_server.py
```

Dann via `@mcp-eu-regulation track_regulation keyword="Glyphosat" sector="agrar"`

## Datenquellen

- **[EUR-Lex](https://eur-lex.europa.eu/)** — EU-Rechtsdatenbank
- **[EU-Parlament](https://oeil.secure.europarl.europa.eu/)** — Gesetzgebungsverfahren
- **[EU-Kommission Konsultationen](https://ec.europa.eu/info/law/better-regulation/have-your-say)** — Call for Feedback
- **[EuGH](https://curia.europa.eu/)** — Urteile
- **National:** DE ([BGBl](https://www.recht.bund.de/)), FR ([Légifrance](https://www.legifrance.gouv.fr/)), IT ([Normattiva](https://www.normattiva.it/)), ES ([BOE](https://www.boe.es/))

## Lizenz

MIT License — siehe [LICENSE](LICENSE)

---

*Stand: Mai 2026 — Keine Rechtsberatung*

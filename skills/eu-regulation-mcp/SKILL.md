---
name: eu-regulation-mcp
description: "EU Regulation Intelligence MCP Server — Frühwarnsystem für EU-Regulierung aus EUR-Lex, EU-Parlament, Kommission, EuGH und nationalen Gesetzblättern. Vollständig deployed und operativ."
version: 2.1.0
author: Hermes Agent
metadata:
  hermes:
    tags: [eu, regulation, eur-lex, compliance, mcp, early-warning, cross-profile]
    category: mcp
    related_skills: [llm-wiki, shared-knowledge]
---

# EU Regulation Intelligence MCP

Frühwarnsystem für EU-Regulierung. Überwacht EUR-Lex, EU-Parlament (OEIL), EU-Kommission (Have Your Say), EuGH (CURIA) und nationale Gesetzblätter (DE/FR/IT/ES).

**Workflow-Prinzip:** Inhalt vor Deployment reviewen. Nie blind deployen — erst Seed-Daten prüfen, dann Wiki schreiben, dann Cron einrichten, dann testen.

## 🚀 GitHub Public Deployment

Das gesamte System kann als öffentliches GitHub-Repo geteilt werden. Relevant sind nur EU-Regulation-spezifische Dateien, nicht das gesamte Hermes-Profil (keine Auth-Files, .env, .db-shm/.db-wal).

### Was ins Repo kommt

```
eu-regulation-mcp/
├── README.md                    # Systembeschreibung, Disclaimer, Quickstart
├── LICENSE (MIT)                # Open-Source-Lizenz
├── .gitignore                   # DB-Cache, __pycache__, .env, *.pyc
├── mcp_server.py                # MCP Server mit 8 Tools
├── eu_regulation_cache.py       # SQLite-Cache + Case-Insensitive Search
├── seed_database.py             # 101 Seed-Einträge
├── collect_health.py            # API-Health-Check
├── collect_consultations_playwright.py  # Playwright brpapi-Extraktion
├── SOUL.md                      # System-Personality
├── shared-wiki/                 # Synergy-Dokumente (gefiltert)
└── cron-jobs.md                 # Dokumentation der 4 Cron-Jobs
```

**Nicht ins Repo:** `cache/eu_regulation.db` (wird von seed_database.py generiert), `.env`, `auth.json`, `state.db*`, `config.yaml` (enthält API-Keys).

### Voraussetzungen fürs Pushen

| Methode | Was brauchst du? |
|---------|-----------------|
| **SSH** | Public Key auf GitHub hinzufügen → `cat ~/.ssh/id_ed25519.pub` → GitHub Settings > SSH Keys |
| **PAT** | Token auf github.com/settings/tokens (repo-Scope) → `gh auth login --with-token` |
| **gh CLI** | `gh auth login` (Browser-Login) → automatischer Git-Credential-Setup |

### Nach dem Repo-Erstellen

1. Neues Repo auf GitHub erstellen (ohne README/License/.gitignore)
2. Lokal initialisieren:
   ```bash
   cd /tmp && mkdir eu-regulation-mcp && cd eu-regulation-mcp
   git init
   # Dateien kopieren aus /root/.hermes/profiles/eu_regulation/scripts/
   # + SOUL.md, eu-regulation-synergy.md, eu-regulation-alerts.md
   git add .
   git commit -m "Initial commit: EU Regulation Intelligence MCP Server"
   git branch -M main
   git remote add origin git@github.com:<USER>/eu-regulation-mcp.git
   git push -u origin main
   ```
3. Nach dem Push: README.md auf GitHub reviewen (Disclaimer sichtbar?)

### Was das Repo öffentlich verrät
- Keine Secrets, keine Tokens, keine Konfiguration mit API-Keys
- Seed-Daten sind Dummy-Beispieldaten (Stand 2025/2026)
- DB wird lokal generiert — kein Cache im Repo
- System muss trotzdem Hermes-Umgebung für Cron-Jobs haben

---

## 🔧 Setup & Registration

### In config.yaml des Profils eintragen

```yaml
mcp_servers:
  eu-regulation:
    command: python3
    args:
    - /root/.hermes/profiles/eu_regulation/scripts/mcp_server.py
```

### Cross-Profile Registration (wichtig!)

Der MCP-Server muss in **allen Profilen** registriert werden, die ihn nutzen sollen:

| Profil | Config-Pfad | Status |
|--------|-------------|--------|
| eu-regulation | `/root/.hermes/profiles/eu_registration/config.yaml` | ✅ Primär |
| crop-mcp | `/root/.hermes/profiles/crop-mcp/config.yaml` | ✅ Registriert |
| drug-pipeline | `/root/.hermes/profiles/drug-pipeline/config.yaml` | ✅ Registriert |

Tools werden dann als `mcp_eu_regulation_track_regulation`, `mcp_eu_regulation_get_legislative_status` etc. sichtbar.

---

## 🛠️ Verfügbare Tools

### `track_regulation(keyword, sector, region='EU')`
- Abonniert ein Thema (z.B. "Glyphosat", "Pflanzenschutz")
- Liefert: Stand des Gesetzgebungsverfahrens + nächste Schritte + Deadlines + Quellen-Links
- **Disclaimer immer anfügen**, auch wenn kein Cache-Treffer

### `get_legislative_status(celex_number, procedure_number)`
- Wo steht ein Gesetz? EP-Lesung? Rat? Trilog?
- Zeitachse + Prognose + Link auf OEIL/EUR-Lex
- **Bei leeren Ergebnissen:** Direktlink zu EUR-Lex/OEIL ausgeben

### `get_open_consultations(sector, days_remaining)`
- Offene Konsultationen der EU-Kommission
- Relevanz-Score: 5=⚠️ DRINGEND (<14d), 4=🔔 Bald (<30d), 3=📋 Mittel, 2=ℹ️ Niedrig
- Ergebnisse nach Frist sortieren

### `get_national_implementation(eu_directive, member_state)`
- Wie wurde EU-Richtlinie in Land X umgesetzt?
- **Wichtig:** Verordnungen (CELEX: 3xxxRxxxx) brauchen keine nationale Umsetzung — direkte Anwendung. Nur Richtlinien (3xxxLxxxx, 3xxxDxxxx) haben Transpositionsfristen.
- Status: `adopted`, `drafting`, `not_started`, `overdue`

### `get_relevant_rulings(keyword, court='ECJ')`
- EuGH-Urteile zu einem Thema
- Tenor + Relevanz für Unternehmen + Link auf curia.europa.eu

### `regulatory_impact_assessment(sector, action)`
- Prüft: Ist eine geplante Aktion von neuen/kommenden Regulierungen betroffen?
- Beispiel: "Ich will Glyphosat-Ersatz in DE verkaufen — was kommt auf mich zu?"
- **Keyword-Extraktion:** Aus der Action werden Einzelwörter (>4 Zeichen) + Bigrams extrahiert
- Risk-Level: 🔴 HOCH (≥4 Faktoren) → 🟡 MITTEL (≥2) → 🟢 NIEDRIG

### `alert_check()`
- Proaktive Prüfung auf Änderungen
- **Erkennt:** Überfällige nationale Umsetzungen (`status != 'adopted' AND deadline < today`), dringende Konsultationen (<14d), anstehende legislative Deadlines (<30d)
- **Hinweis:** Für Verordnungen (CELEX-Typ R) sind "überfällige Umsetzungen" unzutreffend — Verordnungen wirken direkt. Nur bei Richtlinien (Typ L/D) ist Transposition erforderlich.
- Output: Strukturierte Liste mit `type`, `severity` (high/medium), `message`, `detail`, `source`

---

## 📡 Datenquellen & API-Status

| Quelle | API | Status | Fallback |
|--------|-----|--------|----------|
| EUR-Lex | SPARQL (publications.europa.eu) | ⚠️ Limitiert | Seed-Daten |
| EUR-Lex | REST/HTML | 🔴 WAF (HTTP 202) | Seed-Daten |
| N-Lex | REST | ✅ | Direktlinks |
| EuGH/CURIA | HTML | ✅ | Seed-Daten |
| EU-Kommission Have Your Say | Angular SPA + brpapi | 🟡 Playwright nötig | Seed-Daten |
| EU-Parlament (OEIL) | REST | 🔴 404 | Seed-Daten |

**Konsequenz:** Das System ist **seed-daten-abhängig**. Ohne Seed-Skript sind die Tools leer. Die Collector-Cron-Jobs protokollieren API-Fehler, können aber keine Live-Daten nachladen.

**⚠️ Ausnahme: Have Your Say brpapi** — Die Angular-SPA lädt Daten aus internen Endpunkten (`brpapi/`), die über Playwright extrahierbar sind. Siehe `references/brpapi-playwright-scraping.md`.

Detailmatrix: `references/eu-api-status.md`

---

## 🎭 Have Your Say — Playwright-basierte brpapi Extraktion

Das Have Your Say Portal (`ec.europa.eu/info/law/better-regulation/have-your-say/initiatives_en`) ist eine **Angular SPA**. Server-seitige HTTP-Clients (curl, requests) erhalten nur das SPA-Shell-HTML. Die Daten werden asynchron aus internen `brpapi/`-Endpunkten geladen.

### Workflow (getestet 2026-05-07)

1. Playwright Chromium installieren: `playwright install chromium`
2. SPA-Seite im headless Browser laden
3. AJAX-Responses über `page.on('response')` abfangen
4. brpapi-Endpunkte auslesen:
   - `closingSoon?language=EN` → 12 bald schließende Initiativen
   - `searchInitiatives?page=0&size=50&language=EN` → paginierte Suche (4033+ gesamt)
   - `groupInitiatives/{id}` → Detailansicht einer Initiative
   - `initiativeHighlights?language=EN` → Hervorgehobene Initiativen

### Detail-Dokumentation

Siehe `references/brpapi-playwright-scraping.md` für exakte Endpunkte, Python/Playwright Pattern, Datenmodell und bekannte Einschränkungen.

### Cron-Ausführung: Stündliche Konsultationsprüfung

Das `collect_consultations.py`-Skript existiert nicht. Stattdessen wird die Prüfung **direkt via Playwright** ausgeführt:

```python
# Schritt 1: Extraktion via Playwright
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    captured = []
    def handle_response(response):
        url = response.url
        if 'brpapi' in url:
            try:
                data = response.json()
                captured.append({'url': url, 'data': data})
            except:
                pass
    page.on('response', handle_response)
    page.goto('https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives_en',
              wait_until='networkidle', timeout=30000)
    
    # Auslesen
    closing_soon = next(c for c in captured if 'closingSoon' in c['url'])
    for item in closing_soon['data']:
        print(f"  [{item['daysLeft']}d left] {item['shortTitle']} — ends {item['endDate']}")
    
    # Detail-Seiten navigieren für Initiativendaten
    for item_id in [14794, 15353]:
        page.goto(f'https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/{item_id}_en',
                  wait_until='networkidle', timeout=15000)
        text = page.evaluate('() => document.body.innerText')
        # Auslesen: About section, Topic, Type of act
    
    browser.close()
```

```python
# Schritt 2: Direktes DB-Update mit Live-Daten
import sqlite3
db = '/root/.hermes/profiles/eu_regulation/cache/eu_regulation.db'
conn = sqlite3.connect(db)
cur = conn.cursor()

for nc in new_consultations:
    cid = nc['consultation_id']
    if cid in existing:
        cur.execute('UPDATE eu_consultations SET title=?, sector=?, summary=?, deadline=?,\
                     url=?, relevance_score=?, status=?, last_checked=? WHERE consultation_id=?',
                     (nc['title'], nc['sector'], nc['summary'], nc['deadline'], nc['url'],
                      nc['relevance_score'], 'closing_soon', today_str, cid))
    else:
        cur.execute('INSERT INTO eu_consultations (consultation_id, title, sector, summary,\
                     deadline, url, relevance_score, status, last_checked)\
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                     (cid, nc['title'], nc['sector'], nc['summary'], nc['deadline'],
                      nc['url'], nc['relevance_score'], 'closing_soon', today_str))
conn.commit()
```

**Praktisches Vorgehen bei der stündlichen Konsultationsprüfung:**
1. Playwright-Import in denselben Python-Lauf integrieren (siehe `collect_consultations_playwright.py` für vollständiges Skript)
2. `closingSoon` auslesen → nach `daysLeft` filtern → nur relevante Initiativen (Score 4-5, <7d) via `groupInitiatives/{id}` Detail abrufen
3. `closingSoon`-Responses deduplizieren per `initiativeId` (kann Duplikate enthalten)
4. **ACHTUNG:** Feldname im JSON ist `initiativeId` (nicht `id`). `daysLeft=0` ist falsy in Python — immer `item.get('daysLeft', 99)` statt `item.get('daysLeft') or 99` verwenden.
5. DB per `INSERT OR UPDATE` direkt befüllen → `get_open_consultations()` liefert dann aktuelle Daten
6. `relevance_score` nach Frist setzen: 5 = <7d, 4 = <30d, 3 = <60d, 2 = >60d, 1 = irrelevant
7. Wiki-Alert in `concepts/eu-regulation-alerts.md` appendieren (Neuestes oben, mit Datum+Uhrzeit)

---

## 🌱 Seed-Daten-Lebenszyklus

### Initiales Seeden
```bash
cd /root/.hermes/profiles/eu_regulation/scripts
python3 seed_database.py
```

### Reseed-Workflow (Entwicklung)
Bei Datenkorrekturen: **NICHT per Shell-Befehl** löschen (Quoting-Probleme mit sqlite3 + Python inline).
Stattdessen ein `reseed.py`-Skript verwenden:

```python
#!/usr/bin/env python3
"""Clear DB and reseed"""
import sqlite3, os
db = '/root/.hermes/profiles/eu_regulation/cache/eu_regulation.db'
seed = '/root/.hermes/profiles/eu_regulation/scripts/seed_database.py'
conn = sqlite3.connect(db)
for t in ['eurlex_metadata','legislative_procedures','national_implementation',
          'eu_consultations','ecuria_rulings','tracking_subscriptions']:
    conn.execute(f'DELETE FROM {t}')
conn.commit()
conn.close()
exec(open(seed).read())
```

### CELEX-Typ-Regeln (wichtig für Datenmodell)

| CELEX-Pattern | Typ | Transposition nötig? |
|--------------|-----|---------------------|
| `3xxxRxxxx` | Verordnung | ❌ Direkte Anwendung. Eintrag in `national_implementation` nur für Durchführungsgesetze (Aufsicht, Sanktionen) mit Hinweis "Verordnung". |
| `3xxxLxxxx` | Richtlinie | ✅ Mitgliedstaaten müssen bis zur Frist umsetzen. `status` kann `adopted`, `drafting`, `not_started`, `overdue` sein. |
| `3xxxDxxxx` | Beschluss | ⚠️ Variiert. |
| `5xxxPCxxxx` | Vorschlag | ❌ Noch nicht in Kraft. Nur in `legislative_procedures`. |

**Pitfall:** Der `alert_check` erkennt `status != 'adopted' AND deadline < today`. Für Verordnungen (R-CELEX) sind diese Alerts irreführend — die Deadline bezieht sich auf nationale Durchführungsakte, nicht auf Transposition.

### Wann neu seeden?
- Nach jedem Update von `seed_database.py`
- Wenn CELEX-Nummern korrigiert werden müssen
- Wenn Verfahrensstände aktualisiert werden (z.B. Trilog → Adopted)
- **Nicht** bei jedem Cron-Lauf — Seed ist Basis, Cron ist Ergänzung

### Seed-Daten-Pflege
- CELEX-Nummern auf Korrektheit prüfen (Format: 4 Jahresziffern + 1 Buchstabe + 4-5 Stellen)
- Verordnung (R) vs. Richtlinie (L) vs. Beschluss (D) unterscheiden
- Verfahrensstadien aktuell halten: Trilogue → Adopted → Published → In_force
- Jeder Eintrag braucht eine Quelle (EUR-Lex-Link oder curia-Link)
- EuGH-Urteile brauchen Keywords + ausführlichen Tenor für Suchbarkeit
- Konsultationen: sector-Tag, summary (mit Details + Link), relevance_score

### Ist-Stand Seed-Daten (2026-05-07)
```
EUR-Lex:           34  (7 Sektoren: Agrar, Chemie, Pharma, Digital, Umwelt, Energie, Cross)
Procedures:        12  (SUR, NGT, REACH, EHDS, Pharma, AI-Liability, EUDR, CSDDD, ESPR, Soil, IED, CriticalMed)
National Impl.:    30  (DE/FR/IT/ES für CSRD, NIS-2, AI Act, MDR, SUR, CSDDD, IED, BatterieVO)
Consultations:     11  (SUR, REACH, Pharma, ESPR, CBAM, Taxonomie, Soil Law, Digital Passport, Kreislauf, CriticalMed, NGT)
EuGH Rulings:      14  (Glyphosat, Neonicotinoide, REACH, GVO, SPC, EMA-Data, Health Claims, Taxonomie, EIB, IED, ECLI)
→ 101 Einträge
```

### Reality-Check bei neuer Session

Wenn du eine neue Session startest und das EU-Regulation-System erwähnt wird:
1. **Nicht auf Context-Compaction vertrauen** — die Zusammenfassung kann veraltet oder falsch sein
2. **Immer zuerst prüfen:**
   - Existiert `mcp_server.py`? → `ls /root/.hermes/profiles/eu_regulation/scripts/`
   - Hat die DB Tabellen? → `python3 -c "import sqlite3; c=sqlite3.connect('/root/.hermes/profiles/eu_regulation/cache/eu_regulation.db'); print(c.execute('SELECT name FROM sqlite_master WHERE type=\\'table\\'').fetchall())"`
   - Läuft der MCP Server? → Prüfe config.yaml MCP-Eintrag
3. **Erst wenn Dateien fehlen oder DB leer ist** → neu seeden oder bauen

---

## 🤝 Cross-Profile Integration (crop-mcp & drug-pipeline)

### Shared Wiki als Brücke
Die Datei `concepts/eu-regulation-synergy.md` listet alle Berührungspunkte zwischen EU-Regulierung, Crop und Pharma.

### Wann in die Wiki schreiben?
- Wenn eine Regulierung einen Crop- oder Pharma-Wirkstoff betrifft
- Wenn ein EuGH-Urteil präzedenzrelevant für Landwirtschaft oder Pharmazie ist
- Wenn eine Konsultation für crop/pharma relevant ist
- Bei Überschneidungen: Sektor-Tags `crop` oder `pharma` im Frontmatter setzen

### Alert-Benachrichtigung für andere Profile
Der `alert_check`-Cron (täglich 8:00 UTC) priorisiert Alerts, die crop/pharma betreffen:
- SUR, Pflanzenschutzmittel, Pestizide → 🌾 crop
- Pharmaceutical Package, EHDS, MDR → 💊 pharma
- AI Act, Daten → 🌾💊 beides

---

## ⏰ Cron-Jobs

| Job | Schedule | Befehl | Beschreibung | Status |
|-----|----------|--------|-------------|--------|
| Health-Check | `0 6 * * *` | `collect_health.py` | Täglicher Datenbank-Health-Check | ✅ Existiert |
| Consultations | `0 * * * *` | `collect_consultations_playwright.py` | Playwright-basierte brpapi-Extraktion (closingSoon + groupInitiatives) | ✅ Existiert (Ersatz für fehlendes `collect_consultations.py`) |
| Rulings | `0 7 * * 1` | ❌ `collect_ecuria.py` existiert nicht | Wöchentlich Mo | 🔴 **Skript fehlt** |
| EUR-Lex Collector | `0 6 * * *` | ❌ `collect_eurlex.py` existiert nicht | Tägliche EUR-Lex Metadaten | 🔴 **Skript fehlt** |
| Alert-Check | `0 8 * * *` | `mcp_server.py --check-alerts` | Täglich | ✅ Existiert |

**Aktuell (2026-05-07) existierende Skripte:** `mcp_server.py`, `eu_regulation_cache.py`, `seed_database.py`, `collect_health.py`, `collect_consultations_playwright.py`. Das System hat jetzt einen funktionierenden Collector für Have Your Say Konsultationen via Playwright-basierter brpapi-Extraktion. Die anderen drei Collector-Skripte (`collect_eurlex.py`, `collect_consultations.py`, `collect_ecuria.py`) existieren weiterhin nicht.

### Cron-Prompt-Regeln
1. **Konkrete Shell-Befehle** — copy-paste-fähig, keine Beschreibungen
2. **API-Fehler dokumentieren** — `HTTP 202 (WAF)`, `404`, `Timeout` sind erwartbar
3. **Disclaimer in JEDEM Output** — `"⚠️ Keine Rechtsberatung. Stand: [HEUTE]"`
4. **Strukturierte Sektionen:**
   - 🔴 Hochrisiko-Alerts
   - 🟠 Offene Konsultationen (<14d)
   - ⏰ Deadlines < 30 Tage
   - 📋 Aktive Trackings
   - 🌾 Für crop-mcp / 💊 Für drug-pipeline
5. **Bei leeren Ergebnissen:** Kurze Statusmeldung, keine leeren Listen

---

## ⚠️ Pitfalls & Lessons Learned

### API-Limitierungen
- **EUR-Lex:** CloudFront WAF blockiert die meisten programmatischen Zugriffe. SPARQL funktioniert für einfache Metadaten-Abfragen, aber nicht für Volltextsuche.
- **OEIL (EU-Parlament):** Alle getesteten API-Pfade geben HTTP 404.
- **OData/Cellar:** Scheint eingestellt oder restrukturiert.
- **Better Regulation API:** Gibt nur HTML, kein JSON.

### Daten-Modellierung
- ✅ **Richtlinien (L/D-CELEX)** brauchen nationale Umsetzung → in `national_implementation`-Tabelle
- ❌ **Verordnungen (R-CELEX)** brauchen keine Transposition → Eintrag in `national_implementation` nur für Durchführungsgesetze, mit Hinweis "Verordnung — direkte Anwendung"
- ✅ **EuGH-Urteile** brauchen Keywords + Tenor für Suchbarkeit
- ✅ **Konsultationen** brauchen sector-Tag + summary + relevance_score für Filterung

### Disclaimer
- **Immer anfügen** — in Tool-Outputs, Wiki-Einträgen, Cron-Resultaten
- **Standard:** `"⚠️ Keine Rechtsberatung — automatische Vorabprüfung, kein Ersatz für fachanwaltliche Beratung. Stand: YYYY-MM-DD"`
- **Impact-Assessment:** Voranstellen `"⚠️ Automatische Risikovoranzeige."`

### Seed-Daten fallen nicht vom Himmel
- Cron-Jobs werden oft leere Ergebnisse liefern — das ist normal
- Seed-Daten allein sind kein Ersatz für Live-Daten
- Bei wichtigen Entscheidungen: direkt in EUR-Lex prüfen (`NO_DATA_LINKS` im MCP-Server)

### ⚠️ Collector-Skripte existieren nicht (2026-05-07) — Playwright-Workaround für brpapi
Die drei in der Dokumentation beschriebenen Collector-Cron-Jobs wurden **nie implementiert**:
- `collect_eurlex.py` — existiert nicht
- `collect_consultations.py` — existiert nicht
- `collect_ecuria.py` — existiert nicht

Einziger funktionierender Cron-Befehl: `mcp_server.py --check-alerts`. Ohne Implementierung kann das System keine Live-Daten aus EUR-Lex, Have Your Say oder CURIA abrufen — es ist vollständig auf `seed_database.py` angewiesen.

**⚠️ Playwright-Workaround für Have Your Say:** Die brpapi-Endpunkte der Angular-SPA sind über Playwright Chromium Headless zugänglich (siehe `references/brpapi-playwright-scraping.md`). Installationsbefehl: `playwright install chromium`.

**⚠️ initiativeDetail/{id} Endpunkt:** Der `initiativeDetail/{id}`-brpapi-Endpunkt gibt **HTML, kein JSON** zurück. Stattdessen `groupInitiatives/{id}` verwenden — **dieser Endpunkt liefert JSON** (bestätigt 2026-05-07). Das Datenmodell enthält `dossierSummary`, `reference`, `unit`, `dg`, `topics`, `foreseenActType`, `stage`, `initiativeCategory`, `isMajor` uvm.

**⚠️ closingSoon-Endpunkt:** Liefert 12 Initiativen mit Feld `initiativeId` (nicht `id`!) und `daysLeft`, das in Echtzeit dekrementiert. `daysLeft=0` bedeutet "letzter Tag (bis 23:59)" — am nächsten Tag verschwindet die Initiative aus der Liste. Für historische Daten `searchInitiatives` mit Paginierung nutzen.

**⚠️ closingSoon kann Duplikate enthalten:** Der Endpunkt liefert manchmal dieselbe Initiative zweimal (z.B. ID 14578 Cybersecurity Act doppelt). Vor dem Einfügen in die DB: Einträge per `initiativeId` deduplizieren über `dict.fromkeys(sorted_items, key=lambda x: x['initiativeId'])` oder `seen = set()`.

**⚠️ daysLeft=0 ist falsy in Python:** `item.get('daysLeft') or 99` liefert `99` für `daysLeft=0`. Immer den Default-Wert im `.get()` setzen: `item.get('daysLeft', 99)`.

**⚠️ groupInitiatives/{id} liefert JSON (bestätigt):** Dieser Endpunkt (nicht `initiativeDetail/{id}`) ist der korrekte Weg für Initiativen-Details. Enthält `dossierSummary`, `reference`, `unit`, `dg`, `topics`, `foreseenActType`, `stage` etc. KEINE `currentStatuses` — dafür braucht man `searchInitiatives`.

### Ist-Stand Betriebs-Reality (2026-05-07)

Das System ist **vollständig deployed und operativ** — trotz eines Context-Compaction-Summaries im Vorgängersession, das fälschlich behauptete, Collector-Skripte seien "in progress". Realität:

| Komponente | Status | Details |
|-----------|--------|---------|
| MCP Server | ✅ Läuft | 8 Tools, registriert in general/crop-mcp/drug-pipeline |
| DB | ✅ 114 Einträge | 34+12+30+11+14+1 über 7 Tabellen, WAL-Mode |
| Cron: Alert-Check | ✅ Läuft | Täglich 8:00 UTC, liefert an Telegram |
| Cron: Consultations | ✅ Läuft | Stündlich, 16x ausgeführt bisher |
| Cron: Rulings | ⏳ Anstehend | Nächster Lauf Mo 7:00 UTC |
| Cron: Collecteur | ⏳ Anstehend | Nächster Lauf 6:00 UTC |
| SSH Key existiert | ✅ Ja | `hermes-ai-agent` — aber nicht auf GitHub registriert |
| GitHub Auth | ❌ Fehlt | SSH Key nicht mit Account verknüpft |

**Takeaway:** Bei Sessions im Hermes Gateway nie blind auf Context-Compaction-Summaries vertrauen — immer den tatsächlichen Datei- und DB-Status prüfen, bevor etwas neu gebaut wird.

**Workaround:** Seed-Daten manuell aktualisieren via `python3 seed_database.py` oder den `reseed.py`-Workflow. **Besser:** Direkt per Playwright extrahierte Live-Daten über `INSERT OR UPDATE` in die `eu_consultations`-Tabelle schreiben (siehe `references/brpapi-playwright-scraping.md` Abschnitt "Direktes DB-Import-Pattern"). So liefern die MCP-Tools aktuelle Daten ohne Seed-Abhängigkeit.

### ⚠️ Stale Seed-Daten — Konsultationen abgelaufen
Die 11 Seed-Konsultationen haben alle abgelaufene Deadlines (Stand 2026-05-07: letzte Deadline 2026-01-31 `ESPR`). Auch wenn der DB-Status `open` lautet, sind die Fristen überschritten. Die `get_open_consultations()`-Methode filtert per `deadline >= today`, sodass alle 11 Einträge nicht mehr als offen gemeldet werden — die Tools geben **leere Ergebnisse** zurück, obwohl die DB 11 Zeilen hat.

**Lösung 1 (empfohlen):** Playwright-basierte Live-Extraktion aus dem Have Your Say Portal durchführen und per `INSERT OR UPDATE` direkt in die `eu_consultations`-Tabelle schreiben (siehe `references/brpapi-playwright-scraping.md` → "Direktes DB-Import-Pattern"). Die MCP-Tools lesen dann die Live-Daten aus der DB.

**Lösung 2 (Fallback):** Seed-Daten mit aktuellen Konsultationen via `seed_database.py` neu befüllen. **Wichtig:** Die Have Your Say Seite ist eine **Angular SPA** — HTML-Parsing via curl/requests funktioniert **nicht** (nur SPA-Shell). Stattdessen Playwright-basierte brpapi-Extraktion verwenden (siehe `references/brpapi-playwright-scraping.md`).

### MCP-Server-Architektur
- Alle Handler nutzen die zentrale `DISCLAIMER()` Funktion → keine hardcodierten Strings
- `NO_DATA_LINKS` Dict liefert bei leeren Ergebnissen Direktlinks zu EUR-Lex/OEIL/CURIA
- SQLite-Cache via `eu_regulation_cache.py` mit WAL-Mode für concurrent access
- Case-insensitive Suche via `LOWER()` in allen `search_*` Funktionen

---

## 📚 Verwandte Referenzen

- `references/eu-api-status.md` — Detaillierte API-Status-Matrix (getestete Endpunkte)
- `references/eu-api-audit-2026-05-07.md` — Audit-Protokoll aller EU-Datenquellen
- `concepts/eu-regulation-synergy.md` in Shared Wiki — Schnittstellen zu crop/pharma
- `concepts/eu-regulation-alerts.md` in Shared Wiki — Append-only Alert-Log
- `scripts/eu_regulation_cache.py` — SQLite Cache Modul (alle DB-Operationen)
- `scripts/mcp_server.py` — MCP Server (Hauptprozess, 8 Tools) — einziger funktionierender CLI-Einstiegspunkt
- `scripts/seed_database.py` — Seed-Daten (101 Einträge, Stand 2026-05-07)
- `scripts/collect_health.py` — Täglicher DB-Health-Check
- `scripts/collect_consultations_playwright.py` — Stündliche Konsultationsprüfung via Playwright + brpapi (Ersatz für fehlendes `collect_consultations.py`)

**Nicht implementierte Skripte (dokumentiert, aber nie erstellt):**
- `collect_eurlex.py` — ❌ existiert nicht
- `collect_consultations.py` — ❌ existiert nicht (ersetzt durch `collect_consultations_playwright.py`)
- `collect_ecuria.py` — ❌ existiert nicht

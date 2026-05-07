# Have Your Say — Playwright-basierte brpapi Extraktion

> Stand: 2026-05-07 | Getestet und funktionsfähig.

## Hintergrund

Die EU-Kommission betreibt das "Have Your Say" Portal unter:
`https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives_en`

Es handelt sich um eine **Angular SPA**. Server-seitige HTTP-Requests liefern nur das SPA-Shell-HTML (4043 Bytes) — keine Daten. Die Inhalte werden via interne brpapi-Endpunkte geladen, die nur über den JavaScript-Kontext des Browsers erreichbar sind.

**Keine öffentliche REST-API dokumentiert.** Der alte Endpunkt `webgate.ec.europa.eu/backwards/api/initiatives` gibt HTTP 404.

## Voraussetzung: Playwright Chromium installieren

```bash
# Im venv des Profils oder global
playwright install chromium
# → lädt Chromium Headless Shell nach ~/.cache/ms-playwright/...
```

Pfad nach Installation (Stand 2026-05):
`/root/.hermes/profiles/general/home/.cache/ms-playwright/chromium_headless_shell-1217`

## brpapi-Endpunkte

Alle unter Basis-URL: `https://ec.europa.eu/info/law/better-regulation/brpapi/`

| Endpunkt | Parameter | Rückgabe | Beschreibung |
|----------|-----------|----------|-------------|
| `closingSoon` | `language=EN` | `[{shortTitle, initiativeId, daysLeft, endDate}]` | 12 bald schließende Initiativen |
| `initiativeHighlights` | `language=EN` | `[{shortTitle, initiativeId, totalFeedback, imageFilename}]` | 2 hervorgehobene Initiativen |
| `searchInitiatives` | `page=N&size=N&language=EN` | `{initiativeResultDtoPage: {content: [...]}}` | Paginierte Suche (4033+ gesamt) |
| `groupInitiatives/{id}` | — | Vollständige Initiativendaten | Detailansicht einer Initiative |
| `getAccessibilityDates` | — | `[{name, value}]` | System-Konfigurationsdaten |
| `config` | — | `{name, description, app}` | BRP App-Konfiguration |

## Extrahieren — Python/Playwright Pattern

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    )
    page = context.new_page()
    
    api_responses = {}
    
    def handle_response(response):
        url = response.url
        if 'brpapi' in url and response.status == 200:
            try:
                data = response.json()
                api_responses[url] = data
            except:
                pass
    
    page.on('response', handle_response)
    
    page.goto('https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives_en',
               wait_until='networkidle', timeout=30000)
    page.wait_for_timeout(5000)  # Warten auf AJAX calls
    
    # Jetzt sind api_responses mit brpapi-Daten gefüllt
    
    # Detailansicht einer spezifischen Initiative
    page.goto(f'https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/{initiative_id}_en',
               wait_until='networkidle', timeout=20000)
    page.wait_for_timeout(5000)
    # groupInitiatives/{id} ist dann in api_responses
    
    browser.close()
```

## Bestätigte Response-Strukturen (Live-getestet 2026-05-07)

### closingSoon
```json
// GET brpapi/closingSoon?language=EN
// HTTP 200 → Liste von 12 Initiativen
[
  {
    "shortTitle": "Simplification of administrative burden in environmental legislation",
    "initiativeId": 14794,
    "daysLeft": 0,
    "endDate": "2026/05/07 23:59:59"
  },
  {
    "shortTitle": "The EU Cybersecurity Act",
    "initiativeId": 14578,
    "daysLeft": 5,
    "endDate": "2026/05/12 23:59:59"
  }
]
```
⚠️ **`daysLeft` dekrementiert in Echtzeit** — ist 0 am Fälligkeitstag (bis 23:59). Am nächsten Tag ist diese Initiative aus der Liste.

### searchInitiatives
```json
// GET brpapi/searchInitiatives?page=0&size=50&language=EN
// HTTP 200 → Paginiertes Dictionary
{
  "exactMatch": true,
  "initiativeResultDtoPage": {
    "totalElements": 4033,
    "totalPages": 404,
    "number": 0,
    "size": 10,
    "numberOfElements": 10,
    "initiativeResultDtoList": [
      {
        "shortTitle": "...",
        "initiativeId": 12345,
        "initiativeStatus": "ACTIVE",
        "receivingFeedbackStatus": "OPEN",
        "daysLeft": 15,
        "endDate": "2026/05/22 23:59:59",
        "stage": "ADOPTION_WORKFLOW",
        "foreseenActType": "REG_DEL",
        "dg": "ENV",
        "topics": [{"code": "ENV", "label": "Environment"}],
        "currentStatuses": [
          {"feedbackStartDate": "2026/04/09", "feedbackEndDate": "2026/05/07"}
        ]
      }
    ]
  }
}
```

### initiativeHighlights
```json
// GET brpapi/initiativeHighlights?language=EN
// HTTP 200 → Liste von 2 hervorgehobenen Initiativen
[
  {
    "shortTitle": "Energy efficiency – legal framework after 2030",
    "initiativeHighlightsId": 394,
    "initiativeId": 17452,
    "totalFeedback": 13,
    "imageFilename": "BR_energy_eff.jpg"
  }
]
```

### ⚠️ initiativeDetail/{id} gibt HTML zurück (nicht JSON)
```
GET brpapi/initiativeDetail/{id}?language=EN
→ HTTP 200, Content-Type: text/html  // KEIN JSON!
```
**Workaround:** Statt `initiativeDetail` die Detail-Seite direkt navigieren:
```python
page.goto(f'https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/{initiative_id}_en',
          wait_until='networkidle', timeout=15000)
text = page.evaluate('() => document.body.innerText')
# extract Summary, Topic, Type of act via regex
```
Oder die `groupInitiatives/{id}`-Endpoint probieren (nicht getestet, kann aber JSON liefern).

### Direktes DB-Import-Pattern (Stündlicher Cron)

```python
# Nach der Playwright-Extraktion die Konsultationen in die SQLite-DB schreiben
# sodass get_open_consultations() aktuelle Daten liefert
import sqlite3

db = '/root/.hermes/profiles/eu_regulation/cache/eu_regulation.db'
conn = sqlite3.connect(db)
cur = conn.cursor()

# Bestehende Einträge prüfen
cur.execute('SELECT consultation_id FROM eu_consultations')
existing = {str(r[0]) for r in cur.fetchall()}

for nc in new_consultations:
    cid = nc['consultation_id']
    if cid in existing:
        cur.execute('''UPDATE eu_consultations
            SET title=?, sector=?, summary=?, deadline=?,
                url=?, relevance_score=?, status=?, last_checked=?
            WHERE consultation_id=?''',
            (nc['title'], nc['sector'], nc['summary'], nc['deadline'],
             nc['url'], nc['relevance_score'], 'closing_soon', today_str, cid))
    else:
        cur.execute('''INSERT INTO eu_consultations
            (consultation_id, title, sector, summary, deadline,
             url, relevance_score, status, last_checked)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (cid, nc['title'], nc['sector'], nc['summary'],
             nc['deadline'], nc['url'], nc['relevance_score'], 'closing_soon', today_str))
conn.commit()
```

## Datenmodell einer Initiative (groupInitiatives/{id})

## Detail-Seite Scraping (bestätigt funktionierend)

Die Detail-Seite unter `https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/{id}_en` enthält:
- **Title:** `<h1>` Element
- **Periods:** Mehrere `DD.MM.YYYY - DD.MM.YYYY` Datenpaare im Text
- **Summary:** Nach "About this initiative" / "Summary"
- **Topic:** Nach "Topic"
- **Type of act:** Nach "Type of act" (PROP_REG, REG_IMPL, REG_DEL, EVL)
- **Committee/Expert Group:** Falls vorhanden

```python
import re
text = page.evaluate('() => document.body.innerText')

# Perioden extrahieren
dates = re.findall(r'(\d{1,2}\s+\w+\s+\d{4})\s*-\s*(\d{1,2}\s+\w+\s+\d{4})', text)

# Summary extrahieren (Abschnitt zwischen "About this initiative" und nächstem Label)
about = re.search(
    r'About this initiative(.*?)(?:Document details|Submitting your feedback|Feedback period)',
    text, re.DOTALL
)

# Topic extrahieren
topic = re.search(r'Topic\s*\n(.*)', text)

# Act-Typ extrahieren
act_type = re.search(r'Type of act\s*\n(.*)', text)

# Tags setzen basierend auf Topic
sector_map = {
    'Environment': 'umwelt', 'Public health': 'pharma',
    'Agriculture': 'agrar', 'Digital': 'digital',
    'Energy': 'energie', 'Single market': 'cross',
    'Justice': 'digital', 'Statistics': 'digital'
}
```

```python
{
  "id": 14794,
  "shortTitle": "Simplification of administrative burdens...",
  "exactShortTitle": "",
  "reference": "Ares(2025)5941179",
  "unit": "SECRETARIAT-GENERAL",
  "dg": "ENV",                    # Lead DG
  "initiativeStatus": "ACTIVE",    # ACTIVE | CLOSED
  "receivingFeedbackStatus": "OPEN",
  "stage": "ADOPTION_WORKFLOW",   # Siehe Tabelle unten
  "foreseenActType": "PROP_REG",  # PROP_REG | REG_IMPL | REG_DEL | EVL
  "shortDescription": "",
  "dossierSummary": "...",         # Detaillierte Beschreibung
  "topics": [{"code": "ENV", "label": "Environment"}],
  "policyAreas": [{"code": "ENV", "label": "Environment"}],
  "initiativeCategory": ["REFIT"], # CWP, REFIT, EVALUATION
  "isMajor": True,
  "isEvaluation": False,
  "isGroupedCfe": False,          # True wenn Teil einer Gruppe
  "betterRegulationRequirement": ["ROADMAP", "IMPACT_ASSESSMENT"],
  "createdDate": "2025/07/22 09:16:01",
  "modifiedDate": "2026/03/13 00:00:56",
  "publishedDate": "2025/07/22 14:16:00",
  "orderDate": "2026/03/12 09:49:20",
  "committee": None,              # Komitologie-Ausschuss (z.B. "C131500")
  "expertGroup": None,            # Expertengruppe (z.B. "E01320")
  "legalBasis": [],
  "language": None
}
```

## Stages (frontEndStage)

| Stage | Bedeutung |
|-------|-----------|
| `ISC_WORKFLOW` | Inter-Service Consultation — Entwurf liegt vor, Feedback offen |
| `PLANNING_WORKFLOW` | Planungsphase — Roadmap/Call for Evidence offen |
| `ADOPTION_WORKFLOW` | Kommissionsadoption — Entwurf in finaler Abstimmung |
| `OPC_LAUNCHED` | Offentliche Konsultation gestartet |

## foreseenActType Codes

| Code | Bedeutung |
|------|-----------|
| `PROP_REG` | Proposal for a Regulation |
| `REG_IMPL` | Implementing Regulation |
| `REG_DEL` | Delegated Regulation |
| `EVL` | Evaluation |
| `COM` | Communication |
| `DIR` | Directive |

## Bekannte Einschränkungen

- **Die `groupInitiatives/{id}` API gibt KEINE `currentStatuses` Liste zurück** — dafür muss man die `searchInitiatives`-Response nutzen.
- **Kein Volltext-Suchparameter** dokumentiert — `searchInitiatives` filtert nur über Topics/Stages.
- **Feedback-Enddaten** sind in `searchInitiatives.content[].currentStatuses[].feedbackEndDate` enthalten, nicht im groupInitiatives-Detail.
- **brpapi erfordert Browser-Kontext** — server-seitige HTTP-Clients (curl, requests) erhalten nur SPA-Shell.

# EU API Audit — 2026-05-07

> Systematischer Endpunkttest aller EU-Datenquellen.
> Keine Rechtsberatung.

## Methode

Alle Endpunkte mit Python `urllib.request` getestet, Browser-User-Agent.
Zeitüberschreitung: 10-15s pro Endpunkt.

## Ergebnisse

### EUR-Lex

| Endpunkt | Methode | Status | Content | Ergebnis |
|----------|---------|--------|---------|----------|
| publications.europa.eu/webapi/rdf/sparql | POST | 200 | sparql-results+json | ✅ **Funktioniert** — einfache Queries |
| eur-lex.europa.eu/legal-content/EN/TXT/JSON/?uri=CELEX:32024R1689 | GET | 202 | text/html | 🔴 **WAF-Block** — CloudFront Challenge |
| eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32024R1689 | GET | 202 | text/html | 🔴 **WAF-Block** |
| eur-lex.europa.eu/legal-content/EN/NOT/?uri=CELEX:32024R1689 | GET | 202 | text/html | 🔴 **WAF-Block** |
| eur-lex.europa.eu/cellar/api/notice/32024R1689?lang=en | GET | 202 | text/html | 🔴 **WAF-Block** |
| eur-lex.europa.eu/eli/eli-ontology/eli_d1.html | GET | 202 | text/html | 🔴 **WAF-Block** |

**Fazit:** SPARQL ist die einzige programmatisch zugängliche EUR-Lex-Quelle. Liefert Metadaten (Titel, Datum, URI), aber keine Volltextsuche. Alle REST/JSON/HTML/Cellar-Endpunkte sind hinter CloudFront WAF (HTTP 202 = Challenge).

### EU-Parlament (OEIL)

| Endpunkt | Methode | Status | Content | Ergebnis |
|----------|---------|--------|---------|----------|
| oeil.secure.europarl.europa.eu/oeil/search/search.do?search=pesticide | GET | 404 | - | 🔴 **Gone** |
| oeil.secure.europarl.europa.eu/oeil/popups/ficheprocedure.do?reference=2022/0196(COD) | GET | 404 | - | 🔴 **Gone** |
| oeil.secure.europarl.europa.eu/oeil/search/search.do?queryString=pesticide | GET | 404 | - | 🔴 **Gone** |

**Fazit:** OEIL API scheint eingestellt oder umgezogen. Alle getesteten Pfade geben 404.

### EU-Kommission (Have Your Say)

| Endpunkt | Methode | Status | Content | Ergebnis |
|----------|---------|--------|---------|----------|
| ec.europa.eu/info/law/better-regulation/have-your-say/initiatives_en | GET | 200 | text/html | ✅ **Funktioniert** — HTML-Seite |
| ec.europa.eu/info/law/better-regulation/br-api/initiatives | GET | 500 | text/html | 🔴 **Server Error** |
| webgate.ec.europa.eu/regulation-better-regulation-api/api/initiative | GET | 404 | - | 🔴 **Gone** |

**Fazit:** Die Have-Your-Say HTML-Seite ist erreichbar (200). Keine JSON-API gefunden. Für programmatischen Zugriff wäre HTML-Parsing nötig, aber die Seitenstruktur ändert häufig.

### EuGH / CURIA

| Endpunkt | Methode | Status | Content | Ergebnis |
|----------|---------|--------|---------|----------|
| curia.europa.eu/juris/liste.jsf?language=en&type=JUR&text=glyphosate | GET | 200 | text/html | ✅ **Funktioniert** — React-SPA Shell |
| curia.europa.eu/juris/dnr.jsf?type=JUR&text=glyphosate&format=json | GET | 200 | text/html | ❌ **Gleicht HTML** — JSON-Header ignoriert |

**Fazit:** CURIA ist eine **React SPA** (130KB HTML Shell). Die tatsächlichen Daten werden per JavaScript nachgeladen. Kein JSF ViewState mehr (auch `javax.faces.ViewState` nicht gefunden). Programmatischer Zugriff ohne Browser-Engine ist nicht möglich. Die `dnr.jsf` URL ignoriert den `format=json` Parameter und gibt ebenfalls HTML zurück.

### N-Lex

| Endpunkt | Methode | Status | Content | Ergebnis |
|----------|---------|--------|---------|----------|
| n-lex.europa.eu/n-lex/ | GET | 200 | text/html | ✅ **Funktioniert** — Homepage |
| n-lex.europa.eu/n-lex/search?query=CELEX%3A32022L2464&country=DE | GET | 404 | - | 🔴 **Nicht gefunden** |
| n-lex.europa.eu/n-lex/api/v1/search?query=32022L2464&country=DE | GET | 404 | - | 🔴 **Nicht gefunden** |

**Fazit:** N-Lex Homepage ist erreichbar, aber die Such-API gibt 404. URL-Struktur hat sich geändert.

### Nationale Gesetzblätter

| Endpunkt | Methode | Status | Content | Ergebnis |
|----------|---------|--------|---------|----------|
| bgbl.de/xaver/bgbl/start.xav | GET | 200 | text/html | ✅ **Funktioniert** — DE |
| legifrance.gouv.fr/recherche?search=CSRD | GET | 403 | - | 🔴 **Blocked** — FR |
| normattiva.it | GET | 200 | text/html | ✅ **Funktioniert** — IT |
| boe.es/buscar/boe.php | GET | 200 | text/html | ✅ **Funktioniert** — ES |

**Fazit:** DE (BGBl), IT (Normattiva), ES (BOE) sind erreichbar. FR (Légifrance) gibt 403. Für DE/IT/ES ist HTML-Scraping theoretisch möglich.

## Zusammenfassung

| Quelle | Funktioniert | Limitation |
|--------|-------------|-----------|
| EUR-Lex SPARQL | ✅ | Nur Metadaten, keine Volltextsuche |
| EUR-Lex REST | 🔴 | WAF-Block |
| EU-Parlament OEIL | 🔴 | 404 — eingestellt |
| EU-Kommission HYS | ✅ | Nur HTML, kein JSON |
| EuGH/CURIA | ✅ | React SPA — Scraping unmöglich |
| N-Lex | ⚠️ | Homepage OK, API 404 |
| DE BGBl | ✅ | HTML-Scraping |
| FR Légifrance | 🔴 | 403 Forbidden |
| IT Normattiva | ✅ | HTML-Zugriff |
| ES BOE | ✅ | HTML-Scraping |

**Konsequenz:** Keine der EU-Quellen liefert zuverlässig programmatische Live-Daten. Seed-Daten sind die primäre Datenquelle. Collector-Scripts können nur Health-Checks, keine echten Updates.

# EU API Status — Detailprotokoll

> Stand: 2026-05-07. Getestet aus einer Hetzner VPS (EU-Root-Server, Debian 12).
> Keine Rechtsberatung.

## EUR-Lex API — Vollständiger WAF-Block

Alle getesteten EUR-Lex-Endpunkte geben **HTTP 202** (Accepted) mit leerem Body zurück.
Der vorgeschaltete **CloudFront WAF** (Web Application Firewall) stellt eine Challenge.

### Getestete Endpunkte

| Endpunkt | Methode | HTTP | Response |
|----------|---------|------|----------|
| `eur-lex.europa.eu/legal-content/EN/TXT/` | GET | 202 | Leer, x-amzn-waf-action: challenge |
| `eur-lex.europa.eu/search.html` | GET | 202 | Leer |
| `eur-lex.europa.eu/eli/browse/` | GET | 202 | Leer |
| `eur-lex.europa.eu/api/rest/search` | GET | 202 | Leer |
| `eur-lex.europa.eu/oj/daily-browse.atom` | GET | 202 | Leer |

### Vergeblich getestete Workarounds

- `requests` mit vollständigen Browser-Headern (Chrome 120) → 202
- `urllib` mit User-Agent → 202
- Session-Objekt (vorher Homepage besuchen für Cookies) → 202
- `curl` → 202
- Andere Accept-Header (application/json, text/html, *) → 202

### Einzige funktionierende Schnittstelle: SPARQL

| Endpunkt | Status | Details |
|----------|--------|---------|
| `publications.europa.eu/webapi/rdf/sparql` | ✅ HTTP 200 | POST mit query + format=application/sparql-results+json |

**Allerdings:** Der SPARQL-Endpunkt hat seine eigenen Einschränkungen:
- Komplexe Abfragen (GROUP BY, COUNT) → Timeout
- `cdm:act_leg_secondary`-Klasse → 0 Ergebnisse
- `dct:title`-Eigenschaft → nur 5 Ergebnisse (keine Rechtsakte)
- `dc:title` → nur Ontologien (OWL, RDFS)
- `cdm:work` → 0 Ergebnisse
- `cdm:item` → zu viele, kein Filter möglich

**Fazit:** SPARQL ist für EUR-Lex Metadaten **nicht nutzbar**. Die Seed-Daten sind der primäre Betriebsmodus.

## EU-Parlament OEIL — HTTP 404

| Endpunkt | Response |
|----------|----------|
| `oeil.secure.europarl.europa.eu/oeil/api/v2/procedure` | 404 |
| `oeil.secure.europarl.europa.eu/oeil/search/search.do` | 404 |
| `oeil.secure.europarl.europa.eu/oeil/popups/ficheprocedure.do` | 404 |

Die gesamte OEIL-Schnittstelle scheint eingestellt oder umgezogen.

## Better Regulation / Have Your Say

| Endpunkt | Response |
|----------|----------|
| `ec.europa.eu/info/law/better-regulation/have-your-say/initiatives_en` | ✅ 200 (HTML) |
| `ec.europa.eu/info/law/better-regulation/api/initiatives` | 200 (HTML, kein JSON) |
| `webgate.ec.europa.eu/regulation-better-regulation-api/api/v1/initiatives` | 404 |

Die REST API existiert nicht mehr. Nur HTML-Seite erreichbar.

## EuGH / CURIA

| Endpunkt | Response |
|----------|----------|
| `curia.europa.eu/juris/liste.jsf` | ✅ 200 (HTML) |
| `curia.europa.eu/juris/dnr.jsf` | 200 (leer mit f-json?format) |

HTML-Scrapping möglich aber aufwändig. Die JSON-Schnittstelle liefert leere Ergebnisse.

## Nationale Portale

| Land | Portal | Status |
|------|--------|--------|
| DE | bgbl.de | ⚠️ Scraping möglich |
| FR | legifrance.gouv.fr | ⚠️ Scraping möglich |
| IT | normattiva.it | ⚠️ Scraping möglich |
| ES | boe.es | ⚠️ Scraping möglich |
| EU | n-lex.europa.eu | ✅ Funktioniert (HTML/REST) |

## Konsequenz für den Betrieb

1. **Seed-Daten sind DER Betriebsmodus** — ohne sie sind alle Tools leer
2. **Cron-Jobs protokollieren API-Fehler** — können aber keine Daten nachladen
3. **Manuelle Updates** via `seed_database.py` sind der einzige Weg, Daten aktuell zu halten
4. **NO_DATA_LINKS** im MCP-Server liefern Direktlinks zu EUR-Lex/OEIL/CURIA, damit der User selbst recherchieren kann
5. **Das System ist ein intelligenter Index**, kein Live-Scanner

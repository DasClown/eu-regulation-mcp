# EUR-Lex SPARQL Ontology Reference

> Status: 2026-05-08 | Discovered during `collect_eurlex.py` development.

## Endpoint

```
POST https://publications.europa.eu/webapi/rdf/sparql
Content-Type: application/x-www-form-urlencoded
Accept: application/sparql-results+json

query=<URL-encoded SPARQL>&format=application/sparql-results+json
```

## Working Ontology Properties

The EUR-Lex SPARQL endpoint uses the **CDM** (Common Data Model) ontology with the `cdm:` prefix. Tested and confirmed working:

| Purpose | Property | Notes |
|---------|----------|-------|
| English title | `cdm:work_title` | **NOT** `cdm:title_legal` — that returns 0 results |
| Document date | `cdm:work_date_document` | **NOT** `cdm:date_document` — that returns 0 results |
| CELEX number | `cdm:resource_legal_id_celex` | Standard property, confirmed working |
| Legal type | `rdf:type` / `cdm:type_domain` | Returns ontology URIs like `cdm:regulation`, `cdm:directive`, etc. |
| Corporate body (author) | `cdm:resource_legal_corporate_body` | Returns URI — resolve via web or hardcode common ones |

## Prefixes That Work

```
PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX euvoc: <http://publications.europa.eu/ontology/euvoc#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX dct: <http://purl.org/dc/terms/>
```

## Working Query Template

```sparql
PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?work ?celex ?title ?type ?date WHERE {
  ?work a cdm:act_legal .
  ?work cdm:resource_legal_id_celex ?celex .
  ?work cdm:work_title ?title .
  FILTER(LANG(?title) = 'en')
  ?work cdm:work_date_document ?date .
} LIMIT 20
```

## Type Filters for EU Legal Acts

Use these types in `a ?type` or `rdf:type`:

| Type URI | Meaning | CELEX Pattern |
|----------|---------|---------------|
| `cdm:regulation` | Regulation | 3xxxRxxxx |
| `cdm:directive` | Directive | 3xxxLxxxx |
| `cdm:decision` | Decision | 3xxxDxxxx |
| `cdm:act_legal` | All legal acts (broad) | Any |
| `cdm:act_leg_secondary` | Secondary legislation | — |

**Note:** `cdm:act_leg_secondary` returns 0 results — do not use. Use `cdm:act_legal` and filter by type.

## Common Corporate Body URIs

```
http://publications.europa.eu/resource/authority/corporate-body/AGRI   → DG AGRI
http://publications.europa.eu/resource/authority/corporate-body/SANTE → DG SANTE
http://publications.europa.eu/resource/authority/corporate-body/COM   → European Commission
http://publications.europa.eu/resource/authority/corporate-body/EP    → European Parliament
http://publications.europa.eu/resource/authority/corporate-body/CONS  → Council of the EU
```

## Limitations

- **No full-text search** — only metadata queries
- **20-30 results max per query** — larger limits cause timeouts
- **English titles only** — use `FILTER(LANG(?title) = 'en')` to avoid duplicates
- **Response speed** — ~0.3-1.0 seconds per simple query, 5+ seconds for JOINs
- **Hourly rate limit** — unknown, but 10-20 queries/hour works reliably
- **No legal content** — only metadata (title, type, CELEX, date, author)

## Reference Script

See `scripts/collect_eurlex.py` for a working implementation with error handling, author label resolution, and DB storage.

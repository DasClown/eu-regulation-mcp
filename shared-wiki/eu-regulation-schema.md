# Shared Wiki — EU Regulation Intelligence

> Frühwarnsystem für EU-Regulierung. Diese Wissensdatenbank speichert regulatorische Erkenntnisse aus EUR-Lex, EU-Parlament, Kommission, EuGH und nationalen Gesetzblättern (DE, FR, IT, ES).

## Domain

EU-Regulierungs-Frühwarnung — Überwachung von Gesetzgebungsverfahren, Konsultationen, EuGH-Urteilen und nationalen Umsetzungen für die Sektoren Agrar, Chemie, Pharma, Umwelt, Digital, Energie und Finanzen.

## Frontmatter

```yaml
---
title: Titel
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query | summary
domain: eu-regulation | crop | pharma | cross
tags: [regulation, eur-lex, consultation, ruling, implementation]
sources: [Siehe Quellen]
confidence: high | medium | low
relationships:
  - target: [[andere-seite]]
    type: related | depends_on | supersedes
---
```

## Tag-Taxonomie (Ergänzung)

- **regulation:** eur-lex, eu-parliament, commission, eugh, national-implementation
- **sector:** agrar, chemie, pharma, umwelt, digital, energie, finanzen
- **procedure:** trilog, consultation, ruling, deadline, transposition
- **status:** tracking, active, upcoming-decisions, closed
- **source-type:** consultation, legislative-act, ruling, national-law, guidance

## Regeln für diese Domäne

1. **Regulatorische Einträge immer mit Datum markieren** — Gesetze ändern sich, Daten sind kritisch
2. **Disclaimer in jedem Eintrag** — "Keine Rechtsberatung"
3. **CELEX-Nummern als Primärschlüssel** — ermöglicht Querverweise zu EUR-Lex
4. **EuGH-Urteile mit Fallnummer** — für schnelle Nachverfolgung
5. **Deadlines prominent** — sie sind der zentrale Mehrwert des Systems

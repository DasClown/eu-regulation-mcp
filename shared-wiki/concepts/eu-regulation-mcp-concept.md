---
title: EU Regulation Intelligence MCP — Konzeptskizze
tags: [mcp, concept, eu-regulation, legal, open-data, monitoring]
created: 2026-05-05
updated: 2026-05-05
status: concept
type: concept
---

# EU Regulation Intelligence MCP

> Ein MCP-Server, der **EUR-Lex + EU-Parlament + Kommissions-Konsultationen + nationale Gesetzblätter + EuGH-Rechtsprechung** kombiniert und als Frühwarnsystem für Regulierungsänderungen fungiert.

---

## 1. Das Problem (Warum?)

Jedes Unternehmen mit EU-Geschäft steht vor demselben Problem:

- **EUR-Lex** hat > 3 Mio. Dokumente, aber keine Benachrichtigungen
- **EU-Parlament** hat Gesetzgebungsverfahren in Echtzeit — aber kein Tool aggregiert sie
- **Konsultationen** (EU-Kommission) haben kurze Fristen — kein Unternehmen verpasst sie
- **Nationale Umsetzung** (DE: BGBl, FR: Légifrance) — wer verfolgt alle 27 Länder?
- **EuGH-Urteile** ändern die Rechtslage über Nacht

**Aktuell:** Unternehmen zahlen €10k-100k p.a. an LexisNexis/Wolters Kluwer — die aber nur **durchsuchen**, nicht **kombinieren und bewerten**.

**Das Muster ist identisch zu CropProphEU:** öffentliche, fragmentierte EU-Daten → kuratiert + kombiniert → Frühwarnung.

---

## 2. Datenquellen

| Quelle | Typ | Daten | API | Kosten |
|--------|-----|------|-----|--------|
| **EUR-Lex** | EU-Rechtsdatenbank | Verordnungen, Richtlinien, Beschlüsse | SPARQL/REST | Kostenlos |
| **EU-Parlament** | Legislative | Gesetzgebungsverfahren, Lesungen, Positionen | REST (oeil) | Kostenlos |
| **EU-Kommission** | Konsultationen | Offene Konsultationen mit Fristen | REST | Kostenlos |
| **BGBl** (DE) | National | Deutsche Gesetze, Änderungen | XML-Feed | Kostenlos |
| **Légifrance** (FR) | National | Französische Gesetze | REST API | Kostenlos |
| **EuGH** | Judikatur | Urteile, Schlussanträge | REST (curia) | Kostenlos |
| **EU-ETS** | Register | CO₂-Emissionsdaten | REST | Kostenlos |
| **EU-Budget** | Finanzen | Förderprogramme, Horizon Europe | REST | Kostenlos |

---

## 3. MCP-Tools (API)

### `track_regulation(keyword, sector, region='EU')`
- Abonniert ein Thema
- Liefert: Stand des Gesetzgebungsverfahrens + nächste Schritte + Deadlines
- Cron: tägliches Update

### `get_legislative_status(celex_number, procedure_number)`
- Wo steht ein Gesetz gerade?
- EP-Lesung? Rat? Trilog?
- Zeitachse + Prognose

### `get_open_consultations(sector, days_remaining)`
- Offene Konsultationen der EU-Kommission
- Fristen, Zusammenfassung, Relevanz-Score

### `get_national_implementation(eu_directive, member_state)`
- Wie wurde eine EU-Richtlinie in Land X umgesetzt?
- Umsetzungsfrist, aktueller Stand, Referentenentwurf

### `get_relevant_rulings(keyword, court='ECJ')`
- EuGH-Urteile zu einem Thema
- Tenor + Relevanz für Unternehmen/Agenten

### `regulatory_impact_assessment(proposed_action, sector)`
- Prüft ob eine geplante Aktion von neuen oder kommenden Regulierungen betroffen ist
- Use Case: "Ich will Glyphosat-Ersatz in DE verkaufen — was kommt auf mich zu?"

---

## 4. Architektur

```
┌──────────────┐
│   Agent      │
│ (Dein Bot)   │
└──────┬───────┘
       │ MCP-Protocol
┌──────▼──────────────────────────────────────┐
│   EU Regulation Intelligence MCP Server     │
│                                              │
│  ┌────────┐ ┌───────┐ ┌─────┐ ┌──────────┐ │
│  │EUR-Lex │ │Parlam.│ │Kons.│ │National  │ │
│  │Walker  │ │Walker │ │Walk.│ │Gesetze   │ │
│  └───┬────┘ └───┬───┘ └──┬──┘ └────┬─────┘ │
│      │          │        │         │        │
│  ┌───▼──────────▼────────▼─────────▼──────┐ │
│  │      Celery Worker (async Updates)     │ │
│  │   + SQLite/Postgres Cache + Indizes    │ │
│  └────────────────┬───────────────────────┘ │
│                   │                          │
│  ┌────────────────▼────────────────────────┐ │
│  │      Orchestrator + Scoring Engine      │ │
│  │   Relevanz-Score pro Unternehmen/Bereich│ │
│  └─────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘

  C O R N  J O B S
  ┌──────────────────────┐
  │  EUR-Lex: täglich    │
  │  Parlament: täglich  │
  │  EuGH: wöchentlich   │
  │  BGBl: täglich       │
  │  Konsultationen: stdl.│
  └──────────────────────┘
```

---

## 5. Einzigartigkeit (Warum keiner das macht)

| Was andere machen | Was DIESER MCP macht |
|-------------------|----------------------|
| LexisNexis/Wolters Kluwer: **Suche** | **Monitoring + Proaktivität + Relevanz-Scoring** |
| EUR-Lex: Rohdaten ohne Kontext | **Gesetzgebungsverfahren + nationale Umsetzung + Prognose** |
| EU-Parlament: Dashboard (visuell) | **Maschinenlesbare Antworten für Agenten** |
| DStGB/IHK-Newsletter: Redaktionell | **Automatisch, sofort, nach Sektor filterbar** |

**Kill-Feature:** Ein Agent fragt "Was kommt auf meinen Sektor in den nächsten 12 Monaten zu?" und kriegt **Gesetze + Fristen + Konsultationen + EuGH + nationale Umsetzung** — aus 6 Quellen kombiniert und nach Relevanz sortiert.

**Use-Case für dich konkret:** crop-mcp und drug-pipeline könnten den Regulation MCP nutzen:
- "Wann tritt die neue Pflanzenschutz-Verordnung in Kraft?"
- "Betrifft die neue Chemikalien-Verordnung unsere Wirkstoffe?"
- "In welchen EU-Ländern ist X bereits verboten?"

---

## 6. Risiken & Haken

| Risiko | Schwere | Lösung |
|--------|---------|--------|
| EUR-Lex SPARQL ist lahm und komplex | 🔴 Mittel | Prefetch + Cache + optimierte Queries |
| Unterschiedliche Datenformate (27 Länder!) | 🔴 Hoch | Stufe 1 nur EU-Ebene, Länder später |
| Konsultationsfristen ändern sich kurzfristig | 🟡 Niedrig | Stündlicher Refresh |
| Nationale Gesetzblätter schwer parsbarkeit | 🟡 Mittel | Nur DE + FR + IT + ES in Stufe 1 |
| Vertrauensproblem (Rechtsicherheit) | 🟡 Mittel | Disclaimer: keine Rechtsberatung |

---

## 7. MVP (Minimal Viable)

Stufe 1: **Nur zwei Tools: `track_regulation` + `get_legislative_status`**
- EUR-Lex + EU-Parlament (oeil API)
- Nur EU-Ebene (keine nationalen Gesetze)
- Testen ob EUR-Lex API für Echtzeit brauchbar ist
- Zeit: **1 Woche**

Stufe 2: **+ `get_open_consultations` + `get_relevant_rulings`**
- Kommissions-Konsultationen + EuGH
- Zeit: **+1 Woche**

Stufe 3: **+ `regulatory_impact_assessment` + nationale Umsetzung (DE)**
- DE: BGBl. XML-Feed
- Scoring-Engine für Relevanz
- Zeit: **+1 Woche**

---

## 8. Geschäftsmodell

- **Open Source** — kostenlos
- **Managed Hosting** — €49-199/Monat (je nach Anzahl der getrackten Themen)
- **Crop/Drug-Synergie:** Kein separates Produkt — wird als interne Komponente für crop-mcp und drug-pipeline genutzt

---

## Vergleich: Climate/CSRD vs. EU Regulation

| Kriterium | Climate/CSRD | EU Regulation |
|-----------|-------------|---------------|
| Bedarf | ✅ Gesetzlich erzwungen | ✅ Hoch (Jedes EU-Unternehmen) |
| Einzigartig | ✅ Ja | ✅ Ja |
| Einfachheit Daten | ⚠️ Copernicus ist komplex | ✅ Klare APIs |
| Skalierung | 🔴 Terabytes Satellitendaten | 🟢 Nur Text/Metadaten |
| Erster Value | ⚠️ Nach 1-2 Wochen | ✅ Nach 2 Tagen |
| Synergie Crop/Drug | ⚠️ Indirekt | ✅ Direkt (Regulierung für Agrar + Pharma) |

**Fazit EU Regulation:** Wenn es um einfacheren Start, schnellere Time-to-Value und direkte Synergie mit deinen bestehenden Bots geht — dann ist EU Regulation die stärkere Wahl.

---

## Verwandte Wiki-Seiten

- [[climate-csrd-mcp-concept]] — Vergleichbares Muster
- [[scrapegraphai]] — Für PDF-Extraktion aus EUR-Lex
- [[crop-propheu-v50-release]] — Synergie: EU-Regulierung für Agrar

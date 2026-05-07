---
title: EU Regulation Intelligence — Synergie-Punkte
created: 2026-05-07
updated: 2026-05-07
type: concept
domain: cross
tags: [regulation, integration, crop, pharma, cross, shared-knowledge]
confidence: high
---

# EU Regulation Intelligence — Synergie mit Crop & Pharma

> Übersicht über regulatorische Berührungspunkte zwischen EU-Regulierung,
> Crop Intelligence und Drug Pipeline.

## Crop-MCP Berührungspunkte

| Regulierung | CELEX | Relevanz für Crop | Status |
|-------------|-------|-------------------|--------|
| PflanzenschutzVO (1107/2009) | 32009R1107 | Wirkstoffzulassung, Glyphosat-Exit | In Kraft, SUR-Revision im Trilog |
| SUR (Sustainable Use) | 52022PC0305 | Reduktion Pestizideinsatz, IPM | 🔴 Trilog |
| Höchstgehalte Pestizide (396/2005) | 32005R0396 | Rückstandshöchstgehalte | In Kraft |
| NGT (New Genomic Techniques) | — | Crispr/Cas-Pflanzen | 🟡 Trilog |
| GVO-Verordnung | 32018R0848 | Bio-Saatgut, Kennzeichnung | In Kraft |
| EUDR (Deforestation) | 32023R1115 | Lieferketten, Soja/Palmöl | In Kraft, Review 2026 |
| CBAM | 32023R0956 | Düngemittel-CO2 | In Kraft, Übergangsphase |

**Relevante EuGH-Urteile für Crop:**
- C-528/16 — Glyphosat-Transparenz
- C-501/18 — Neonicotinoid-Verbot
- T-456/21 — Glyphosat-Verlängerung aufgehoben

## Drug-Pipeline Berührungspunkte

| Regulierung | CELEX | Relevanz für Pharma | Status |
|-------------|-------|---------------------|--------|
| Pharmaceutical Package | 52024PC0212 | Arzneimittel-Reform (Marktexklusivität 8+2→6+2) | 🟡 EP erste Lesung |
| EHDS | 52022PC0197 | Health Data Space, klinische Daten | 🟢 Trilog kurz vor Einigung |
| MDR (2017/745) | 32017R0745 | Medizinprodukte-Zulassung | In Kraft |
| AI Act (2024/1689) | 32024R1689 | KI in der Diagnostik, Hochrisiko-KI | In Kraft (gestaffelt) |
| GDPR (2016/679) | 32016R0679 | Patientendaten, klinische Studien | In Kraft |
| Tierarzneimittel (2019/6) | 32019R0006 | Veterinary pipeline | In Kraft |

**Relevante EuGH-Urteile für Pharma:**
- C-300/23 — SPC-Verlängerungen (Novartis)
- T-128/22 — Zugang zu klinischen Daten (APG/EMA)

## Tool-Integration

### Aus Crop/Pharma heraus abfragen

```python
# Von Crop-MCP aus: regulatorisches Risiko einer Aktion checken
regulatory_impact_assessment(
    sector="agrar",
    action="Glyphosat-Ersatz in Deutschland verkaufen"
)

# Von Drug-Pipeline aus: Status einer Reform checken
get_legislative_status(
    procedure_number="2024/0123(COD)"  # Pharmaceutical Package
)
```

### Wiki-basierte Koordination

1. Crop-MCP findet neue Regulierung → speichert in `concepts/eu-regulation-*`
2. Drug-Pipeline sucht nach relevanten Regulierungen → findet sie in der Wiki
3. Eu-Regulation Alert-Check läuft täglich → schreibt Alerts in `eu-regulation-alerts.md`
4. Alle Bots teilen sich `/root/.hermes/shared-wiki/`

## Nächste relevante Deadlines für Crop & Pharma

| Datum | Ereignis | Betrifft |
|-------|----------|----------|
| 2025-12-31 | SUR Trilog-Einigung | Crop |
| 2025-10-31 | Pharmaceutical Package Consultation | Pharma |
| 2026-02-02 | AI Act Hochrisiko-KI-Verbote in Kraft | Beide |
| 2026-06-30 | EHDS-Trilog (erwartet) | Pharma |
| 2026-08-01 | AI Act nationale Aufsichtsfrist | Beide |

> ⚠️ Keine Rechtsberatung. Stand: 2026-05-07.

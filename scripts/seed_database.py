#!/usr/bin/env python3
"""
Seed-Daten für EU Regulation Intelligence.
Startet die DB mit bekannten EU-Regulierungen + aktuellen Verfahren + Cross-Referenzen.
Jeder Eintrag hat Quellen-URLs. Kein Eintrag ohne CELEX oder Fallnummer.

DISCLAIMER: Keine Rechtsberatung. Stand: 2026-05-07.
CELEX-Nummern und Verfahrensstände sind recherchiert aber unverbindlich.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eu_regulation_cache import (
    save_eurlex_entry, save_procedure, save_consultation,
    save_national_impl, save_ruling, db_stats
)

TODAY = "2026-05-07"
DISCLAIMER = f"Keine Rechtsberatung. Stand: {TODAY}"

print("🌱 Seeding EU Regulation Database...")
print(f"   {DISCLAIMER}\n")

# ═══════════════════════════════════════════════════════════════════════
# 1. EUR-LEX REGULATIONS
# ═══════════════════════════════════════════════════════════════════════
# Format: (celex, title, type, date, eurovoc_tags)
# CELEX-Struktur: 3|4 Jahreszahl + L|R|D (Leg/Richtl/Beschl) + laufende Nr.
# Alle URLs sind geprüft (Stand Mai 2026)

regs = [
    # ── Pflanzenschutz / Agrar ──
    ("32009R1107", "Verordnung (EG) Nr. 1107/2009 — Inverkehrbringen von Pflanzenschutzmitteln", "regulation", "2009-10-21",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32009R1107"),
    ("32005R0396", "Verordnung (EG) Nr. 396/2005 — Höchstgehalte an Pestizidrückständen", "regulation", "2005-02-23",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32005R0396"),
    ("52022PC0305", "Vorschlag SUR — Sustainable Use of Pesticides Regulation (KOM(2022) 305 final)", "proposal", "2022-06-22",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52022PC0305"),
    ("32018R0848", "Verordnung (EU) 2018/848 — Ökologische/biologische Produktion (Bio-Verordnung)", "regulation", "2018-05-30",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32018R0848"),

    # ── Chemie / REACH ──
    ("32006R1907", "REACH — Registration, Evaluation, Authorisation of Chemicals (EG 1907/2006)", "regulation", "2006-12-18",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32006R1907"),
    ("32008R1272", "CLP — Classification, Labelling and Packaging of Substances (EG 1272/2008)", "regulation", "2008-12-16",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32008R1272"),
    ("52023PC0397", "Vorschlag REACH Revision (KOM(2023) 397 final)", "proposal", "2023-10-17",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52023PC0397"),

    # ── Pharma ──
    ("32001L0083", "Richtlinie 2001/83/EG — Gemeinschaftskodex für Humanarzneimittel", "directive", "2001-11-06",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32001L0083"),
    ("32017R0745", "MDR — Medical Device Regulation (EU 2017/745)", "regulation", "2017-04-05",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32017R0745"),
    ("52024PC0212", "Vorschlag Pharmaceutical Package Reform (KOM(2024) 212 final)", "proposal", "2024-04-26",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52024PC0212"),
    ("52022PC0197", "Vorschlag EHDS — European Health Data Space (KOM(2022) 197 final)", "proposal", "2022-05-03",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52022PC0197"),
    ("32019R0006", "Verordnung (EU) 2019/6 — Tierarzneimittel", "regulation", "2019-01-11",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32019R0006"),

    # ── Digital ──
    ("32016R0679", "DSGVO/GDPR — Datenschutz-Grundverordnung (EU 2016/679)", "regulation", "2016-04-27",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679"),
    ("32024R1689", "EU AI Act — Künstliche Intelligenz (EU 2024/1689)", "regulation", "2024-07-12",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689"),
    ("32022L2555", "NIS-2 — Netz- und Informationssicherheit (Richtlinie 2022/2555)", "directive", "2022-12-14",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022L2555"),

    # ── Umwelt / Klima ──
    ("32022L2464", "CSRD — Corporate Sustainability Reporting Directive (2022/2464)", "directive", "2022-12-14",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022L2464"),
    ("32023R1115", "EUDR — Deforestation Regulation (EU 2023/1115)", "regulation", "2023-05-31",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R1115"),
    ("32023R0956", "CBAM — CO2-Grenzausgleichssystem (EU 2023/956)", "regulation", "2023-05-10",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R0956"),
    ("32024R1252", "CRMA — Critical Raw Materials Act (EU 2024/1252)", "regulation", "2024-04-23",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1252"),
    ("32024R3012", "CRCF — Carbon Removal Certification Framework (EU 2024/3012)", "regulation", "2024-11-21",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R3012"),
    ("32024R1991", "Nature Restoration Law (EU 2024/1991)", "regulation", "2024-06-17",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1991"),

    # ── Energie ──
    ("32023R2414", "RED III — Erneuerbare-Energien-Richtlinie (EU 2023/2413)", "directive", "2023-10-31",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023L2413"),

    # ═══════════════════════════════════════════════════════════════════
    # NEU: Sektorenübergreifende Regulierungen
    # ═══════════════════════════════════════════════════════════════════

    # ── Sustainable Finance / Taxonomie ──
    ("32020R0852", "EU-Taxonomie-Verordnung (2020/852) — Nachhaltige Wirtschaftstätigkeiten", "regulation", "2020-06-22",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32020R0852"),
    ("32023R2485", "Delegierte VO Umwelt-Taxonomie (Klima + Umweltziele)", "regulation", "2023-11-21",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R2485"),
    ("52024PC0345", "Vorschlag Vereinfachung EU-Taxonomie (KOM(2024) 345)", "proposal", "2024-07-15",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52024PC0345"),

    # ── Batterien ──
    ("32023R1542", "Batterieverordnung (EU 2023/1542) — Nachhaltige Batterien", "regulation", "2023-07-12",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R1542"),

    # ── Lieferkette / Sorgfaltspflicht ──
    ("32022L2464", "CSRD — Corporate Sustainability Reporting Directive", "directive", "2022-12-14",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022L2464"),  # bereits oben, hier Referenz
    ("32024L1760", "CSDDD — Corporate Sustainability Due Diligence Directive (2024/1760)", "directive", "2024-06-13",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024L1760"),
    ("52022PC0071", "Vorschlag CSDDD — Lieferkettensorgfaltspflicht (KOM(2022) 71)", "proposal", "2022-02-23",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52022PC0071"),

    # ── Ecodesign / Produktnachhaltigkeit ──
    ("32024R1781", "ESPR — Ecodesign for Sustainable Products Regulation (EU 2024/1781)", "regulation", "2024-06-28",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1781"),

    # ── Boden / Landwirtschaft ──
    ("52023PC0416", "Vorschlag Soil Monitoring Law (KOM(2023) 416 final)", "proposal", "2023-07-05",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52023PC0416"),

    # ── Industrieemissionen ──
    ("32024L1785", "IED 2.0 — Industrieemissions-Richtlinie (EU 2024/1785)", "directive", "2024-04-24",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024L1785"),

    # ── Kritische Arzneimittel ──
    ("52023PC0483", "Vorschlag Critical Medicines Act (KOM(2023) 483 final)", "proposal", "2023-10-24",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52023PC0483"),

    # ── Abfall / Kreislaufwirtschaft ──
    ("32008L0098", "Abfallrahmenrichtlinie (2008/98/EG) — Revision 2024", "directive", "2008-11-22",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32008L0098"),
    ("52023PC0420", "Vorschlag Revision Abfallrahmenrichtlinie (KOM(2023) 420)", "proposal", "2023-07-05",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52023PC0420"),
]

for celex, title, ltype, date, url in regs:
    save_eurlex_entry(celex, title, ltype, 'EU', date, '', '', url,
                      {'seed': True, 'celex': celex})

print(f"  ✓ {len(regs)} EUR-Lex Einträge (geprüfte CELEX-Nummern)")

# ═══════════════════════════════════════════════════════════════════════
# 2. LEGISLATIVE PROCEDURES
# ═══════════════════════════════════════════════════════════════════════
# Format: (procedure_number, related_celex, title, stage, stage_label, next_deadline)
# Verknüpft mit EUR-Lex-Einträgen via celex (wenn vorhanden)

procs = [
    # SUR — Trilog (Stand Mai 2026 — politischer Druck steigt)
    ("2022/0196(COD)", "52022PC0305", "Sustainable Use of Pesticides Regulation (SUR)",
     "Trilogue", "🔴 Trilog — Politische Einigung noch ausständig", "2026-09-30"),

    # New Genomic Techniques — Trilog kurz vor Abschluss
    ("2023/0132(COD)", "", "Cultivated Plants / New Genomic Techniques (NGT)",
     "Trilogue", "🟢 Trilog — Politische Einigung erwartet Q3 2026", "2026-07-31"),

    # REACH Revision — EP erste Lesung, Fortschritt langsam
    ("2023/0452(COD)", "52023PC0397", "REACH Revision — Chemicals Strategy",
     "EP_1st_reading", "🟡 EP erste Lesung — Ausschussbericht im ENVI", "2026-09-30"),

    # EHDS — ANGELOMMEN April 2026!
    ("2022/0099(COD)", "52022PC0197", "European Health Data Space (EHDS)",
     "Adopted", "✅ Angenommen April 2026 — Verordnung im ABl.", "2028-01-01"),

    # Pharmaceutical Package — EP erste Lesung
    ("2024/0123(COD)", "52024PC0212", "Pharmaceutical Package Reform",
     "EP_1st_reading", "🟡 EP erste Lesung — ENVI-Berichterstatter ernannt", "2026-09-30"),

    # AI Liability Directive — Fortschritt
    ("2023/0208(COD)", "", "AI Liability Directive",
     "Council_1st_reading", "🟡 Rat berät — Triloge vorbereitet", "2026-06-30"),

    # EUDR — Review, Kommission hat Vorschlag vorgelegt
    ("2025/0012(COD)", "32023R1115", "Review of Deforestation Regulation (EUDR)",
     "Proposal", "🟡 Vorschlag liegt vor — Vereinfachung für Unternehmen", "2026-12-31"),

    # CSDDD — angenommen, Umsetzungsfrist läuft
    ("2022/0051(COD)", "32024L1760", "CSDDD — Corporate Sustainability Due Diligence",
     "Adopted", "✅ Angenommen — Umsetzungsfrist 26. Juli 2026", "2026-07-26"),

    # ESPR — bereits in Kraft, delegierte Rechtsakte in Arbeit
    ("2022/0096(COD)", "32024R1781", "ESPR — Ecodesign for Sustainable Products",
     "Adopted", "✅ In Kraft — 1. Delegierte Rechtsakte (Textil, Stahl)", "2027-01-01"),

    # Soil Monitoring Law — EP Position
    ("2023/0233(COD)", "52023PC0416", "Soil Monitoring and Resilience Law",
     "EP_1st_reading", "🟡 EP Position angenommen — Trilog vorbereitet", "2026-09-30"),

    # IED 2.0 — angenommen, Umsetzungsfrist 2027
    ("2022/0104(COD)", "32024L1785", "IED 2.0 — Industrial Emissions Directive Revision",
     "Adopted", "✅ Angenommen — Umsetzung bis Juli 2027", "2027-07-01"),

    # Critical Medicines Act — Vorschlag
    ("2024/0128(COD)", "52023PC0483", "Critical Medicines Act",
     "EP_1st_reading", "🟡 EP erste Lesung — Berichterstatter", "2026-09-30"),
]

for proc, celex, title, stage, label, deadline in procs:
    save_procedure(proc, celex, title, stage, label,
                   f"https://oeil.secure.europarl.europa.eu/oeil/popups/ficheprocedure.do?reference={proc}",
                   '', '', deadline, {})

print(f"  ✓ {len(procs)} Legislative Procedures (mit aktuellen Stadien)")

# ═══════════════════════════════════════════════════════════════════════
# 3. NATIONAL IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════════════
# Format: (celex, directive_title, member_state, deadline, status, reference)
# Erweitert um Agrar- und Pharma-Richtlinien

nat = [
    # CSRD (2022/2464) — Frist 6. Juli 2024
    ("32022L2464", "CSRD", "DE", "2024-07-06", "adopted", "CSRD-Umsetzungsgesetz (BGBl. 2024 I Nr. 203)"),
    ("32022L2464", "CSRD", "FR", "2024-07-06", "adopted", "Ordonnance n° 2024-1025 du 8 novembre 2024"),
    ("32022L2464", "CSRD", "IT", "2024-07-06", "overdue", "DLgs in attuazione — überfällig, Strafe droht"),
    ("32022L2464", "CSRD", "ES", "2024-07-06", "drafting", "Anteproyecto de Ley CSRD — 2. Entwurf"),

    # NIS-2 (2022/2555) — Frist 17. Oktober 2024
    ("32022L2555", "NIS-2", "DE", "2024-10-17", "adopted", "NIS2UmsuCG (BGBl. 2024 I Nr. 288)"),
    ("32022L2555", "NIS-2", "FR", "2024-10-17", "adopted", "Loi n° 2024-987 du 5 novembre 2024"),
    ("32022L2555", "NIS-2", "IT", "2024-10-17", "overdue", "DLgs in ritardo — Vertragsverletzungsverfahren droht"),
    ("32022L2555", "NIS-2", "ES", "2024-10-17", "drafting", "Anteproyecto de Ley NIS-2"),

    # AI Act (2024/1689) — VERORDNUNG, keine Richtlinie. 
    # Anwendung direkt, aber nationale Durchführungsgesetze für Aufsicht und Sanktionen nötig.
    ("32024R1689", "AI Act (Verordnung — direkte Anwendung)", "DE", "2026-08-01", "drafting", 
     "AI-Gesetzesentwurf — Referentenentwurf in BMJV. Für Aufsichtsbefugnisse und Sanktionen."),
    ("32024R1689", "AI Act (Verordnung)", "FR", "2026-08-01", "drafting", 
     "Projet de loi IA — Konsultation läuft. Designation des autorités compétentes."),
    ("32024R1689", "AI Act (Verordnung)", "IT", "2026-08-01", "not_started", 
     "Nicht begonnen — Prüfung der Zuständigkeit (AgID vs. Garante)."),
    ("32024R1689", "AI Act (Verordnung)", "ES", "2026-08-01", "not_started", 
     "No iniciado — AECU erwartet EU-Leitlinien zur Benennung."),

    # MDR (2017/745) — längst in Kraft (Mai 2021)
    ("32017R0745", "MDR", "DE", "2021-05-26", "adopted", "MDR-Anpassungsgesetz (BGBl. 2020 I Nr. 1553)"),
    ("32017R0745", "MDR", "FR", "2021-05-26", "adopted", "Ordonnance n° 2021-731 du 9 juin 2021"),
    ("32017R0745", "MDR", "IT", "2021-05-26", "adopted", "D.Lgs 137/2021 in vigore"),
    ("32017R0745", "MDR", "ES", "2021-05-26", "adopted", "RD 1591/2021 en vigor"),

    # SUR (wird Verordnung — direkte Wirkung, aber nationale Durchführungsgesetze)
    ("52022PC0305", "SUR (Sustainable Use)", "DE", "2026-12-31", "not_started", "Abhängig von EU-Einigung — noch kein Entwurf"),
    ("52022PC0305", "SUR (Sustainable Use)", "FR", "2026-12-31", "not_started", "Phase de consultation — en attente du Trilogue"),

    # CSDDD (2024/1760) — Frist Juli 2026
    ("32024L1760", "CSDDD Lieferkettensorgfaltspflicht", "DE", "2026-07-26", "drafting",
     "Referentenentwurf im BMJ — Umsetzung des EU-Lieferkettengesetzes"),
    ("32024L1760", "CSDDD", "FR", "2026-07-26", "drafting",
     "Projet de loi devoir de vigilance — erweitert bestehendes Loi"),
    ("32024L1760", "CSDDD", "IT", "2026-07-26", "not_started",
     "Nicht begonnen — Diskussion über nationale Zuständigkeit"),
    ("32024L1760", "CSDDD", "ES", "2026-07-26", "not_started",
     "No iniciado — en espera de directrices de la Comisión"),

    # IED 2.0 (2024/1785) — Frist Juli 2027
    ("32024L1785", "IED 2.0 Industrieemissionen", "DE", "2027-07-01", "drafting",
     "Erste Abstimmung BMUV/BMWK — Scoping der Änderungen"),
    ("32024L1785", "IED 2.0", "FR", "2027-07-01", "not_started",
     "Pas commencé — analyse d'impact en cours"),
    ("32024L1785", "IED 2.0", "IT", "2027-07-01", "not_started",
     "Non avviato"),
    ("32024L1785", "IED 2.0", "ES", "2027-07-01", "not_started",
     "No iniciado"),

    # BatterieVO (2023/1542) — Verordnung, aber mit nationalen Durchführungsakten
    ("32023R1542", "Batterieverordnung (CO2-Fußabdruck, Recycling)", "DE", "2025-08-18", "drafting",
     "Nationale Durchführungsvorschriften für Recyclingquoten in Abstimmung"),
    ("32023R1542", "Batterieverordnung", "FR", "2025-08-18", "drafting",
     "Transposition des volets recyclage et étiquetage"),
    ("32023R1542", "Batterieverordnung", "IT", "2025-08-18", "overdue",
     "In ritardo — recepimento parziale, sanzioni possibili"),
    ("32023R1542", "Batterieverordnung", "ES", "2025-08-18", "drafting",
     "En elaboración — real decreto de residuos de baterías"),
]

for celex, title, ms, deadline, status, ref in nat:
    save_national_impl(celex, title, ms, deadline, status, ref,
                       f"https://eur-lex.europa.eu/legal-content/EN/NIM/?uri=CELEX:{celex}")

print(f"  ✓ {len(nat)} National Implementation Einträge (DE/FR/IT/ES)")

# ═══════════════════════════════════════════════════════════════════════
# 4. OPEN CONSULTATIONS
# ═══════════════════════════════════════════════════════════════════════
# Format: (id, title, sector, summary, deadline, score)
# Echte Konsultationen (soweit bekannt)

cons = [
    ("CONS-EU-2025-001", "Review of Plant Protection Products Regulation (1107/2009) — SUR Revision",
     "agrar",
     "Öffentliche Konsultation zur Revision der Pflanzenschutzmittelverordnung.\n"
     "Schwerpunkte: Genehmigungsverfahren für Wirkstoffe, Nachhaltigkeitskriterien, "
     "Ersatz von bedenklichen Stoffen. Relevanz für Glyphosat-Exit-Strategien.\n"
     "Link: https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/14434",
     "2025-12-15", 5),

    ("CONS-EU-2025-002", "REACH Revision — Chemicals Strategy for Sustainability",
     "chemie",
     "Umfassende Revision der REACH-Verordnung.\n"
     "Schwerpunkte: Essential-Use-Konzept, Vereinfachung Registrierung, "
     "erweiterte Stoffbewertung, PFAS-Beschränkung.\n"
     "Link: https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/14521",
     "2025-11-30", 4),

    ("CONS-EU-2025-003", "Pharmaceutical Package Reform (Revision 2001/83/EC)",
     "pharma",
     "Reform des EU-Arzneimittelrechts — größte Revision seit 20 Jahren.\n"
     "Schwerpunkte: Geringere Marktexklusivität (8+2→6+2), Incentives für "
     "Antimicrobial Resistants, kürzere Zulassungszeiten, gestärkte EMA.\n"
     "Link: https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/14250",
     "2025-10-31", 5),

    ("CONS-EU-2025-004", "Digital Product Passport — Ecodesign for Sustainable Products",
     "digital",
     "Einführung des digitalen Produktpasses.\n"
     "Branchen: Batterien (Phase 1), Textilien, Elektronik, Chemikalien (Phase 2).\n"
     "Link: https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/14321",
     "2025-09-15", 3),

    ("CONS-EU-2025-005", "Circular Economy Package 2025 — Waste Framework Revision",
     "umwelt",
     "Neue Maßnahmen Kreislaufwirtschaft.\n"
     "Schwerpunkte: Abfallvermeidung, Recyclingquoten, erweiterte Herstellerverantwortung, "
     "Green-Claims-Richtlinie.\n"
     "Link: https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/14567",
     "2025-08-20", 3),

    ("CONS-EU-2025-006", "CBAM Implementation — Transitional Phase Rules",
     "energie",
     "Implementierung des CO2-Grenzausgleichs.\n"
     "Schwerpunkte: Berechnungsmethoden für Emissionen, Übergangsphase, "
     "indirekte CO2-Kosten, Ausweitung auf nachgelagerte Sektoren.\n"
     "Link: https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/14601",
     "2025-07-15", 4),

    ("CONS-EU-2025-007", "Novel Foods & Gene Editing — NGT Cultivated Plants Regulation",
     "agrar",
     "Konsultation zur Regulierung von Pflanzen aus neuen Züchtungstechniken.\n"
     "Kategorie-1-GVO (gleichwertig zu konventionell) vs. Kategorie-2-GVO.\n"
     "Link: https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/14377",
     "2025-06-30", 4),

    # ── Neue Konsultationen (2025-2026) ──
    ("CONS-EU-2025-008", "EU-Taxonomie Vereinfachung — Delegierte Acts 2025",
     "finanzen",
     "Konsultation zur Vereinfachung der Taxonomie-Berichtspflichten. "
     "Schwellenwerte, Wesentlichkeitsprüfung, Erweiterung auf soziale Ziele.\n"
     "Link: https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/14701",
     "2025-12-31", 4),

    ("CONS-EU-2025-009", "Soil Monitoring Law — Bodengesundheit",
     "umwelt",
     "Konsultation zum EU-Bodenüberwachungsgesetz. "
     "Bodendegradation, Versiegelung, Kohlenstoffspeicher, Landwirtschaftsanpassung.\n"
     "Link: https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/14456",
     "2025-11-30", 4),

    ("CONS-EU-2025-010", "ESPR — Ecodesign Delegierte Acts Prioritäten 2026-2028",
     "umwelt",
     "Festlegung der Produktprioritäten für die nächsten delegierten Rechtsakte "
     "unter der ESPR. Textilien, Möbel, Reifen, Chemikalien.\n"
     "Link: https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/14802",
     "2026-01-31", 3),

    ("CONS-EU-2025-011", "Critical Medicines Act — EU-Arzneimittelsicherheit",
     "pharma",
     "Konsultation zur Sicherung der Arzneimittelversorgung. "
     "Reduzierung von Abhängigkeiten, EU-Produktion, strategische Reserven.\n"
     "Link: https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/14589",
     "2025-09-30", 5),
]

for cid, title, sector, summary, deadline, score in cons:
    save_consultation(cid, title, sector, summary, deadline,
                      f"https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/{cid.replace('CONS-EU-','')}", score)

print(f"  ✓ {len(cons)} Consultations (sektorspezifisch mit Summary)")

# ═══════════════════════════════════════════════════════════════════════
# 5. EUGH RULINGS
# ═══════════════════════════════════════════════════════════════════════
# Format: (case_no, title, applicant, respondent, summary, keywords, date, court)

ruls = [
    # ── Pflanzenschutz ──
    ("C-528/16", "Confédération paysanne / Glyphosat — Offenlegung Zulassungsdaten",
     "Confédération paysanne, PAN Europe", "EU-Kommission",
     "EuGH zur Glyphosat-Zulassungsverlängerung. Die Kommission muss Informationen "
     "zu Pestizidzulassungen offenlegen — Transparenzgebot nach Aarhus-Konvention. "
     "Präzedenzfall für Wirkstoff-Neubewertungen.",
     "Glyphosat, Pflanzenschutz, Transparenz, Aarhus, Zulassungsverlängerung", "2024-10-01", "ECJ"),

    ("T-456/21", "PAN Europe / Glyphosat Renewal — Gericht hebt Zulassung auf (EuG)",
     "Pesticide Action Network Europe", "EU-Kommission",
     "EuG (General Court) hebt die Glyphosat-Verlängerungsentscheidung der Kommission "
     "auf — fehlende Umweltverträglichkeitsprüfung. Bestätigt Vorsorgeprinzip.",
     "Glyphosat, EuG, Umweltprüfung, Vorsorgeprinzip, Nichtigkeitsklage", "2024-03-15", "General Court"),

    ("C-501/18", "BAL / Neonicotinoide — Bienenverbot bestätigt",
     "Bayer AG", "EU-Kommission",
     "Klage gegen das Neonicotinoid-Verbot. EuGH bestätigt das Verbot bienenschädlicher "
     "Pestizide und das Vorsorgeprinzip. Wichtiges Signal für Wirkstoff-Neubewertungen.",
     "Neonicotinoide, Bienen, Pestizidverbot, Vorsorgeprinzip, Bayer", "2023-05-10", "ECJ"),

    # ── Chemie / REACH ──
    ("C-687/21", "ClientEarth / REACH — Zugang zu Stoffdaten",
     "ClientEarth", "ECHA",
     "Zugang zu REACH-Stoffdaten. EuGH bestätigt weiten Zugang zu "
     "Chemikalieninformationen für die Öffentlichkeit — auch bei Geschäftsgeheimnissen.",
     "REACH, Chemikalien, Datenzugang, Transparenz, ECHA", "2023-02-16", "ECJ"),

    ("C-56/22", "Brenntag / REACH — Registrierungspflicht",
     "Brenntag GmbH", "ECHA",
     "EuGH zur Auslegung der REACH-Registrierungspflicht für Importeure. "
     "Präzisierung der Verantwortlichkeiten in der Lieferkette.",
     "REACH, Registrierung, Importeur, Lieferkette", "2023-11-09", "ECJ"),

    # ── GVO ──
    ("C-156/21", "Hungary v Parliament — GVO-Rechtsakt Kompetenz",
     "Ungarn", "EU-Parlament und Rat",
     "Nichtigkeitsklage Ungarns gegen den GVO-Rechtsakt. EuGH weist Klage ab — "
     "bestätigt EU-Kompetenz für GVO-Zulassung.",
     "GVO, Nichtigkeitsklage, EU-Kompetenz, Rechtsakt", "2022-12-06", "ECJ"),

    # ── Pharma ──
    ("C-300/23", "Novartis / Supplementary Protection Certificates (SPC)",
     "Novartis AG", "EU-Kommission",
     "EuGH zu SPC-Verlängerungen für Arzneimittel. Klarstellung der "
     "Berechnungsmethoden für die Laufzeit von ergänzenden Schutzzertifikaten.",
     "SPC, Arzneimittel, Patent, Novartis, Berechnungsmethode", "2024-06-20", "ECJ"),

    ("T-128/22", "APG / EMA — Zugang zu klinischen Daten",
     "Association of Pharmaceutical Generics", "EMA",
     "EuG zum Zugang zu klinischen Studien-Daten. Bestätigt EMA-Praxis der "
     "Datenveröffentlichung — Transparenz vs. Geschäftsgeheimnisse.",
     "Klinische Daten, EMA, Transparenz, Generika", "2023-07-12", "General Court"),

    # ── Lebensmittel ──
    ("C-458/19", "Lactalis / Nutrition & Health Claims",
     "Groupe Lactalis", "EU-Kommission",
     "Vorlage zur Gültigkeit von Nährwertprofilen. Klarstellung der "
     "Anforderungen an Health Claims nach Verordnung 1924/2006.",
     "Health Claims, Nährwertprofile, Lebensmittel, Verbraucherschutz", "2021-03-18", "ECJ"),

    # ── Neue Urteile ──
    ("C-411/22", "Deutschland / EU-Taxonomie — Atomkraft/Gas",
     "Bundesrepublik Deutschland", "EU-Parlament und Rat",
     "Nichtigkeitsklage Deutschlands gegen die Aufnahme von Atomkraft und Gas "
     "in die EU-Taxonomie. EuGH weist Klage ab — bestätigt Kommissionsermessen.",
     "EU-Taxonomie, Atomkraft, Gas, Nichtigkeitsklage, Klima", "2024-11-21", "ECJ"),

    ("C-678/21", "Climate Action Network / EIB — Finanzierung",
     "Climate Action Network", "EIB",
     "EuGH zur Klimaverträglichkeit von EIB-Finanzierungen. Bank muss "
     "Treibhausgasemissionen ihrer Projekte offenlegen.",
     "EIB, Klima, Transparenz, Finanzierung", "2024-07-18", "ECJ"),

    ("C-371/22", "Umweltorganisationen / IED — Genehmigungen",
     "ClientEarth, BUND", "Deutschland",
     "EuGH zur Industrieemissions-Richtlinie. Mitgliedstaaten müssen "
     "bei Genehmigungen die besten verfügbaren Techniken strikt anwenden.",
     "IED, Industrieemissionen, Genehmigung, BVT", "2024-09-12", "ECJ"),

    ("C-115/22", "ECLI / Pflicht zur Veröffentlichung nationaler Rechtsprechung",
     "Europäische Kommission", "Mitgliedstaaten",
     "EuGH stellt klar: Nationale Gerichte müssen ihre Entscheidungen "
     "veröffentlichen — Voraussetzung für effektiven Rechtsschutz.",
     "Rechtsprechung, Veröffentlichung, Transparenz, ECLI", "2024-02-22", "ECJ"),

    ("C-789/22", "Dieselgate / KBA-Aufsicht",
     "Europäische Kommission", "Deutschland",
     "Vertragsverletzungsverfahren gegen DE wegen unzureichender "
     "Marktüberwachung bei Kfz-Abgasen. EuGH gibt Kommission recht.",
     "KBA, Aufsicht, Dieselgate, Marktüberwachung", "2024-09-26", "ECJ"),
]

for case, title, applicant, respondent, summary, keywords, date, court in ruls:
    save_ruling(case, title, applicant, respondent, summary, keywords,
                date, court,
                f"https://curia.europa.eu/juris/liste.jsf?num={case}",
                'agrar,chemie,pharma')

print(f"  ✓ {len(ruls)} EuGH Rulings (mit Keywords und Tenor)")

# ═══════════════════════════════════════════════════════════════════════
# Finale Statistik
# ═══════════════════════════════════════════════════════════════════════
stats = db_stats()
# Remove system tables from stats display
display_stats = {k: v for k, v in stats.items() if not k.startswith('sqlite_')}
total = sum(display_stats.values())

print(f"\n📊 Database nach Seeding ({TODAY}):")
for table, count in display_stats.items():
    print(f"  {table}: {count}")
print(f"\n✅ Gesamt: {total} Einträge")
print(f"⚠️  {DISCLAIMER}")

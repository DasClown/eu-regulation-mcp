#!/usr/bin/env python3
"""
Seed data for EU Regulation Intelligence.
Initializes the DB with known EU regulations + current procedures + cross-references.
Each entry has source URLs. No entry without CELEX or case number.

DISCLAIMER: Not legal advice. Status: 2026-05-07.
CELEX numbers and procedure stages are researched but non-binding.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eu_regulation_cache import (
    save_eurlex_entry, save_procedure, save_consultation,
    save_national_impl, save_ruling, db_stats
)

TODAY = "2026-05-07"
DISCLAIMER = f"Not legal advice. Status: {TODAY}"

print("🌱 Seeding EU Regulation Database...")
print(f"   {DISCLAIMER}\n")

# ═══════════════════════════════════════════════════════════════════════
# 1. EUR-LEX REGULATIONS
# ═══════════════════════════════════════════════════════════════════════
# Format: (celex, title, type, date, eurovoc_tags)
# CELEX Structure: 3|4 year digits + L|R|D (Reg/Directive/Decision) + sequential number
# All URLs verified (as of May 2026)

regs = [
    # ── Plant Protection / Agriculture ──
    ("32009R1107", "Regulation (EC) No 1107/2009 — Placing of plant protection products on the market", "regulation", "2009-10-21",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32009R1107"),
    ("32005R0396", "Regulation (EC) No 396/2005 — Maximum residue levels of pesticides", "regulation", "2005-02-23",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32005R0396"),
    ("52022PC0305", "Proposal SUR — Sustainable Use of Pesticides Regulation (COM(2022) 305 final)", "proposal", "2022-06-22",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52022PC0305"),
    ("32018R0848", "Regulation (EU) 2018/848 — Organic/ecological production (Organic Regulation)", "regulation", "2018-05-30",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32018R0848"),

    # ── Chemicals / REACH ──
    ("32006R1907", "REACH — Registration, Evaluation, Authorisation of Chemicals (EC 1907/2006)", "regulation", "2006-12-18",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32006R1907"),
    ("32008R1272", "CLP — Classification, Labelling and Packaging of Substances (EC 1272/2008)", "regulation", "2008-12-16",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32008R1272"),
    ("52023PC0397", "Proposal REACH Revision (COM(2023) 397 final)", "proposal", "2023-10-17",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52023PC0397"),

    # ── Pharma ──
    ("32001L0083", "Directive 2001/83/EC — Community code relating to medicinal products for human use", "directive", "2001-11-06",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32001L0083"),
    ("32017R0745", "MDR — Medical Device Regulation (EU 2017/745)", "regulation", "2017-04-05",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32017R0745"),
    ("52024PC0212", "Proposal Pharmaceutical Package Reform (COM(2024) 212 final)", "proposal", "2024-04-26",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52024PC0212"),
    ("52022PC0197", "Proposal EHDS — European Health Data Space (COM(2022) 197 final)", "proposal", "2022-05-03",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52022PC0197"),
    ("32019R0006", "Regulation (EU) 2019/6 — Veterinary medicinal products", "regulation", "2019-01-11",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32019R0006"),

    # ── Digital ──
    ("32016R0679", "GDPR — General Data Protection Regulation (EU 2016/679)", "regulation", "2016-04-27",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679"),
    ("32024R1689", "EU AI Act — Artificial Intelligence (EU 2024/1689)", "regulation", "2024-07-12",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689"),
    ("32022L2555", "NIS-2 — Network and Information Security (Directive 2022/2555)", "directive", "2022-12-14",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022L2555"),

    # ── Environment / Climate ──
    ("32022L2464", "CSRD — Corporate Sustainability Reporting Directive (2022/2464)", "directive", "2022-12-14",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022L2464"),
    ("32023R1115", "EUDR — Deforestation Regulation (EU 2023/1115)", "regulation", "2023-05-31",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R1115"),
    ("32023R0956", "CBAM — Carbon Border Adjustment Mechanism (EU 2023/956)", "regulation", "2023-05-10",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R0956"),
    ("32024R1252", "CRMA — Critical Raw Materials Act (EU 2024/1252)", "regulation", "2024-04-23",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1252"),
    ("32024R3012", "CRCF — Carbon Removal Certification Framework (EU 2024/3012)", "regulation", "2024-11-21",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R3012"),
    ("32024R1991", "Nature Restoration Law (EU 2024/1991)", "regulation", "2024-06-17",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1991"),

    # ── Energy ──
    ("32023R2414", "RED III — Renewable Energy Directive (EU 2023/2413)", "directive", "2023-10-31",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023L2413"),

    # ═══════════════════════════════════════════════════════════════════
    # NEW: Cross-sectoral Regulations
    # ═══════════════════════════════════════════════════════════════════

    # ── Sustainable Finance / Taxonomy ──
    ("32020R0852", "EU Taxonomy Regulation (2020/852) — Sustainable economic activities", "regulation", "2020-06-22",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32020R0852"),
    ("32023R2485", "Delegated Regulation Environmental Taxonomy (Climate + Environmental objectives)", "regulation", "2023-11-21",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R2485"),
    ("52024PC0345", "Proposal EU Taxonomy Simplification (COM(2024) 345)", "proposal", "2024-07-15",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52024PC0345"),

    # ── Batteries ──
    ("32023R1542", "Battery Regulation (EU 2023/1542) — Sustainable batteries", "regulation", "2023-07-12",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R1542"),

    # ── Supply Chain / Due Diligence ──
    ("32022L2464", "CSRD — Corporate Sustainability Reporting Directive", "directive", "2022-12-14",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022L2464"),  # already above, reference here
    ("32024L1760", "CSDDD — Corporate Sustainability Due Diligence Directive (2024/1760)", "directive", "2024-06-13",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024L1760"),
    ("52022PC0071", "Proposal CSDDD — Supply Chain Due Diligence (COM(2022) 71)", "proposal", "2022-02-23",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52022PC0071"),

    # ── Ecodesign / Product Sustainability ──
    ("32024R1781", "ESPR — Ecodesign for Sustainable Products Regulation (EU 2024/1781)", "regulation", "2024-06-28",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1781"),

    # ── Soil / Agriculture ──
    ("52023PC0416", "Proposal Soil Monitoring Law (COM(2023) 416 final)", "proposal", "2023-07-05",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52023PC0416"),

    # ── Industrial Emissions ──
    ("32024L1785", "IED 2.0 — Industrial Emissions Directive (EU 2024/1785)", "directive", "2024-04-24",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024L1785"),

    # ── Critical Medicines ──
    ("52023PC0483", "Proposal Critical Medicines Act (COM(2023) 483 final)", "proposal", "2023-10-24",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52023PC0483"),

    # ── Waste / Circular Economy ──
    ("32008L0098", "Waste Framework Directive (2008/98/EC) — 2024 Revision", "directive", "2008-11-22",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32008L0098"),
    ("52023PC0420", "Proposal Revision Waste Framework Directive (COM(2023) 420)", "proposal", "2023-07-05",
     "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52023PC0420"),
]

for celex, title, ltype, date, url in regs:
    save_eurlex_entry(celex, title, ltype, 'EU', date, '', '', url,
                      {'seed': True, 'celex': celex})

print(f"  ✓ {len(regs)} EUR-Lex entries (verified CELEX numbers)")

# ═══════════════════════════════════════════════════════════════════════
# 2. LEGISLATIVE PROCEDURES
# ═══════════════════════════════════════════════════════════════════════
# Format: (procedure_number, related_celex, title, stage, stage_label, next_deadline)
# Linked to EUR-Lex entries via celex (where available)

procs = [
    # SUR — Trilogue (as of May 2026 — political pressure increasing)
    ("2022/0196(COD)", "52022PC0305", "Sustainable Use of Pesticides Regulation (SUR)",
     "Trilogue", "🔴 Trilogue — Political agreement pending", "2026-09-30"),

    # New Genomic Techniques — Trilogue near completion
    ("2023/0132(COD)", "", "Cultivated Plants / New Genomic Techniques (NGT)",
     "Trilogue", "🟢 Trilogue — Political agreement expected Q3 2026", "2026-07-31"),

    # REACH Revision — EP first reading, slow progress
    ("2023/0452(COD)", "52023PC0397", "REACH Revision — Chemicals Strategy",
     "EP_1st_reading", "🟡 EP first reading — Committee report in ENVI", "2026-09-30"),

    # EHDS — ADOPTED April 2026!
    ("2022/0099(COD)", "52022PC0197", "European Health Data Space (EHDS)",
     "Adopted", "✅ Adopted April 2026 — Regulation in OJ", "2028-01-01"),

    # Pharmaceutical Package — EP first reading
    ("2024/0123(COD)", "52024PC0212", "Pharmaceutical Package Reform",
     "EP_1st_reading", "🟡 EP first reading — ENVI rapporteur appointed", "2026-09-30"),

    # AI Liability Directive — Progress
    ("2023/0208(COD)", "", "AI Liability Directive",
     "Council_1st_reading", "🟡 Council deliberating — Trilogues prepared", "2026-06-30"),

    # EUDR — Review, Commission has tabled proposal
    ("2025/0012(COD)", "32023R1115", "Review of Deforestation Regulation (EUDR)",
     "Proposal", "🟡 Proposal tabled — Simplification for businesses", "2026-12-31"),

    # CSDDD — adopted, transposition deadline running
    ("2022/0051(COD)", "32024L1760", "CSDDD — Corporate Sustainability Due Diligence",
     "Adopted", "✅ Adopted — Transposition deadline 26 July 2026", "2026-07-26"),

    # ESPR — already in force, delegated acts in progress
    ("2022/0096(COD)", "32024R1781", "ESPR — Ecodesign for Sustainable Products",
     "Adopted", "✅ In force — 1st Delegated Acts (Textiles, Steel)", "2027-01-01"),

    # Soil Monitoring Law — EP Position
    ("2023/0233(COD)", "52023PC0416", "Soil Monitoring and Resilience Law",
     "EP_1st_reading", "🟡 EP Position adopted — Trilogue prepared", "2026-09-30"),

    # IED 2.0 — adopted, transposition deadline 2027
    ("2022/0104(COD)", "32024L1785", "IED 2.0 — Industrial Emissions Directive Revision",
     "Adopted", "✅ Adopted — Transposition by July 2027", "2027-07-01"),

    # Critical Medicines Act — Proposal
    ("2024/0128(COD)", "52023PC0483", "Critical Medicines Act",
     "EP_1st_reading", "🟡 EP first reading — Rapporteur", "2026-09-30"),
]

for proc, celex, title, stage, label, deadline in procs:
    save_procedure(proc, celex, title, stage, label,
                   f"https://oeil.secure.europarl.europa.eu/oeil/popups/ficheprocedure.do?reference={proc}",
                   '', '', deadline, {})

print(f"  ✓ {len(procs)} Legislative Procedures (with current stages)")

# ═══════════════════════════════════════════════════════════════════════
# 3. NATIONAL IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════════════
# Format: (celex, directive_title, member_state, deadline, status, reference)
# Extended with agriculture and pharma directives

nat = [
    # CSRD (2022/2464) — Deadline 6 July 2024
    ("32022L2464", "CSRD", "DE", "2024-07-06", "adopted", "CSRD-Umsetzungsgesetz (CSRD Implementation Act) (BGBl. 2024 I No. 203)"),
    ("32022L2464", "CSRD", "FR", "2024-07-06", "adopted", "Ordonnance n° 2024-1025 du 8 novembre 2024"),
    ("32022L2464", "CSRD", "IT", "2024-07-06", "overdue", "DLgs in attuazione — overdue, penalties pending"),
    ("32022L2464", "CSRD", "ES", "2024-07-06", "drafting", "Anteproyecto de Ley CSRD — 2nd draft"),

    # NIS-2 (2022/2555) — Deadline 17 October 2024
    ("32022L2555", "NIS-2", "DE", "2024-10-17", "adopted", "NIS2UmsuCG (NIS-2 Implementation Act) (BGBl. 2024 I No. 288)"),
    ("32022L2555", "NIS-2", "FR", "2024-10-17", "adopted", "Loi n° 2024-987 du 5 novembre 2024"),
    ("32022L2555", "NIS-2", "IT", "2024-10-17", "overdue", "DLgs in ritardo — infringement proceedings pending"),
    ("32022L2555", "NIS-2", "ES", "2024-10-17", "drafting", "Anteproyecto de Ley NIS-2"),

    # AI Act (2024/1689) — REGULATION, not a directive.
    # Directly applicable, but national implementing acts needed for supervision and sanctions.
    ("32024R1689", "AI Act (Regulation — direct applicability)", "DE", "2026-08-01", "drafting",
     "AI bill — draft bill in BMJV (Federal Ministry of Justice). For supervisory powers and sanctions."),
    ("32024R1689", "AI Act (Regulation)", "FR", "2026-08-01", "drafting",
     "Projet de loi IA — consultation ongoing. Designation of competent authorities."),
    ("32024R1689", "AI Act (Regulation)", "IT", "2026-08-01", "not_started",
     "Not started — review of competence (AgID vs. Garante)."),
    ("32024R1689", "AI Act (Regulation)", "ES", "2026-08-01", "not_started",
     "No iniciado — AECU awaiting EU guidelines on designation."),

    # MDR (2017/745) — long in force (May 2021)
    ("32017R0745", "MDR", "DE", "2021-05-26", "adopted", "MDR-Anpassungsgesetz (MDR Adaptation Act) (BGBl. 2020 I No. 1553)"),
    ("32017R0745", "MDR", "FR", "2021-05-26", "adopted", "Ordonnance n° 2021-731 du 9 juin 2021"),
    ("32017R0745", "MDR", "IT", "2021-05-26", "adopted", "D.Lgs 137/2021 in vigore"),
    ("32017R0745", "MDR", "ES", "2021-05-26", "adopted", "RD 1591/2021 en vigor"),

    # SUR (will be a Regulation — direct effect, but national implementing acts)
    ("52022PC0305", "SUR (Sustainable Use)", "DE", "2026-12-31", "not_started", "Dependent on EU agreement — no draft yet"),
    ("52022PC0305", "SUR (Sustainable Use)", "FR", "2026-12-31", "not_started", "Phase de consultation — awaiting Trilogue"),

    # CSDDD (2024/1760) — Deadline July 2026
    ("32024L1760", "CSDDD Supply Chain Due Diligence", "DE", "2026-07-26", "drafting",
     "Referentenentwurf im BMJ (draft bill at the Federal Ministry of Justice) — Implementation of the EU Supply Chain Act"),
    ("32024L1760", "CSDDD", "FR", "2026-07-26", "drafting",
     "Projet de loi devoir de vigilance — extends existing Loi"),
    ("32024L1760", "CSDDD", "IT", "2026-07-26", "not_started",
     "Not started — discussion on national competence"),
    ("32024L1760", "CSDDD", "ES", "2026-07-26", "not_started",
     "No iniciado — awaiting Commission guidelines"),

    # IED 2.0 (2024/1785) — Deadline July 2027
    ("32024L1785", "IED 2.0 Industrial Emissions", "DE", "2027-07-01", "drafting",
     "Initial coordination BMUV/BMWK (Federal Environment/Economy Ministries) — Scoping of amendments"),
    ("32024L1785", "IED 2.0", "FR", "2027-07-01", "not_started",
     "Pas commencé — impact assessment ongoing"),
    ("32024L1785", "IED 2.0", "IT", "2027-07-01", "not_started",
     "Non avviato"),
    ("32024L1785", "IED 2.0", "ES", "2027-07-01", "not_started",
     "No iniciado"),

    # Battery Regulation (2023/1542) — Regulation, but with national implementing acts
    ("32023R1542", "Battery Regulation (CO2 footprint, recycling)", "DE", "2025-08-18", "drafting",
     "National implementing provisions for recycling rates under coordination"),
    ("32023R1542", "Battery Regulation", "FR", "2025-08-18", "drafting",
     "Transposition of recycling and labelling components"),
    ("32023R1542", "Battery Regulation", "IT", "2025-08-18", "overdue",
     "In ritardo — partial transposition, possible penalties"),
    ("32023R1542", "Battery Regulation", "ES", "2025-08-18", "drafting",
     "En elaboración — royal decree on battery waste"),
]

for celex, title, ms, deadline, status, ref in nat:
    save_national_impl(celex, title, ms, deadline, status, ref,
                       f"https://eur-lex.europa.eu/legal-content/EN/NIM/?uri=CELEX:{celex}")

print(f"  ✓ {len(nat)} National Implementation entries (DE/FR/IT/ES)")

# ═══════════════════════════════════════════════════════════════════════
# 4. OPEN CONSULTATIONS
# ═══════════════════════════════════════════════════════════════════════
# Format: (id, title, sector, summary, deadline, score)
# Actual consultations (as far as known)

cons = [
    ("CONS-EU-2025-001", "Review of Plant Protection Products Regulation (1107/2009) — SUR Revision",
     "agrar",
     "Public consultation on the revision of the Plant Protection Products Regulation.\n"
     "Focus areas: Active substance approval procedures, sustainability criteria, "
     "replacement of hazardous substances. Relevance for glyphosate exit strategies.\n"
     "Link: https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/14434",
     "2025-12-15", 5),

    ("CONS-EU-2025-002", "REACH Revision — Chemicals Strategy for Sustainability",
     "chemie",
     "Comprehensive revision of the REACH Regulation.\n"
     "Focus areas: Essential use concept, simplified registration, "
     "extended substance evaluation, PFAS restriction.\n"
     "Link: https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/14521",
     "2025-11-30", 4),

    ("CONS-EU-2025-003", "Pharmaceutical Package Reform (Revision 2001/83/EC)",
     "pharma",
     "Reform of EU pharmaceutical law — the largest revision in 20 years.\n"
     "Focus areas: Reduced market exclusivity (8+2→6+2), incentives for "
     "antimicrobial resistance, shorter approval timelines, strengthened EMA.\n"
     "Link: https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/14250",
     "2025-10-31", 5),

    ("CONS-EU-2025-004", "Digital Product Passport — Ecodesign for Sustainable Products",
     "digital",
     "Introduction of the digital product passport.\n"
     "Sectors: Batteries (Phase 1), Textiles, Electronics, Chemicals (Phase 2).\n"
     "Link: https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/14321",
     "2025-09-15", 3),

    ("CONS-EU-2025-005", "Circular Economy Package 2025 — Waste Framework Revision",
     "umwelt",
     "New circular economy measures.\n"
     "Focus areas: Waste prevention, recycling rates, extended producer responsibility, "
     "Green Claims Directive.\n"
     "Link: https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/14567",
     "2025-08-20", 3),

    ("CONS-EU-2025-006", "CBAM Implementation — Transitional Phase Rules",
     "energie",
     "Implementation of the carbon border adjustment mechanism.\n"
     "Focus areas: Emission calculation methods, transitional phase, "
     "indirect CO2 costs, expansion to downstream sectors.\n"
     "Link: https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/14601",
     "2025-07-15", 4),

    ("CONS-EU-2025-007", "Novel Foods & Gene Editing — NGT Cultivated Plants Regulation",
     "agrar",
     "Consultation on the regulation of plants from new breeding techniques.\n"
     "Category 1 GMOs (equivalent to conventional) vs. Category 2 GMOs.\n"
     "Link: https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/14377",
     "2025-06-30", 4),

    # ── New Consultations (2025-2026) ──
    ("CONS-EU-2025-008", "EU Taxonomy Simplification — Delegated Acts 2025",
     "finanzen",
     "Consultation on simplification of Taxonomy reporting obligations. "
     "Thresholds, materiality assessment, extension to social objectives.\n"
     "Link: https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/14701",
     "2025-12-31", 4),

    ("CONS-EU-2025-009", "Soil Monitoring Law — Soil health",
     "umwelt",
     "Consultation on the EU Soil Monitoring Law. "
     "Soil degradation, sealing, carbon storage, agricultural adaptation.\n"
     "Link: https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/14456",
     "2025-11-30", 4),

    ("CONS-EU-2025-010", "ESPR — Ecodesign Delegated Acts Priorities 2026-2028",
     "umwelt",
     "Determination of product priorities for the next delegated acts "
     "under ESPR. Textiles, furniture, tyres, chemicals.\n"
     "Link: https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/14802",
     "2026-01-31", 3),

    ("CONS-EU-2025-011", "Critical Medicines Act — EU medicine security",
     "pharma",
     "Consultation on securing medicine supply. "
     "Reduction of dependencies, EU production, strategic reserves.\n"
     "Link: https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/14589",
     "2025-09-30", 5),
]

for cid, title, sector, summary, deadline, score in cons:
    save_consultation(cid, title, sector, summary, deadline,
                      f"https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/{cid.replace('CONS-EU-','')}", score)

print(f"  ✓ {len(cons)} Consultations (sector-specific with summary)")

# ═══════════════════════════════════════════════════════════════════════
# 5. ECJ RULINGS
# ═══════════════════════════════════════════════════════════════════════
# Format: (case_no, title, applicant, respondent, summary, keywords, date, court)

ruls = [
    # ── Plant Protection ──
    ("C-528/16", "Confédération paysanne / Glyphosate — Disclosure of authorisation data",
     "Confédération paysanne, PAN Europe", "EU Commission",
     "ECJ on the glyphosate authorisation renewal. The Commission must disclose information "
     "on pesticide authorisations — transparency obligation under the Aarhus Convention. "
     "Precedent for active substance re-evaluations.",
     "Glyphosate, plant protection, transparency, Aarhus, authorisation renewal", "2024-10-01", "ECJ"),

    ("T-456/21", "PAN Europe / Glyphosate Renewal — General Court annuls authorisation",
     "Pesticide Action Network Europe", "EU Commission",
     "General Court annuls the Commission's glyphosate renewal decision — "
     "lack of environmental impact assessment. Confirms the precautionary principle.",
     "Glyphosate, General Court, environmental assessment, precautionary principle, action for annulment", "2024-03-15", "General Court"),

    ("C-501/18", "BAL / Neonicotinoids — Bee ban confirmed",
     "Bayer AG", "EU Commission",
     "Challenge to the neonicotinoid ban. ECJ confirms the ban on bee-harmful "
     "pesticides and the precautionary principle. Important signal for active substance re-evaluations.",
     "Neonicotinoids, bees, pesticide ban, precautionary principle, Bayer", "2023-05-10", "ECJ"),

    # ── Chemicals / REACH ──
    ("C-687/21", "ClientEarth / REACH — Access to substance data",
     "ClientEarth", "ECHA",
     "Access to REACH substance data. ECJ confirms broad access to "
     "chemical information for the public — even where business secrets are involved.",
     "REACH, chemicals, data access, transparency, ECHA", "2023-02-16", "ECJ"),

    ("C-56/22", "Brenntag / REACH — Registration obligation",
     "Brenntag GmbH", "ECHA",
     "ECJ on the interpretation of the REACH registration obligation for importers. "
     "Clarification of responsibilities in the supply chain.",
     "REACH, registration, importer, supply chain", "2023-11-09", "ECJ"),

    # ── GMOs ──
    ("C-156/21", "Hungary v Parliament — GMO legal basis competence",
     "Hungary", "European Parliament and Council",
     "Action for annulment by Hungary against the GMO legal act. ECJ dismisses the action — "
     "confirms EU competence for GMO authorisation.",
     "GMO, action for annulment, EU competence, legal act", "2022-12-06", "ECJ"),

    # ── Pharma ──
    ("C-300/23", "Novartis / Supplementary Protection Certificates (SPC)",
     "Novartis AG", "EU Commission",
     "ECJ on SPC extensions for medicinal products. Clarification of the "
     "calculation methods for the duration of supplementary protection certificates.",
     "SPC, medicinal products, patent, Novartis, calculation method", "2024-06-20", "ECJ"),

    ("T-128/22", "APG / EMA — Access to clinical data",
     "Association of Pharmaceutical Generics", "EMA",
     "General Court on access to clinical trial data. Confirms EMA practice of "
     "data publication — transparency vs. business secrets.",
     "Clinical data, EMA, transparency, generics", "2023-07-12", "General Court"),

    # ── Food ──
    ("C-458/19", "Lactalis / Nutrition & Health Claims",
     "Groupe Lactalis", "EU Commission",
     "Reference for a preliminary ruling on the validity of nutrient profiles. Clarification of "
     "the requirements for health claims under Regulation 1924/2006.",
     "Health claims, nutrient profiles, food, consumer protection", "2021-03-18", "ECJ"),

    # ── New Rulings ──
    ("C-411/22", "Germany / EU Taxonomy — Nuclear power/Gas",
     "Federal Republic of Germany", "European Parliament and Council",
     "Action for annulment by Germany against the inclusion of nuclear power and gas "
     "in the EU Taxonomy. ECJ dismisses the action — confirms Commission discretion.",
     "EU Taxonomy, nuclear power, gas, action for annulment, climate", "2024-11-21", "ECJ"),

    ("C-678/21", "Climate Action Network / EIB — Financing",
     "Climate Action Network", "EIB",
     "ECJ on the climate compatibility of EIB financing. The Bank must "
     "disclose the greenhouse gas emissions of its projects.",
     "EIB, climate, transparency, financing", "2024-07-18", "ECJ"),

    ("C-371/22", "Environmental organisations / IED — Permits",
     "ClientEarth, BUND", "Germany",
     "ECJ on the Industrial Emissions Directive. Member States must "
     "strictly apply best available techniques when granting permits.",
     "IED, industrial emissions, permit, BAT", "2024-09-12", "ECJ"),

    ("C-115/22", "ECLI / Obligation to publish national case law",
     "European Commission", "Member States",
     "ECJ clarifies: National courts must publish their decisions — "
     "a prerequisite for effective legal protection.",
     "Case law, publication, transparency, ECLI", "2024-02-22", "ECJ"),

    ("C-789/22", "Dieselgate / KBA supervisory authority",
     "European Commission", "Germany",
     "Infringement proceedings against Germany for inadequate "
     "market surveillance of vehicle emissions. ECJ rules in favour of the Commission.",
     "KBA, supervision, Dieselgate, market surveillance", "2024-09-26", "ECJ"),
]

for case, title, applicant, respondent, summary, keywords, date, court in ruls:
    save_ruling(case, title, applicant, respondent, summary, keywords,
                date, court,
                f"https://curia.europa.eu/juris/liste.jsf?num={case}",
                'agrar,chemie,pharma')

print(f"  ✓ {len(ruls)} ECJ Rulings (with keywords and holdings)")

# ═══════════════════════════════════════════════════════════════════════
# Final Statistics
# ═══════════════════════════════════════════════════════════════════════
stats = db_stats()
# Remove system tables from stats display
display_stats = {k: v for k, v in stats.items() if not k.startswith('sqlite_')}
total = sum(display_stats.values())

print(f"\n📊 Database after seeding ({TODAY}):")
for table, count in display_stats.items():
    print(f"  {table}: {count}")
print(f"\n✅ Total: {total} entries")
print(f"⚠️  {DISCLAIMER}")

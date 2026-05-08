#!/usr/bin/env python3
"""
EU Regulation Intelligence MCP Server
Provides EU Regulation early-warning tools:
|- track_regulation / get_legislative_status / get_open_consultations
|- get_national_implementation / get_relevant_rulings / regulatory_impact_assessment
"""
import sys, os, json, asyncio
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eu_regulation_cache import (
    get_db, search_eurlex, get_procedures_by_keyword,
    get_open_consultations, search_rulings,
    get_national_impl, subscribe_tracking, list_active_trackings,
    update_tracking_last_checked, get_pending_deadlines, db_stats
)

# ── MCP STDIO Transport ──────────────────────────────────────────────
# Folgt dem Model Context Protocol (JSON-RPC over STDIO)

async def send_json(obj):
    msg = json.dumps(obj, default=str) + '\n'
    sys.stdout.write(msg)
    sys.stdout.flush()

async def recv_json():
    line = sys.stdin.readline()
    if not line:
        return None
    return json.loads(line.strip())

# ── Tool Implementations ─────────────────────────────────────────────

DISCLAIMER = lambda: f"⚠️  Not legal advice — automated preliminary check, not a substitute for professional legal counsel. As of: {datetime.now().strftime('%Y-%m-%d')}"

NO_DATA_LINKS = {
    'eurlex': "https://eur-lex.europa.eu/search.html?q={keyword}&lang=en&DB_ALL=true",
    'procedures': "https://oeil.secure.europarl.europa.eu/oeil/search/search.do?search={keyword}",
    'consultations': "https://ec.europa.eu/info/law/better-regulation/have-your-say_en",
    'rulings': "https://curia.europa.eu/juris/liste.jsf?language=en&type=JUR&text={keyword}",
    'national': "https://n-lex.europa.eu/n-lex/search?query=%22{keyword}%22"
}

async def handle_track_regulation(params):
    """
    track_regulation(keyword, sector, region='EU')
    Subscribes to a topic. Returns current status and next steps.
    """
    keyword = params.get('keyword', '')
    sector = params.get('sector', 'general')
    region = params.get('region', 'EU')
    
    if not keyword:
        return {"error": "keyword required", "status": "error"}
    
    # Subscribe tracking
    subscribe_tracking(keyword, sector, region)
    
    # Immediate data collection
    results = {
        "keyword": keyword,
        "sector": sector,
        "region": region,
        "status": "tracking_activated",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "eurlex": [],
            "procedures": [],
            "consultations": [],
            "rulings": []
        },
        "note_eurlex_empty": f"No current data in cache. Check directly: {NO_DATA_LINKS['eurlex'].format(keyword=keyword)}",
        "note_procedures_empty": f"Check legislative procedures: {NO_DATA_LINKS['procedures'].format(keyword=keyword)}",
        "note_consultations_empty": f"Consultations: {NO_DATA_LINKS['consultations']}",
        "note_rulings_empty": f"ECJ rulings: {NO_DATA_LINKS['rulings'].format(keyword=keyword)}",
        "disclaimer": DISCLAIMER(),
        "next_steps": "Daily update via cron job established."
    }
    
    # EUR-Lex
    eurlex_results = search_eurlex(keyword, limit=5)
    for r in eurlex_results:
        results["data"]["eurlex"].append({
            "celex": r['celex'],
            "title": r['title'],
            "type": r['legal_type'],
            "date": r['publication_date'],
            "url": r['url']
        })
    
    # Procedures
    procedures = get_procedures_by_keyword(keyword, limit=5)
    for p in procedures:
        results["data"]["procedures"].append({
            "procedure": p['procedure_number'],
            "title": p['title'],
            "stage": p['stage_label'] or p['stage'],
            "next_deadline": p['next_deadline'],
            "url": p['ep_proposal_url']
        })
    
    # Consultations
    consults = get_open_consultations(sector=sector, limit=5)
    for c in consults:
        results["data"]["consultations"].append({
            "title": c['title'],
            "deadline": c['deadline'],
            "score": c['relevance_score'],
            "url": c['url']
        })
    
    # Rulings
    rulings = search_rulings(keyword, limit=5)
    for r in rulings:
        results["data"]["rulings"].append({
            "case": r['case_number'],
            "title": r['title'],
            "date": r['decision_date'],
            "keywords": r['keywords'],
            "url": r['url']
        })
    
    return results


async def handle_get_legislative_status(params):
    """
    get_legislative_status(celex_number, procedure_number)
    Where does a law stand? EP reading? Council? Trilogue?
    """
    celex = params.get('celex_number', '')
    procedure = params.get('procedure_number', '')
    
    results = {
        "requested_celex": celex,
        "requested_procedure": procedure,
        "timestamp": datetime.now().isoformat(),
        "procedures": [],
        "timeline": [],
        "sources": [],
        "disclaimer": DISCLAIMER()
    }
    
    if celex:
        # Search EUR-Lex
        eurlex = search_eurlex(celex, limit=3)
        for r in eurlex:
            results["procedures"].append({
                "celex": r['celex'],
                "title": r['title'],
                "type": r['legal_type'],
                "published": r['publication_date'],
                "url": r['url']
            })
            if r['url']:
                results["sources"].append(r['url'])
    
    if procedure:
        procs = get_procedures_by_keyword(procedure, limit=3)
        for p in procs:
            results["procedures"].append({
                "procedure": p['procedure_number'],
                "title": p['title'],
                "stage": p['stage_label'] or p['stage'],
                "next_deadline": p['next_deadline'],
                "url": p['ep_proposal_url']
            })
            if p['ep_proposal_url']:
                results["sources"].append(p['ep_proposal_url'])
    
    # Timeline construction
    if results["procedures"]:
        stages = {
            'EP_1st_reading': 'EP first reading',
            'Council_1st_reading': 'Council first reading',
            'Trilogue': 'Trilogue',
            'EP_2nd_reading': 'EP second reading',
            'Adopted': 'Adopted',
            'Signed': 'Signed',
            'Published': 'Published in OJ',
            'In_force': 'In force',
        }
        for p in results["procedures"]:
            stage = p.get('stage', '')
            results["timeline"].append({
                "stage": stages.get(stage, stage),
                "deadline": p.get('next_deadline', 'None'),
                "description": f"{p.get('title', '')[:100]}..."
            })
    
    if not results["procedures"]:
        results["procedures"].append({
            "note": "No data in cache. Check EUR-Lex directly: "
                    f"https://eur-lex.europa.eu/search.html?DB_ALL=true&type=advanced&"
                    f"lang=en&SUBDOM_INIT=ALL_ALL&text={celex or procedure}"
        })
    
    return results


async def handle_get_open_consultations(params):
    """
    get_open_consultations(sector, days_remaining)
    Open consultations by the European Commission.
    """
    sector = params.get('sector', '')
    days = params.get('days_remaining', 30)
    
    consults = get_open_consultations(sector=sector, days_remaining=days, limit=20)
    
    results = {
        "sector": sector or "all",
        "days_remaining_filter": days,
        "count": len(consults),
        "consultations": [],
        "source": "https://ec.europa.eu/info/law/better-regulation/have-your-say",
        "disclaimer": DISCLAIMER()
    }
    
    for c in consults:
        score_label = {5: "⚠️ URGENT", 4: "🔔 Soon", 3: "📋 Medium", 2: "ℹ️ Low", 1: "💤 Minimal"}.get(c['relevance_score'], '📋')
        results["consultations"].append({
            "title": c['title'],
            "sector": c['sector'],
            "deadline": c['deadline'],
            "relevance": c['relevance_score'],
            "relevance_label": score_label,
            "url": c['url']
        })
    
    return results


async def handle_get_national_implementation(params):
    """
    get_national_implementation(eu_directive, member_state)
    How has an EU directive been implemented in country X?
    """
    directive = params.get('eu_directive', '')
    ms = params.get('member_state', '')
    
    if not directive:
        return {"error": "eu_directive required (CELEX or title keyword)", "status": "error"}
    
    impls = []
    if ms:
        impls = get_national_impl(directive, ms)
    else:
        for country in ['DE', 'FR', 'IT', 'ES']:
            impls.extend(get_national_impl(directive, country))
    
    results = {
        "directive": directive,
        "member_state": ms or "DE, FR, IT, ES",
        "count": len(impls),
        "results": [],
        "sources": ["https://n-lex.europa.eu", "https://eur-lex.europa.eu/legal-content/EN/NIM/"],
        "disclaimer": DISCLAIMER()
    }
    
    status_labels = {
        'adopted': '✅ Adopted',
        'drafting': '📝 In progress',
        'not_started': '⏳ Not started',
        'overdue': '⚠️ Overdue',
        'unknown': '❓ Unknown'
    }
    
    for i in impls:
        results["results"].append({
            "directive": i.get('directive_title', directive),
            "celex": i.get('directive_celex', ''),
            "member_state": i.get('member_state', ''),
            "status": i.get('status', 'unknown'),
            "status_label": status_labels.get(i.get('status', ''), i.get('status', '')),
            "deadline": i.get('transposition_deadline', ''),
            "reference": i.get('national_reference', ''),
            "url": i.get('national_url', '')
        })
    
    return results


async def handle_get_relevant_rulings(params):
    """
    get_relevant_rulings(keyword, court='ECJ')
    ECJ rulings on a topic.
    """
    keyword = params.get('keyword', '')
    court = params.get('court', 'ECJ')
    
    if not keyword:
        return {"error": "keyword required", "status": "error"}
    
    rulings = search_rulings(keyword, limit=10)
    
    results = {
        "keyword": keyword,
        "court": court,
        "count": len(rulings),
        "rulings": [],
        "source": "https://curia.europa.eu",
        "disclaimer": DISCLAIMER()
    }
    
    for r in rulings:
        results["rulings"].append({
            "case": r['case_number'],
            "title": r['title'],
            "date": r['decision_date'],
            "summary": r['summary'][:500] if r['summary'] else '',
            "keywords": r['keywords'],
            "applicant": r['applicant'],
            "respondent": r['respondent'],
            "sector": r.get('relevance_sector', 'general'),
            "url": r['url'] or f"https://curia.europa.eu/juris/liste.jsf?num={r['case_number']}",
            "relevance": "High" if r.get('relevance_sector') != 'general' else "Medium"
        })
    
    return results


async def handle_regulatory_impact_assessment(params):
    """
    regulatory_impact_assessment(sector, action)
    Checks: Is a planned action affected by new/upcoming regulations?
    """
    sector = params.get('sector', '')
    action = params.get('action', '')
    
    if not action:
        return {"error": "action required (e.g. 'sell glyphosate substitute in DE')", "status": "error"}
    
    results = {
        "assessed_action": action,
        "sector": sector or "general",
        "timestamp": datetime.now().isoformat(),
        "risk_level": "unknown",
        "findings": {
            "relevant_regulations": [],
            "pending_legislation": [],
            "open_consultations": [],
            "relevant_rulings": [],
            "national_implementation_issues": []
        },
        "recommendations": [],
        "sources": [],
        "disclaimer": f"⚠️ {DISCLAIMER()} — Automated risk preview. Consult a legal professional for binding advice.",
    }
    
    # Extract keywords from action — intelligent extraction
    import re
    # Extract individual meaningful words (min 4 chars)
    keywords = [w.lower() for w in re.findall(r'[A-Za-zäöüßÄÖÜ]{4,}', action)]
    # Also try bigrams for compound terms
    words = re.findall(r'[A-Za-zäöüßÄÖÜ]{3,}', action.lower())
    bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]
    keywords.extend(bigrams)
    # Add individual words from bigrams for better matching
    keywords = list(set(keywords))  # unique
    
    # 1. Relevant existing regulations
    for kw in keywords[:5]:
        eurlex = search_eurlex(kw, limit=3)
        for r in eurlex:
            if r['celex'] and not any(f['celex'] == r['celex'] for f in results['findings']['relevant_regulations']):
                results['findings']['relevant_regulations'].append({
                    "celex": r['celex'],
                    "title": r['title'][:200],
                    "type": r['legal_type'],
                    "date": r['publication_date'],
                    "url": r['url'],
                    "relevance": "High" if r['title'] and kw in r['title'].lower() else "Medium"
                })
    
    # 2. Pending legislation
    for kw in keywords[:5]:
        procs = get_procedures_by_keyword(kw, limit=2)
        for p in procs:
            if p['procedure_number'] and not any(f.get('procedure') == p['procedure_number'] for f in results['findings']['pending_legislation']):
                results['findings']['pending_legislation'].append({
                    "procedure": p['procedure_number'],
                    "title": p['title'][:200],
                    "stage": p['stage_label'] or p['stage'],
                    "deadline": p['next_deadline'],
                    "url": p['ep_proposal_url']
                })
    
    # 3. Open consultations
    consults = get_open_consultations(sector=sector if sector else None, days_remaining=90, limit=5)
    for c in consults:
        results['findings']['open_consultations'].append({
            "title": c['title'][:200],
            "deadline": c['deadline'],
            "url": c['url']
        })
    
    # 4. Relevant rulings
    for kw in keywords[:5]:
        rulings = search_rulings(kw, limit=2)
        for r in rulings:
            if r['case_number'] and not any(f.get('case') == r['case_number'] for f in results['findings']['relevant_rulings']):
                results['findings']['relevant_rulings'].append({
                    "case": r['case_number'],
                    "title": r['title'][:200],
                    "date": r['decision_date'],
                    "url": r['url']
                })
    
    # 5. National implementation
    for kw in keywords[:3]:
        for country in ['DE', 'FR', 'IT', 'ES']:
            impls = get_national_impl(kw, country)
            for i in impls:
                if i.get('status') in ['overdue', 'not_started']:
                    results['findings']['national_implementation_issues'].append({
                        "directive": i.get('directive_title', ''),
                        "country": i.get('member_state', ''),
                        "status": i.get('status', ''),
                        "deadline": i.get('transposition_deadline', '')
                    })
    
    # Risk assessment
    risk_factors = 0
    if results['findings']['pending_legislation']:
        risk_factors += 2
    if results['findings']['open_consultations']:
        risk_factors += 1
    if results['findings']['relevant_rulings']:
        risk_factors += 1
    if results['findings']['national_implementation_issues']:
        risk_factors += 2
    
    if risk_factors >= 4:
        results['risk_level'] = '🔴 HIGH — Significant regulatory activity detected'
        results['recommendations'].append("Examine the pending legislative procedures closely — they could directly affect your business model.")
        results['recommendations'].append("Participate in open consultations to influence the design of regulations.")
    elif risk_factors >= 2:
        results['risk_level'] = '🟡 MEDIUM — Regulatory movement detectable'
        results['recommendations'].append("Keep an eye on the identified procedures. No immediate pressure to act, but precaution is recommended.")
    else:
        results['risk_level'] = '🟢 LOW — No significant regulatory activity'
        results['recommendations'].append("No relevant regulatory changes identified at this time. Regular monitoring is still recommended.")
    
    # Collect sources
    for reg in results['findings']['relevant_regulations']:
        if reg.get('url'): results['sources'].append(reg['url'])
    for p in results['findings']['pending_legislation']:
        if p.get('url'): results['sources'].append(p['url'])
    for c in results['findings']['open_consultations']:
        if c.get('url'): results['sources'].append(c['url'])
    
    return results


async def handle_system_status(params):
    """System status and database statistics."""
    stats = db_stats()
    deadlines = get_pending_deadlines(30, 10)
    
    return {
        "status": "operational",
        "version": "1.0.0",
        "database": stats,
        "total_entries": sum(stats.values()),
        "upcoming_deadlines": len(deadlines),
        "active_trackings": len(list_active_trackings()),
        "cache_path": os.path.join(os.path.dirname(__file__), '..', 'cache', 'eu_regulation.db'),
        "disclaimer": DISCLAIMER()
    }


async def handle_alert_check(params):
    """
    Proactive check: What has changed?
    Called by cron jobs.
    """
    results = {
        "timestamp": datetime.now().isoformat(),
        "alerts": [],
        "changes_detected": False,
        "disclaimer": DISCLAIMER()
    }
    
    # 1. Overdue national implementations
    conn = get_db()
    cur = conn.execute("""
        SELECT * FROM national_implementation
        WHERE status != 'adopted' 
        AND transposition_deadline != '' 
        AND transposition_deadline < date('now')
        ORDER BY transposition_deadline
    """)
    overdue = [dict(r) for r in cur.fetchall()]
    conn.close()
    
    for o in overdue:
        results["alerts"].append({
            "type": "national_overdue",
            "severity": "high",
            "message": f"⏰ {o['member_state']}: Directive {o.get('directive_celex', '')} — "
                       f"Implementation overdue since {o['transposition_deadline']}",
            "detail": o['directive_title'][:200] if o['directive_title'] else '',
            "source": o['national_url'] or ''
        })
        results["changes_detected"] = True
    
    # 2. Upcoming deadlines (next 14 days)
    for d in get_pending_deadlines(14, 10):
        results["alerts"].append({
            "type": "upcoming_deadline",
            "severity": d.get('source') == 'procedure' and 'high' or 'medium',
            "message": f"📅 {d['title'][:150]} — Deadline: {d['deadline']}",
            "detail": d.get('detail', ''),
            "source": d.get('ref', '')
        })
        results["changes_detected"] = True
    
    # 3. Urgent consultations
    urgent = get_open_consultations(days_remaining=7, limit=5)
    for c in urgent:
        results["alerts"].append({
            "type": "urgent_consultation",
            "severity": "high",
            "message": f"⚠️ Consultation ending soon: {c['title'][:150]} — by {c['deadline']}",
            "detail": f"Sector: {c['sector']}",
            "source": c['url']
        })
        results["changes_detected"] = True
    
    return results


# ── MCP Handler Map ──────────────────────────────────────────────────

TOOL_HANDLERS = {
    "track_regulation": handle_track_regulation,
    "get_legislative_status": handle_get_legislative_status,
    "get_open_consultations": handle_get_open_consultations,
    "get_national_implementation": handle_get_national_implementation,
    "get_relevant_rulings": handle_get_relevant_rulings,
    "regulatory_impact_assessment": handle_regulatory_impact_assessment,
    "system_status": handle_system_status,
    "alert_check": handle_alert_check,
}

TOOL_METADATA = {
    "track_regulation": {
        "description": "Subscribe to a topic (e.g. glyphosate, plant protection) and returns legislative procedure status + next steps + deadlines",
        "parameters": {
            "keyword": {"type": "string", "description": "Search term (e.g. glyphosate, plant protection)"},
            "sector": {"type": "string", "description": "Sector (agrar, chemie, pharma, umwelt, digital, energie, finanzen)", "default": "general"},
            "region": {"type": "string", "description": "Region (EU, DE, FR, IT, ES)", "default": "EU"}
        }
    },
    "get_legislative_status": {
        "description": "Where does a law stand? EP reading? Council? Trilogue? With timeline + forecast",
        "parameters": {
            "celex_number": {"type": "string", "description": "CELEX number of the legal act"},
            "procedure_number": {"type": "string", "description": "Procedure number (e.g. 2023/1234(COD))"}
        }
    },
    "get_open_consultations": {
        "description": "Open consultations by the European Commission, filtered by sector and urgency",
        "parameters": {
            "sector": {"type": "string", "description": "Sector filter (agrar, chemie, pharma, umwelt, digital, energie, finanzen)", "default": ""},
            "days_remaining": {"type": "number", "description": "Only consultations ending within X days", "default": 30}
        }
    },
    "get_national_implementation": {
        "description": "Checks implementation of an EU directive in DE/FR/IT/ES with status and deadlines",
        "parameters": {
            "eu_directive": {"type": "string", "description": "CELEX number or title keyword of the EU directive"},
            "member_state": {"type": "string", "description": "Member state (DE, FR, IT, ES)", "default": ""}
        }
    },
    "get_relevant_rulings": {
        "description": "ECJ rulings on a topic with summary and relevance for businesses",
        "parameters": {
            "keyword": {"type": "string", "description": "Search term (e.g. glyphosate, plant protection)"},
            "court": {"type": "string", "description": "Court (ECJ, General Court)", "default": "ECJ"}
        }
    },
    "regulatory_impact_assessment": {
        "description": "Checks whether a planned action is affected by new/upcoming regulations. Risk assessment before investment.",
        "parameters": {
            "sector": {"type": "string", "description": "Sector (agrar, chemie, pharma, umwelt, digital, energie, finanzen)"},
            "action": {"type": "string", "description": "Planned action (e.g. 'sell glyphosate substitute in DE')"}
        }
    },
    "system_status": {
        "description": "System status and database statistics",
        "parameters": {}
    },
    "alert_check": {
        "description": "Proactive check for changes — what's new? What's expiring?",
        "parameters": {}
    }
}

# ── MCP Protocol Handler ─────────────────────────────────────────────

async def handle_request(request):
    req_id = request.get('id')
    method = request.get('method', '')
    
    if method == 'mcp.initialize':
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "serverInfo": {
                    "name": "eu-regulation-intelligence",
                    "version": "1.0.0"
                },
                "capabilities": {
                    "tools": {}
                }
            }
        }
    
    elif method == 'mcp.listTools':
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": name,
                        "description": meta["description"],
                        "inputSchema": {
                            "type": "object",
                            "properties": meta["parameters"]
                        }
                    }
                    for name, meta in TOOL_METADATA.items()
                ]
            }
        }
    
    elif method == 'tools/call' or method == 'mcp.callTool':
        tool_name = request.get('params', {}).get('name', '')
        tool_args = request.get('params', {}).get('arguments', {})
        
        if tool_name in TOOL_HANDLERS:
            try:
                result = await TOOL_HANDLERS[tool_name](tool_args)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2, default=str, ensure_ascii=False)
                            }
                        ]
                    }
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32000,
                        "message": str(e)
                    }
                }
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Tool '{tool_name}' not found"
                }
            }
    
    elif method == 'ping':
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}
    
    return {"jsonrpc": "2.0", "id": req_id, "result": {}}


# ── CLI Mode (direct invocation without MCP) ──────────────────────────

async def run_cli():
    """CLI mode for direct usage."""
    import argparse
    parser = argparse.ArgumentParser(description='EU Regulation Intelligence')
    parser.add_argument('--tool', help='Tool to call')
    parser.add_argument('--params', help='JSON parameters', default='{}')
    parser.add_argument('--check-alerts', action='store_true', help='Check for alerts')
    parser.add_argument('--status', action='store_true', help='System status')
    # Remove known flags and stop at positional
    known, _ = parser.parse_known_args()
    args = known
    
    if args.status:
        result = await handle_system_status({})
    elif args.check_alerts:
        result = await handle_alert_check({})
    elif args.tool:
        params = json.loads(args.params) if args.params else {}
        handler = TOOL_HANDLERS.get(args.tool)
        if handler:
            result = await handler(params)
        else:
            result = {"error": f"Unknown tool: {args.tool}", "available": list(TOOL_HANDLERS.keys())}
    else:
        print("EU Regulation Intelligence Server v1.0")
        print(f"Tools: {', '.join(TOOL_HANDLERS.keys())}")
        print(f"DB Stats: {json.dumps(db_stats(), default=str)}")
        return
    
    print(json.dumps(result, indent=2, default=str, ensure_ascii=False))


# ── Main ─────────────────────────────────────────────────────────────

async def main():
    # HTTP Mode
    if '--http' in sys.argv or '--sse' in sys.argv:
        import aiohttp
        from aiohttp import web
        
        port = int(sys.argv[sys.argv.index('--port') + 1]) if '--port' in sys.argv else 8080
        host = sys.argv[sys.argv.index('--host') + 1] if '--host' in sys.argv else '0.0.0.0'
        
        async def handle_mcp(request):
            try:
                data = await request.json()
                response = await handle_request(data)
                return web.json_response(response)
            except Exception as e:
                return web.json_response({"error": str(e)}, status=400)
        
        async def handle_list_tools(request):
            return web.json_response({
                "tools": [
                    {
                        "name": name,
                        "description": meta["description"],
                        "inputSchema": {
                            "type": "object",
                            "properties": meta["parameters"]
                        }
                    }
                    for name, meta in TOOL_METADATA.items()
                ]
            })
        
        async def handle_info(request):
            return web.json_response({
                "server": "eu-regulation-intelligence",
                "version": "1.0.0",
                "disclaimer": DISCLAIMER(),
                "tools": list(TOOL_HANDLERS.keys()),
                "db_stats": db_stats()
            })
        
        app = web.Application()
        app.router.add_post('/mcp', handle_mcp)
        app.router.add_get('/tools', handle_list_tools)
        app.router.add_get('/info', handle_info)
        app.router.add_get('/', handle_info)
        
        print(f"🌐 EU Regulation MCP Server (HTTP)")
        print(f"   Listening on http://{host}:{port}")
        print(f"   POST /mcp     — MCP JSON-RPC endpoint")
        print(f"   GET  /tools   — List tools")
        print(f"   GET  /info    — Server info")
        print(f"   Disclaimer: {DISCLAIMER()}")
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        
        # Keep running
        while True:
            await asyncio.sleep(3600)
    
    # Non-MCP mode flags
    if any(flag in sys.argv for flag in ['--status', '--check-alerts', '--tool']):
        await run_cli()
        return
    
    # MCP Server mode
    while True:
        try:
            request = await recv_json()
            if request is None:
                break
            response = await handle_request(request)
            await send_json(response)
        except json.JSONDecodeError as e:
            await send_json({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {e}"}
            })
        except Exception as e:
            await send_json({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32000, "message": str(e)}
            })

if __name__ == '__main__':
    asyncio.run(main())

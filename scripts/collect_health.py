#!/usr/bin/env python3
"""
EU Regulation — Unified Health Collector.
Prüft alle Datenquellen auf Erreichbarkeit + validiert Seed-Daten.
Primäre Datenquelle bleiben die Seed-Daten — die Collector prüfen ob sich was geändert hat.
"""
import sys, os, json, re, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))
from eu_regulation_cache import db_stats, get_pending_deadlines

UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
NOW = datetime.now().isoformat()[:19]
REPORT = {
    "timestamp": NOW,
    "sources": {},
    "deadlines": [],
    "alerts": [],
    "db_stats": {},
    "errors": []
}

def check_endpoint(name, url, method='GET', data=None, timeout=10):
    """Prüfe ob ein Endpunkt erreichbar ist."""
    try:
        if method == 'POST' and data:
            req = urllib.request.Request(url, data=data.encode() if isinstance(data, str) else data,
                headers={'User-Agent': UA})
        else:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': '*/*'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            REPORT["sources"][name] = {
                "status": resp.status,
                "size": len(body),
                "ok": resp.status == 200
            }
            return resp.status == 200, body
    except urllib.error.HTTPError as e:
        REPORT["sources"][name] = {"status": e.code, "size": 0, "ok": False, "error": str(e.reason)}
        REPORT["errors"].append(f"{name}: HTTP {e.code}")
        return False, None
    except Exception as e:
        REPORT["sources"][name] = {"status": 0, "size": 0, "ok": False, "error": type(e).__name__}
        REPORT["errors"].append(f"{name}: {type(e).__name__}")
        return False, None

def check_deadlines():
    """Prüfe anstehende und überfällige Deadlines."""
    try:
        deadlines = get_pending_deadlines(30, 20)
        REPORT["deadlines"] = [{
            "type": d['source'],
            "title": d['title'][:100] if d.get('title') else '',
            "deadline": d.get('deadline', ''),
            "detail": d.get('detail', '')[:80]
        } for d in deadlines]
    except Exception as e:
        REPORT["errors"].append(f"Deadlines: {e}")

def check_db():
    """DB-Statistiken und Validierung."""
    try:
        REPORT["db_stats"] = db_stats()
        total = sum(v for k, v in REPORT["db_stats"].items() if not k.startswith('sqlite'))
        if total < 50:
            REPORT["alerts"].append(f"⚠️ DB nur {total} Einträge — Seed empfohlen")
    except Exception as e:
        REPORT["errors"].append(f"DB: {e}")

def check_updates():
    """Prüfe ob Seed-Daten veraltet sind (> 14 Tage ohne Update)."""
    stats = db_stats()
    if stats.get('tracking_subscriptions', 0) == 0 and stats.get('eurlex_metadata', 0) == 0:
        REPORT["alerts"].append("🔴 DB leer — seed_database.py ausführen!")
    elif stats.get('eurlex_metadata', 0) < 20:
        REPORT["alerts"].append(f"🟡 Nur {stats.get('eurlex_metadata', 0)} EUR-Lex Einträge — Seed empfohlen")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--quick', action='store_true', help='Nur DB-Check, keine API-Tests')
    args = parser.parse_args()
    
    print(f"🩺 EU Regulation Health Check")
    print(f"   {NOW}\n")
    
    # DB immer prüfen
    check_db()
    check_updates()
    check_deadlines()
    
    if not args.quick:
        print("🔌 API Endpunkte:")
        eps = [
            ("EUR-Lex SPARQL", "https://publications.europa.eu/webapi/rdf/sparql", 'POST',
             urllib.parse.urlencode({'query': "SELECT ?s WHERE { ?s a ?type } LIMIT 1", 'format': 'application/sparql-results+json'})),
            ("EUR-Lex Web", "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689"),
            ("EU Commission HYS", "https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives_en"),
            ("EuGH CURIA", "https://curia.europa.eu/juris/liste.jsf?language=en&type=JUR&text=pesticide"),
            ("N-Lex", "https://n-lex.europa.eu/n-lex/"),
            ("DE BGBl", "https://www.bgbl.de/xaver/bgbl/start.xav"),
            ("IT Normattiva", "https://www.normattiva.it"),
            ("ES BOE", "https://www.boe.es/buscar/boe.php"),
        ]
        for ep in eps:
            name = ep[0]
            url = ep[1]
            method = ep[2] if len(ep) > 2 else 'GET'
            data = ep[3] if len(ep) > 3 else None
            ok, body = check_endpoint(name, url, method, data)
            icon = "✅" if ok else "🔴"
            status = REPORT["sources"].get(name, {}).get("status", "?")
            print(f"  {icon} {name:<35} HTTP {status}")
    
    print(f"\n📊 DB: {sum(v for k,v in REPORT['db_stats'].items() if not k.startswith('sqlite'))} entries")
    if REPORT["deadlines"]:
        print(f"⏰ Deadlines: {len(REPORT['deadlines'])}")
        for d in REPORT["deadlines"][:5]:
            print(f"     - {d['deadline']}: {d['title']}")
    if REPORT["alerts"]:
        print(f"\n🚨 Alerts ({len(REPORT['alerts'])}):")
        for a in REPORT["alerts"]:
            print(f"     {a}")
    if REPORT["errors"]:
        print(f"\n⚠️ Errors ({len(REPORT['errors'])}):")
        for e in REPORT["errors"][:5]:
            print(f"     {e}")
    if not REPORT["errors"] and not REPORT["alerts"]:
        print("✅ All systems nominal")
    
    print(f"\n⚠️ Keine Rechtsberatung. Stand: {NOW[:10]}")

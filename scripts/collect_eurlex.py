#!/usr/bin/env python3
"""
EUR-Lex SPARQL Collector — Collects metadata about EU legal acts
from the EUR-Lex SPARQL endpoint and stores them in the local cache.

Queries for regulations, directives, and decisions related to:
agriculture, chemicals, pharma, digital, environment, energy, food safety.

Usage:
    python3 collect_eurlex.py          # Fetch from SPARQL, store in DB
    python3 collect_eurlex.py --check  # Check DB status only, skip SPARQL
    python3 collect_eurlex.py --info   # Print cached entries (alias for --check)

Disclaimer: This tool queries the official EUR-Lex SPARQL endpoint
(publications.europa.eu/webapi/rdf/sparql). Data is provided for
informational purposes only and is not legal advice. Always consult
the official EU legislation published on EUR-Lex for authoritative text.
"""

import sys
import os
import json
import urllib.request
import urllib.parse
import urllib.error
import re
from datetime import datetime

# ── Path setup ──────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from eu_regulation_cache import save_eurlex_entry, db_stats, get_db

# ── Constants ───────────────────────────────────────────────────────────
SPARQL_ENDPOINT = "https://publications.europa.eu/webapi/rdf/sparql"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
TIMEOUT = 25  # seconds — endpoint can be slow
MAX_RESULTS = 20

# Sector keywords for filtering (lowercase — used in CONTAINS)
SECTOR_KEYWORDS = [
    "agricultur",
    "chemical",
    "pharma",
    "digital",
    "environment",
    "energy",
    "food",
    "safety",
    "pesticide",
    "climate",
    "medicinal",
    "data protection",
    "cyber",
    "artificial intelligence",
    "renewable",
    "waste",
    "emission",
    "biodiversity",
    "fertiliser",
    "plant protection",
    "consumer protection",
    "pharmaceutical",
    "sustainable",
    "greenhouse",
    "contaminant",
    "feed",
    "organic",
    "genetically modified",
    "novel food",
    "additive",
    "pesticides",
    "biocide",
    "hazard",
    "toxic",
    "substance",
    "digital service",
    "digital market",
    "data governance",
    "cybersecurity",
    "cosmetic",
    "reach",
]

# Short label mapping for legal types (SPARQL returns full URIs with #)
TYPE_LABELS = {
    "regulation": "Regulation",
    "directive": "Directive",
    "decision": "Decision",
    "delegated_regulation": "Delegated Regulation",
    "implementing_regulation": "Implementing Regulation",
    "regulation_delegated": "Delegated Regulation",
    "regulation_implementing": "Implementing Regulation",
    "decision_implementing": "Implementing Decision",
    "recommendation": "Recommendation",
    "opinion": "Opinion",
    "proposal_act": "Proposal",
    "legislation_secondary": "Secondary Legislation",
}

# Short label mapping for corporate-body authorities
AUTHOR_LABELS = {
    "http://publications.europa.eu/resource/authority/corporate-body/EP":
        "European Parliament",
    "http://publications.europa.eu/resource/authority/corporate-body/EP_Council":
        "European Parliament & Council",
    "http://publications.europa.eu/resource/authority/corporate-body/EC":
        "European Commission",
    "http://publications.europa.eu/resource/authority/corporate-body/COM":
        "European Commission",
    "http://publications.europa.eu/resource/authority/corporate-body/Council":
        "Council of the EU",
    "http://publications.europa.eu/resource/authority/corporate-body/ECB":
        "European Central Bank",
    "http://publications.europa.eu/resource/authority/corporate-body/UNECE":
        "UNECE",
    "http://publications.europa.eu/resource/authority/corporate-body/SANTE":
        "DG SANTE",
    "http://publications.europa.eu/resource/authority/corporate-body/GROW":
        "DG GROW",
    "http://publications.europa.eu/resource/authority/corporate-body/ENV":
        "DG ENV",
    "http://publications.europa.eu/resource/authority/corporate-body/ENER":
        "DG ENER",
    "http://publications.europa.eu/resource/authority/corporate-body/AGRI":
        "DG AGRI",
    "http://publications.europa.eu/resource/authority/corporate-body/CNECT":
        "DG CNECT",
    "http://publications.europa.eu/resource/authority/corporate-body/MOVE":
        "DG MOVE",
    "http://publications.europa.eu/resource/authority/corporate-body/CLIMA":
        "DG CLIMA",
    "http://publications.europa.eu/resource/authority/corporate-body/TAXUD":
        "DG TAXUD",
    "http://publications.europa.eu/resource/authority/corporate-body/COMP":
        "DG COMP",
    "http://publications.europa.eu/resource/authority/corporate-body/JUST":
        "DG JUST",
    "http://publications.europa.eu/resource/authority/corporate-body/HOME":
        "DG HOME",
}


def build_sparql_query():
    """
    Build a SPARQL query that fetches recent legal acts (regulations,
    directives, decisions) with CELEX numbers, English titles,
    legal types, authors, and publication dates.

    Uses keyword filtering via CONTAINS to focus on relevant sectors.
    The VALUES clause restricts to the main legal act types.
    """
    keyword_conditions = " ||\n    ".join(
        f'CONTAINS(LCASE(?title), "{kw}")'
        for kw in SECTOR_KEYWORDS
    )

    query = f"""
PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>

SELECT DISTINCT ?work ?celex ?title ?type ?date ?author WHERE {{
  VALUES ?type {{
    cdm:regulation cdm:directive cdm:decision
    cdm:regulation_delegated cdm:regulation_implementing
  }}
  ?work a ?type .
  ?work cdm:resource_legal_id_celex ?celex .
  ?work cdm:work_title ?title .
  FILTER(LANG(?title) = "en")
  ?work cdm:work_date_document ?date .
  OPTIONAL {{ ?work cdm:work_created_by_agent ?author . }}
  # Sector relevance filtering on title keywords
  FILTER({keyword_conditions})
}}
ORDER BY DESC(?date)
LIMIT {MAX_RESULTS}
"""
    return query.strip()


def query_sparql():
    """
    Send the SPARQL query to the EUR-Lex endpoint via POST with
    URL-encoded parameters (application/x-www-form-urlencoded).
    Returns parsed JSON response on success, raises on error.
    """
    query = build_sparql_query()
    params = urllib.parse.urlencode({"query": query})
    data = params.encode("utf-8")

    req = urllib.request.Request(
        SPARQL_ENDPOINT,
        data=data,
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/sparql-results+json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body)


def extract_type_label(type_uri):
    """Map a full type URI to a short human-readable label."""
    # Extract the fragment after # or the last path segment
    short = type_uri.rsplit("#", 1)[-1] if "#" in type_uri else type_uri
    short = short.rsplit("/", 1)[-1]
    # Look up in label map (exact match or suffix match only)
    if short in TYPE_LABELS:
        return TYPE_LABELS[short]
    # Try matching by suffix (e.g., "regulation_delegated" -> key "delegated_regulation")
    for key, label in TYPE_LABELS.items():
        if short == key or short.endswith(key) or key.endswith(short):
            return label
    # Clean up snake_case as fallback
    return short.replace("_", " ").title()


def extract_author_label(author_uri):
    """Map an author URI to a short human-readable label."""
    if not author_uri:
        return "Unknown"
    # Direct lookup
    if author_uri in AUTHOR_LABELS:
        return AUTHOR_LABELS[author_uri]
    # Extract code from URI path
    if "/authority/corporate-body/" in author_uri:
        code = author_uri.rsplit("/", 1)[-1]
        return code.replace("_", " ").title()
    # Extract last path segment as fallback
    short = author_uri.rstrip("/").rsplit("/", 1)[-1]
    return short.replace("_", " ").replace("-", " ").title() if short else "Unknown"


def process_results(data):
    """
    Process SPARQL JSON results into a list of unique entry dicts.
    Deduplicates by CELEX number (a CELEX may appear with multiple authors).
    Each entry has: celex, title, legal_type, author, pub_date, url, raw.
    """
    bindings = data.get("results", {}).get("bindings", [])
    seen_celex = set()
    entries = []

    for binding in bindings:
        celex = _binding_value(binding, "celex")
        if not celex or celex in seen_celex:
            continue
        seen_celex.add(celex)

        title = _binding_value(binding, "title")
        type_uri = _binding_value(binding, "type")
        author_uri = _binding_value(binding, "author")
        date_str = _binding_value(binding, "date")
        work_uri = _binding_value(binding, "work")

        legal_type = extract_type_label(type_uri) if type_uri else "Unknown"
        author = extract_author_label(author_uri) if author_uri else "Unknown"

        # Build EUR-Lex URL from CELEX
        url = f"https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:{celex}"

        # Normalize date to YYYY-MM-DD
        pub_date = date_str[:10] if date_str else None

        # Keep a clean raw record for the DB
        raw = {
            "celex": celex,
            "title": title,
            "type_uri": type_uri,
            "author_uri": author_uri,
            "author_label": author,
            "date": date_str,
            "work_uri": work_uri,
            "source": "eurlex_sparql",
            "collected_at": datetime.utcnow().isoformat(),
        }

        entries.append({
            "celex": celex,
            "title": title,
            "legal_type": legal_type,
            "author": author,
            "pub_date": pub_date,
            "url": url,
            "raw": raw,
        })

    return entries


def _binding_value(binding, key):
    """Safely extract a value from a SPARQL JSON results binding."""
    entry = binding.get(key)
    if entry is None:
        return ""
    return entry.get("value", "")


def store_entries(entries):
    """
    Store entries in the local SQLite cache via the eu_regulation_cache
    module's save_eurlex_entry function.

    save_eurlex_entry(celex, title, legal_type, author, pub_date,
                      eif, deadline, url, raw)
    - eif (entry_into_force) and deadline (transposition_deadline) are
      left as None since the SPARQL query doesn't provide them directly.
    """
    stored = 0
    errors = 0

    for entry in entries:
        try:
            save_eurlex_entry(
                celex=entry["celex"],
                title=entry["title"],
                legal_type=entry["legal_type"],
                author=entry["author"],
                pub_date=entry["pub_date"],
                eif=None,
                deadline=None,
                url=entry["url"],
                raw=entry["raw"],
            )
            stored += 1
        except Exception as e:
            print(f"  ⚠️  Error storing {entry.get('celex', '?')}: {e}")
            errors += 1

    return stored, errors


def print_report(entries, stored, errors, duration):
    """Print a summary report of the SPARQL collection run."""
    print(f"\n{'='*60}")
    print(f"  EUR-Lex SPARQL Collection Report")
    print(f"{'='*60}")
    print(f"  Timestamp:  {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"  Duration:   {duration:.1f}s")
    print(f"  Retrieved:  {len(entries)} unique results from SPARQL")
    print(f"  Stored:     {stored} entries in DB")

    if entries:
        print(f"\n  {'─'*58}")
        print(f"  {'CELEX':<18} {'Type':<22} {'Date':<12} {'Author'}")
        print(f"  {'─'*58}")
        for entry in entries[:10]:
            celex = entry["celex"][:16]
            typ = entry["legal_type"][:20]
            date = (entry["pub_date"] or "????-??-??")[:10]
            author = entry["author"][:18]
            print(f"  {celex:<18} {typ:<22} {date:<12} {author}")
        if len(entries) > 10:
            print(f"  ... and {len(entries) - 10} more")

    if errors:
        print(f"\n  ⚠️  {errors} storage error(s)")

    # Disclaimer
    print(f"\n  {'─'*58}")
    print(f"  ⚠️  DISCLAIMER: This data is collected from the EUR-Lex SPARQL")
    print(f"     endpoint (publications.europa.eu) for informational purposes")
    print(f"     only. It is not legal advice. Always consult the official")
    print(f"     EU legislation published on EUR-Lex for authoritative text.")
    print(f"{'='*60}")


def print_db_status():
    """Print current DB statistics and the most recent cached entries."""
    try:
        stats = db_stats()
        print(f"\n{'='*60}")
        print(f"  Database Status")
        print(f"{'='*60}")
        for table, count in sorted(stats.items()):
            print(f"  {table:<35} {count} entries")
        print(f"{'='*60}")

        # Show recent entries from eurlex_metadata
        conn = get_db()
        cur = conn.execute(
            "SELECT celex, title, legal_type, publication_date, author "
            "FROM eurlex_metadata ORDER BY publication_date DESC LIMIT 20"
        )
        rows = cur.fetchall()
        conn.close()

        if rows:
            print(f"\n  Recent EUR-Lex entries in cache:")
            print(f"  {'─'*68}")
            print(f"  {'CELEX':<18} {'Type':<22} {'Date':<12} {'Author'}")
            print(f"  {'─'*68}")
            for r in rows:
                celex = (r["celex"] or "?")[:16]
                typ = (r["legal_type"] or "?")[:20]
                date = (r["publication_date"] or "????-??-??")[:10]
                author = (r["author"] or "?")[:18]
                print(f"  {celex:<18} {typ:<22} {date:<12} {author}")
            print()
        else:
            print("\n  ℹ️  No EUR-Lex entries cached yet.\n")

    except Exception as e:
        print(f"  🔴 Error reading DB: {e}")


def check_endpoint_availability():
    """
    Quick availability check: send a minimal SPARQL query to see
    if the endpoint responds.
    """
    try:
        simple_query = urllib.parse.urlencode({
            "query": "SELECT ?s WHERE { ?s a ?type } LIMIT 1"
        })
        req = urllib.request.Request(
            SPARQL_ENDPOINT,
            data=simple_query.encode("utf-8"),
            headers={
                "User-Agent": USER_AGENT,
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/sparql-results+json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200, None
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return False, f"Connection failed: {e.reason}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def main():
    """Main entry point. Returns 0 on success, 1 on error."""
    args = set(sys.argv[1:])

    # ── Check / info mode ───────────────────────────────────────────────
    if "--check" in args or "--info" in args:
        print_db_status()
        return 0

    # ── Normal mode: fetch from SPARQL endpoint ────────────────────────
    print(f"\n  EUR-Lex SPARQL Collector")
    print(f"  {'─'*58}")
    print(f"  Endpoint:  {SPARQL_ENDPOINT}")
    print(f"  Timeout:   {TIMEOUT}s  |  Max results: {MAX_RESULTS}")
    print(f"  Sectors:   {', '.join(sorted(set(k.capitalize() for k in SECTOR_KEYWORDS[:6])))}...")
    print()

    # Quick availability check before the full query
    ok, err_msg = check_endpoint_availability()
    if not ok:
        print(f"  ⚠️  SPARQL endpoint not reachable ({err_msg}).")
        print(f"  ℹ️  Falling back to DB status report...")
        print_db_status()
        print(f"\n  ⚠️  Disclaimer: Cannot reach EUR-Lex SPARQL endpoint.")
        print(f"     Data shown above is from local cache only.")
        return 1

    # ── Execute SPARQL query ──────────────────────────────────────────
    start = datetime.utcnow()
    try:
        print(f"  Querying SPARQL endpoint...")
        data = query_sparql()
    except urllib.error.HTTPError as e:
        print(f"  🔴 HTTP Error {e.code}: {e.reason}")
        print(f"  ℹ️  Falling back to DB status report...")
        print_db_status()
        return 1
    except urllib.error.URLError as e:
        print(f"  🔴 Connection Error: {e.reason}")
        print(f"  ℹ️  Falling back to DB status report...")
        print_db_status()
        return 1
    except json.JSONDecodeError as e:
        print(f"  🔴 Invalid JSON response from SPARQL: {e}")
        print(f"  ℹ️  Falling back to DB status report...")
        print_db_status()
        return 1
    except Exception as e:
        print(f"  🔴 Unexpected error: {type(e).__name__}: {e}")
        print(f"  ℹ️  Falling back to DB status report...")
        print_db_status()
        return 1

    # ── Process results ───────────────────────────────────────────────
    entries = process_results(data)
    elapsed = (datetime.utcnow() - start).total_seconds()

    if not entries:
        print(f"  ℹ️  SPARQL returned 0 unique results (empty or all filtered out).")
        print(f"  ℹ️  Checking DB status...")
        print_db_status()
        return 0

    # ── Store in DB ───────────────────────────────────────────────────
    stored, errors = store_entries(entries)

    # ── Print report ──────────────────────────────────────────────────
    print_report(entries, stored, errors, elapsed)

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

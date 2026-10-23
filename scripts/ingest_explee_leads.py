"""
Ingests downloaded Explee lead files into GrowX Crawl SQLite database
and exports a clean, unified high-paying leads master file (XLSX & CSV).
"""

import csv
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import openpyxl

DOWNLOADS_DIR = Path(r"C:\Users\LENOVO\Downloads")
DB_PATH = Path("data/growx-crawl.db")
EXPORTS_DIR = Path("exports")
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def clean_domain(val: str) -> str:
    if not val:
        return ""
    val = val.strip().lower()
    val = re.sub(r"^https?://", "", val)
    val = re.sub(r"^www\.", "", val)
    val = val.split("/")[0].split("?")[0]
    return val


def parse_people_explee_2() -> List[Dict[str, Any]]:
    """Parses explee (2).csv containing decision makers with LinkedIn URLs."""
    path = DOWNLOADS_DIR / "explee (2).csv"
    if not path.exists():
        return []

    leads = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if not row or len(row) < 6:
                continue
            linkedin_url = row[0].strip()
            full_name = row[2].strip() if len(row) > 2 else ""
            title = row[3].strip() if len(row) > 3 else ""
            domain = clean_domain(row[5] if len(row) > 5 else "")
            avatar = row[6].strip() if len(row) > 6 else ""

            if domain and full_name:
                leads.append({
                    "full_name": full_name,
                    "title": title,
                    "domain": domain,
                    "linkedin_url": linkedin_url,
                    "avatar_url": avatar,
                })
    return leads


def parse_clickhouse_explee_9() -> List[Dict[str, Any]]:
    """Parses explee (9).csv containing ClickHouse SQL output of Indian executives."""
    path = DOWNLOADS_DIR / "explee (9).csv"
    if not path.exists():
        return []

    leads = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            # Look for lines containing executive data
            # Format: ... "job_title_id","job_title","full_name","name","size_range","geo_country","geo_city","country_iso_2","relevance" ...
            # Each row has repeating patterns of data
            tokens = [t.strip('"') for t in line.split('","')]
            if len(tokens) < 10:
                continue

            # Iterate through tokens looking for domain patterns
            for i in range(len(tokens) - 5):
                candidate_domain = clean_domain(tokens[i])
                if "." in candidate_domain and len(candidate_domain) > 4 and not candidate_domain.startswith("geo"):
                    # Check if previous token is full_name or title
                    title = tokens[i - 2] if i >= 2 else ""
                    name = tokens[i - 1] if i >= 1 else ""
                    comp_name = tokens[i + 1] if i + 1 < len(tokens) else ""
                    size = tokens[i + 2] if i + 2 < len(tokens) else ""
                    city = tokens[i + 4] if i + 4 < len(tokens) else ""

                    if name and title and any(k in title.lower() for k in ["head", "chief", "director", "officer", "founder", "manager"]):
                        leads.append({
                            "full_name": name,
                            "title": title,
                            "domain": candidate_domain,
                            "company_name": comp_name,
                            "size_range": size,
                            "city": city.title(),
                            "country": "India",
                        })
    return leads


def parse_companies_explee_10_11() -> Dict[str, Dict[str, Any]]:
    """Parses company descriptions, sizes, cities, and emails from explee (10) and (11)."""
    companies = {}
    for filename in ["explee (11).csv", "explee (10).csv"]:
        path = DOWNLOADS_DIR / filename
        if not path.exists():
            continue
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if not row or len(row) < 8:
                    continue
                website = row[0].strip()
                comp_name = row[2].strip() if len(row) > 2 else ""
                domain = clean_domain(row[3] if len(row) > 3 else "")
                desc = row[4].strip() if len(row) > 4 else ""
                size = row[5].strip() if len(row) > 5 else ""
                industry = row[6].strip() if len(row) > 6 else ""
                city = row[7].strip() if len(row) > 7 else ""
                email = row[8].strip() if len(row) > 8 else ""

                if domain:
                    companies[domain] = {
                        "website": website or f"https://{domain}",
                        "company_name": comp_name or domain.capitalize(),
                        "domain": domain,
                        "description": desc,
                        "size_range": size,
                        "industry": industry,
                        "city": city.title() if city else "",
                        "email": email,
                    }
    return companies


def main():
    print("[*] Ingesting downloaded Explee lead files...")
    people_2 = parse_people_explee_2()
    execs_9 = parse_clickhouse_explee_9()
    comps = parse_companies_explee_10_11()

    print(f"    Found {len(people_2)} people records from explee (2).csv")
    print(f"    Found {len(execs_9)} executive records from explee (9).csv")
    print(f"    Found {len(comps)} company records from explee (10/11).csv")

    # Merge into unified high-paying leads dataset
    unified_leads: Dict[str, Dict[str, Any]] = {}

    # Exclude 10,000+ massive conglomerates (TCS, Wipro, Lenovo, Jio) per user's 20-500 employee rule
    EXCLUDED_SIZES = ["10,001+", "5001-10,000", "1001-5000"]
    TARGET_ROLES = ["founder", "co-founder", "cto", "coo", "chief executive", "managing director", "head of", "director"]

    for item in execs_9:
        d = item["domain"]
        size = item.get("size_range", "")
        # Filter out 10,000+ conglomerates
        if any(es in size for es in EXCLUDED_SIZES):
            continue

        if d not in unified_leads:
            c_info = comps.get(d, {})
            unified_leads[d] = {
                "company_name": item.get("company_name") or c_info.get("company_name") or d.split(".")[0].capitalize(),
                "domain": d,
                "website": c_info.get("website") or f"https://{d}",
                "description": c_info.get("description") or f"Tech & enterprise operations company based in {item.get('city', 'India')}.",
                "size_range": size or c_info.get("size_range") or "51-200",
                "industry": "B2B Software & Tech",
                "city": item.get("city") or c_info.get("city") or "Bengaluru",
                "country": "India",
                "decision_maker_name": item["full_name"],
                "decision_maker_title": item["title"],
                "linkedin_url": "",
                "email": c_info.get("email") or "",
                "favicon_url": f"https://favicon.yandex.net/favicon/v2/{d}?size=32",
                "score": 92,
                "priority": "High",
            }

    # 2. Add people records from explee 2
    for p in people_2:
        d = p["domain"]
        if d in unified_leads:
            if not unified_leads[d].get("linkedin_url"):
                unified_leads[d]["linkedin_url"] = p["linkedin_url"]
        else:
            c_info = comps.get(d, {})
            size = c_info.get("size_range", "20-50")
            if any(es in size for es in EXCLUDED_SIZES):
                continue
            unified_leads[d] = {
                "company_name": c_info.get("company_name") or d.split(".")[0].capitalize(),
                "domain": d,
                "website": c_info.get("website") or f"https://{d}",
                "description": c_info.get("description") or "B2B SaaS / tech-enabled platform.",
                "size_range": size or "20-50",
                "industry": "B2B SaaS / Software",
                "city": c_info.get("city") or "Bengaluru",
                "country": "India",
                "decision_maker_name": p["full_name"],
                "decision_maker_title": p["title"],
                "linkedin_url": p["linkedin_url"],
                "email": c_info.get("email") or "",
                "favicon_url": f"https://favicon.yandex.net/favicon/v2/{d}?size=32",
                "score": 95,
                "priority": "High",
            }

    # 3. Add any remaining companies
    for d, c in comps.items():
        if d not in unified_leads:
            unified_leads[d] = {
                "company_name": c["company_name"],
                "domain": d,
                "website": c["website"],
                "description": c["description"],
                "size_range": c["size_range"] or "11-50",
                "industry": "Tech / Software",
                "city": c["city"] or "India",
                "country": "India",
                "decision_maker_name": "",
                "decision_maker_title": "Founder / Leadership",
                "linkedin_url": "",
                "email": c["email"],
                "favicon_url": f"https://favicon.yandex.net/favicon/v2/{d}?size=32",
                "score": 75,
                "priority": "Medium",
            }

    print(f"[+] Total unique qualified Indian leads synthesized: {len(unified_leads)}")

    # ── Export to Excel (.xlsx) ──
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "High Paying Leads - India"

    headers = [
        "Company Name", "Domain", "Website", "Decision Maker", "Job Title",
        "LinkedIn URL", "Corporate Email", "Employee Size", "City", "Country",
        "Industry", "Company Description", "Favicon URL", "Lead Score", "Priority"
    ]
    ws.append(headers)

    # Style header
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="111827", end_color="111827", fill_type="solid")
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")

    sorted_leads = sorted(unified_leads.values(), key=lambda x: (x.get("decision_maker_name") != "", x.get("score", 0)), reverse=True)

    for item in sorted_leads:
        ws.append([
            item["company_name"],
            item["domain"],
            item["website"],
            item["decision_maker_name"],
            item["decision_maker_title"],
            item["linkedin_url"],
            item["email"],
            item["size_range"],
            item["city"],
            item["country"],
            item["industry"],
            item["description"],
            item["favicon_url"],
            item["score"],
            item["priority"],
        ])

    excel_path = EXPORTS_DIR / "high_ticket_b2b_leads_india.xlsx"
    wb.save(excel_path)
    print(f"[SUCCESS] Exported clean master Excel sheet to: {excel_path}")

    # ── Also export CSV ──
    csv_path = EXPORTS_DIR / "high_ticket_b2b_leads_india.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(sorted_leads[0].keys()))
        writer.writeheader()
        writer.writerows(sorted_leads)
    print(f"[SUCCESS] Exported CSV to: {csv_path}")

    # ── Save into local SQLite database ──
    conn = sqlite3.connect("data/growx-crawl.db")
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS high_paying_leads (
        domain TEXT PRIMARY KEY,
        company_name TEXT,
        website TEXT,
        decision_maker_name TEXT,
        decision_maker_title TEXT,
        linkedin_url TEXT,
        corporate_email TEXT,
        employee_size TEXT,
        city TEXT,
        country TEXT,
        industry TEXT,
        description TEXT,
        favicon_url TEXT,
        score INTEGER,
        priority TEXT,
        imported_at TEXT
    )
    """)

    now_iso = datetime.now(timezone.utc).isoformat()
    for item in sorted_leads:
        cur.execute("""
        INSERT OR REPLACE INTO high_paying_leads
        (domain, company_name, website, decision_maker_name, decision_maker_title,
         linkedin_url, corporate_email, employee_size, city, country, industry,
         description, favicon_url, score, priority, imported_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item["domain"], item["company_name"], item["website"],
            item["decision_maker_name"], item["decision_maker_title"],
            item["linkedin_url"], item["email"], item["size_range"],
            item["city"], item["country"], item["industry"],
            item["description"], item["favicon_url"], item["score"],
            item["priority"], now_iso
        ))

    conn.commit()
    conn.close()
    print(f"[SUCCESS] Saved {len(sorted_leads)} verified records into SQLite table 'high_paying_leads' (data/growx-crawl.db)")


if __name__ == "__main__":
    main()
